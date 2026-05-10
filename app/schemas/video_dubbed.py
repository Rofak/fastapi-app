from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from app.enum.transcript import Type
from datetime import datetime


class VideoDubbedCreate(BaseModel):
    user_id: int
    file_name: str
    status: str


class VideoDubbedUpdate(BaseModel):
    user_id: int | None = None
    file_name: str | None = None
    file_url: str | None = None
    thumbnail_url: str | None = None
    status: str | None = None


class VideoDubbedListResponse(BaseModel):
    file_name: str
    file_url: str | None = None
    thumbnail_url: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
