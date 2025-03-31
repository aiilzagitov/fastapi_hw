from datetime import datetime
from pydantic import BaseModel, HttpUrl
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str

class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = None
    expires_at: datetime | None = None

class LinkResponse(BaseModel):
    original_url: str
    short_code: str
    expires_at: datetime | None
    created_at: datetime


class LinkStatsResponse(BaseModel):
    original_url: str
    created_at: datetime
    hit_count: int
    last_accessed_at: Optional[datetime]

    class Config:
        orm_mode = True

class LinkUpdate(BaseModel):
    original_url: str

class RedirectResponse(BaseModel):
    original_url: str