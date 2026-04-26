from fastapi import APIRouter,Request
from app.schemas.video_dubber_ai import TranscribeResponse,TrancribeRequest,VoiceResponse,GenerateVoiceReqeust,GenerateVoiceResponse,RenderVideoRequest,LanguageNameResponse
from app.services.video_dubber_ai_service import VideoDubberAIService
from app.services.azure_tts_service import AzureTTSService
from typing import List

router = APIRouter(tags=["Video Dubber AI"],prefix="/video_dubber_ai")
service = VideoDubberAIService()
azureService = AzureTTSService() 


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(reg:TrancribeRequest):
    return service.transcribe(reg)

@router.get("/list/voices",response_model=List[VoiceResponse])
def list_voices():
    return azureService.getVoiceNames()


@router.get("/list/languages",response_model=List[LanguageNameResponse])
def list_voices():
    return azureService.get_all_languages()

@router.post("/generate/voice",response_model=GenerateVoiceResponse)
def generate_voice(reqeust:GenerateVoiceReqeust):
    audio_base64 = azureService.azure_tts(text=reqeust.text,voiceName=reqeust.name,locale=reqeust.locale)
    response = GenerateVoiceResponse(start=reqeust.start,end=reqeust.end,audio_base64=audio_base64)
    return response


@router.post("/generate/voices",response_model=List[GenerateVoiceResponse])
def generate_voices(reqeusts:List[GenerateVoiceReqeust]):
    result:List[GenerateVoiceResponse] = []

    for req in reqeusts:
        audio_base64 = azureService.azure_tts(text=req.text,voiceName=req.name,locale=req.locale)
        response = GenerateVoiceResponse(start=req.start,end=req.end,audio_base64=audio_base64)
        result.append(response)
    return result

@router.post("/render/video")
def render_video(req:RenderVideoRequest):
    service.build_audio_timeline(req)
    return "ok"