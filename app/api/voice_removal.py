from fastapi import APIRouter, Request, Depends, Query
import os
import subprocess
import uuid
from app.schemas.voice_removal import VoiceRemovalRequest
from app.services.voice_removal_service import VoiceRemovalservice
router = APIRouter(tags=["Voice Removal"], prefix="/vocie")


voice_removal_service = VoiceRemovalservice()


@router.post("/removal")
async def remove_voice(req: VoiceRemovalRequest):
    return await voice_removal_service.remove_voice(req)
