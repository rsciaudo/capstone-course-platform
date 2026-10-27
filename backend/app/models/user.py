from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), index=True)
    name: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text)

    group: Mapped["Group | None"] = relationship(back_populates="users")
    enrollments: Mapped[list["CourseEnrollment"]] = relationship(back_populates="user")
    edit_grants: Mapped[list["CourseEditGrant"]] = relationship(back_populates="user")

    __table_args__ = (
        CheckConstraint(
            "role IN ('super-user', 'admin', 'educator', 'student')",
            name="users_role_check",
        ),
        CheckConstraint(
            "(role IN ('educator', 'student') AND group_id IS NOT NULL) "
            "OR (role IN ('super-user', 'admin') AND group_id IS NULL)",
            name="users_group_membership_check",
        ),
    )
