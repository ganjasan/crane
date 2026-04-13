from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Invitation,
    KeywordCategory,
    Language,
    Organization,
    OrganizationMembership,
    Platform,
    Project,
    ProjectFieldConfig,
    ProjectMembership,
    ProjectSettings,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )


class MembershipInline(admin.TabularInline):
    model = OrganizationMembership
    extra = 1


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 0
    show_change_link = True
    fields = ("name", "slug")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline, ProjectInline]


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1


class FieldConfigInline(admin.TabularInline):
    model = ProjectFieldConfig
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "slug", "created_at")
    list_filter = ("organization",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProjectMembershipInline, FieldConfigInline]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "organization", "project", "org_role", "accepted", "expires_at")
    list_filter = ("accepted", "organization")


admin.site.register(Platform)
admin.site.register(Language)
admin.site.register(KeywordCategory)
admin.site.register(ProjectSettings)
