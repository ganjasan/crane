from django.conf import settings
from django.db import models

from apps.core.models import KeywordCategory, OrgScopedManager, Organization, Project


class Keyword(models.Model):
    objects = OrgScopedManager()
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DEPRECATED = "deprecated", "Deprecated"
        CANDIDATE = "candidate", "Candidate"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="keywords"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="keywords"
    )
    term = models.CharField(max_length=500)
    language = models.CharField(max_length=100)
    category = models.ForeignKey(
        KeywordCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="keywords"
    )
    platform_relevance = models.JSONField(
        default=list, blank=True, help_text="List of platform names where this keyword is effective"
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="keywords_added"
    )
    date_added = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    shared = models.BooleanField(
        default=False, help_text="Visible to all projects in the same organization"
    )

    class Meta:
        ordering = ["-date_added"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "term", "language"],
                name="unique_keyword_per_project_lang",
            )
        ]

    @property
    def match_count(self):
        return self.incidents.count()

    def __str__(self):
        return f"{self.term} ({self.language})"
