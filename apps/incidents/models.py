from django.conf import settings
from django.db import models

from apps.core.models import Organization, Platform, Project, ProjectSettings


class Incident(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        REVIEWED = "reviewed", "Reviewed"
        FLAGGED = "flagged", "Flagged"

    class Confidence(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="incidents"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="incidents"
    )

    # Auto-generated, unique per project
    record_id = models.CharField(max_length=50, editable=False)

    # Core fields
    platform = models.ForeignKey(
        Platform, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents"
    )
    url = models.URLField(max_length=2048, blank=True)
    screenshot = models.ImageField(upload_to="screenshots/%Y/%m/", blank=True)
    date_of_post = models.DateField(null=True, blank=True)
    date_collected = models.DateTimeField(auto_now_add=True)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="incidents"
    )
    location_mentioned = models.CharField(max_length=255, blank=True)
    probable_location = models.CharField(max_length=255, blank=True)
    language = models.CharField(max_length=100, blank=True)
    confidence = models.CharField(
        max_length=10, choices=Confidence.choices, blank=True
    )
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    # Domain-specific fields (configured per project)
    extra_fields = models.JSONField(default=dict, blank=True)

    # Keywords matched (M2M to keywords app)
    keywords_matched = models.ManyToManyField(
        "keywords.Keyword", blank=True, related_name="incidents"
    )

    # Deduplication
    duplicate_of = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="duplicates"
    )

    class Meta:
        ordering = ["-date_collected"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "record_id"],
                name="unique_record_id_per_project",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.record_id:
            self.record_id = self._generate_record_id()
        if not self.organization_id and self.project_id:
            self.organization_id = self.project.organization_id
        # Duplicate detection
        if self.url and not self.duplicate_of:
            existing = (
                Incident.objects.filter(project=self.project, url=self.url)
                .exclude(pk=self.pk)
                .first()
            )
            if existing:
                self.duplicate_of = existing
        super().save(*args, **kwargs)

    def _generate_record_id(self):
        try:
            prefix = self.project.settings.record_id_prefix
        except ProjectSettings.DoesNotExist:
            prefix = "REC"
        last = (
            Incident.objects.filter(project=self.project)
            .order_by("-date_collected")
            .values_list("record_id", flat=True)
            .first()
        )
        if last:
            try:
                num = int(last.split("-")[-1]) + 1
            except (ValueError, IndexError):
                num = Incident.objects.filter(project=self.project).count() + 1
        else:
            num = 1
        return f"{prefix}-{num:03d}"

    def __str__(self):
        return self.record_id
