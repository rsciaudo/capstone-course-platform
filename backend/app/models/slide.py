from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Slide(Base):
    __tablename__ = "slides"

    content_item_id: Mapped[int] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    slide_data: Mapped[str] = mapped_column(Text)

    content_item: Mapped["ContentItem"] = relationship(back_populates="slide")
