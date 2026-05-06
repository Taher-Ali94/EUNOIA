from .speech_to_text.stt import SpeechToText
from .text_to_speech.tts import TextToSpeech

class VoiceManager:
    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "en",
        sample_rate: int = 16000,
        silence_duration: float = 2.0,
        silence_threshold: float = 0.01,
        tts_lang_code: str = "a",
        tts_voice: str = "af_bella",
        tts_speed: float = 1.0,
        tts_sample_rate: int = 24000,
        tts_num_workers: int = 2,
    ):
        self.stt = SpeechToText(
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            language=language,
            sample_rate=sample_rate,
            silence_duration=silence_duration,
            silence_threshold=silence_threshold,
        )

        self.tts = TextToSpeech(
            lang_code=tts_lang_code,
            voice=tts_voice,
            speed=tts_speed,
            sample_rate=tts_sample_rate,
            num_workers=tts_num_workers,
        )

    def stop_stt(self) -> None:
        self.stt.stop_recording()

    async def record_manual(self) -> str:
        return await self.stt.record_on_button_press()

    async def record_auto(self) -> str:
        return await self.stt.record_on_button_auto_silence()
    
    async def start_tts(self) -> None:
        await self.tts.start()

    async def stop_tts(self) -> None:
        await self.tts.close()

    async def speak(self, text: str) -> None:
        await self.tts.speak(text)

    async def flush_tts(self) -> None:
        await self.tts.flush()

    async def flush_tts(self) -> None:
        await self.tts.flush()

    async def shutdown(self) -> None:
        await self.stop_tts()
        self.stop_stt()
