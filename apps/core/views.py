import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView, UpdateView

from .forms import (
    AddProjectMemberForm,
    InviteAcceptForm,
    InviteForm,
    KeywordCategoryForm,
    LanguageForm,
    OrganizationForm,
    PlatformForm,
    ProjectFieldConfigForm,
    ProjectForm,
    RegistrationForm,
)
from .mixins import OrgRequiredMixin, ProjectRequiredMixin, RequireOrgRole, RequireProjectRole
from .models import (
    APIToken,
    Invitation,
    KeywordCategory,
    Language,
    Organization,
    OrganizationMembership,
    Platform,
    ProjectFieldConfig,
    ProjectMembership,
    ProjectSettings,
    User,
)


class RegisterView(FormView):
    template_name = "auth/register.html"
    form_class = RegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("org_selector")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("org_selector")


class OrgSelectorView(LoginRequiredMixin, TemplateView):
    template_name = "core/org_selector.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["memberships"] = (
            OrganizationMembership.objects.filter(user=self.request.user)
            .select_related("organization")
            .order_by("organization__name")
        )
        return ctx


class OrgDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/org_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        # Middleware lets unauthenticated requests through; bounce non-members to login/selector.
        if not getattr(request, "organization", None):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.request.organization
        ctx["organization"] = org
        ctx["projects"] = org.projects.order_by("name")
        membership = self.request.org_membership
        ctx["can_manage"] = (
            self.request.user.is_superuser
            or (
                membership
                and membership.role
                in (
                    OrganizationMembership.Role.OWNER,
                    OrganizationMembership.Role.ADMIN,
                )
            )
        )
        return ctx


class OrgCreateView(LoginRequiredMixin, FormView):
    template_name = "core/org_create.html"
    form_class = OrganizationForm

    def form_valid(self, form):
        org = form.save()
        OrganizationMembership.objects.create(
            user=self.request.user,
            organization=org,
            role=OrganizationMembership.Role.OWNER,
        )
        return redirect("org_dashboard", org_slug=org.slug)


class ProjectCreateView(RequireOrgRole, FormView):
    template_name = "core/project_create.html"
    form_class = ProjectForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.organization
        return kwargs

    def form_valid(self, form):
        project = form.save(commit=False)
        project.organization = self.request.organization
        project.save()
        ProjectMembership.objects.create(
            user=self.request.user,
            project=project,
            role=ProjectMembership.Role.COORDINATOR,
        )
        return redirect("org_dashboard", org_slug=self.request.organization.slug)


class OrgSettingsView(RequireOrgRole, UpdateView):
    template_name = "core/org_settings.html"
    form_class = OrganizationForm

    def get_object(self):
        return self.request.organization

    def get_success_url(self):
        return reverse("org_dashboard", kwargs={"org_slug": self.object.slug})

    def form_valid(self, form):
        # Re-slug if name changed
        old_slug = self.object.slug
        response = super().form_valid(form)
        if self.object.slug != old_slug:
            messages.success(self.request, "Organization updated.")
        return response


class OrgMembersView(RequireOrgRole, TemplateView):
    template_name = "core/org_members.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.request.organization
        ctx["organization"] = org
        ctx["memberships"] = (
            org.memberships.select_related("user").order_by("role", "user__email")
        )
        ctx["invite_form"] = InviteForm(organization=org)
        ctx["pending_invites"] = org.invitations.filter(
            accepted=False, expires_at__gt=timezone.now()
        ).order_by("-created_at")
        return ctx

    def post(self, request, *args, **kwargs):
        org = request.organization
        form = InviteForm(request.POST, organization=org)
        if form.is_valid():
            invitation = Invitation(
                email=form.cleaned_data["email"],
                organization=org,
                org_role=form.cleaned_data["org_role"],
                invited_by=request.user,
            )
            project = form.cleaned_data.get("project")
            if project:
                invitation.project = project
                invitation.project_role = form.cleaned_data["project_role"]
            invitation.save()
            messages.success(
                request,
                f"Invitation sent to {invitation.email}. "
                f"Share this link: {request.build_absolute_uri(reverse('invite_accept', kwargs={'token': invitation.token}))}",
            )
            return redirect("org_members", org_slug=org.slug)

        ctx = self.get_context_data(**kwargs)
        ctx["invite_form"] = form
        return self.render_to_response(ctx)


class InviteAcceptView(TemplateView):
    template_name = "auth/invite_accept.html"

    def get_invitation(self):
        invitation = get_object_or_404(Invitation, token=self.kwargs["token"])
        if invitation.accepted or invitation.is_expired:
            return None
        return invitation

    def get(self, request, *args, **kwargs):
        invitation = self.get_invitation()
        if not invitation:
            return self.render_to_response({"expired": True})

        ctx = {"invitation": invitation, "expired": False}
        if request.user.is_authenticated:
            # Logged-in user just needs to confirm
            ctx["existing_user"] = True
        else:
            existing = User.objects.filter(email=invitation.email).exists()
            if existing:
                ctx["needs_login"] = True
            else:
                ctx["form"] = InviteAcceptForm()
        return self.render_to_response(ctx)

    def post(self, request, *args, **kwargs):
        invitation = self.get_invitation()
        if not invitation:
            return self.render_to_response({"expired": True})

        # Determine or create the user
        if request.user.is_authenticated:
            user = request.user
        else:
            existing_user = User.objects.filter(email=invitation.email).first()
            if existing_user:
                # They need to log in first
                return redirect(
                    f"{reverse('login')}?next={request.path}"
                )
            else:
                form = InviteAcceptForm(request.POST)
                if not form.is_valid():
                    return self.render_to_response({
                        "invitation": invitation,
                        "expired": False,
                        "form": form,
                    })
                user = User.objects.create_user(
                    email=invitation.email,
                    password=form.cleaned_data["password"],
                )
                login(request, user)

        # Add org membership
        OrganizationMembership.objects.get_or_create(
            user=user,
            organization=invitation.organization,
            defaults={"role": invitation.org_role},
        )

        # Add project membership if specified
        if invitation.project and invitation.project_role:
            ProjectMembership.objects.get_or_create(
                user=user,
                project=invitation.project,
                defaults={"role": invitation.project_role},
            )

        invitation.accepted = True
        invitation.save()

        messages.success(
            request,
            f"You've joined {invitation.organization.name}.",
        )
        return redirect("org_dashboard", org_slug=invitation.organization.slug)


class ProjectMembersView(RequireProjectRole, TemplateView):
    template_name = "core/project_members.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.request.project
        ctx["project"] = project
        ctx["memberships"] = (
            project.memberships.select_related("user").order_by("role", "user__email")
        )
        ctx["add_form"] = AddProjectMemberForm(
            organization=self.request.organization, project=project
        )
        return ctx

    def post(self, request, *args, **kwargs):
        project = request.project
        form = AddProjectMemberForm(
            request.POST,
            organization=request.organization,
            project=project,
        )
        if form.is_valid():
            ProjectMembership.objects.create(
                user=form.cleaned_data["user"],
                project=project,
                role=form.cleaned_data["role"],
            )
            messages.success(request, "Member added to project.")
            return redirect(
                "project_members",
                org_slug=request.organization.slug,
                project_slug=project.slug,
            )

        ctx = self.get_context_data(**kwargs)
        ctx["add_form"] = form
        return self.render_to_response(ctx)


class ProjectDashboardView(ProjectRequiredMixin, TemplateView):
    template_name = "core/project_dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.request.project
        org = self.request.organization
        now = timezone.now()

        from apps.coverage.models import SearchSession
        from apps.incidents.models import Incident
        from apps.keywords.models import Keyword

        # --- Summary cards (9.2) ---
        total_incidents = Incident.objects.filter(project=project).count()
        week_ago = now - datetime.timedelta(days=7)
        incidents_this_week = Incident.objects.filter(
            project=project, date_collected__gte=week_ago
        ).count()

        active_volunteers = (
            SearchSession.objects.filter(project=project, date__gte=now.date() - datetime.timedelta(days=30))
            .values("volunteer").distinct().count()
        )

        # Coverage score: % of (platform x language x category) cells searched in 30 days
        from apps.core.models import KeywordCategory, Language, Platform
        platforms = Platform.objects.filter(project=project)
        languages = Language.objects.filter(project=project)
        categories = KeywordCategory.objects.filter(project=project)
        total_cells = platforms.count() * languages.count() * categories.count()

        covered_cells = 0
        if total_cells > 0:
            thirty_days_ago = now.date() - datetime.timedelta(days=30)
            recent_sessions = list(
                SearchSession.objects.filter(project=project, date__gte=thirty_days_ago)
            )
            for plat in platforms:
                for lang in languages:
                    for cat in categories:
                        for s in recent_sessions:
                            if (
                                s.platform_id == plat.pk
                                and s.language == lang.name
                                and cat.slug in (s.keyword_categories or [])
                            ):
                                covered_cells += 1
                                break

        coverage_score = round(covered_cells / total_cells * 100) if total_cells else 0

        ctx["summary"] = {
            "total_incidents": total_incidents,
            "incidents_this_week": incidents_this_week,
            "active_volunteers": active_volunteers,
            "coverage_score": coverage_score,
        }

        # --- Recent incidents (9.3) ---
        ctx["recent_incidents"] = (
            Incident.objects.filter(project=project)
            .select_related("platform", "collected_by")
            .order_by("-date_collected")[:20]
        )

        # --- Review queue (9.4) ---
        ctx["review_count"] = Incident.objects.filter(
            project=project, status=Incident.Status.SUBMITTED
        ).count()

        # --- Keyword candidates (9.6) ---
        ctx["candidate_keywords"] = Keyword.objects.filter(
            project=project, status=Keyword.Status.CANDIDATE
        ).count()

        # --- Data quality flags (9.7) ---
        required_fields = list(
            ProjectFieldConfig.objects.filter(project=project, required=True)
            .values_list("field_name", flat=True)
        )
        quality_issues = []

        no_screenshot = Incident.objects.filter(
            project=project, screenshot=""
        ).exclude(status=Incident.Status.DRAFT).count()
        if no_screenshot:
            quality_issues.append(f"{no_screenshot} incidents without screenshot")

        duplicates = Incident.objects.filter(
            project=project, duplicate_of__isnull=False
        ).count()
        if duplicates:
            quality_issues.append(f"{duplicates} duplicate incidents")

        if required_fields:
            # Count incidents missing required extra_fields
            all_incidents = Incident.objects.filter(project=project).exclude(
                status=Incident.Status.DRAFT
            )
            missing_count = 0
            for inc in all_incidents.only("extra_fields"):
                extra = inc.extra_fields or {}
                for f in required_fields:
                    if f not in extra or extra[f] in ("", None):
                        missing_count += 1
                        break
            if missing_count:
                quality_issues.append(f"{missing_count} incidents missing required fields")

        ctx["quality_issues"] = quality_issues

        # --- Coverage heatmap widget (9.5) — top gaps ---
        from apps.coverage.models import SearchSession

        top_gaps = []
        if platforms.exists() and languages.exists() and categories.exists():
            thirty_days_ago = now.date() - datetime.timedelta(days=30)
            recent_sessions = list(
                SearchSession.objects.filter(project=project, date__gte=thirty_days_ago)
            )
            for plat in platforms[:5]:
                for lang in languages[:5]:
                    for cat in categories[:5]:
                        covered = any(
                            s.platform_id == plat.pk
                            and s.language == lang.name
                            and cat.slug in (s.keyword_categories or [])
                            for s in recent_sessions
                        )
                        if not covered:
                            top_gaps.append({
                                "platform": plat.name,
                                "language": lang.name,
                                "category": cat.name,
                            })
                            if len(top_gaps) >= 8:
                                break
                    if len(top_gaps) >= 8:
                        break
                if len(top_gaps) >= 8:
                    break

        ctx["top_gaps"] = top_gaps

        return ctx


class ProjectSettingsView(RequireProjectRole, TemplateView):
    template_name = "core/project_settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.request.project
        ctx["platforms"] = Platform.objects.filter(project=project).order_by("name")
        ctx["languages"] = Language.objects.filter(project=project).order_by("name")
        ctx["categories"] = KeywordCategory.objects.filter(project=project).order_by("name")
        ctx["field_configs"] = ProjectFieldConfig.objects.filter(project=project).order_by("order")
        ctx["platform_form"] = PlatformForm()
        ctx["language_form"] = LanguageForm()
        ctx["category_form"] = KeywordCategoryForm()
        ctx["field_config_form"] = ProjectFieldConfigForm()

        settings_obj, _ = ProjectSettings.objects.get_or_create(project=project)
        ctx["record_id_prefix"] = settings_obj.record_id_prefix
        return ctx

    def post(self, request, *args, **kwargs):
        project = request.project
        action = request.POST.get("action")

        if action == "add_platform":
            form = PlatformForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.project = project
                obj.save()
                messages.success(request, f'Platform "{obj.name}" added.')

        elif action == "delete_platform":
            Platform.objects.filter(pk=request.POST.get("pk"), project=project).delete()

        elif action == "add_language":
            form = LanguageForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.project = project
                obj.save()
                messages.success(request, f'Language "{obj.name}" added.')

        elif action == "delete_language":
            Language.objects.filter(pk=request.POST.get("pk"), project=project).delete()

        elif action == "add_category":
            form = KeywordCategoryForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.project = project
                obj.save()
                messages.success(request, f'Category "{obj.name}" added.')

        elif action == "delete_category":
            KeywordCategory.objects.filter(pk=request.POST.get("pk"), project=project).delete()

        elif action == "add_field":
            form = ProjectFieldConfigForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.project = project
                obj.save()
                messages.success(request, f'Field "{obj.label}" added.')

        elif action == "delete_field":
            ProjectFieldConfig.objects.filter(pk=request.POST.get("pk"), project=project).delete()

        elif action == "update_prefix":
            prefix = request.POST.get("record_id_prefix", "REC").strip()
            settings_obj, _ = ProjectSettings.objects.get_or_create(project=project)
            settings_obj.record_id_prefix = prefix or "REC"
            settings_obj.save()
            messages.success(request, f"Record ID prefix set to '{settings_obj.record_id_prefix}'.")

        return redirect(
            "project_settings",
            org_slug=request.organization.slug,
            project_slug=project.slug,
        )


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "auth/account_settings.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["api_token"] = APIToken.objects.filter(user=self.request.user).first()
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")

        if action == "generate":
            APIToken.objects.filter(user=request.user).delete()
            token = APIToken.objects.create(user=request.user)
            messages.success(request, f"API token generated. Copy it now — it won't be shown again: {token.key}")

        elif action == "revoke":
            APIToken.objects.filter(user=request.user).delete()
            messages.success(request, "API token revoked.")

        return redirect("account_settings")


class SeedImportView(RequireProjectRole, TemplateView):
    """Upload CSV to bulk-import platforms, languages, or keyword categories."""

    template_name = "core/seed_import.html"

    def post(self, request, *args, **kwargs):
        import csv as csv_mod
        import io

        csv_file = request.FILES.get("csv_file")
        data_type = request.POST.get("data_type")
        project = request.project

        if not csv_file or data_type not in ("platforms", "languages", "categories"):
            messages.error(request, "Select a data type and CSV file.")
            return self.render_to_response(self.get_context_data())

        decoded = csv_file.read().decode("utf-8-sig")
        reader = csv_mod.DictReader(io.StringIO(decoded))
        created = 0

        for row in reader:
            if data_type == "platforms":
                name = row.get("name", "").strip()
                if not name:
                    continue
                _, was_created = Platform.objects.get_or_create(
                    project=project, name=name,
                    defaults={"url_pattern": row.get("url_pattern", "").strip()},
                )
                if was_created:
                    created += 1

            elif data_type == "languages":
                name = row.get("name", "").strip()
                if not name:
                    continue
                _, was_created = Language.objects.get_or_create(
                    project=project, name=name,
                    defaults={"code": row.get("code", "").strip()},
                )
                if was_created:
                    created += 1

            elif data_type == "categories":
                name = row.get("name", "").strip()
                if not name:
                    continue
                from django.utils.text import slugify as _slugify

                slug = _slugify(name)
                _, was_created = KeywordCategory.objects.get_or_create(
                    project=project, slug=slug,
                    defaults={"name": name},
                )
                if was_created:
                    created += 1

        messages.success(request, f"Imported {created} {data_type}.")
        return redirect(
            "project_settings",
            org_slug=request.organization.slug,
            project_slug=project.slug,
        )
