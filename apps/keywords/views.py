import csv
import io

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView, ListView, View

from apps.core.mixins import ProjectRequiredMixin, RequireProjectRole
from apps.core.models import KeywordCategory, OrganizationMembership

from .forms import KeywordFilterForm, KeywordForm
from .models import Keyword


class _CoordinatorCheck:
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


class KeywordListView(_CoordinatorCheck, ProjectRequiredMixin, ListView):
    template_name = "keywords/list.html"
    context_object_name = "keywords"
    paginate_by = 30

    def get_queryset(self):
        # Own keywords + shared keywords from other projects in the same org (7.7)
        qs = Keyword.objects.filter(
            Q(project=self.request.project)
            | Q(organization=self.request.organization, shared=True)
        ).annotate(
            match_count_val=Count("incidents")
        ).select_related("category")

        form = KeywordFilterForm(self.request.GET, project=self.request.project)
        if form.is_valid():
            if form.cleaned_data.get("search"):
                qs = qs.filter(term__icontains=form.cleaned_data["search"])
            if form.cleaned_data.get("status"):
                qs = qs.filter(status=form.cleaned_data["status"])
            if form.cleaned_data.get("category"):
                qs = qs.filter(category=form.cleaned_data["category"])
            if form.cleaned_data.get("language"):
                qs = qs.filter(language__icontains=form.cleaned_data["language"])
            sort = form.cleaned_data.get("sort")
            if sort == "term":
                qs = qs.order_by("term")
            elif sort == "-match_count":
                qs = qs.order_by("-match_count_val")
            else:
                qs = qs.order_by("-date_added")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = KeywordFilterForm(
            self.request.GET, project=self.request.project
        )
        ctx["is_coordinator"] = self._is_coordinator()
        return ctx


class KeywordCreateView(_CoordinatorCheck, ProjectRequiredMixin, FormView):
    template_name = "keywords/form.html"
    form_class = KeywordForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.request.project
        kwargs["is_coordinator"] = self._is_coordinator()
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_new"] = True
        return ctx

    def form_valid(self, form):
        keyword = form.save(commit=False)
        keyword.project = self.request.project
        keyword.organization = self.request.organization
        keyword.added_by = self.request.user
        keyword.save()
        messages.success(self.request, f'Keyword "{keyword.term}" added.')
        return redirect(
            "keyword_list",
            org_slug=self.request.organization.slug,
            project_slug=self.request.project.slug,
        )


class KeywordEditView(_CoordinatorCheck, ProjectRequiredMixin, FormView):
    template_name = "keywords/form.html"
    form_class = KeywordForm

    def get_keyword(self):
        return get_object_or_404(
            Keyword, pk=self.kwargs["pk"], project=self.request.project
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_keyword()
        kwargs["project"] = self.request.project
        kwargs["is_coordinator"] = self._is_coordinator()
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["keyword"] = self.get_keyword()
        ctx["is_new"] = False
        return ctx

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Keyword updated.")
        return redirect(
            "keyword_list",
            org_slug=self.request.organization.slug,
            project_slug=self.request.project.slug,
        )


class KeywordStatusView(ProjectRequiredMixin, View):
    """Quick status change for keyword approval workflow. Coordinator only."""

    def post(self, request, *args, **kwargs):
        keyword = get_object_or_404(
            Keyword, pk=kwargs["pk"], project=request.project
        )
        new_status = request.POST.get("status")
        if new_status in dict(Keyword.Status.choices):
            keyword.status = new_status
            keyword.save(update_fields=["status"])
            messages.success(request, f'"{keyword.term}" → {keyword.get_status_display()}.')
        return redirect(
            "keyword_list",
            org_slug=request.organization.slug,
            project_slug=request.project.slug,
        )


class KeywordBulkImportView(RequireProjectRole, View):
    """Bulk import keywords from CSV. Expects columns: term, language, category.
    Skips duplicates. Coordinator only."""

    def get(self, request, *args, **kwargs):
        from django.shortcuts import render
        return render(request, "keywords/import.html")

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, "Please select a CSV file.")
            from django.shortcuts import render
            return render(request, "keywords/import.html")

        decoded = csv_file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(decoded))

        project = request.project
        org = request.organization
        created = 0
        skipped = 0

        # Pre-fetch categories
        cat_map = {
            c.slug: c
            for c in KeywordCategory.objects.filter(project=project)
        }

        for row in reader:
            term = row.get("term", "").strip()
            language = row.get("language", "").strip()
            category_name = row.get("category", "").strip()

            if not term or not language:
                skipped += 1
                continue

            # Resolve category
            from django.utils.text import slugify
            cat_slug = slugify(category_name) if category_name else None
            category = cat_map.get(cat_slug) if cat_slug else None

            # Skip duplicates
            if Keyword.objects.filter(project=project, term=term, language=language).exists():
                skipped += 1
                continue

            Keyword.objects.create(
                project=project,
                organization=org,
                term=term,
                language=language,
                category=category,
                added_by=request.user,
                status=Keyword.Status.ACTIVE,
            )
            created += 1

        messages.success(request, f"Imported {created} keywords, skipped {skipped}.")
        return redirect(
            "keyword_list",
            org_slug=org.slug,
            project_slug=project.slug,
        )
