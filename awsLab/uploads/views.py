from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from django.contrib import messages

from .forms import UploadForm
from .models import Upload
from .s3_service import build_key, upload_fileobj, presigned_get_url, S3NotConfiguredError

def upload_view(request):
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data["image"]
            title = form.cleaned_data["title"]

            key = build_key(f.name)

            try:
                upload_fileobj(f.file, key=key, content_type=getattr(f, "content_type", None))
            except S3NotConfiguredError as e:
                messages.warning(request, str(e))
                return render(request, "uploads/upload.html", {"form": form})
            except Exception:
                messages.error(request, "Error subiendo el archivo a S3. Revisá permisos/configuración.")
                return render(request, "uploads/upload.html", {"form": form})

            Upload.objects.create(
                title=title,
                s3_key=key,
                original_name=f.name,
                content_type=getattr(f, "content_type", None),
            )
            messages.success(request, "Archivo subido correctamente a S3.")
            return redirect("uploads:list")
    else:
        form = UploadForm()

    return render(request, "uploads/upload.html", {"form": form})

def list_view(request):
    items = Upload.objects.order_by("-created_at")
    return render(request, "uploads/list.html", {"items": items})

def view_file(request, pk: int):
    item = get_object_or_404(Upload, pk=pk)
    if not item.s3_key:
        return HttpResponseBadRequest("Este registro no tiene s3_key")

    try:
        url = presigned_get_url(item.s3_key, expires_seconds=60)
    except S3NotConfiguredError as e:
        messages.warning(request, str(e))
        return redirect("uploads:list")
    except Exception:
        messages.error(request, "No se pudo generar el enlace. Revisá configuración/permisos.")
        return redirect("uploads:list")

    return redirect(url)