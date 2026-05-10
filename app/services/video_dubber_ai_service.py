import subprocess
from app.schemas.video_dubber_ai import RenderVideoRequest, TrancribeRequest, VideoRequest, RanderVideoResponse
import requests
from faster_whisper import WhisperModel
from typing import List
from app.schemas.video_dubber_ai import Segment, TranscribeResponse
from app.services.azure_tts_service import AzureTTSService
from app.services.s3_service import S3Service
from pydub import AudioSegment
import base64
import tempfile
import shutil
import io
import asyncio
import os
from app.core.logger import logger
import uuid

azureService = AzureTTSService()
s3Service = S3Service()
MIN_DURATION_MS = 400   # 👈 minimum for single word (tune this)
PADDING_MS = 100
FINAL_OUT_AUDIO = "final_audio.wav"


class VideoDubberAIService:
    def __init__(self):
        self.model = WhisperModel(
            "./whisper_model/small", device="auto", compute_type="int8", cpu_threads=6)

    def run_ffmpeg(self, cmd):
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("FFmpeg ERROR:", result.stderr.decode())
            raise Exception("FFmpeg failed")

    def transcribe(self, reg: TrancribeRequest):
        segments, info = self.model.transcribe(
            reg.video_url, word_timestamps=True, vad_filter=True)
        results: List[Segment] = []

        for segment in segments:
            original_text = segment.text.strip()
            translated_text = self.translate(
                original_text, target=reg.target_lang)
            results.append(
                Segment(
                    start=segment.start,
                    end=segment.end,
                    originalText=original_text,
                    translateText=translated_text)
            )

        return TranscribeResponse(
            language=info.language,
            total_duration_sec=info.duration,
            segments=results
        )

    def translate(self, text, target="km"):
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target,
            "dt": "t",
            "q": text
        }

        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        try:
            res = requests.get(url, params=params, headers=headers, timeout=10)
            data = res.json()
            # 🔥 FIX: join ALL translated chunks (not just [0][0][0])
            translated = "".join([item[0] for item in data[0] if item[0]])
            return translated
        except:
            return text

    def build_audio_timeline(self, renderReqeust: RenderVideoRequest):

        if not renderReqeust.segments:
            raise Exception("No audio segments")

        total_duration = (renderReqeust.video_duration_sec * 1000)
        final_audio = AudioSegment.silent(duration=total_duration)

        last_end_ms = 0  # 👈 prevent overlap

        for seg in renderReqeust.segments:
            start_ms = int(seg.start * 1000)
            duration_ms = int((seg.end - seg.start) * 1000)
            # =========================
            # 🔥 FIX 1: handle zero-duration
            # =========================
            if duration_ms <= 0:
                duration_ms = MIN_DURATION_MS

            if not seg.audio_base64:
                continue

            try:
                audio_bytes = base64.b64decode(seg.audio_base64)
                clip = AudioSegment.from_file(
                    io.BytesIO(audio_bytes), format="mp3")
            except Exception as e:
                print("decode error:", e)
                continue

            # =========================
            # 🔥 FIX 2: match duration
            # =========================
            clip = self.match_duration(clip, duration_ms)

            # =========================
            # 🔥 FIX 3: prevent overlap stacking
            # =========================
            if start_ms < last_end_ms:
                start_ms = last_end_ms  # shift forward

            # padding
            clip = AudioSegment.silent(PADDING_MS) + clip
            final_audio = final_audio.overlay(clip, position=start_ms)
            last_end_ms = start_ms + len(clip)

        final_audio.export(FINAL_OUT_AUDIO, format="wav")
        return FINAL_OUT_AUDIO

    def build_audio_timeline_no_video_duration(self, segments: RenderVideoRequest):

        if not segments:
            raise Exception("No segments")

        decoded = []
        last_end_ms = 0

        # =========================
        # 🔥 STEP 1: decode + compute timeline
        # =========================
        for seg in segments.segments:
            if not seg.audio_base64:
                continue

            try:
                audio_bytes = base64.b64decode(seg.audio_base64)
                clip = AudioSegment.from_file(
                    io.BytesIO(audio_bytes), format="mp3")
            except Exception as e:
                print("decode error:", e)
                continue

            start_ms = int(seg.start * 1000)

            # prevent overlap (same as JS)
            if start_ms < last_end_ms:
                start_ms = last_end_ms

            end_ms = start_ms + len(clip)

            decoded.append({
                "clip": clip,
                "start_ms": start_ms
            })

            last_end_ms = end_ms

        # =========================
        # 🔥 STEP 2: total duration (same as JS)
        # =========================
        total_duration = last_end_ms if last_end_ms > 0 else 1000

        # =========================
        # 🔥 STEP 3: build timeline
        # =========================
        final_audio = AudioSegment.silent(duration=total_duration)

        for item in decoded:
            final_audio = final_audio.overlay(
                item["clip"],
                position=item["start_ms"]
            )

        # =========================
        # 🔥 STEP 4: export WAV
        # =========================
        final_audio.export(FINAL_OUT_AUDIO, format="wav")
        self.export_video(video_path="https://sin1.contabostorage.com/f3dc5ccef6ea4e62b8fa33db51a4c53d:public/AITools/Chinese Short Films.mp4",
                          audio_path="https://sin1.contabostorage.com/f3dc5ccef6ea4e62b8fa33db51a4c53d:video-translation/final_audio.wav", output_path="test.mp4")
        return FINAL_OUT_AUDIO

    def match_duration(self, audio: AudioSegment, target_duration_ms: int) -> AudioSegment:
        current = len(audio)

        if current == 0:
            return audio

        # avoid division by zero
        if target_duration_ms <= 0:
            return audio

        speed = current / target_duration_ms
        speed = max(0.8, min(1.25, speed))

        return audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * speed)
        }).set_frame_rate(audio.frame_rate)

    def change_speed(self, audio: AudioSegment, speed: float):
        return audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * speed)
        }).set_frame_rate(audio.frame_rate)

    def change_speed(self, sound: AudioSegment, speed: float) -> AudioSegment:
        if speed <= 0:
            return sound

        # FFmpeg atempo supports 0.5–2.0 per filter
        def _atempo_chain(sound, speed):
            if speed < 0.5:
                sound = _atempo_chain(sound, 0.5)
                speed /= 0.5
            elif speed > 2.0:
                sound = _atempo_chain(sound, 2.0)
                speed /= 2.0

            return sound._spawn(
                sound.raw_data,
                overrides={"frame_rate": int(sound.frame_rate * speed)}
            ).set_frame_rate(sound.frame_rate)

        return _atempo_chain(sound, speed)

    def get_duration(self, file):
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return float(result.stdout)

    # def build_atempo_chain(self,tempo: float) -> str:
    #     filters = []

    #     while tempo > 2.0:
    #         filters.append("atempo=2.0")
    #         tempo /= 2.0

    #     while tempo < 0.5:
    #         filters.append("atempo=1.0")
    #         tempo /= 1.0

    #     filters.append(f"atempo={tempo:.5f}")
    #     return ",".join(filters)

    # def build_atempo_chain(self, tempo: float) -> str:
    #     if tempo > 2.0:
    #         return "atempo=2.0"
    #     if tempo < 0.5:
    #         return "atempo=1.0"
    #     return f"atempo={tempo:.5f}"

    def build_atempo_chain(self, tempo: float) -> str:
        if tempo <= 0:
            return "atempo=1.0"

        # your rule: force normal speed if below 1
        if tempo < 1.0:
            return "atempo=1.0"

        # clamp upper limit only
        tempo = min(tempo, 1.80)

        return f"atempo={tempo:.5f}"

    async def merge_segments_to_video(self, req: RenderVideoRequest):
        temp_dir = "temp"
        member_folder = os.path.join(temp_dir, f"member_{str(req.member_id)}")
        output_dir = os.path.join(member_folder, "output")
        audio_dir = os.path.join(member_folder, "audio")

        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(member_folder, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        # ✅ safe uuid string
        file_id = uuid.uuid4().hex
        filename = f"{file_id}.mp4"
        output_path = os.path.join(
            output_dir, f"{req.member_id}_{file_id}.mp4")

        inputs = []
        filter_parts = [
            "anullsrc=channel_layout=stereo:sample_rate=44100,apad[base]"]
        mix_labels = ["[base]"]

        try:
            # =========================
            # 1. Prepare audio segments
            # =========================
            for i, seg in enumerate(req.segments):
                if not seg.audio_base64:
                    continue

                audio_file_id = uuid.uuid4().hex
                file_path = os.path.join(
                    audio_dir, f"{req.member_id}_{audio_file_id}_{i}.wav")

                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(seg.audio_base64))

                start = max(float(seg.start), 0)
                end = max(float(seg.end), start + 0.05)
                target_dur = end - start
                original_dur = self.get_duration(file_path)

                if original_dur <= 0:
                    continue

                tempo = original_dur / target_dur
                atempo = self.build_atempo_chain(tempo)
                delay = int(start * 1000)

                input_idx = len(inputs) + 1
                label = f"v_a{i}"

                filter_parts.append(
                    f"[{input_idx}:a]"
                    f"aformat=sample_rates=44100:channel_layouts=stereo,aresample=44100,"
                    f"{atempo},"
                    f"adelay={delay}|{delay}"
                    f"[{label}]"
                )

                mix_labels.append(f"[{label}]")
                inputs.append(file_path)

            if not mix_labels:
                raise Exception("No valid audio generated")

            # =========================
            # 2. Mix all VO tracks
            # =========================
            vo = "vo"

            filter_parts.append(
                f"{''.join(mix_labels)}"
                f"amix=inputs={len(mix_labels)}:duration=longest:dropout_transition=0:normalize=0,volume=2[aout]"
            )

            # =========================
            # 3. Build FFmpeg command
            # =========================
            cmd = [
                "ffmpeg", "-y",
                "-i", req.video_url
            ]

            for f_path in inputs:
                cmd += ["-i", f_path]

            cmd += [
                "-filter_complex", ";".join(filter_parts),
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",

                # audio
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                "-ac", "2",
                "-shortest",
                output_path
            ]

            # print("FFMPEG:", " ".join(cmd))

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(result.stderr)
                raise Exception(f"FFmpeg failed:\n{result.stderr}")

            s3_response = await s3Service.upload_file_to_s3(file_path=output_path, filename=filename, member_id=str(req.member_id))

            for i, path in enumerate(inputs):
                if os.path.exists(path):
                    os.remove(path)

            if os.path.exists(output_path):
                os.remove(output_path)

            return RanderVideoResponse(video_url=s3_response.video_url, path=s3_response.path)
        except Exception as e:
            print(f"Error occurred: {e}")
            for i, path in enumerate(inputs):
                if os.path.exists(path):
                    os.remove(path)

            if os.path.exists(output_path):
                os.remove(output_path)
