from pydantic import BaseModel
from typing import List, Optional
from app.enum.transcript import Type
from app.enum.plan import UserPlan


class Segment(BaseModel):
    start: float
    end: float
    originalText: str
    translateText: Optional[str] = None


class TranscribeResponse(BaseModel):
    language: str
    segments: List[Segment]
    total_duration_sec: float


class TrancribeRequest(BaseModel):
    video_url: str
    target_lang: str
    type: Type


class VoiceResponse(BaseModel):
    locale: str
    name: str
    display_name: str
    gender: str


class GenerateVoiceReqeust(BaseModel):
    locale: str
    name: str
    text: str
    start: float
    end: float


class GenerateVoiceResponse(BaseModel):
    start: float
    end: float
    audio_base64: str


class VideoRequest(BaseModel):
    start: float
    end: float
    audio_base64: str


class RenderVideoRequest(BaseModel):
    member_id: int
    video_duration_sec: float
    video_url: str
    segments: List[VideoRequest]


class LanguageNameResponse(BaseModel):
    locale: str
    name: str


class GeminiTranscribeResponse(BaseModel):
    start: str
    end: str
    originalText: str


class RanderVideoResponse(BaseModel):
    video_url: str
    path: str


class VideoDubberRequestI(BaseModel):
    member_id: int
    video_url: str
    target_lang: str
    type: Optional[str] = None
    voice_name: str
    file_name: str
    plan: UserPlan
    video_duration: float


class CutVideoRequest(BaseModel):
    video_url: str
    video_duration: float
    plan: str


class S3UploadResponse(BaseModel):
    path: str
    video_url: str


class GenerateThumbRequest(BaseModel):
    member_id: int
    video_url: str


class VideoDubbedListRequest(BaseModel):
    member_id: int
    page: int = 1
    page_size: int = 10
