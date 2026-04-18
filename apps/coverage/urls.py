from django.urls import path

from . import views

urlpatterns = [
    path("", views.CoverageMatrixView.as_view(), name="coverage_matrix"),
    path("log/", views.SearchSessionLogView.as_view(), name="coverage_log"),
    path("activity/", views.VolunteerActivityView.as_view(), name="volunteer_activity"),
]
