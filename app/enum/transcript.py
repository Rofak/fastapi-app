from enum import Enum

class Type(Enum):
    GEMINI="GEMINI"
    WHISPER="WHISPER"

class RenderState(str,Enum):
    TRANCRIBED="TRANCRIBED"
    GENERATE_VOICE="GENERATE_VOICE"    
    RENDER_VIDEO="RENDER_VIDEO"
    DONE="DONE"