from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import OrganizationMembership, ProjectMembership


class OrgRequiredMixin(LoginRequiredMixin):
    """Ensures request.organization is set."""

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, "organization", None):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ProjectRequiredMixin(OrgRequiredMixin):
    """Ensures request.project is set."""

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, "project", None):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class RequireOrgRole(OrgRequiredMixin):
    """Requires a minimum org role. Set `required_org_roles` on the view."""

    required_org_roles = [
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
    ]

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_superuser:
            return response
        membership = getattr(request, "org_membership", None)
        if not membership or membership.role not in self.required_org_roles:
            raise PermissionDenied
        return response


class RequireProjectRole(ProjectRequiredMixin):
    """Requires a minimum project role. Set `required_project_roles` on the view."""

    required_project_roles = [ProjectMembership.Role.COORDINATOR]

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_superuser:
            return response
        # Org owners/admins have full project access
        org_membership = getattr(request, "org_membership", None)
        if org_membership and org_membership.role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        ):
            return response
        proj_membership = getattr(request, "project_membership", None)
        if not proj_membership or proj_membership.role not in self.required_project_roles:
            raise PermissionDenied
        return response
