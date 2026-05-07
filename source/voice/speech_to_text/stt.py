import asyncio
import queue
import threading
from typing import List

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from ...pydantic.error_model import ErrorDetail


VALID_MODELS = ["tiny", "base", "small", "medium", "large"]
VALID_COMPUTE_TYPES = ["float32", "float16", "int8", "int8_float32", "int8_float16"]
    


class SpeechToText:
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
        if model_size not in VALID_MODELS:
            raise ValueError(f"Invalid model_size. Choose from {VALID_MODELS}")
    
        if compute_type not in VALID_COMPUTE_TYPES:
            raise ValueError(f"Invalid compute_type. Choose from {VALID_COMPUTE_TYPES}")
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.sample_rate = sample_rate
        self.silence_duration = silence_duration
        self.silence_threshold = silence_threshold

        try:
            self.model = WhisperModel(
                 model_size_or_path=model_size,
                device=device,
                compute_type=compute_type,
            )

        except Exception as e:
            print(f"Error loading model: {e}")
            raise e
        
        self.is_recording = False
        self.audio_queue: queue.Queue = queue.Queue()

    def record_button_mode_sync(self):
        print("\nPress Enter to START recording...")
        input()

        print("Recording... Press Enter again to stop.")

        self.is_recording = True

        chunks: List[np.ndarray] = []

        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio callback status: {status}")

            if self.is_recording:
                self.audio_queue.put(indata.copy())

        def wait_for_stop():
            input()
            self.is_recording = False

        stop_thread = threading.Thread(target=wait_for_stop,daemon=True)
        stop_thread.start()

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=audio_callback,
                blocksize=1024,
            ):
                while self.is_recording:
                    try:
                        chunk = self.audio_queue.get(timeout=0.1)
                        chunks.append(chunk)
                    except queue.Empty:
                        continue

                while not self.audio_queue.empty():
                    try:
                        chunk = self.audio_queue.get_nowait()
                        chunks.append(chunk)
                    except queue.Empty:
                        break

        except Exception as e:
                print(f"Error during recording: {e}")
                self.is_recording = False
                return ""

        if not chunks:
            print("No audio captured.")
            return ""

        audio_data = np.concatenate(chunks, axis=0).flatten()

        return self.transcribe(audio_data)
    
    def record_auto_silence_mode_sync(self) -> str:

        print("\nPress Enter to START recording...")
        input()
        
        print(f"Recording... (will stop after {self.silence_duration}s of silence)")
        
        self.is_recording = True
        self.audio_queue = queue.Queue()
        chunks: List[np.ndarray] = []
        
        silence_count = 0
        
        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"Audio callback status: {status}")
            
            if self.is_recording:
                self.audio_queue.put(indata.copy())
        
        try:
            
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=audio_callback,
                blocksize=1024,
            ):
                chunk_duration = 1024 / self.sample_rate  
                silence_chunks_needed = int(self.silence_duration / chunk_duration)
                
                while self.is_recording:
                    try:
                        chunk = self.audio_queue.get(timeout=0.1)
                        
                        chunk_max = np.abs(chunk).max()
                        
                        if chunk_max < self.silence_threshold:

                            silence_count += 1
                            
                            if silence_count >= silence_chunks_needed:
                                print(f"Silence detected for {self.silence_duration} seconds. Stopping recording.")
                                self.is_recording = False
                                break
                        else:
                            silence_count = 0
                        
                        chunks.append(chunk)
                    
                    except queue.Empty:
                        continue
                
                while not self.audio_queue.empty():
                    try:
                        chunk = self.audio_queue.get_nowait()
                        chunks.append(chunk)
                    except queue.Empty:
                        break
        
        except Exception as e:
            print(f"Error during recording: {e}")
            self.is_recording = False
            return ""
        
        if not chunks:
            print("No audio captured.")
            return ""

        audio_data = np.concatenate(chunks, axis=0).flatten()
        return self.transcribe(audio_data)
    
    def transcribe(self, audio_data: np.ndarray) -> str:
        
        
        try:
        
            segments, info = self.model.transcribe(
                audio_data,
                language=self.language,
            )
            
            # Extract text from segments
            text = " ".join(segment.text for segment in segments).strip()
            
            if not text:
                print("No speech detected in the audio.")
                return ""
            
            
            return text
        
        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""
        
    
    async def record_on_button_press(self) -> str:
        
        loop = asyncio.get_event_loop()    
        text = await loop.run_in_executor(
            None,
            self.record_button_mode_sync,
        )
        
        return text
    
    async def record_on_button_auto_silence(self) -> str:
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(
            None,
            self.record_auto_silence_mode_sync,
        )
        
        return text

    
    def stop_recording(self) -> None:
        self.is_recording = False
        print("Recording stopped.")