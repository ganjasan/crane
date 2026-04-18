from django import forms
from django.utils.text import slugify

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
    User,
)


class RegistrationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        pw2 = cleaned.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", "Passwords do not match.")
        return cleaned

    def save(self):
        return User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
        )


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)
        if not slug:
            raise forms.ValidationError("Name must contain at least one letter or number.")
        qs = Organization.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("An organization with this name already exists.")
        return name


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization

    def clean_name(self):
        name = self.cleaned_data["name"]
        slug = slugify(name)
        if not slug:
            raise forms.ValidationError("Name must contain at least one letter or number.")
        if self.organization and Project.objects.filter(
            organization=self.organization, slug=slug
        ).exists():
            raise forms.ValidationError(
                "A project with this name already exists in this organization."
            )
        return name


class InviteForm(forms.Form):
    email = forms.EmailField()
    org_role = forms.ChoiceField(
        label="Organization role",
        choices=OrganizationMembership.Role.choices,
        initial=OrganizationMembership.Role.MEMBER,
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        required=False,
        empty_label="— No project —",
    )
    project_role = forms.ChoiceField(
        label="Project role",
        choices=[("", "—")] + list(ProjectMembership.Role.choices),
        required=False,
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        if organization:
            self.fields["project"].queryset = organization.projects.order_by("name")

    def clean(self):
        cleaned = super().clean()
        project = cleaned.get("project")
        project_role = cleaned.get("project_role")
        if project and not project_role:
            self.add_error("project_role", "Select a role when assigning to a project.")
        if project_role and not project:
            self.add_error("project", "Select a project for this role.")
        return cleaned


class InviteAcceptForm(forms.Form):
    """Registration form for accepting an invitation (new users only)."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        pw2 = cleaned.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", "Passwords do not match.")
        return cleaned


class AddProjectMemberForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Organization member",
    )
    role = forms.ChoiceField(
        choices=ProjectMembership.Role.choices,
        initial=ProjectMembership.Role.VOLUNTEER,
    )

    def __init__(self, *args, organization=None, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if organization and project:
            existing_member_ids = project.members.values_list("pk", flat=True)
            self.fields["user"].queryset = (
                User.objects.filter(organizations=organization)
                .exclude(pk__in=existing_member_ids)
                .order_by("email")
            )


class PlatformForm(forms.ModelForm):
    class Meta:
        model = Platform
        fields = ["name", "url_pattern"]


class LanguageForm(forms.ModelForm):
    class Meta:
        model = Language
        fields = ["name", "code"]


class KeywordCategoryForm(forms.ModelForm):
    class Meta:
        model = KeywordCategory
        fields = ["name"]


class ProjectFieldConfigForm(forms.ModelForm):
    class Meta:
        model = ProjectFieldConfig
        fields = ["field_name", "label", "field_type", "required", "order"]

    choices_text = forms.CharField(
        required=False,
        label="Choices (one per line, for dropdown fields)",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.choices:
            self.initial["choices_text"] = "\n".join(self.instance.choices)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("field_type") == ProjectFieldConfig.FieldType.CHOICE:
            text = cleaned.get("choices_text", "").strip()
            if not text:
                self.add_error("choices_text", "Choices are required for dropdown fields.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        text = self.cleaned_data.get("choices_text", "").strip()
        if text:
            instance.choices = [line.strip() for line in text.splitlines() if line.strip()]
        else:
            instance.choices = None
        if commit:
            instance.save()
        return instance
