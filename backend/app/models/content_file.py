from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ContentFile(Base):
    __tablename__ = "files"

    content_item_id: Mapped[int] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    filename: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(Text)
    storage_path: Mapped[str] = mapped_column(Text)

    content_item: Mapped["ContentItem"] = relationship(back_populates="file")
