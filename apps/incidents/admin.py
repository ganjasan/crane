from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("record_id", "project", "platform", "status", "confidence", "collected_by", "date_collected")
    list_filter = ("status", "confidence", "project", "platform")
    search_fields = ("record_id", "url", "notes", "location_mentioned")
    readonly_fields = ("record_id", "date_collected")
