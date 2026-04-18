from django import forms

from apps.core.models import KeywordCategory, Platform

from .models import SearchSession


class SearchSessionForm(forms.ModelForm):
    class Meta:
        model = SearchSession
        fields = ["platform", "language", "date", "duration_minutes", "incidents_found", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    keyword_categories_select = forms.ModelMultipleChoiceField(
        queryset=KeywordCategory.objects.none(),
        required=False,
        label="Keyword categories",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if project:
            self.fields["platform"].queryset = Platform.objects.filter(project=project)
            self.fields["keyword_categories_select"].queryset = (
                KeywordCategory.objects.filter(project=project)
            )
            # Pre-fill from existing keyword_categories JSON
            if self.instance and self.instance.pk:
                slugs = self.instance.keyword_categories or []
                self.initial["keyword_categories_select"] = (
                    KeywordCategory.objects.filter(project=project, slug__in=slugs)
                )

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert selected categories to slug list for JSON storage
        cats = self.cleaned_data.get("keyword_categories_select", [])
        instance.keyword_categories = [c.slug for c in cats]
        if commit:
            instance.save()
        return instance
