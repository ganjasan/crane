from django.urls import path

from . import views

urlpatterns = [
    path("", views.KeywordListView.as_view(), name="keyword_list"),
    path("new/", views.KeywordCreateView.as_view(), name="keyword_create"),
    path("<int:pk>/edit/", views.KeywordEditView.as_view(), name="keyword_edit"),
    path("<int:pk>/status/", views.KeywordStatusView.as_view(), name="keyword_status"),
    path("import/", views.KeywordBulkImportView.as_view(), name="keyword_import"),
]
