from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class EnrollmentCreate(BaseModel):
    user_id: int
    course_id: int


class EnrollmentUpdate(BaseModel):
    user_id: int | None = None
    course_id: int | None = None

    @field_validator("user_id", "course_id", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("value cannot be empty")
        return value

    @model_validator(mode="after")
    def require_change(self):
        if self.user_id is None and self.course_id is None:
            raise ValueError("user_id or course_id is required")
        return self


class EnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    created_at: datetime
    updated_at: datetime
