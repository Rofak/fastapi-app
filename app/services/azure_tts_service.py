import azure.cognitiveservices.speech as speechsdk
from app.core.config import settings
from typing import List
from app.schemas.video_dubber_ai import VoiceResponse,LanguageNameResponse
import base64
from babel import Locale
import json

class AzureTTSService:

    def __init__(self):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_TTS_KEY,
            region=settings.AZURE_TTS_REGION
        )


    def azure_tts(self,text: str,voiceName:str,locale:str, filename: str = None) -> bytes:
        self.speech_config = speechsdk.SpeechConfig(subscription=settings.AZURE_TTS_KEY,region=settings.AZURE_TTS_REGION)

        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
        )

        # SSML (same as your original)
        ssml = f"""
        <speak version='1.0' xml:lang='{locale}'>
            <voice name='{voiceName}'>
                {text}
            </voice>
        </speak>
        """

        # Output config
        if filename:
            audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)
        else:
            audio_config = None  # in-memory

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        result = synthesizer.speak_ssml_async(ssml).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            if filename:
                return b""  # already saved to file
            else:
                return base64.b64encode(result.audio_data).decode("utf-8")
        else:
            cancellation = result.cancellation_details
            raise Exception(
                f"Azure TTS failed: {cancellation.reason} | {cancellation.error_details}"
            )
        
    def getVoiceNames(self):
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
        voices = synthesizer.get_voices_async().get()
        result: List[VoiceResponse] = []
        for v in voices.voices:
            display_name=f"{v.short_name} ({v.gender.name})"
            result.append(VoiceResponse(locale=v.locale,name=v.short_name,gender=v.gender.name,display_name=display_name))

        return result    
    
    
    def get_all_languages(self):
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config
        )

        result = synthesizer.get_voices_async().get()
        if result.reason != speechsdk.ResultReason.VoicesListRetrieved:
            raise Exception("Failed to fetch voices")

        supported = {}

        for v in result.voices:
            locale = v.locale  # KEEP FULL: en-US, en-AU
            lang_code = locale.split("-")[0]
            try:
                base_name = Locale('en').languages.get(lang_code, lang_code).title()
            except:
                base_name = lang_code

            # combine region into label
            display_name = f"{base_name} ({locale.split('-')[1]})" if "-" in locale else base_name
            if locale not in supported:
                supported[locale] = LanguageNameResponse(
                    locale=locale,
                    name=display_name
                )
        return sorted(supported.values(), key=lambda x: x.name)