from .speech_to_text.stt import SpeechToText

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

    def transcribe(self, audio_data) -> str:
        return self.stt.transcribe(audio_data)

    def stop(self) -> None:
        self.stt.stop_recording()

    async def record_manual(self) -> str:
        return await self.stt.record_on_button_press()

    async def record_auto(self) -> str:
        return await self.stt.record_on_button_auto_silence()