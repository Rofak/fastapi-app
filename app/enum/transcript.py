from enum import Enum

class Type(Enum):
    GEMINI="GEMINI"
    WHISPER="WHISPER"
    OPEN_AI="OPEN_AI"

class RenderState(str,Enum):
    TRANCRIBED="TRANCRIBED"
    GENERATE_VOICE="GENERATE_VOICE"    
    RENDER_VIDEO="RENDER_VIDEO"
    DONE="DONE"

class TaskQueueStatus(str,Enum):
    PROGRESS="PROGRESS"
    SUCCESS="SUCCESS"
    FAILURE="FAILURE"