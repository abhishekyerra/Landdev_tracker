"""
Storage service for project documents.
Uses Google Cloud Storage when configured, with local fallback.
"""

from __future__ import annotations

from datetime import timedelta
import logging
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

try:
    from google.cloud import storage
except Exception:  # pragma: no cover
    storage = None

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self) -> None:
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "").strip()
        self.signed_url_ttl = int(os.getenv("GCS_SIGNED_URL_TTL_SECONDS", "3600"))
        self.local_upload_dir = Path(os.getenv("LOCAL_UPLOAD_DIR", "/app/uploads"))
        self.local_upload_dir.mkdir(parents=True, exist_ok=True)

        self.client = None
        self.bucket = None
        if self.bucket_name and storage:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
            except Exception as exc:
                logger.error("Failed to initialize GCS client: %s", exc)
                self.bucket = None

    @property
    def using_gcs(self) -> bool:
        return self.bucket is not None

    def _parse_gs_uri(self, file_path: str) -> tuple[Optional[str], Optional[str]]:
        if not file_path.startswith("gs://"):
            return None, None
        parsed = urlparse(file_path)
        bucket_name = parsed.netloc or None
        object_name = parsed.path.lstrip("/") if parsed.path else None
        return bucket_name, object_name

    def upload_bytes(self, project_id: str, filename: str, content: bytes, content_type: Optional[str]) -> str:
        object_name = f"projects/{project_id}/{filename}"
        if self.using_gcs:
            blob = self.bucket.blob(object_name)
            blob.upload_from_string(content, content_type=content_type or "application/octet-stream")
            return f"gs://{self.bucket_name}/{object_name}"

        project_dir = self.local_upload_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        local_path = project_dir / filename
        local_path.write_bytes(content)
        return str(local_path)

    def delete_path(self, file_path: str) -> None:
        if file_path.startswith("gs://") and self.using_gcs:
            bucket_name, object_name = self._parse_gs_uri(file_path)
            if bucket_name and object_name:
                target_bucket = self.client.bucket(bucket_name)
                target_bucket.blob(object_name).delete()
            return

        local = Path(file_path)
        if local.exists():
            local.unlink()

    def read_bytes(self, file_path: str) -> bytes:
        if file_path.startswith("gs://") and self.using_gcs:
            bucket_name, object_name = self._parse_gs_uri(file_path)
            if bucket_name and object_name:
                target_bucket = self.client.bucket(bucket_name)
                return target_bucket.blob(object_name).download_as_bytes()
            raise FileNotFoundError(f"Invalid GCS path: {file_path}")

        return Path(file_path).read_bytes()

    def get_read_url(self, file_path: str) -> Optional[str]:
        if file_path.startswith("gs://") and self.using_gcs:
            bucket_name, object_name = self._parse_gs_uri(file_path)
            if not bucket_name or not object_name:
                return None
            blob = self.client.bucket(bucket_name).blob(object_name)
            try:
                return blob.generate_signed_url(version="v4", expiration=timedelta(seconds=self.signed_url_ttl), method="GET")
            except Exception as exc:
                logger.warning("Could not create signed URL: %s", exc)
                return None
        return None


storage_service = StorageService()
