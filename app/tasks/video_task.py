
from app.core.celery_app import celery
from app.services.video_dubber_ai_service import VideoDubberAIService
from app.services.azure_tts_service import AzureTTSService
from app.services.google_gemini_ai_service import GoogleGeminiAiService
from typing import List
from app.services.open_ai_servcie import OpenAIService
from app.enum.transcript import Type, RenderState
from app.repositories.videos_dubbed_repo import VideosDubbedRepo
import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.enum.transcript import TaskQueueStatus
from app.core.database import AsyncSessionLocal
from app.schemas.video_dubber_ai import TrancribeRequest, GenerateVoiceReqeust, GenerateVoiceResponse, TranscribeResponse, RenderVideoRequest, VideoRequest, VideoDubberRequestI, CutVideoRequest
from app.schemas.video_dubbed import VideoDubbedCreate, VideoDubbedUpdate
from app.core.logger import logger
from app.services.video_servcie import VideoService

video_dubber_ai_servcice = VideoDubberAIService()
azure_tts_service = AzureTTSService()
gemini_service = GoogleGeminiAiService()
open_ai_service = OpenAIService()
video_dubbed_repo = VideosDubbedRepo()
vidoe_service = VideoService()


async def create_video_dubbed(db: AsyncSession, data: dict, status: str):
    req = VideoDubberRequestI(**data)
    create_req = VideoDubbedCreate(user_id=req.member_id,
                                   file_name=req.file_name,
                                   status=status)
    video = await video_dubbed_repo.create(db, create_req)
    return video.id


async def update_video_dubber_status(db: AsyncSession, video_url: str, status: str, video_id: int):
    update = VideoDubbedUpdate(status=status, file_url=video_url)
    await video_dubbed_repo.update_video_id(db=db, video_id=video_id, video_dubbed_update=update)


async def process_video_dubbing(self, payload: dict):
    async with AsyncSessionLocal() as db:
        video_url = payload["video_url"]
        target_lang = payload["target_lang"]
        trancribe_model_type = payload["type"]
        voice_name = payload["voice_name"]
        member_id = payload["member_id"]

        output_cut_path = ""
        video_id = 0
        try:
            video_id = await create_video_dubbed(db, payload, TaskQueueStatus.PROGRESS)

            cut_req = CutVideoRequest(video_url=video_url, duration=40)
            # output_cut_path = vidoe_service.cut_video(cut_req)
            # video_url = output_cut_path
            self.update_state(state="PROGRESS", meta={
                "message": "Transcript...", "video_url": ""})
            trancribe = TrancribeRequest(
                video_url=video_url, target_lang=target_lang, type=trancribe_model_type)
            logger.info("=== start transcribe ====")
            if (trancribe.type == Type.WHISPER):
                transcribeResponse = video_dubber_ai_servcice.transcribe(
                    trancribe)
            elif (trancribe.type == Type.OPEN_AI):
                transcribeResponse = open_ai_service.transcribe(trancribe)
            else:
                transcribeResponse = gemini_service.transcribe_from_file_uri(
                    trancribe)
            logger.info("=== end transcribe ====")

            logger.info("===== start generate voice=======")
            self.update_state(state="PROGRESS", meta={
                "message": "Generate Voice...", "video_url": ""})
            generate_voice_request = map_transcribe_to_voice_requests(
                transcribe=transcribeResponse, locale=target_lang, voice_name=voice_name)
            voices_result = []
            for req in generate_voice_request:
                audio_base64 = azure_tts_service.azure_tts(
                    text=req.text, voiceName=req.name, locale=req.locale)
                response = GenerateVoiceResponse(
                    start=req.start, end=req.end, audio_base64=audio_base64)
                voices_result.append(response)

            logger.info("===== end generate voice =======")

            logger.info("===== start render video=====")
            self.update_state(state="PROGRESS", meta={
                "message": "Render Video...", "video_url": ""})
            render_video_request = map_voice_response_to_render_video(voices=voices_result,
                                                                      member_id=member_id,
                                                                      video_url=video_url,
                                                                      video_duration=transcribeResponse.total_duration_sec)

            result = await video_dubber_ai_servcice.merge_segments_to_video(render_video_request)
            logger.info("===== end render video=====")
            await update_video_dubber_status(db, result.video_url, TaskQueueStatus.SUCCESS, video_id)
            return {
                "message": RenderState.DONE,
                "video_url": result.video_url
            }
        except Exception as e:
            await update_video_dubber_status(db, video_url=None, status=TaskQueueStatus.FAILURE, video_id=video_id)
            raise e
        finally:
            if os.path.exists(output_cut_path):
                logger.info("Delete Cuted Video")
                os.remove(output_cut_path)


@celery.task(name="video_process", bind=True)
def video_dubber_task(self, payload: dict):
    result = asyncio.run(process_video_dubbing(self, payload))
    return result


def map_transcribe_to_voice_requests(
    transcribe: TranscribeResponse,
    locale: str,
    voice_name: str
) -> list[GenerateVoiceReqeust]:

    generate_voice_request = []

    for seg in transcribe.segments:
        req = GenerateVoiceReqeust(
            locale=locale,
            name=voice_name,
            text=seg.translateText,
            start=seg.start,
            end=seg.end
        )

        generate_voice_request.append(req)

    return generate_voice_request


def map_voice_response_to_render_video(voices: List[GenerateVoiceResponse], member_id: int, video_duration: int, video_url: str):
    video_request = []
    for voice in voices:
        req = VideoRequest(audio_base64=voice.audio_base64,
                           start=voice.start, end=voice.end)
        video_request.append(req)

    return RenderVideoRequest(member_id=member_id,
                              video_duration_sec=video_duration,
                              video_url=video_url,
                              segments=video_request)
