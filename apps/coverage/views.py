import datetime

from django.contrib import messages
from django.db.models import Count, Max, Sum
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from apps.core.mixins import ProjectRequiredMixin
from apps.core.models import KeywordCategory, Language, Platform

from .forms import SearchSessionForm
from .models import SearchSession


class SearchSessionLogView(ProjectRequiredMixin, FormView):
    template_name = "coverage/log_search.html"
    form_class = SearchSessionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.request.project
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["date"] = timezone.now().date()

        # Pre-fill from GET params (8.6 — click gap cell)
        project = self.request.project
        platform_name = self.request.GET.get("platform")
        if platform_name:
            plat = Platform.objects.filter(project=project, name=platform_name).first()
            if plat:
                initial["platform"] = plat.pk
        language = self.request.GET.get("language")
        if language:
            initial["language"] = language

        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Pre-select category from GET param
        category_name = self.request.GET.get("category")
        if category_name and not self.request.POST:
            cat = KeywordCategory.objects.filter(
                project=self.request.project, name=category_name
            ).first()
            if cat:
                form.initial["keyword_categories_select"] = [cat.pk]
        return form

    def form_valid(self, form):
        session = form.save(commit=False)
        session.project = self.request.project
        session.volunteer = self.request.user
        session.save()
        messages.success(self.request, "Search session logged.")
        return redirect(
            "coverage_matrix",
            org_slug=self.request.organization.slug,
            project_slug=self.request.project.slug,
        )


class CoverageMatrixView(ProjectRequiredMixin, TemplateView):
    template_name = "coverage/matrix.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.request.project

        platforms = Platform.objects.filter(project=project).order_by("name")
        languages = Language.objects.filter(project=project).order_by("name")
        categories = KeywordCategory.objects.filter(project=project).order_by("name")

        # Build matrix: for each (platform, language) pair, find the latest
        # search session date per category
        sessions = SearchSession.objects.filter(project=project)

        now = timezone.now().date()
        matrix = []

        # Pre-fetch all sessions to avoid N+1 and SQLite JSON limitations
        all_sessions = list(sessions.order_by("-date"))

        for platform in platforms:
            for lang in languages:
                row = {
                    "platform": platform.name,
                    "language": lang.name,
                    "cells": [],
                }
                plat_lang_sessions = [
                    s for s in all_sessions
                    if s.platform_id == platform.pk and s.language == lang.name
                ]
                for cat in categories:
                    # Find latest session covering this category
                    latest = None
                    for s in plat_lang_sessions:
                        cats = s.keyword_categories or []
                        if cat.slug in cats:
                            latest = s.date
                            break  # already sorted by -date
                    if latest:
                        days_ago = (now - latest).days
                        if days_ago <= 7:
                            color = "green"
                        elif days_ago <= 30:
                            color = "yellow"
                        else:
                            color = "red"
                    else:
                        days_ago = None
                        color = "red"

                    row["cells"].append({
                        "category": cat.name,
                        "last_date": latest,
                        "days_ago": days_ago,
                        "color": color,
                    })
                matrix.append(row)

        ctx["platforms"] = platforms
        ctx["languages"] = languages
        ctx["categories"] = categories
        ctx["matrix"] = matrix
        return ctx


class VolunteerActivityView(ProjectRequiredMixin, TemplateView):
    template_name = "coverage/volunteer_activity.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.request.project

        volunteers = (
            SearchSession.objects.filter(project=project)
            .values("volunteer__email")
            .annotate(
                total_sessions=Count("id"),
                total_incidents=Sum("incidents_found"),
                last_active=Max("date"),
            )
            .order_by("-last_active")
        )
        ctx["volunteers"] = volunteers
        return ctx
