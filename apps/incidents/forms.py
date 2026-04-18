from django import forms

from apps.core.models import Platform, ProjectFieldConfig

from .models import Incident


class IncidentForm(forms.ModelForm):
    """Incident form with dynamic project-specific fields from ProjectFieldConfig."""

    class Meta:
        model = Incident
        fields = [
            "platform",
            "url",
            "screenshot",
            "date_of_post",
            "location_mentioned",
            "probable_location",
            "language",
            "confidence",
            "notes",
        ]
        widgets = {
            "date_of_post": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "url": forms.URLInput(),
        }

    def __init__(self, *args, project=None, submit_mode=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.submit_mode = submit_mode

        # Scope platform choices to project
        if project:
            self.fields["platform"].queryset = Platform.objects.filter(project=project)

        # Add dynamic fields from ProjectFieldConfig
        self._field_configs = []
        if project:
            configs = ProjectFieldConfig.objects.filter(project=project).order_by("order")
            for config in configs:
                field = self._make_dynamic_field(config)
                field_key = f"extra_{config.field_name}"
                self.fields[field_key] = field
                self._field_configs.append(config)

                # Pre-fill from existing extra_fields
                if self.instance and self.instance.pk:
                    extra = self.instance.extra_fields or {}
                    if config.field_name in extra:
                        self.initial[field_key] = extra[config.field_name]

        # In submit mode, mark required fields
        if submit_mode:
            for config in self._field_configs:
                if config.required:
                    self.fields[f"extra_{config.field_name}"].required = True

    def _make_dynamic_field(self, config):
        """Create a form field from a ProjectFieldConfig."""
        common = {"label": config.label, "required": False}

        if config.field_type == ProjectFieldConfig.FieldType.TEXT:
            return forms.CharField(**common, max_length=500)
        elif config.field_type == ProjectFieldConfig.FieldType.NUMBER:
            return forms.DecimalField(**common)
        elif config.field_type == ProjectFieldConfig.FieldType.BOOLEAN:
            return forms.BooleanField(**common)
        elif config.field_type == ProjectFieldConfig.FieldType.CHOICE:
            choices = [("", "—")] + [
                (c, c) for c in (config.choices or [])
            ]
            return forms.ChoiceField(**common, choices=choices)
        else:
            return forms.CharField(**common)

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Collect dynamic field values into extra_fields
        extra = instance.extra_fields or {}
        for config in self._field_configs:
            key = f"extra_{config.field_name}"
            value = self.cleaned_data.get(key)
            # Ensure JSON-serializable types
            from decimal import Decimal

            if isinstance(value, Decimal):
                value = float(value)
            # Store value (including False for booleans)
            if value is not None and (value != "" or isinstance(value, bool)):
                extra[config.field_name] = value
            elif config.field_name in extra and value == "":
                del extra[config.field_name]
        instance.extra_fields = extra

        if commit:
            instance.save()
            self.save_m2m()
        return instance


class IncidentFilterForm(forms.Form):
    """Filter form for incident list (not bound to model)."""

    search = forms.CharField(required=False, widget=forms.TextInput(
        attrs={"placeholder": "Search notes, URL, location..."}
    ))
    platform = forms.ModelChoiceField(
        queryset=Platform.objects.none(), required=False, empty_label="All platforms"
    )
    status = forms.ChoiceField(
        choices=[("", "All statuses")] + list(Incident.Status.choices),
        required=False,
    )
    confidence = forms.ChoiceField(
        choices=[("", "All")] + list(Incident.Confidence.choices),
        required=False,
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            self.fields["platform"].queryset = Platform.objects.filter(project=project)
