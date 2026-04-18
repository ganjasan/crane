import csv

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, FormView, ListView, TemplateView, View

from apps.core.mixins import ProjectRequiredMixin, RequireProjectRole
from apps.core.models import OrganizationMembership, ProjectFieldConfig

from .forms import IncidentFilterForm, IncidentForm
from .models import Incident


class IncidentListView(ProjectRequiredMixin, ListView):
    template_name = "incidents/list.html"
    context_object_name = "incidents"
    paginate_by = 25

    def get_queryset(self):
        qs = Incident.objects.filter(project=self.request.project).select_related(
            "platform", "collected_by"
        )
        form = IncidentFilterForm(self.request.GET, project=self.request.project)
        if form.is_valid():
            if form.cleaned_data.get("search"):
                q = form.cleaned_data["search"]
                qs = qs.filter(
                    Q(notes__icontains=q)
                    | Q(url__icontains=q)
                    | Q(location_mentioned__icontains=q)
                    | Q(record_id__icontains=q)
                )
            if form.cleaned_data.get("platform"):
                qs = qs.filter(platform=form.cleaned_data["platform"])
            if form.cleaned_data.get("status"):
                qs = qs.filter(status=form.cleaned_data["status"])
            if form.cleaned_data.get("confidence"):
                qs = qs.filter(confidence=form.cleaned_data["confidence"])
            if form.cleaned_data.get("date_from"):
                qs = qs.filter(date_of_post__gte=form.cleaned_data["date_from"])
            if form.cleaned_data.get("date_to"):
                qs = qs.filter(date_of_post__lte=form.cleaned_data["date_to"])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = IncidentFilterForm(
            self.request.GET, project=self.request.project
        )
        ctx["is_htmx"] = self.request.headers.get("HX-Request") == "true"
        return ctx

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true":
            return ["incidents/_list_rows.html"]
        return [self.template_name]


class IncidentDetailView(ProjectRequiredMixin, DetailView):
    template_name = "incidents/detail.html"
    context_object_name = "incident"

    def get_queryset(self):
        return Incident.objects.filter(
            project=self.request.project
        ).select_related("platform", "collected_by", "duplicate_of")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Build extra fields display with labels
        configs = ProjectFieldConfig.objects.filter(
            project=self.request.project
        ).order_by("order")
        extra = self.object.extra_fields or {}
        ctx["extra_fields_display"] = [
            {"label": c.label, "value": extra.get(c.field_name, "—")}
            for c in configs
            if c.field_name in extra
        ]
        ctx["can_review"] = self._can_review()
        return ctx

    def _can_review(self):
        user = self.request.user
        if user.is_superuser:
            return True
        org_membership = getattr(self.request, "org_membership", None)
        if org_membership and org_membership.role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        ):
            return True
        proj_membership = getattr(self.request, "project_membership", None)
        return proj_membership and proj_membership.role == "coordinator"


class IncidentCreateView(ProjectRequiredMixin, FormView):
    template_name = "incidents/form.html"
    form_class = IncidentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.request.project
        kwargs["submit_mode"] = "submit" in self.request.POST
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        incident = form.save(commit=False)
        incident.project = self.request.project
        incident.organization = self.request.organization
        incident.collected_by = self.request.user

        if "submit" in self.request.POST:
            incident.status = Incident.Status.SUBMITTED
        else:
            incident.status = Incident.Status.DRAFT

        incident.save()
        form.save_m2m()

        messages.success(self.request, f"Incident {incident.record_id} saved.")
        return redirect(
            "incident_detail",
            org_slug=self.request.organization.slug,
            project_slug=self.request.project.slug,
            pk=incident.pk,
        )


class IncidentEditView(ProjectRequiredMixin, FormView):
    template_name = "incidents/form.html"
    form_class = IncidentForm

    def get_incident(self):
        return get_object_or_404(
            Incident, pk=self.kwargs["pk"], project=self.request.project
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.request.project
        kwargs["instance"] = self.get_incident()
        kwargs["submit_mode"] = "submit" in self.request.POST
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["incident"] = self.get_incident()
        ctx["is_new"] = False
        return ctx

    def form_valid(self, form):
        incident = form.save(commit=False)

        if "submit" in self.request.POST:
            incident.status = Incident.Status.SUBMITTED
        # Keep current status if just saving draft edits

        incident.save()
        form.save_m2m()

        messages.success(self.request, f"Incident {incident.record_id} updated.")
        return redirect(
            "incident_detail",
            org_slug=self.request.organization.slug,
            project_slug=self.request.project.slug,
            pk=incident.pk,
        )


class IncidentStatusView(RequireProjectRole, View):
    """Change incident status. Coordinator only (except draft→submitted for any member)."""

    def post(self, request, *args, **kwargs):
        incident = get_object_or_404(
            Incident, pk=kwargs["pk"], project=request.project
        )
        new_status = request.POST.get("status")

        if new_status not in dict(Incident.Status.choices):
            messages.error(request, "Invalid status.")
            return self._redirect(incident)

        # Volunteers can only submit their own drafts
        is_coordinator = self._is_coordinator()
        if not is_coordinator:
            if not (
                incident.status == Incident.Status.DRAFT
                and new_status == Incident.Status.SUBMITTED
                and incident.collected_by == request.user
            ):
                messages.error(request, "You can only submit your own draft incidents.")
                return self._redirect(incident)

        incident.status = new_status
        incident.save(update_fields=["status"])
        messages.success(request, f"Status changed to {incident.get_status_display()}.")
        return self._redirect(incident)

    def _redirect(self, incident):
        return redirect(
            "incident_detail",
            org_slug=self.request.organization.slug,
            project_slug=self.request.project.slug,
            pk=incident.pk,
        )

    def _is_coordinator(self):
        if self.request.user.is_superuser:
            return True
        org_membership = getattr(self.request, "org_membership", None)
        if org_membership and org_membership.role in (
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        ):
            return True
        proj_membership = getattr(self.request, "project_membership", None)
        return proj_membership and proj_membership.role == "coordinator"


class IncidentExportView(RequireProjectRole, View):
    """Export incidents as CSV. Coordinator only."""

    def get(self, request, *args, **kwargs):
        project = request.project
        qs = Incident.objects.filter(project=project).select_related(
            "platform", "collected_by"
        ).order_by("record_id")

        # Get project field configs for extra_fields columns
        configs = ProjectFieldConfig.objects.filter(project=project).order_by("order")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="{project.slug}-incidents.csv"'
        )

        writer = csv.writer(response)

        # Header row
        headers = [
            "record_id", "status", "platform", "url", "date_of_post",
            "date_collected", "collected_by", "location_mentioned",
            "probable_location", "language", "confidence", "notes",
            "duplicate_of",
        ]
        headers += [c.label for c in configs]
        writer.writerow(headers)

        # Data rows
        for inc in qs:
            row = [
                inc.record_id,
                inc.get_status_display(),
                inc.platform.name if inc.platform else "",
                inc.url,
                inc.date_of_post or "",
                inc.date_collected.strftime("%Y-%m-%d %H:%M"),
                inc.collected_by.email if inc.collected_by else "",
                inc.location_mentioned,
                inc.probable_location,
                inc.language,
                inc.get_confidence_display(),
                inc.notes,
                inc.duplicate_of.record_id if inc.duplicate_of else "",
            ]
            extra = inc.extra_fields or {}
            row += [extra.get(c.field_name, "") for c in configs]
            writer.writerow(row)

        return response
