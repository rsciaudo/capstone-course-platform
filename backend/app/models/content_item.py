from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"))
    type: Mapped[str] = mapped_column(Text)
    position: Mapped[int]

    module: Mapped["Module"] = relationship(back_populates="content_items")

    __table_args__ = (
        CheckConstraint(
            "type IN ('quiz', 'file', 'slide')",
            name="content_items_type_check",
        ),
        CheckConstraint("position > 0", name="content_items_position_check"),
        UniqueConstraint("module_id", "position"),
    )
