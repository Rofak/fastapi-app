from pydantic import BaseModel
from typing import List,Optional
from app.enum.transcript import Type

class VideoDubbedCreate(BaseModel):
    user_id:int
    file_name:str
    status:str


class VideoDubbedUpdate(BaseModel):
    user_id:int | None = None
    file_name:str | None = None
    file_url:str | None = None
    status:str | None = None