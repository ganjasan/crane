from django.urls import path

from . import views

urlpatterns = [
    path("", views.IncidentListView.as_view(), name="incident_list"),
    path("new/", views.IncidentCreateView.as_view(), name="incident_create"),
    path("export/", views.IncidentExportView.as_view(), name="incident_export"),
    path("<int:pk>/", views.IncidentDetailView.as_view(), name="incident_detail"),
    path("<int:pk>/edit/", views.IncidentEditView.as_view(), name="incident_edit"),
    path(
        "<int:pk>/status/",
        views.IncidentStatusView.as_view(),
        name="incident_status",
    ),
]
