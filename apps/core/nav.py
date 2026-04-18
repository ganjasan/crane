"""Sidebar navigation tree builders.

Pure functions that produce the sidebar nav data structure based on the
current request and the org/project resolved by ``OrgProjectMiddleware``.
The sidebar template iterates the resulting list — no URL-name comparisons
inline in templates.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from django.urls import reverse


@dataclass
class NavItem:
    label: str
    url: str
    icon_name: str
    active_url_names: list[str] = field(default_factory=list)
    active: bool = False


def _resolve_active(items: list[NavItem], current_url_name: str | None) -> list[NavItem]:
    if not current_url_name:
        return items
    for item in items:
        if current_url_name in item.active_url_names:
            item.active = True
    return items


def build_org_nav(request, organization) -> list[NavItem]:
    slug = organization.slug
    items = [
        NavItem(
            label="Dashboard",
            url=reverse("org_dashboard", kwargs={"org_slug": slug}),
            icon_name="home",
            active_url_names=["org_dashboard"],
        ),
        NavItem(
            label="Members",
            url=reverse("org_members", kwargs={"org_slug": slug}),
            icon_name="users",
            active_url_names=["org_members"],
        ),
        NavItem(
            label="Settings",
            url=reverse("org_settings", kwargs={"org_slug": slug}),
            icon_name="settings",
            active_url_names=["org_settings"],
        ),
    ]
    current = getattr(getattr(request, "resolver_match", None), "url_name", None)
    return _resolve_active(items, current)


def build_project_nav(request, organization, project) -> list[NavItem]:
    kwargs = {"org_slug": organization.slug, "project_slug": project.slug}
    items = [
        NavItem(
            label="Dashboard",
            url=reverse("project_dashboard", kwargs=kwargs),
            icon_name="home",
            active_url_names=["project_dashboard"],
        ),
        NavItem(
            label="Incidents",
            url=reverse("incident_list", kwargs=kwargs),
            icon_name="file-text",
            active_url_names=[
                "incident_list",
                "incident_detail",
                "incident_create",
                "incident_edit",
                "incident_status",
            ],
        ),
        NavItem(
            label="Keywords",
            url=reverse("keyword_list", kwargs=kwargs),
            icon_name="tag",
            active_url_names=[
                "keyword_list",
                "keyword_create",
                "keyword_edit",
                "keyword_status",
                "keyword_import",
            ],
        ),
        NavItem(
            label="Coverage",
            url=reverse("coverage_matrix", kwargs=kwargs),
            icon_name="grid",
            active_url_names=[
                "coverage_matrix",
                "coverage_log",
                "volunteer_activity",
            ],
        ),
        NavItem(
            label="Members",
            url=reverse("project_members", kwargs=kwargs),
            icon_name="users",
            active_url_names=["project_members"],
        ),
        NavItem(
            label="Settings",
            url=reverse("project_settings", kwargs=kwargs),
            icon_name="settings",
            active_url_names=["project_settings", "seed_import"],
        ),
    ]
    current = getattr(getattr(request, "resolver_match", None), "url_name", None)
    return _resolve_active(items, current)
