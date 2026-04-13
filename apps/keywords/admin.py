from django.contrib import admin

from .models import Keyword


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ("term", "language", "category", "status", "shared", "added_by", "date_added")
    list_filter = ("status", "language", "category", "project")
    search_fields = ("term",)
