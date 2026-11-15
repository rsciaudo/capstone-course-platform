from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.content_access import (
    commit_or_conflict,
    get_content_or_404,
    require_edit_content,
    require_edit_module,
    to_content_read,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models import ContentItem, Slide, User
from app.schemas.content import SlideContentRead, SlideCreate, SlideUpdate

router = APIRouter(prefix="/slides", tags=["slides"])

POSITION_CONFLICT = "A content item with this position already exists"


async def _get_slide_or_404(db: AsyncSession, content_id: int) -> ContentItem:
    item = await get_content_or_404(db, content_id)
    if item.type != "slide" or item.slide is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Slide not found"
        )
    return item


@router.post("", response_model=SlideContentRead, status_code=status.HTTP_201_CREATED)
async def create_slide(
    slide_data: SlideCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_edit_module(db, current_user, slide_data.module_id)
    item = ContentItem(
        module_id=slide_data.module_id,
        type="slide",
        title=slide_data.title,
        position=slide_data.position,
        slide=Slide(slide_data=slide_data.slide_data),
    )
    db.add(item)
    await commit_or_conflict(db, POSITION_CONFLICT)
    saved = await get_content_or_404(db, item.id)
    return to_content_read(saved)


@router.patch("/{content_id}", response_model=SlideContentRead)
async def update_slide(
    content_id: int,
    slide_data: SlideUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_slide_or_404(db, content_id)
    await require_edit_content(db, current_user, item)
    if item.slide is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Slide not found"
        )
    item.slide.slide_data = slide_data.slide_data
    await commit_or_conflict(db, POSITION_CONFLICT)
    saved = await get_content_or_404(db, item.id)
    return to_content_read(saved)
