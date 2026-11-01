from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Course, CourseEditGrant, CourseEnrollment, Group, User


async def get_current_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def can_view_group(user: User, group: Group) -> bool:
    if user.role == "super-user":
        return True
    if group.created_by is None:
        return False
    if user.role == "admin":
        return group.created_by == user.id
    return group.id == user.group_id


def can_edit_group(user: User, group: Group) -> bool:
    if user.role == "super-user":
        return True
    if group.created_by is None or user.role != "admin":
        return False
    return group.created_by == user.id


async def load_group(db: AsyncSession, group_id: int) -> Group | None:
    result = await db.execute(select(Group).where(Group.id == group_id))
    return result.scalar_one_or_none()


async def _has_enrollment(db: AsyncSession, user_id: int, course_id: int) -> bool:
    result = await db.execute(
        select(CourseEnrollment.id).where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def _has_edit_grant(db: AsyncSession, user_id: int, course_id: int) -> bool:
    result = await db.execute(
        select(CourseEditGrant.id).where(
            CourseEditGrant.user_id == user_id,
            CourseEditGrant.course_id == course_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def can_view_course(db: AsyncSession, user: User, course: Course) -> bool:
    if user.role == "super-user":
        return True
    if user.role == "admin":
        group = await load_group(db, course.group_id)
        return group is not None and group.created_by == user.id
    if user.role == "educator":
        return course.group_id == user.group_id
    if user.role == "student":
        return await _has_enrollment(db, user.id, course.id)
    return False


async def can_edit_course(db: AsyncSession, user: User, course: Course) -> bool:
    if user.role == "super-user":
        return True
    if user.role == "admin":
        group = await load_group(db, course.group_id)
        return group is not None and group.created_by == user.id
    if user.role == "educator":
        if course.group_id != user.group_id:
            return False
        return await _has_edit_grant(db, user.id, course.id)
    return False


async def get_course_or_404(db: AsyncSession, course_id: int) -> Course:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    return course
