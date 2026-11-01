from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", use_alter=True),
        index=True,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="group",
        foreign_keys="User.group_id",
    )
    creator: Mapped["User | None"] = relationship(
        foreign_keys=[created_by],
    )
    courses: Mapped[list["Course"]] = relationship(back_populates="group")
