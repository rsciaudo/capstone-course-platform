from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import can_edit_course, can_view_course, get_course_or_404
from app.models import ContentItem, Course, Module, QuizQuestion
from app.schemas.content import (
    FileContentRead,
    QuestionRead,
    QuizContentRead,
    SlideContentRead,
)


def content_load_options():
    return (
        selectinload(ContentItem.file),
        selectinload(ContentItem.slide),
        selectinload(ContentItem.questions).selectinload(QuizQuestion.choices),
    )


async def get_content_or_404(db: AsyncSession, content_id: int) -> ContentItem:
    result = await db.execute(
        select(ContentItem)
        .where(ContentItem.id == content_id)
        .options(*content_load_options())
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
        )
    return item


async def get_module_or_404(db: AsyncSession, module_id: int) -> Module:
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Module not found"
        )
    return module


async def course_for_module(db: AsyncSession, module: Module) -> Course:
    return await get_course_or_404(db, module.course_id)


async def course_for_content(db: AsyncSession, item: ContentItem) -> Course:
    module = await get_module_or_404(db, item.module_id)
    return await course_for_module(db, module)


async def require_view_content(db: AsyncSession, user, item: ContentItem) -> Course:
    course = await course_for_content(db, item)
    if not await can_view_course(db, user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view this course",
        )
    return course


async def require_edit_content(db: AsyncSession, user, item: ContentItem) -> Course:
    course = await course_for_content(db, item)
    if not await can_edit_course(db, user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )
    return course


async def require_edit_module(db: AsyncSession, user, module_id: int) -> Module:
    module = await get_module_or_404(db, module_id)
    course = await course_for_module(db, module)
    if not await can_edit_course(db, user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )
    return module


async def commit_or_conflict(db: AsyncSession, detail: str) -> None:
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def to_content_read(item: ContentItem):
    if item.type == "file":
        if item.file is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File record is missing",
            )
        return FileContentRead(
            id=item.id,
            module_id=item.module_id,
            type="file",
            title=item.title,
            position=item.position,
            filename=item.file.filename,
            content_type=item.file.content_type,
        )
    if item.type == "quiz":
        return QuizContentRead(
            id=item.id,
            module_id=item.module_id,
            type="quiz",
            title=item.title,
            position=item.position,
            questions=[QuestionRead.model_validate(question) for question in item.questions],
        )
    if item.type == "slide":
        if item.slide is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Slide record is missing",
            )
        return SlideContentRead(
            id=item.id,
            module_id=item.module_id,
            type="slide",
            title=item.title,
            position=item.position,
            slide_data=item.slide.slide_data,
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unknown content type",
    )


def require_question_shape(choices: list) -> None:
    correct = sum(1 for choice in choices if choice.is_correct)
    if len(choices) < 2 or correct != 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A question needs at least two choices and exactly one correct choice",
        )
