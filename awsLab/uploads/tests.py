import io
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import Upload


def make_image_file(fmt="JPEG", name="test.jpg"):
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buf, format=fmt)
    buf.seek(0)
    buf.name = name
    return buf


class AuthRequiredTests(TestCase):
    """Antes, upload/list/view eran públicas: cualquiera podía subir y listar
    todo lo que subieron otros. Estos tests fijan que ahora exigen login."""

    def test_list_requires_login(self):
        response = self.client.get(reverse("uploads:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_upload_requires_login(self):
        response = self.client.get(reverse("uploads:upload"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_view_file_requires_login(self):
        upload = Upload.objects.create(title="x", s3_key="images/x.jpg")
        response = self.client.get(reverse("uploads:view", args=[upload.public_id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


class UploadFormValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="s3cret-pass-1")
        self.client.login(username="tester", password="s3cret-pass-1")

    @patch("uploads.views.upload_fileobj", return_value="images/fake.jpg")
    def test_valid_image_upload_creates_record(self, mock_upload):
        response = self.client.post(reverse("uploads:upload"), {
            "title": "Foto",
            "image": make_image_file(),
        })
        self.assertRedirects(response, reverse("uploads:list"))
        self.assertEqual(Upload.objects.count(), 1)
        mock_upload.assert_called_once()

    def test_oversized_file_rejected(self):
        with self.settings(MAX_UPLOAD_SIZE_MB=0):
            response = self.client.post(reverse("uploads:upload"), {
                "title": "Foto",
                "image": make_image_file(),
            })
        self.assertEqual(Upload.objects.count(), 0)
        self.assertContains(response, "tamaño máximo")

    def test_non_image_file_rejected(self):
        fake = io.BytesIO(b"esto no es una imagen")
        fake.name = "malware.jpg"
        response = self.client.post(reverse("uploads:upload"), {
            "title": "Foto",
            "image": fake,
        })
        self.assertEqual(Upload.objects.count(), 0)


class ViewFileTests(TestCase):
    """El pk autoincremental permitía enumerar /files/1/, /files/2/... Ahora
    la URL pública usa un UUID no adivinable."""

    def setUp(self):
        self.user = User.objects.create_user(username="tester2", password="s3cret-pass-2")
        self.client.login(username="tester2", password="s3cret-pass-2")

    def test_unknown_public_id_returns_404(self):
        response = self.client.get(
            reverse("uploads:view", args=["11111111-1111-1111-1111-111111111111"])
        )
        self.assertEqual(response.status_code, 404)

    def test_sequential_int_id_is_not_a_valid_url(self):
        Upload.objects.create(title="x", s3_key="images/x.jpg")
        response = self.client.get("/files/1/view/")
        self.assertEqual(response.status_code, 404)

    @patch(
        "uploads.views.presigned_get_url",
        return_value="https://example-bucket.s3.amazonaws.com/signed",
    )
    def test_view_file_redirects_to_presigned_url(self, mock_presign):
        upload = Upload.objects.create(title="x", s3_key="images/x.jpg")
        response = self.client.get(reverse("uploads:view", args=[upload.public_id]))
        self.assertRedirects(
            response,
            "https://example-bucket.s3.amazonaws.com/signed",
            fetch_redirect_response=False,
        )
        mock_presign.assert_called_once_with("images/x.jpg", expires_seconds=60)
