
from app.schemas.video_dubber_ai import CutVideoRequest
import os
import uuid
import asyncio
import subprocess
from app.enum.plan import UserPlan
from app.core.logger import logger
from app.services.s3_service import S3Service
import sys

s3_service = S3Service()

MAX_PREMIUM_DURATION = 150
MAX_FREE_DURATION = 40


class VideoService:

    def __init__(self):
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(
                asyncio.WindowsProactorEventLoopPolicy()
            )

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def cut_video(self, req: CutVideoRequest) -> str:

        mix_video_duration = MAX_FREE_DURATION
        if req.plan == UserPlan.FREE:
            mix_video_duration = MAX_FREE_DURATION
        elif req.plan == UserPlan.PREMIUM and req.video_duration > MAX_PREMIUM_DURATION:
            mix_video_duration = MAX_PREMIUM_DURATION
            return req.video_url
        else:
            return req.video_url

        logger.info("start cutting video")

        file_id = uuid.uuid4().hex
        filename = f"{file_id}.mp4"

        temp_dir = "temp"
        video_dir = os.path.join(temp_dir, "cut_videos")

        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(video_dir, exist_ok=True)

        output_cut_video = os.path.join(video_dir, filename)

        cmd = [
            "ffmpeg",
            "-ss", "0",
            "-y",
            "-i", req.video_url,
            "-t", str(mix_video_duration),
            "-c", "copy",
            output_cut_video
        ]

        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if process.returncode != 0:
            raise Exception(
                f"FFmpeg failed: {process.stderr}"
            )

        return output_cut_video

    async def generate_thumbnail(self, video_url: str, member_id: int) -> str:
        file_id = uuid.uuid4().hex
        filename = f"{file_id}_thumb.jpg"

        temp_dir = "temp"
        thumb_dir = os.path.join(temp_dir, "thumb")

        os.makedirs(thumb_dir, exist_ok=True)

        thumb_output = os.path.join(thumb_dir, filename)

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", "1",
            "-i", video_url,
            "-vframes", "1",
            "-q:v", "2",
            thumb_output
        ]

        try:

            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if process.returncode != 0:
                raise Exception(
                    f"FFmpeg failed: {process.stderr}"
                )

            result = await s3_service.upload_file_to_s3(
                file_path=thumb_output, filename=filename, member_id=member_id)
            return result
        finally:
            if os.path.exists(thumb_output):
                os.remove(thumb_output)
