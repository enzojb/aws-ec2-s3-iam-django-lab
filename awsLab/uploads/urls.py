from django.urls import path
from . import views

app_name = "uploads"

urlpatterns = [
    path("upload/", views.upload_view, name="upload"),
    path("files/", views.list_view, name="list"),
    path("files/<uuid:public_id>/view/", views.view_file, name="view"),
]
