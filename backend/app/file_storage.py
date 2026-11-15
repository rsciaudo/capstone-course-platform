import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status


def storage_dir() -> Path:
    directory = Path(os.environ.get("FILE_STORAGE_DIR", "/app/uploads"))
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def normalized_type(value: str | None) -> str:
    if not value:
        return ""
    return value.split(";", 1)[0].strip().lower()


def is_allowed_type(value: str) -> bool:
    return value == "application/pdf" or value.startswith("image/")


def safe_filename(name: str | None) -> str:
    if not name:
        return "upload"
    base = Path(name).name.strip()
    return base or "upload"


async def save_upload(upload: UploadFile) -> tuple[Path, str, str]:
    content_type = normalized_type(upload.content_type)
    if not is_allowed_type(content_type):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be an image or PDF",
        )
    data = await upload.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is empty",
        )
    path = storage_dir() / uuid4().hex
    path.write_bytes(data)
    return path, safe_filename(upload.filename), content_type


def remove_stored_file(path: str | None) -> None:
    if not path:
        return
    Path(path).unlink(missing_ok=True)
