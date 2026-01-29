import uuid
import boto3
from django.conf import settings

class S3NotConfiguredError(RuntimeError):
    pass

def _ensure_s3_ready():
    if getattr(settings, "ENV", "local") != "production":
        raise S3NotConfiguredError(
            "Subida a S3 deshabilitada en entorno local. "
            "Este laboratorio está pensado para ejecutarse en AWS EC2 con un IAM Role."
        )

    if not settings.AWS_S3_BUCKET:
        raise S3NotConfiguredError(
            "Falta configurar AWS_S3_BUCKET. Completá el .env en el entorno de producción."
        )

def _s3_client():
    _ensure_s3_ready()
    return boto3.client("s3", region_name=settings.AWS_REGION)


def build_key(original_name: str) -> str:
    ext = ""
    if "." in original_name:
        ext = "." + original_name.rsplit(".", 1)[-1].lower()
    prefix = settings.S3_PREFIX or "images/"
    if not prefix.endswith("/"):
        prefix += "/"
    return f"{prefix}{uuid.uuid4().hex}{ext}"


def upload_fileobj(file_obj, key: str, content_type: str | None = None) -> str:
    s3 = _s3_client()
    extra = {}
    if content_type:
        extra["ContentType"] = content_type

    s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=settings.AWS_S3_BUCKET,
        Key=key,
        ExtraArgs=extra or None,
    )
    return key


def presigned_get_url(key: str, expires_seconds: int = 60) -> str:
    s3 = _s3_client()
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
        ExpiresIn=expires_seconds,
    )
