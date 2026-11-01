from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.names import strip_name


class ModuleCreate(BaseModel):
    name: str = Field(min_length=1)
    course_id: int
    position: int = Field(ge=1)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name_field(cls, value: object) -> object:
        if value is None:
            raise ValueError("name cannot be empty")
        return strip_name(value)


class ModuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    position: int | None = Field(default=None, ge=1)

    @field_validator("name", "position", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("value cannot be empty")
        if isinstance(value, str):
            return strip_name(value)
        return value


class ModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    name: str
    position: int
    created_at: datetime
    updated_at: datetime
