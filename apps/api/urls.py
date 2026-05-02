from django.urls import path

from . import views

urlpatterns = [
    path(
        "v1/incidents/capture",
        views.IncidentCaptureView.as_view(),
        name="api_incident_capture",
    ),
    path(
        "v1/incidents/check",
        views.IncidentCheckView.as_view(),
        name="api_incident_check",
    ),
    path(
        "v1/projects",
        views.ProjectListView.as_view(),
        name="api_project_list",
    ),
    path(
        "v1/coverage/suggest",
        views.CoverageSuggestView.as_view(),
        name="api_coverage_suggest",
    ),
]
