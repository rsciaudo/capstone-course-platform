from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_access import (
    commit_or_conflict,
    content_load_options,
    get_content_or_404,
    get_module_or_404,
    require_edit_content,
    require_view_content,
    to_content_read,
)
from app.database import get_db
from app.dependencies import can_view_course, get_course_or_404, get_current_user
from app.file_storage import remove_stored_file
from app.models import ContentItem, Course, CourseEnrollment, Group, Module, User
from app.schemas.content import ContentRead, ContentUpdate

router = APIRouter(prefix="/content", tags=["content"])

POSITION_CONFLICT = "A content item with this position already exists"


def _visible_content_query(current_user: User):
    query = (
        select(ContentItem)
        .join(Module, ContentItem.module_id == Module.id)
        .join(Course, Module.course_id == Course.id)
        .order_by(ContentItem.module_id, ContentItem.position)
        .options(*content_load_options())
    )
    if current_user.role == "admin":
        query = query.join(Group, Course.group_id == Group.id).where(
            Group.created_by == current_user.id
        )
    elif current_user.role == "educator":
        query = query.where(Course.group_id == current_user.group_id)
    elif current_user.role == "student":
        query = query.join(
            CourseEnrollment, CourseEnrollment.course_id == Course.id
        ).where(CourseEnrollment.user_id == current_user.id)
    elif current_user.role != "super-user":
        query = query.where(ContentItem.id.is_(None))
    return query


@router.get("", response_model=list[ContentRead])
async def list_content(
    module_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if module_id is not None:
        module = await get_module_or_404(db, module_id)
        course = await get_course_or_404(db, module.course_id)
        if not await can_view_course(db, current_user, course):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot view this course",
            )
        result = await db.execute(
            select(ContentItem)
            .where(ContentItem.module_id == module_id)
            .order_by(ContentItem.position)
            .options(*content_load_options())
        )
        return [to_content_read(item) for item in result.scalars().unique().all()]

    result = await db.execute(_visible_content_query(current_user))
    return [to_content_read(item) for item in result.scalars().unique().all()]


@router.get("/{content_id}", response_model=ContentRead)
async def get_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await get_content_or_404(db, content_id)
    await require_view_content(db, current_user, item)
    return to_content_read(item)


@router.patch("/{content_id}", response_model=ContentRead)
async def update_content(
    content_id: int,
    content_data: ContentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await get_content_or_404(db, content_id)
    await require_edit_content(db, current_user, item)
    for field, value in content_data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await commit_or_conflict(db, POSITION_CONFLICT)
    item = await get_content_or_404(db, content_id)
    return to_content_read(item)


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await get_content_or_404(db, content_id)
    await require_edit_content(db, current_user, item)
    storage_path = item.file.storage_path if item.file is not None else None
    await db.delete(item)
    await commit_or_conflict(db, "Content is still referenced by another record")
    remove_stored_file(storage_path)
