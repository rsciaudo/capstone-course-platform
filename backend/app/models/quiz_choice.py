from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class QuizChoice(Base):
    __tablename__ = "quiz_choices"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
    )
    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    position: Mapped[int]

    question: Mapped["QuizQuestion"] = relationship(back_populates="choices")

    __table_args__ = (
        CheckConstraint("position > 0", name="quiz_choices_position_check"),
        CheckConstraint("btrim(text) <> ''", name="quiz_choices_text_check"),
        UniqueConstraint("question_id", "position"),
    )
