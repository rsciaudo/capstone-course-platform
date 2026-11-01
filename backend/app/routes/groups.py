from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import can_edit_group, can_view_group, get_current_user
from app.models import Group, User
from app.schemas.group import GroupCreate, GroupRead, GroupUpdate

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("", response_model=list[GroupRead])
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Group).order_by(Group.id)
    if current_user.role == "admin":
        query = query.where(Group.created_by == current_user.id)
    elif current_user.role in ("educator", "student"):
        query = query.where(
            Group.id == current_user.group_id,
            Group.created_by.is_not(None),
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{group_id}", response_model=GroupRead)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    if not can_view_group(current_user, group):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view this group",
        )
    return group


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("super-user", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot create groups"
        )
    group = Group(name=group_data.name, created_by=current_user.id)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.patch("/{group_id}", response_model=GroupRead)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    if not can_edit_group(current_user, group):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot edit this group"
        )

    for field, value in group_data.model_dump(exclude_unset=True).items():
        setattr(group, field, value)

    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Group not found"
        )
    if not can_edit_group(current_user, group):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot edit this group"
        )

    await db.delete(group)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Group is still referenced by another record",
        )
