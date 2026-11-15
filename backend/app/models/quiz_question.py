from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_item_id: Mapped[int] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"),
    )
    text: Mapped[str] = mapped_column(Text)
    position: Mapped[int]

    content_item: Mapped["ContentItem"] = relationship(back_populates="questions")
    choices: Mapped[list["QuizChoice"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="QuizChoice.position",
    )

    __table_args__ = (
        CheckConstraint("position > 0", name="quiz_questions_position_check"),
        CheckConstraint("btrim(text) <> ''", name="quiz_questions_text_check"),
        UniqueConstraint("content_item_id", "position"),
    )
