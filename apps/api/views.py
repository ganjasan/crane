import json
import re

from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.models import APIToken, KeywordCategory, Language, OrganizationMembership, Platform, Project
from apps.coverage.models import SearchSession
from apps.incidents.models import Incident
from apps.incidents.utils import normalize_url
from apps.keywords.models import Keyword


def token_required(view_func):
    """Authenticate via Authorization: Bearer <token> header."""

    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)

        key = auth_header[7:].strip()
        try:
            api_token = APIToken.objects.select_related("user").get(key=key)
        except APIToken.DoesNotExist:
            return JsonResponse({"error": "Invalid API token"}, status=401)

        request.user = api_token.user
        return view_func(request, *args, **kwargs)

    return wrapper


def _user_projects_qs(user):
    if user.is_superuser:
        return Project.objects.select_related("organization")
    return (
        Project.objects.filter(
            Q(memberships__user=user)
            | Q(
                organization__memberships__user=user,
                organization__memberships__role__in=[
                    OrganizationMembership.Role.OWNER,
                    OrganizationMembership.Role.ADMIN,
                ],
            )
        )
        .select_related("organization")
        .distinct()
    )


def _user_can_access_project(user, project):
    if user.is_superuser:
        return True
    return _user_projects_qs(user).filter(pk=project.pk).exists()


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(token_required, name="dispatch")
class IncidentCaptureView(View):
    """POST /api/v1/incidents/capture
    Accepts: url, platform (name), title, screenshot (file), project_slug, org_slug.
    Creates a draft incident. Returns incident ID + annotation form URL.
    """

    def post(self, request, *args, **kwargs):
        org_slug = request.POST.get("org_slug") or request.GET.get("org_slug")
        project_slug = request.POST.get("project_slug") or request.GET.get("project_slug")

        if not org_slug or not project_slug:
            return JsonResponse(
                {"error": "org_slug and project_slug are required"}, status=400
            )

        from apps.core.models import Organization

        try:
            org = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            return JsonResponse({"error": "Organization not found"}, status=404)

        if not request.user.is_superuser:
            if not OrganizationMembership.objects.filter(
                user=request.user, organization=org
            ).exists():
                return JsonResponse({"error": "Not a member of this organization"}, status=403)

        try:
            project = Project.objects.get(organization=org, slug=project_slug)
        except Project.DoesNotExist:
            return JsonResponse({"error": "Project not found"}, status=404)

        url = request.POST.get("url", "")
        platform_name = request.POST.get("platform", "")
        screenshot = request.FILES.get("screenshot")

        platform = None
        if platform_name:
            platform = Platform.objects.filter(project=project, name=platform_name).first()
        if not platform and url:
            for p in Platform.objects.filter(project=project).exclude(url_pattern=""):
                if p.url_pattern and re.search(p.url_pattern, url):
                    platform = p
                    break

        language = request.POST.get("language", "")
        note = request.POST.get("note") or request.POST.get("title", "")

        incident = Incident(
            project=project,
            organization=org,
            collected_by=request.user,
            url=url,
            platform=platform,
            language=language,
            status=Incident.Status.DRAFT,
            notes=note,
        )
        if screenshot:
            incident.screenshot = screenshot
        incident.save()

        form_url = reverse(
            "incident_edit",
            kwargs={
                "org_slug": org.slug,
                "project_slug": project.slug,
                "pk": incident.pk,
            },
        )

        return JsonResponse({
            "id": incident.pk,
            "record_id": incident.record_id,
            "form_url": request.build_absolute_uri(form_url),
            "duplicate_of": (
                {"id": incident.duplicate_of.pk, "record_id": incident.duplicate_of.record_id}
                if incident.duplicate_of else None
            ),
        }, status=201)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(token_required, name="dispatch")
class IncidentCheckView(View):
    """POST /api/v1/incidents/check
    Body: { "urls": [...], "project_id": "<uuid>" }
    Returns per-URL duplicate status against `url_normalized` in the given project.
    """

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)

        urls = body.get("urls") or []
        project_id = body.get("project_id")

        if not isinstance(urls, list) or not project_id:
            return JsonResponse({"error": "urls (list) and project_id are required"}, status=400)

        try:
            project = Project.objects.get(pk=project_id)
        except (Project.DoesNotExist, ValueError):
            return JsonResponse({"error": "Project not found"}, status=404)

        if not _user_can_access_project(request.user, project):
            return JsonResponse({"error": "Forbidden"}, status=403)

        normalized_to_originals: dict[str, list[str]] = {}
        for raw in urls[:200]:  # cap at 200 per request
            if not isinstance(raw, str):
                continue
            n = normalize_url(raw)
            normalized_to_originals.setdefault(n, []).append(raw)

        existing = {
            i.url_normalized: i
            for i in Incident.objects.filter(
                project=project, url_normalized__in=list(normalized_to_originals)
            ).only("pk", "record_id", "url_normalized", "collected_by_id", "date_collected")
            if i.url_normalized
        }

        results: dict[str, dict] = {}
        for normalized, originals in normalized_to_originals.items():
            inc = existing.get(normalized)
            payload = (
                {
                    "duplicate": True,
                    "record_id": inc.record_id,
                    "id": inc.pk,
                    "captured_at": inc.date_collected.isoformat(),
                }
                if inc else
                {"duplicate": False, "record_id": None}
            )
            for original in originals:
                results[original] = payload

        return JsonResponse({"results": results}, status=200)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(token_required, name="dispatch")
class ProjectListView(View):
    """GET /api/v1/projects
    Returns the authenticated user's accessible projects with their language list.
    """

    def get(self, request, *args, **kwargs):
        projects = _user_projects_qs(request.user).order_by("organization__name", "name")
        seen = set()
        out = []
        for project in projects:
            if project.pk in seen:
                continue
            seen.add(project.pk)
            out.append({
                "id": str(project.pk),
                "name": project.name,
                "slug": project.slug,
                "org_name": project.organization.name,
                "org_slug": project.organization.slug,
                "languages": [
                    {"code": l.code, "name": l.name}
                    for l in Language.objects.filter(project=project).order_by("name")
                ],
            })
        return JsonResponse({"projects": out}, status=200)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(token_required, name="dispatch")
class CoverageSuggestView(View):
    """GET /api/v1/coverage/suggest?project_id=<uuid>
    Returns top-3 stalest (Platform, Language, KeywordCategory) cells.
    """

    def get(self, request, *args, **kwargs):
        project_id = request.GET.get("project_id")
        if not project_id:
            return JsonResponse({"error": "project_id is required"}, status=400)

        try:
            project = Project.objects.get(pk=project_id)
        except (Project.DoesNotExist, ValueError):
            return JsonResponse({"error": "Project not found"}, status=404)

        if not _user_can_access_project(request.user, project):
            return JsonResponse({"error": "Forbidden"}, status=403)

        platforms = list(Platform.objects.filter(project=project).order_by("name"))
        languages = list(Language.objects.filter(project=project).order_by("name"))
        categories = list(KeywordCategory.objects.filter(project=project).order_by("name"))

        if not (platforms and languages and categories):
            return JsonResponse({"suggestions": []}, status=200)

        # Build last-search map for each (platform_id, language_lower, category_slug) cell
        sessions = SearchSession.objects.filter(project=project).values(
            "platform_id", "language", "keyword_categories", "date"
        )
        last_seen: dict[tuple, object] = {}
        for s in sessions:
            for cat_slug in (s.get("keyword_categories") or []):
                key = (s["platform_id"], (s["language"] or "").lower(), cat_slug)
                prev = last_seen.get(key)
                if prev is None or s["date"] > prev:
                    last_seen[key] = s["date"]

        # Build the full cell grid; rank by stalest (None ranks first)
        cells = []
        for p in platforms:
            for lang in languages:
                for cat in categories:
                    key = (p.pk, (lang.code or lang.name).lower(), cat.slug)
                    cells.append({
                        "platform": p,
                        "language": lang,
                        "category": cat,
                        "last_searched": last_seen.get(key),
                    })

        cells.sort(key=lambda c: (c["last_searched"] is not None, c["last_searched"] or 0))

        suggestions = []
        for cell in cells[:3]:
            example_keyword = (
                Keyword.objects.filter(
                    project=project,
                    category=cell["category"],
                    status=Keyword.Status.ACTIVE,
                )
                .values_list("term", flat=True)
                .first()
            )
            suggestions.append({
                "platform": cell["platform"].name,
                "language": cell["language"].name,
                "language_code": cell["language"].code,
                "category": cell["category"].name,
                "category_slug": cell["category"].slug,
                "last_searched": (
                    cell["last_searched"].isoformat() if cell["last_searched"] else None
                ),
                "example_keyword": example_keyword,
                "search_url": _construct_search_url(cell["platform"], example_keyword),
            })

        return JsonResponse({"suggestions": suggestions}, status=200)


_PLATFORM_SEARCH_TEMPLATES = {
    "telegram": "https://t.me/s/?q={q}",
    "vkontakte": "https://vk.com/search?c[q]={q}&c[section]=auto",
    "vk": "https://vk.com/search?c[q]={q}&c[section]=auto",
    "facebook": "https://www.facebook.com/search/posts/?q={q}",
}


def _construct_search_url(platform, keyword):
    if not keyword:
        return None
    from urllib.parse import quote_plus

    name_lc = platform.name.lower()
    template = _PLATFORM_SEARCH_TEMPLATES.get(name_lc)
    if template:
        return template.format(q=quote_plus(keyword))
    # Fallback: Google site:domain search if url_pattern looks like a domain
    if platform.url_pattern:
        domain_match = re.search(r"([a-z0-9-]+\.[a-z]{2,})", platform.url_pattern, re.I)
        if domain_match:
            return f"https://www.google.com/search?q=site%3A{domain_match.group(1)}+{quote_plus(keyword)}"
    return None
