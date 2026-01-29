from django.db import models


class Upload(models.Model):
    title = models.CharField(max_length=120)
    s3_key = models.CharField(max_length=512, blank=True, null=True)
    original_name = models.CharField(max_length=255, blank=True, null=True)
    content_type = models.CharField(max_length=120, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - {self.title}"
