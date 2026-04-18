from django.urls import path

from . import views

urlpatterns = [
    path(
        "v1/incidents/capture",
        views.IncidentCaptureView.as_view(),
        name="api_incident_capture",
    ),
]
