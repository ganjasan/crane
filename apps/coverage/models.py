from django.conf import settings
from django.db import models

from apps.core.models import OrgScopedManager, Platform, Project


class SearchSession(models.Model):
    objects = OrgScopedManager()
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="search_sessions"
    )
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="search_sessions"
    )
    platform = models.ForeignKey(
        Platform, on_delete=models.CASCADE, related_name="search_sessions"
    )
    language = models.CharField(max_length=100)
    keyword_categories = models.JSONField(
        default=list, help_text="List of keyword category slugs covered in this session"
    )
    date = models.DateField()
    duration_minutes = models.IntegerField(null=True, blank=True)
    incidents_found = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.volunteer} — {self.platform} ({self.language}) — {self.date}"
