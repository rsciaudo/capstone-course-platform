from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    can_edit_course,
    can_view_course,
    get_course_or_404,
    get_current_user,
)
from app.models import Course, CourseEnrollment, Group, Module, User
from app.schemas.module import ModuleCreate, ModuleRead, ModuleUpdate

router = APIRouter(prefix="/modules", tags=["modules"])


async def _get_module_or_404(db: AsyncSession, module_id: int) -> Module:
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Module not found"
        )
    return module


@router.get("", response_model=list[ModuleRead])
async def list_modules(
    course_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if course_id is not None:
        course = await get_course_or_404(db, course_id)
        if not await can_view_course(db, current_user, course):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot view this course",
            )
        result = await db.execute(
            select(Module)
            .where(Module.course_id == course_id)
            .order_by(Module.position)
        )
        return result.scalars().all()

    query = (
        select(Module)
        .join(Course, Module.course_id == Course.id)
        .order_by(Module.course_id, Module.position)
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
        query = query.where(Module.id.is_(None))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{module_id}", response_model=ModuleRead)
async def get_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    module = await _get_module_or_404(db, module_id)
    course = await get_course_or_404(db, module.course_id)
    if not await can_view_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view this course",
        )
    return module


@router.post("", response_model=ModuleRead, status_code=status.HTTP_201_CREATED)
async def create_module(
    module_data: ModuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course = await get_course_or_404(db, module_data.course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )
    module = Module(
        name=module_data.name,
        course_id=module_data.course_id,
        position=module_data.position,
    )
    db.add(module)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A module with this position already exists",
        )
    await db.refresh(module)
    return module


@router.patch("/{module_id}", response_model=ModuleRead)
async def update_module(
    module_id: int,
    module_data: ModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    module = await _get_module_or_404(db, module_id)
    course = await get_course_or_404(db, module.course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )

    for field, value in module_data.model_dump(exclude_unset=True).items():
        setattr(module, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A module with this position already exists",
        )
    await db.refresh(module)
    return module


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    module = await _get_module_or_404(db, module_id)
    course = await get_course_or_404(db, module.course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )

    await db.delete(module)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Module is still referenced by another record",
        )
