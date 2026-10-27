from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    name: Mapped[str] = mapped_column(Text)
    position: Mapped[int]

    course: Mapped["Course"] = relationship(back_populates="modules")
    content_items: Mapped[list["ContentItem"]] = relationship(back_populates="module")

    __table_args__ = (
        CheckConstraint("position > 0", name="modules_position_check"),
        UniqueConstraint("course_id", "position"),
    )
