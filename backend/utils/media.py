import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from backend.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def save_upload(file: UploadFile) -> str:
    """Save an uploaded file and return its public URL path."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported file type: {file.content_type}")

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest = upload_dir / filename

    async with aiofiles.open(dest, "wb") as f:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise ValueError("File too large (max 10 MB)")
        await f.write(content)

    return f"/uploads/{filename}"
