import base64
from openai import OpenAI
from app.schemas.video_dubber_ai import TrancribeRequest, TranscribeResponse, Segment
from app.core.config import settings
from app.services.translate_service import TranslateService
import os
import uuid
import subprocess

translate_service = TranslateService()


class OpenAIService:

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPEN_AI_API_KEY)

    def _convert_to_mp3(self, input_path: str, output_path: str):
        command = [
            "ffmpeg",
            "-y",  # overwrite
            "-i", input_path,
            "-vn",  # no video
            "-acodec", "mp3",
            output_path,
        ]
        subprocess.run(command, check=True)

    def transcribe(self, req: TrancribeRequest):
        file_id = uuid.uuid4().hex
        filename = f"{file_id}.mp3"

        temp_dir = "temp"
        audio_dir = os.path.join(temp_dir, "temp_open_ai_audio")

        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        output_audio = os.path.join(audio_dir, filename)

        try:
            # 2. Convert to MP3
            self._convert_to_mp3(req.video_url, output_audio)

            # 3. Send to OpenAI
            with open(output_audio, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="gpt-4o-transcribe-diarize",
                    file=audio_file,
                    response_format="diarized_json",
                    chunking_strategy={
                        "type": "server_vad",
                        "threshold": 0.4,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 400
                    },
                )

            # 4. Process result
            results = []
            for segment in transcript.segments:
                original_text = segment.text.strip()
                translated_text = translate_service.translate(
                    original_text, target=req.target_lang)
                results.append(
                    Segment(
                        start=segment.start,
                        end=segment.end,
                        originalText=original_text,
                        translateText=translated_text)
                )
            return TranscribeResponse(
                language="",
                total_duration_sec=0,
                segments=results
            )
        finally:
            for f in [output_audio]:
                if os.path.exists(f):
                    os.remove(f)
