import subprocess
from app.schemas.video_dubber_ai import RenderVideoRequest,TrancribeRequest
import requests
from faster_whisper import WhisperModel
from typing import List
from app.schemas.video_dubber_ai import Segment,TranscribeResponse
from app.services.azure_tts_service import AzureTTSService
from app.services.google_gemini_ai_service import GoogleGeminiAiService
from pydub import AudioSegment
import base64
import io
from app.enum.transcript import Type

azureService = AzureTTSService()
geminiService = GoogleGeminiAiService()

MIN_DURATION_MS = 400   # 👈 minimum for single word (tune this)
PADDING_MS = 100
FINAL_OUT_AUDIO ="final_audio.wav"

class VideoDubberAIService:
    def __init__(self):
        self.model = WhisperModel("./whisper_model/small",device="cpu", compute_type="int8")

    def run_ffmpeg(self,cmd):
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("FFmpeg ERROR:", result.stderr.decode())
            raise Exception("FFmpeg failed")
        

    def transcribe(self,reg:TrancribeRequest):
        segments, info = self.model.transcribe(reg.video_url,word_timestamps=True,vad_filter=True)
        results : List[Segment] = []

        for segment in segments:
            original_text = segment.text.strip()
            translated_text = self.translate(original_text,target=reg.target_lang)
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
    
    
    def translate(self,text, target="km"):
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
        
    def build_audio_timeline(self,renderReqeust: RenderVideoRequest):
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
                clip = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
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



    def match_duration(self,audio: AudioSegment, target_duration_ms: int) -> AudioSegment:
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
    


    def change_speed(self,audio: AudioSegment, speed: float):
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