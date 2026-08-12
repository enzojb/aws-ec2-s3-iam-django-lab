from django import forms
from django.conf import settings
from PIL import Image

ALLOWED_IMAGE_FORMATS = {
    "JPEG": "jpg",
    "PNG": "png",
    "GIF": "gif",
    "WEBP": "webp",
}


class UploadForm(forms.Form):
    title = forms.CharField(max_length=120)
    image = forms.ImageField()

    def clean_image(self):
        image = self.cleaned_data["image"]

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if image.size > max_bytes:
            raise forms.ValidationError(
                f"El archivo supera el tamaño máximo permitido ({settings.MAX_UPLOAD_SIZE_MB} MB)."
            )

        image.seek(0)
        try:
            with Image.open(image) as img:
                img.verify()
                detected_format = img.format
        except Exception:
            raise forms.ValidationError("El archivo no es una imagen válida.")
        image.seek(0)

        if detected_format not in ALLOWED_IMAGE_FORMATS:
            raise forms.ValidationError("Formato no permitido. Usá JPG, PNG, GIF o WEBP.")

        image.detected_extension = ALLOWED_IMAGE_FORMATS[detected_format]
        return image
