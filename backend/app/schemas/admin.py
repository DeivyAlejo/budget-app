from datetime import datetime

from pydantic import BaseModel, Field


class PendingUserRead(BaseModel):
    id: int
    email: str
    full_name: str | None
    created_at: datetime


class InviteCodeRead(BaseModel):
    id: int
    code: str
    created_at: datetime
    used_at: datetime | None
    used_by_user_id: int | None


class InviteCodeCreateRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=50)
    length: int = Field(default=12, ge=8, le=32)


class InviteCodeCreateResponse(BaseModel):
    codes: list[str]
