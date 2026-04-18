from django import forms

from apps.core.models import KeywordCategory

from .models import Keyword


class KeywordForm(forms.ModelForm):
    class Meta:
        model = Keyword
        fields = ["term", "language", "category", "status", "shared"]

    def __init__(self, *args, project=None, is_coordinator=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        if project:
            self.fields["category"].queryset = KeywordCategory.objects.filter(
                project=project
            )
        # Volunteers can only create candidates
        if not is_coordinator:
            self.fields["status"].choices = [
                (Keyword.Status.CANDIDATE, "Candidate"),
            ]
            self.fields["status"].initial = Keyword.Status.CANDIDATE
            self.fields["shared"].widget = forms.HiddenInput()


class KeywordFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"placeholder": "Search terms..."}
    ))
    status = forms.ChoiceField(
        choices=[("", "All statuses")] + list(Keyword.Status.choices),
        required=False,
    )
    category = forms.ModelChoiceField(
        queryset=KeywordCategory.objects.none(),
        required=False,
        empty_label="All categories",
    )
    language = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"placeholder": "Language"}
    ))
    sort = forms.ChoiceField(
        choices=[
            ("-date_added", "Newest"),
            ("term", "A-Z"),
        ],
        required=False,
        initial="-date_added",
    )

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields["category"].queryset = KeywordCategory.objects.filter(
                project=project
            )
