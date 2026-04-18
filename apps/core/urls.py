from django.contrib.auth.views import LoginView, LogoutView
from django.urls import include, path

from . import views

urlpatterns = [
    # Root
    path("", views.OrgSelectorView.as_view(), name="org_selector"),
    # Auth (under /auth/ — exempt from OrgProjectMiddleware)
    path(
        "auth/login/",
        LoginView.as_view(
            template_name="auth/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path(
        "auth/invite/<str:token>/",
        views.InviteAcceptView.as_view(),
        name="invite_accept",
    ),
    path(
        "auth/account/",
        views.AccountSettingsView.as_view(),
        name="account_settings",
    ),
    # Org creation (must be before <slug:org_slug> catch-all)
    path("orgs/new/", views.OrgCreateView.as_view(), name="org_create"),
    # Org-scoped
    path(
        "<slug:org_slug>/",
        views.OrgDashboardView.as_view(),
        name="org_dashboard",
    ),
    path(
        "<slug:org_slug>/settings/",
        views.OrgSettingsView.as_view(),
        name="org_settings",
    ),
    path(
        "<slug:org_slug>/members/",
        views.OrgMembersView.as_view(),
        name="org_members",
    ),
    path(
        "<slug:org_slug>/projects/new/",
        views.ProjectCreateView.as_view(),
        name="project_create",
    ),
    path(
        "<slug:org_slug>/<slug:project_slug>/",
        views.ProjectDashboardView.as_view(),
        name="project_dashboard",
    ),
    path(
        "<slug:org_slug>/<slug:project_slug>/settings/",
        views.ProjectSettingsView.as_view(),
        name="project_settings",
    ),
    path(
        "<slug:org_slug>/<slug:project_slug>/settings/import/",
        views.SeedImportView.as_view(),
        name="seed_import",
    ),
    path(
        "<slug:org_slug>/<slug:project_slug>/members/",
        views.ProjectMembersView.as_view(),
        name="project_members",
    ),
    # Project-scoped app URLs
    path(
        "<slug:org_slug>/<slug:project_slug>/incidents/",
        include("apps.incidents.urls"),
    ),
    path(
        "<slug:org_slug>/<slug:project_slug>/keywords/",
        include("apps.keywords.urls"),
    ),
    path(
        "<slug:org_slug>/<slug:project_slug>/coverage/",
        include("apps.coverage.urls"),
    ),
]
