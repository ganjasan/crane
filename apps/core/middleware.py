import re

from django.http import Http404
from django.urls import resolve

from .models import Organization, OrganizationMembership, Project, ProjectMembership

# URL patterns that bypass org/project resolution
EXEMPT_PATTERNS = [
    re.compile(r"^/auth/"),
    re.compile(r"^/admin/"),
    re.compile(r"^/api/"),
    re.compile(r"^/static/"),
    re.compile(r"^/media/"),
    re.compile(r"^/$"),
]


class OrgProjectMiddleware:
    """
    Resolve organization and project from URL pattern:
      /{org-slug}/                    → request.organization
      /{org-slug}/{project-slug}/...  → request.organization + request.project

    Enforces membership: user must belong to org (and project if in URL).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organization = None
        request.project = None

        path = request.path

        # Skip exempt paths
        for pattern in EXEMPT_PATTERNS:
            if pattern.match(path):
                return self.get_response(request)

        # Skip if user not authenticated
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Try to resolve org-slug and project-slug from URL kwargs
        try:
            match = resolve(path)
        except Exception:
            return self.get_response(request)

        org_slug = match.kwargs.get("org_slug")
        project_slug = match.kwargs.get("project_slug")

        if org_slug:
            try:
                org = Organization.objects.get(slug=org_slug)
            except Organization.DoesNotExist:
                raise Http404

            # Superusers bypass membership check
            if not request.user.is_superuser:
                if not OrganizationMembership.objects.filter(
                    user=request.user, organization=org
                ).exists():
                    raise Http404

            request.organization = org
            request.org_membership = OrganizationMembership.objects.filter(
                user=request.user, organization=org
            ).first()

        if project_slug and request.organization:
            try:
                project = Project.objects.get(
                    slug=project_slug, organization=request.organization
                )
            except Project.DoesNotExist:
                raise Http404

            if not request.user.is_superuser:
                org_role = getattr(request, "org_membership", None)
                is_org_admin = org_role and org_role.role in (
                    OrganizationMembership.Role.OWNER,
                    OrganizationMembership.Role.ADMIN,
                )
                if not is_org_admin:
                    if not ProjectMembership.objects.filter(
                        user=request.user, project=project
                    ).exists():
                        raise Http404

            request.project = project
            request.project_membership = ProjectMembership.objects.filter(
                user=request.user, project=project
            ).first()

        return self.get_response(request)
