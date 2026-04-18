import json
import re

from django.http import JsonResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.core.models import APIToken, Platform
from apps.incidents.models import Incident


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

        from apps.core.models import Organization, OrganizationMembership, Project

        try:
            org = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            return JsonResponse({"error": "Organization not found"}, status=404)

        # Check membership
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

        # Auto-detect platform from URL if not provided
        platform = None
        if platform_name:
            platform = Platform.objects.filter(project=project, name=platform_name).first()
        if not platform and url:
            for p in Platform.objects.filter(project=project).exclude(url_pattern=""):
                if p.url_pattern and re.search(p.url_pattern, url):
                    platform = p
                    break

        incident = Incident(
            project=project,
            organization=org,
            collected_by=request.user,
            url=url,
            platform=platform,
            status=Incident.Status.DRAFT,
            notes=request.POST.get("title", ""),
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
        }, status=201)
