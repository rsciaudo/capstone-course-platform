from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)

    users: Mapped[list["User"]] = relationship(back_populates="group")
    courses: Mapped[list["Course"]] = relationship(back_populates="group")
