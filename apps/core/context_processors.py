from django.urls import reverse

from .models import OrganizationMembership
from .nav import build_org_nav, build_project_nav


def user_organizations(request):
    if request.user.is_authenticated:
        memberships = (
            OrganizationMembership.objects.filter(user=request.user)
            .select_related("organization")
            .order_by("organization__name")
        )
        return {"user_org_memberships": memberships}
    return {}


def sidebar_nav(request):
    """Inject sidebar navigation context for `base_app.html`.

    Provides:
      - sidebar_nav_items: list[NavItem]
      - sidebar_scope: "org" | "project" | None
      - sidebar_workspace_label: str (e.g. project name when in project scope)
      - sidebar_workspace_sub: str | None (e.g. org name shown under project)
      - sidebar_back_url: str | None (link out of project scope back to org)
    """
    if not request.user.is_authenticated:
        return {}

    organization = getattr(request, "organization", None)
    project = getattr(request, "project", None)

    if project and organization:
        return {
            "sidebar_nav_items": build_project_nav(request, organization, project),
            "sidebar_scope": "project",
            "sidebar_workspace_label": project.name,
            "sidebar_workspace_sub": organization.name,
            "sidebar_back_url": reverse(
                "org_dashboard", kwargs={"org_slug": organization.slug}
            ),
        }

    if organization:
        return {
            "sidebar_nav_items": build_org_nav(request, organization),
            "sidebar_scope": "org",
            "sidebar_workspace_label": organization.name,
            "sidebar_workspace_sub": None,
            "sidebar_back_url": None,
        }

    return {
        "sidebar_nav_items": [],
        "sidebar_scope": None,
        "sidebar_workspace_label": None,
        "sidebar_workspace_sub": None,
        "sidebar_back_url": None,
    }
