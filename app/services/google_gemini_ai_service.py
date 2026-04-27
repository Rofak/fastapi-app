from google import genai
from google.genai import types
from app.core.config import settings
from app.schemas.video_dubber_ai import TranscribeResponse,Segment
from app.schemas.video_dubber_ai import TrancribeRequest
from app.services.translate_service import TranslateService
import json
from typing import List


translateService = TranslateService()

class GoogleGeminiAiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)


    def transcribe_from_file_uri(self, reg:TrancribeRequest):
        response = self.client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_text(
                            text=(
                                "Please transcribe the provided media by processing each segment individually, "
                                "using the given start and end timestamps, and return the transcription aligned "
                                "to those exact time ranges."
                            )
                        ),
                        types.Part.from_uri(
                            file_uri=reg.video_url,
                            mime_type="video/mp4"
                        ),
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "video_duration_sec": {
                            "type": "NUMBER",
                            "description": "Vidoe duration in second"
                        },
                        "language":{
                            "type":"STRING",
                            "description":"Language that deteced, response only lang code"
                        },
                        "segments": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "originalText": {
                                        "type": "STRING",
                                        "description": "Original text"
                                    },
                                    "start": {
                                        "type": "NUMBER"
                                    },
                                    "end": {
                                        "type": "NUMBER"
                                    }
                                }
                            }
                        }
                    }
                }
            ),
        )

        data = json.loads(response.text)
        segments = self.map_segments(response.text)
        results = []
        
        for segment in segments:
            original_text = segment.originalText.strip()
            translated_text = translateService.translate(original_text,target=reg.target_lang)
            results.append(
                  Segment(
                    start=segment.start,
                    end=segment.end,
                    originalText=original_text,
                    translateText=translated_text)
            )
        return TranscribeResponse(
            language=data.get("language"),
            total_duration_sec=data.get("video_duration_sec"),
            segments=results
        )  
    


    def map_segments(self,response_text: str) -> List[Segment]:
        data = json.loads(response_text)

        segments = data.get("segments", [])
        return [Segment(**seg) for seg in segments]