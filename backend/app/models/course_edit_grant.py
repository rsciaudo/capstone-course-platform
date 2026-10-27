from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CourseEditGrant(Base):
    __tablename__ = "course_edit_grants"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)

    user: Mapped["User"] = relationship(back_populates="edit_grants")
    course: Mapped["Course"] = relationship(back_populates="edit_grants")

    __table_args__ = (UniqueConstraint("user_id", "course_id"),)
