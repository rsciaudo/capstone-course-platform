from app.schemas.names import strip_name
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

class CourseCreate(BaseModel):
    name: str = Field(min_length=1)
    group_id: int

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("name cannot be empty")
        return strip_name(value)


class CourseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("name cannot be empty")
        return strip_name(value)

class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    group_id: int
    created_by: int | None
    created_at: datetime
    updated_at: datetime