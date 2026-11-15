from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.content_access import (
    commit_or_conflict,
    get_content_or_404,
    require_edit_content,
    require_edit_module,
    require_question_shape,
    to_content_read,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models import ContentItem, QuizChoice, QuizQuestion, User
from app.schemas.content import (
    ChoiceCreate,
    ChoiceRead,
    ChoiceUpdate,
    QuestionCreate,
    QuestionRead,
    QuestionUpdate,
    QuizContentRead,
    QuizCreate,
)

router = APIRouter(tags=["quizzes"])

CONTENT_POSITION_CONFLICT = "A content item with this position already exists"
QUESTION_POSITION_CONFLICT = "A question with this position already exists"
CHOICE_POSITION_CONFLICT = "A choice with this position already exists"


async def _get_quiz_or_404(db: AsyncSession, content_id: int) -> ContentItem:
    item = await get_content_or_404(db, content_id)
    if item.type != "quiz":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return item


async def _get_question_or_404(db: AsyncSession, question_id: int) -> QuizQuestion:
    result = await db.execute(
        select(QuizQuestion)
        .where(QuizQuestion.id == question_id)
        .options(selectinload(QuizQuestion.choices), selectinload(QuizQuestion.content_item))
    )
    question = result.scalar_one_or_none()
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )
    return question


async def _get_choice_or_404(db: AsyncSession, choice_id: int) -> QuizChoice:
    result = await db.execute(
        select(QuizChoice)
        .where(QuizChoice.id == choice_id)
        .options(
            selectinload(QuizChoice.question).selectinload(QuizQuestion.choices),
            selectinload(QuizChoice.question).selectinload(QuizQuestion.content_item),
        )
    )
    choice = result.scalar_one_or_none()
    if choice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Choice not found"
        )
    return choice


def _question_read(question: QuizQuestion) -> QuestionRead:
    return QuestionRead.model_validate(question)


@router.post("/quizzes", response_model=QuizContentRead, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_data: QuizCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_edit_module(db, current_user, quiz_data.module_id)
    item = ContentItem(
        module_id=quiz_data.module_id,
        type="quiz",
        title=quiz_data.title,
        position=quiz_data.position,
    )
    db.add(item)
    await commit_or_conflict(db, CONTENT_POSITION_CONFLICT)
    saved = await get_content_or_404(db, item.id)
    return to_content_read(saved)


@router.post(
    "/quizzes/{content_id}/questions",
    response_model=QuestionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    content_id: int,
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_quiz_or_404(db, content_id)
    await require_edit_content(db, current_user, item)
    question = QuizQuestion(
        content_item_id=item.id,
        text=question_data.text,
        position=question_data.position,
        choices=[
            QuizChoice(
                text=choice.text,
                position=choice.position,
                is_correct=choice.is_correct,
            )
            for choice in question_data.choices
        ],
    )
    db.add(question)
    await commit_or_conflict(db, QUESTION_POSITION_CONFLICT)
    saved = await _get_question_or_404(db, question.id)
    return _question_read(saved)


@router.patch("/questions/{question_id}", response_model=QuestionRead)
async def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = await _get_question_or_404(db, question_id)
    await require_edit_content(db, current_user, question.content_item)
    for field, value in question_data.model_dump(exclude_unset=True).items():
        setattr(question, field, value)
    await commit_or_conflict(db, QUESTION_POSITION_CONFLICT)
    saved = await _get_question_or_404(db, question.id)
    return _question_read(saved)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = await _get_question_or_404(db, question_id)
    await require_edit_content(db, current_user, question.content_item)
    await db.delete(question)
    await commit_or_conflict(db, "Question is still referenced by another record")


@router.post(
    "/questions/{question_id}/choices",
    response_model=ChoiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_choice(
    question_id: int,
    choice_data: ChoiceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = await _get_question_or_404(db, question_id)
    await require_edit_content(db, current_user, question.content_item)
    if choice_data.is_correct:
        for existing in question.choices:
            existing.is_correct = False
    choice = QuizChoice(
        question_id=question.id,
        text=choice_data.text,
        position=choice_data.position,
        is_correct=choice_data.is_correct,
    )
    db.add(choice)
    question.choices.append(choice)
    require_question_shape(question.choices)
    await commit_or_conflict(db, CHOICE_POSITION_CONFLICT)
    await db.refresh(choice)
    return ChoiceRead.model_validate(choice)


@router.patch("/choices/{choice_id}", response_model=ChoiceRead)
async def update_choice(
    choice_id: int,
    choice_data: ChoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    choice = await _get_choice_or_404(db, choice_id)
    question = choice.question
    await require_edit_content(db, current_user, question.content_item)
    changes = choice_data.model_dump(exclude_unset=True)
    if changes.get("is_correct") is True:
        for existing in question.choices:
            if existing.id != choice.id:
                existing.is_correct = False
    for field, value in changes.items():
        setattr(choice, field, value)
    require_question_shape(question.choices)
    await commit_or_conflict(db, CHOICE_POSITION_CONFLICT)
    await db.refresh(choice)
    return ChoiceRead.model_validate(choice)


@router.delete("/choices/{choice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_choice(
    choice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    choice = await _get_choice_or_404(db, choice_id)
    question = choice.question
    await require_edit_content(db, current_user, question.content_item)
    remaining = [existing for existing in question.choices if existing.id != choice.id]
    require_question_shape(remaining)
    await db.delete(choice)
    await commit_or_conflict(db, "Choice is still referenced by another record")
