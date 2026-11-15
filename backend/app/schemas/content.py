from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.names import strip_name


def _strip_required(value: object) -> object:
    if value is None:
        raise ValueError("value cannot be empty")
    return strip_name(value)


class ContentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    position: int | None = Field(default=None, ge=1)

    @field_validator("title", "position", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("value cannot be empty")
        if isinstance(value, str):
            return strip_name(value)
        return value


class SlideCreate(BaseModel):
    module_id: int
    title: str = Field(min_length=1)
    position: int = Field(ge=1)
    slide_data: str

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        return _strip_required(value)


class SlideUpdate(BaseModel):
    slide_data: str


class QuizCreate(BaseModel):
    module_id: int
    title: str = Field(min_length=1)
    position: int = Field(ge=1)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        return _strip_required(value)


class ChoiceCreate(BaseModel):
    text: str = Field(min_length=1)
    position: int = Field(ge=1)
    is_correct: bool

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return _strip_required(value)


class QuestionCreate(BaseModel):
    text: str = Field(min_length=1)
    position: int = Field(ge=1)
    choices: list[ChoiceCreate] = Field(min_length=2)

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return _strip_required(value)

    @model_validator(mode="after")
    def one_correct_choice(self) -> "QuestionCreate":
        correct = sum(1 for choice in self.choices if choice.is_correct)
        if correct != 1:
            raise ValueError("exactly one choice must be correct")
        positions = [choice.position for choice in self.choices]
        if len(positions) != len(set(positions)):
            raise ValueError("choice positions must be unique")
        return self


class QuestionUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1)
    position: int | None = Field(default=None, ge=1)

    @field_validator("text", "position", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("value cannot be empty")
        if isinstance(value, str):
            return strip_name(value)
        return value


class ChoiceUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1)
    position: int | None = Field(default=None, ge=1)
    is_correct: bool | None = None

    @field_validator("text", "position", "is_correct", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("value cannot be empty")
        if isinstance(value, str):
            return strip_name(value)
        return value


class ChoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    position: int
    is_correct: bool


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    position: int
    choices: list[ChoiceRead]


class FileContentRead(BaseModel):
    id: int
    module_id: int
    type: Literal["file"]
    title: str
    position: int
    filename: str
    content_type: str


class QuizContentRead(BaseModel):
    id: int
    module_id: int
    type: Literal["quiz"]
    title: str
    position: int
    questions: list[QuestionRead]


class SlideContentRead(BaseModel):
    id: int
    module_id: int
    type: Literal["slide"]
    title: str
    position: int
    slide_data: str


ContentRead = Annotated[
    FileContentRead | QuizContentRead | SlideContentRead,
    Field(discriminator="type"),
]
