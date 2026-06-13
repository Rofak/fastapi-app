import os
import subprocess
import uuid
from app.schemas.voice_removal import VoiceRemovalRequest
from app.services.s3_service import S3Service
import aiohttp

s3_service = S3Service()


class VoiceRemovalservice:
    def remove_voice(self, req: VoiceRemovalRequest):
        audio_temp_id = uuid.uuid4().hex
        out_dir = "separated/htdemucs"
        if req.audio_path is None:
            out_audio_temp = os.path.join(
                out_dir, f"audio_temp/{audio_temp_id}.wav")
            self.download_audio(url=req.audio_url, output_path=out_audio_temp)
        else:
            out_audio_temp = req.audio_path

        subprocess.run([
            "demucs",
            "--two-stems=vocals",
            "-n", "htdemucs",
            "--segment", "7",
            out_audio_temp
        ])
        base = os.path.splitext(os.path.basename(out_audio_temp))[0]
        return f"{out_dir}/{base}/no_vocals.wav"

    async def extract_audio(self, video_path, output_audio):
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "44100",
            "-ac", "2",
            output_audio
        ])

    async def download_audio(self, url: str, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()

                with open(output_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)
