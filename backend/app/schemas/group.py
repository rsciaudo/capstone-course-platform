from app.schemas.names import strip_name
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GroupCreate(BaseModel):
    name: str = Field(min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("name cannot be empty")
        return strip_name(value)


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("name cannot be empty")
        return strip_name(value)


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_by: int | None
    created_at: datetime
    updated_at: datetime
