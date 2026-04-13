from django.contrib import admin

from .models import SearchSession


@admin.register(SearchSession)
class SearchSessionAdmin(admin.ModelAdmin):
    list_display = ("volunteer", "platform", "language", "date", "incidents_found", "duration_minutes")
    list_filter = ("platform", "language", "date", "project")
    search_fields = ("notes",)
