
from app.schemas.video_dubber_ai import CutVideoRequest
import os
import uuid
import asyncio


class VideoService:

    async def cut_video(self, req: CutVideoRequest) -> str:
        file_id = uuid.uuid4().hex
        filename = f"{file_id}.mp4"

        temp_dir = "temp"
        video_dir = os.path.join(temp_dir, "cut_videos")

        os.makedirs(temp_dir, exist_ok=True)
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

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(
                f"FFmpeg failed: {stderr.decode()}"
            )

        return output_cut_video
