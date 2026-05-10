from fastapi import APIRouter, Request, Depends, Query
from app.schemas.video_dubber_ai import TranscribeResponse, TrancribeRequest, VoiceResponse, GenerateVoiceReqeust, GenerateVoiceResponse, RenderVideoRequest, LanguageNameResponse, RanderVideoResponse
from app.schemas.video_dubber_ai import GenerateThumbRequest, VideoDubbedListRequest
from app.schemas.video_dubber_ai import VideoDubberRequestI
from app.services.video_dubber_ai_service import VideoDubberAIService
from app.services.azure_tts_service import AzureTTSService
from app.services.google_gemini_ai_service import GoogleGeminiAiService
from app.services.open_ai_servcie import OpenAIService
from typing import List
from app.enum.transcript import Type
from app.deps import db
from app.repositories.videos_dubbed_repo import VideosDubbedRepo
from sqlalchemy.ext.asyncio import AsyncSession
from app.tasks.video_task import video_dubber_task
from celery.result import AsyncResult
from app.core.celery_app import celery
import json
from app.core.cache_decorator import redis_cache
from app.deps.validate_request import decrypt_request
from app.core.config import settings
from app.services.video_servcie import VideoService

router = APIRouter(tags=["Video Dubber AI"], prefix="/video_dubber_ai")
service = VideoDubberAIService()
azureService = AzureTTSService()
geminiService = GoogleGeminiAiService()
open_ai_service = OpenAIService()
video_service = VideoService()


repo = VideosDubbedRepo()


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TrancribeRequest):
    if (req.type == Type.WHISPER):
        return service.transcribe(req)
    elif (req.type == Type.OPEN_AI):
        return open_ai_service.transcribe(req)
    else:
        return geminiService.transcribe_from_file_uri(req)


@router.get("/list/voices", response_model=List[VoiceResponse])
@redis_cache(3600)
async def list_voices():
    return azureService.getVoiceNames()


@router.get("/list/languages", response_model=List[LanguageNameResponse])
@redis_cache(3600)
async def list_languages():
    return azureService.get_all_languages()


@router.post("/generate/voice", response_model=GenerateVoiceResponse)
async def generate_voice(reqeust: GenerateVoiceReqeust):
    audio_base64 = azureService.azure_tts(
        text=reqeust.text, voiceName=reqeust.name, locale=reqeust.locale)
    response = GenerateVoiceResponse(
        start=reqeust.start, end=reqeust.end, audio_base64=audio_base64)
    return response


@router.post("/generate/voices", response_model=List[GenerateVoiceResponse])
async def generate_voices(reqeusts: List[GenerateVoiceReqeust]):
    result: List[GenerateVoiceResponse] = []

    for req in reqeusts:
        audio_base64 = azureService.azure_tts(
            text=req.text, voiceName=req.name, locale=req.locale)
        response = GenerateVoiceResponse(
            start=req.start, end=req.end, audio_base64=audio_base64)
        result.append(response)
    return result


@router.post("/render/video", response_model=RanderVideoResponse)
async def render_video(req: RenderVideoRequest):
    # service.build_audio_timeline(req)
    return await service.merge_segments_to_video(req=req)


@router.post("/list/video-dubbed")
async def get_list_video_dubbed(req: VideoDubbedListRequest, db: AsyncSession = Depends(db.get_db)):
    return await repo.get_by_user_id(db=db, user_id=req.member_id, page=req.page, page_size=req.page_size)


@router.post("/video_dubber")
async def video_dubber(req: VideoDubberRequestI, d1=Depends(decrypt_request)):
    if req.type is None:
        req.type = settings.TRANSCRIBE_TYPE

    payload = req.model_dump(exclude_none=True)
    job = video_dubber_task.delay(payload)
    return {"job_id": job.id}


@router.get("/video_dubber/status/{job_id}")
async def check_video_dubber_status(job_id: str):
    result = AsyncResult(job_id, app=celery)
    return {
        "job_id": job_id,
        "status": result.state,
        "result": result.info
    }


@router.post("/generate/thumbnail")
async def generate_thumbnail(req: GenerateThumbRequest):
    result = await video_service.generate_thumbnail(video_url=req.video_url, member_id=req.member_id)
    return result
