import asyncio
import requests
from fastapi import UploadFile

from backend.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def save_upload(file: UploadFile) -> str:
    """Upload a file to ImgBB and return its public URL."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported file type: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File too large (max 10 MB)")

    def _upload():
        resp = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": settings.IMGBB_API_KEY},
            files={"image": (file.filename or "image.jpg", content)}
        )
        resp.raise_for_status()
        return resp.json()["data"]["url"]

    try:
        url = await asyncio.to_thread(_upload)
        return url
    except Exception as e:
        raise ValueError(f"Failed to upload image to cloud storage: {e}")
