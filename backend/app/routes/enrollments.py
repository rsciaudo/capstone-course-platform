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
from app.models import Course, CourseEnrollment, Group, User
from app.schemas.enrollment import EnrollmentCreate, EnrollmentRead, EnrollmentUpdate

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


def _visible_enrollments(current_user: User):
    query = (
        select(CourseEnrollment)
        .join(Course, CourseEnrollment.course_id == Course.id)
        .order_by(CourseEnrollment.id)
    )
    if current_user.role == "admin":
        return query.join(Group, Course.group_id == Group.id).where(
            Group.created_by == current_user.id
        )
    if current_user.role == "educator":
        return query.where(Course.group_id == current_user.group_id)
    if current_user.role == "student":
        return query.where(CourseEnrollment.user_id == current_user.id)
    if current_user.role != "super-user":
        return query.where(CourseEnrollment.id.is_(None))
    return query


async def _get_enrollment_or_404(
    db: AsyncSession, enrollment_id: int
) -> CourseEnrollment:
    result = await db.execute(
        select(CourseEnrollment).where(CourseEnrollment.id == enrollment_id)
    )
    enrollment = result.scalar_one_or_none()
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found"
        )
    return enrollment


def _require_student(user: User, course: Course) -> None:
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enrollment requires a student",
        )
    if user.group_id != course.group_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Student must belong to this course's group",
        )


@router.get("", response_model=list[EnrollmentRead])
async def list_enrollments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(_visible_enrollments(current_user))
    return result.scalars().all()


@router.post("", response_model=EnrollmentRead, status_code=status.HTTP_201_CREATED)
async def create_enrollment(
    body: EnrollmentCreate,
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
    _require_student(user, course)

    enrollment = CourseEnrollment(user_id=user.id, course_id=course.id)
    db.add(enrollment)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Enrollment already exists",
        )
    await db.refresh(enrollment)
    return enrollment


@router.patch("/{enrollment_id}", response_model=EnrollmentRead)
async def update_enrollment(
    enrollment_id: int,
    body: EnrollmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enrollment = await _get_enrollment_or_404(db, enrollment_id)
    course = await get_course_or_404(db, enrollment.course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )

    updates = body.model_dump(exclude_unset=True)
    user_id = updates.get("user_id", enrollment.user_id)
    course_id = updates.get("course_id", enrollment.course_id)
    if course_id != enrollment.course_id:
        course = await get_course_or_404(db, course_id)
        if not await can_edit_course(db, current_user, course):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot edit this course",
            )

    user = await get_user_or_404(db, user_id)
    _require_student(user, course)
    enrollment.user_id = user.id
    enrollment.course_id = course.id
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Enrollment already exists",
        )
    await db.refresh(enrollment)
    return enrollment


@router.delete("/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enrollment(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    enrollment = await _get_enrollment_or_404(db, enrollment_id)
    course = await get_course_or_404(db, enrollment.course_id)
    if not await can_edit_course(db, current_user, course):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this course",
        )

    await db.delete(enrollment)
    await db.commit()
