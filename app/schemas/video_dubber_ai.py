from pydantic import BaseModel
from typing import List

class Segment(BaseModel):
    start:float
    end:float
    originalText:str
    translateText:str

class TranscribeResponse(BaseModel):
    language:str
    segments:List[Segment]
    total_duration_sec:float


class TrancribeRequest(BaseModel):
    video_url:str
    target_lang:str


class VoiceResponse(BaseModel):
    locale:str
    name:str  
    display_name:str 
    gender:str

class GenerateVoiceReqeust(BaseModel):
    locale:str
    name:str
    text:str    
    start:float
    end:float

class GenerateVoiceResponse(BaseModel):
    start:float
    end:float
    audio_base64:str

class VideoRequest(BaseModel):
    start:float
    end:float
    audio_base64:str


class RenderVideoRequest(BaseModel):
    video_duration_sec:float
    segments:List[VideoRequest]


class LanguageNameResponse(BaseModel):
    locale:str
    name:str