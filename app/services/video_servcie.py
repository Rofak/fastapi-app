
from app.schemas.video_dubber_ai import CutVideoRequest
import os
import uuid
import asyncio
import subprocess
from app.core.logger import logger


class VideoService:

    def cut_video(self, req: CutVideoRequest) -> str:
        logger.info("start cutting video")

        file_id = uuid.uuid4().hex
        filename = f"{file_id}.mp4"

        temp_dir = "temp"
        video_dir = os.path.join(temp_dir, "cut_videos")

        os.makedirs(video_dir, exist_ok=True)

        output_cut_video = os.path.join(video_dir, filename)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", req.video_url,
            "-t", str(req.duration),
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
