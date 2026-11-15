from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_access import (
    commit_or_conflict,
    get_content_or_404,
    require_edit_content,
    require_edit_module,
    require_view_content,
    to_content_read,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.file_storage import remove_stored_file, save_upload
from app.models import ContentFile, ContentItem, User
from app.schemas.content import ContentUpdate, FileContentRead

router = APIRouter(prefix="/files", tags=["files"])

POSITION_CONFLICT = "A content item with this position already exists"


def _file_fields(title: str, position: int) -> ContentUpdate:
    try:
        fields = ContentUpdate.model_validate({"title": title, "position": position})
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc
    if fields.title is None or fields.position is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="title and position are required",
        )
    return fields


async def _get_file_or_404(db: AsyncSession, content_id: int) -> ContentItem:
    item = await get_content_or_404(db, content_id)
    if item.type != "file" or item.file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return item


@router.post("", response_model=FileContentRead, status_code=status.HTTP_201_CREATED)
async def create_file(
    module_id: int = Form(),
    title: str = Form(),
    position: int = Form(),
    file: UploadFile = File(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fields = _file_fields(title, position)
    await require_edit_module(db, current_user, module_id)
    path, filename, content_type = await save_upload(file)
    item = ContentItem(
        module_id=module_id,
        type="file",
        title=fields.title,
        position=fields.position,
        file=ContentFile(
            filename=filename,
            content_type=content_type,
            storage_path=str(path),
        ),
    )
    db.add(item)
    try:
        await commit_or_conflict(db, POSITION_CONFLICT)
    except Exception:
        remove_stored_file(str(path))
        raise
    saved = await get_content_or_404(db, item.id)
    return to_content_read(saved)


@router.get("/{content_id}")
async def download_file(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_file_or_404(db, content_id)
    await require_view_content(db, current_user, item)
    stored = item.file
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(
        stored.storage_path,
        media_type=stored.content_type,
        filename=stored.filename,
        content_disposition_type="inline",
    )


@router.patch("/{content_id}", response_model=FileContentRead)
async def replace_file(
    content_id: int,
    file: UploadFile = File(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_file_or_404(db, content_id)
    await require_edit_content(db, current_user, item)
    stored = item.file
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    path, filename, content_type = await save_upload(file)
    previous = stored.storage_path
    stored.filename = filename
    stored.content_type = content_type
    stored.storage_path = str(path)
    try:
        await commit_or_conflict(db, POSITION_CONFLICT)
    except Exception:
        remove_stored_file(str(path))
        raise
    remove_stored_file(previous)
    saved = await get_content_or_404(db, item.id)
    return to_content_read(saved)
