from app.schemas.names import strip_name
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Role = Literal["super-user", "admin", "educator", "student"]

GROUP_ROLES = frozenset({"educator", "student"})
UNGROUPED_ROLES = frozenset({"super-user", "admin"})


def check_group_membership(role: str, group_id: int | None) -> None:
    if role in GROUP_ROLES and group_id is None:
        raise ValueError("educator and student require a group_id")
    if role in UNGROUPED_ROLES and group_id is not None:
        raise ValueError("super-user and admin must not have a group_id")


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    role: Role
    group_id: int | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("name cannot be empty")
        return strip_name(value)

    @model_validator(mode="after")
    def validate_group_membership(self):
        check_group_membership(self.role, self.group_id)
        return self


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    role: Role | None = None
    group_id: int | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        if value is None:
            raise ValueError("name cannot be empty")
        return strip_name(value)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: str
    group_id: int | None
    created_at: datetime
    updated_at: datetime
