from django.contrib import admin

from .models import Upload


@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "original_name", "content_type", "created_at")
    readonly_fields = ("public_id", "s3_key", "created_at")
    search_fields = ("title", "original_name", "s3_key")
