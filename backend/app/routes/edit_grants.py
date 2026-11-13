from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    can_edit_course,
    get_course_or_404,
    get_current_user,
    get_user_or_404,
)
from app.models import Course, CourseEditGrant, Group, User
from app.schemas.edit_grant import EditGrantCreate, EditGrantRead, EditGrantUpdate

router = APIRouter(prefix="/edit-grants", tags=["edit-grants"])


def _visible_edit_grants(current_user: User):
    query = (
        select(CourseEditGrant)
        .join(Course, CourseEditGrant.course_id == Course.id)
        .order_by(CourseEditGrant.id)
    )
    if current_user.role == "admin":
        return query.join(Group, Course.group_id == Group.id).where(
            Group.created_by == current_user.id
        )
    if current_user.role == "educator":
        return query.where(Course.group_id == current_user.group_id)
    if current_user.role != "super-user":
        return query.where(CourseEditGrant.id.is_(None))
    return query


async def _get_edit_grant_or_404(
    db: AsyncSession, grant_id: int
) -> CourseEditGrant:
    result = await db.execute(
        select(CourseEditGrant).where(CourseEditGrant.id == grant_id)
    )
    grant = result.scalar_one_or_none()
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Edit grant not found"
        )
    return grant


def _require_educator(user: User, course: Course) -> None:
    if user.role != "educator":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Edit grant requires an educator",
        )
    if user.group_id != course.group_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Educator must belong to this course's group",
        )


@router.get("", response_model=list[EditGrantRead])
async def list_edit_grants(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(_visible_edit_grants(current_user))
    return result.scalars().all()


@router.post("", response_model=EditGrantRead, status_code=status.HTTP_201_CREATED)
async def create_edit_grant(
    body: EditGrantCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course = await get_course_or_404(db, body.course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )

    user = await get_user_or_404(db, body.user_id)
    _require_educator(user, course)

    grant = CourseEditGrant(user_id=user.id, course_id=course.id)
    db.add(grant)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Edit grant already exists",
        )
    await db.refresh(grant)
    return grant


@router.patch("/{grant_id}", response_model=EditGrantRead)
async def update_edit_grant(
    grant_id: int,
    body: EditGrantUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    grant = await _get_edit_grant_or_404(db, grant_id)
    course = await get_course_or_404(db, grant.course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )

    updates = body.model_dump(exclude_unset=True)
    user_id = updates.get("user_id", grant.user_id)
    course_id = updates.get("course_id", grant.course_id)
    if course_id != grant.course_id:
        course = await get_course_or_404(db, course_id)
        if not await can_edit_course(db, current_user, course):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot edit this course",
            )

    user = await get_user_or_404(db, user_id)
    _require_educator(user, course)
    grant.user_id = user.id
    grant.course_id = course.id
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Edit grant already exists",
        )
    await db.refresh(grant)
    return grant


@router.delete("/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edit_grant(
    grant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    grant = await _get_edit_grant_or_404(db, grant_id)
    course = await get_course_or_404(db, grant.course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )

    await db.delete(grant)
    await db.commit()
