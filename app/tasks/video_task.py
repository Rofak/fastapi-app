
from app.core.celery_app import celery
from app.services.video_dubber_ai_service import VideoDubberAIService
from app.services.azure_tts_service import AzureTTSService
from app.services.google_gemini_ai_service import GoogleGeminiAiService
from typing import List
from app.services.open_ai_servcie import OpenAIService
from app.enum.transcript import Type,RenderState
from app.repositories.videos_dubbed_repo import VideosDubbedRepo
import asyncio
from app.enum.transcript import TaskQueueStatus
from app.core.database import AsyncSessionLocal
from app.schemas.video_dubber_ai import TrancribeRequest,GenerateVoiceReqeust,GenerateVoiceResponse,TranscribeResponse,RenderVideoRequest,VideoRequest,VideoDubberRequestI
from app.schemas.video_dubbed import VideoDubbedCreate,VideoDubbedUpdate

video_dubber_ai_servcice = VideoDubberAIService()
azure_tts_service = AzureTTSService()
gemini_service = GoogleGeminiAiService()
open_ai_service = OpenAIService()
video_dubbed_repo = VideosDubbedRepo()



async def create_video_dubbed(data: dict,status:str):
    async with AsyncSessionLocal() as db:
        req = VideoDubberRequestI(**data)
        create_req = VideoDubbedCreate(user_id=req.member_id,
                                       file_name=req.file_name,
                                       status=status)
        video = await video_dubbed_repo.create(db, create_req)
        return video.id
    

async def update_video_dubber_status(video_url:str,status:str,video_id:int):
    async with AsyncSessionLocal() as db:
        update = VideoDubbedUpdate(status=status,file_url=video_url)
        video = await video_dubbed_repo.update_video_id(db=db,video_id=video_id,video_dubbed_update=update)
        return video.id


async def process_video_dubbing(self,payload: dict):
        video_url=payload["video_url"]
        target_lang=payload["target_lang"]
        trancribe_model_type=payload["type"]
        voice_name=payload["voice_name"]
        member_id=payload["member_id"]

        try:
            self.update_state(state="PROGRESS",meta={"message":"Transcript...","video_url": ""})
            video_id= await create_video_dubbed(payload,TaskQueueStatus.PROGRESS)
            trancribe = TrancribeRequest(video_url=video_url,target_lang=target_lang,type=trancribe_model_type)
            print("=== start transcribe ====")
            if(trancribe.type == Type.WHISPER):
                transcribeResponse = video_dubber_ai_servcice.transcribe(trancribe)
            elif (trancribe.type == Type.OPEN_AI):
                transcribeResponse = open_ai_service.transcribe(trancribe)
            else:
                transcribeResponse = gemini_service.transcribe_from_file_uri(trancribe)
            print("=== end transcribe ====")

            print("===== start generate voice=======")
            self.update_state(state="PROGRESS",meta={"message":"Generate Voice...","video_url": ""})
            generate_voice_request = map_transcribe_to_voice_requests(transcribe=transcribeResponse,locale=target_lang,voice_name=voice_name)
            voices_result = []
            for req in generate_voice_request:
                audio_base64 = azure_tts_service.azure_tts(text=req.text,voiceName=req.name,locale=req.locale)
                response = GenerateVoiceResponse(start=req.start,end=req.end,audio_base64=audio_base64)
                voices_result.append(response)

            print("===== end generate voice =======")

            print("===== start render video=====")
            self.update_state(state="PROGRESS",meta={"message":"Render Video...", "video_url": ""})
            render_video_request=map_voice_response_to_render_video(voices=voices_result,
                                                                    member_id=member_id,
                                                                    video_url=video_url,
                                                                    video_duration=transcribeResponse.total_duration_sec)
            
            result = await video_dubber_ai_servcice.merge_segments_to_video(render_video_request)
            print("===== end render video=====")
            await update_video_dubber_status(result.video_url,TaskQueueStatus.SUCCESS,video_id)
            return {
                "message":RenderState.DONE,
                "video_url": result.video_url
            }
        except Exception as e:
            await update_video_dubber_status(video_url=None,status=TaskQueueStatus.FAILURE,video_id=video_id)
            raise e


@celery.task(name="video_process",bind=True)
def video_dubber_task(self,payload:dict):
    result= asyncio.run(process_video_dubbing(self,payload))
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


def map_voice_response_to_render_video(voices:List[GenerateVoiceResponse],member_id:int,video_duration:int,video_url:str):
    video_request=[]
    for voice in voices:
        req = VideoRequest(audio_base64=voice.audio_base64,start=voice.start,end=voice.end)
        video_request.append(req)

    return RenderVideoRequest(member_id=member_id,
                              video_duration_sec=video_duration,
                              video_url=video_url,
                              segments=video_request)   