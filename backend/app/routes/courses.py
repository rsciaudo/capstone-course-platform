from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    can_edit_course,
    can_view_course,
    can_view_group,
    get_course_or_404,
    get_current_user,
    load_group,
)
from app.models import Course, CourseEditGrant, CourseEnrollment, Group, User
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseRead])
async def list_courses(
    group_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if group_id is not None:
        group = await load_group(db, group_id)
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
            )
        if not can_view_group(current_user, group):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot view this group",
            )

    query = select(Course).order_by(Course.id)
    if current_user.role == "admin":
        query = (
            select(Course)
            .join(Group, Course.group_id == Group.id)
            .where(Group.created_by == current_user.id)
            .order_by(Course.id)
        )
    elif current_user.role == "educator":
        query = query.where(Course.group_id == current_user.group_id)
    elif current_user.role == "student":
        query = (
            select(Course)
            .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
            .where(CourseEnrollment.user_id == current_user.id)
            .order_by(Course.id)
        )
    elif current_user.role != "super-user":
        query = query.where(Course.id.is_(None))
    if group_id is not None:
        query = query.where(Course.group_id == group_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course = await get_course_or_404(db, course_id)
    if not await can_view_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view this course",
        )
    return course


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("super-user", "admin", "educator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot create courses"
        )
    if (
        current_user.role == "educator"
        and course_data.group_id != current_user.group_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot create a course in this group",
        )

    group = await load_group(db, course_data.group_id)
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    if current_user.role == "admin" and group.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot create a course in this group",
        )

    course = Course(
        name=course_data.name,
        group_id=course_data.group_id,
        created_by=current_user.id,
    )
    db.add(course)
    if current_user.role == "educator":
        await db.flush()
        db.add(CourseEditGrant(user_id=current_user.id, course_id=course.id))
    await db.commit()
    await db.refresh(course)
    return course


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course = await get_course_or_404(db, course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )

    for field, value in course_data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    await db.commit()
    await db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    course = await get_course_or_404(db, course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )

    # Grants and enrollments belong to the course, so they go with it.
    # Modules are left in place and make this delete return 409.
    enrollment_rows = await db.execute(
        select(CourseEnrollment).where(CourseEnrollment.course_id == course.id)
    )
    for enrollment in enrollment_rows.scalars().all():
        await db.delete(enrollment)
    grant_rows = await db.execute(
        select(CourseEditGrant).where(CourseEditGrant.course_id == course.id)
    )
    for grant in grant_rows.scalars().all():
        await db.delete(grant)
    await db.flush()

    await db.delete(course)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course is still referenced by another record",
        )
