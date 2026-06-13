from pydantic import BaseModel
from typing import List, Optional


class VoiceRemovalRequest(BaseModel):
    audio_path: Optional[str]
    audio_url: Optional[str]
