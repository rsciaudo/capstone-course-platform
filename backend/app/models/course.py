from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    name: Mapped[str] = mapped_column(Text)

    group: Mapped["Group"] = relationship(back_populates="courses")
    modules: Mapped[list["Module"]] = relationship(back_populates="course")
    enrollments: Mapped[list["CourseEnrollment"]] = relationship(back_populates="course")
    edit_grants: Mapped[list["CourseEditGrant"]] = relationship(back_populates="course")
