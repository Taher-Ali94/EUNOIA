import sounddevice as sd
from kokoro import KPipeline
import asyncio
from typing import Optional


class TextToSpeech():
    def __init__(self,lang_code:str = "a",voice:str ="af_bella",speed:float = 1.0,sample_rate:int = 24000,num_workers:int=2):
        self.pipeline = KPipeline(lang_code=lang_code)
        self.voice = voice
        self.speed = speed
        self.sample_rate = sample_rate
        self.num_workers = num_workers
        self.text_queue :asyncio.Queue[Optional[str]] = asyncio.Queue()
        self.audio_queue :asyncio.Queue[Optional[tuple]] = asyncio.Queue()

        self.worker_tasks: list[asyncio.Task] = []
        self.playback_task: Optional[asyncio.Task] = None

        self.is_running = False
        self.stop_requested = False
        self.current_text: Optional[str] = None


    async def worker(self,worker_id:int):
        try:
            while True:
                text = await self.text_queue.get()

                if text is None:
                    self.text_queue.task_done()
                    break

                self.current_text = text
                try:
                    generator = self.pipeline(
                        text,
                        voice = self.voice,
                        speed = self.speed,
                    )

                    for segment_id, segment_text, audio in generator:
                        if self.stop_requested:
                            break
                        await self.audio_queue.put((audio, self.sample_rate))
                        
                except Exception as e:
                    print(f"Worker {worker_id} error: {e}")

                finally:
                    self.text_queue.task_done()
                    self.current_text = None
        except asyncio.CancelledError:
            print(f"Worker {worker_id} cancelled")
            raise

    def play_audio(self, audio, sample_rate: int) -> None:

        try:
            sd.play(audio, sample_rate)
            sd.wait()
        except Exception as e:
            print(f"Audio playback error: {e}")
    

    async def playback_worker(self):
        try:
            while self.is_running:
                try:
                    audio, sample_rate = await asyncio.wait_for(
                        self.audio_queue.get(),
                        timeout=0.5,
                    )

                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        self.play_audio,
                        audio,
                        sample_rate,
                    )

                    self.audio_queue.task_done()

                except asyncio.TimeoutError:
                    continue

                except Exception as e:
                    print(f"Playback worker error: {e}")

        except asyncio.CancelledError:
            print("Playback worker cancelled")
            raise


    async def start(self):
        if self.is_running:
            print("TTS is already running")
            return
        
        self.is_running = True
        self.stop_requested = False

        for i in range(self.num_workers):
            task = asyncio.create_task(self.worker(i))
            self.worker_tasks.append(task)

        self.playback_task = asyncio.create_task(self.playback_worker())

    async def speak(self, text: str):
        if not self.is_running:
            print("TTS is not running. Please start it first.")
            return
        
        if text is None or text.strip() == "":
            print("Empty text provided. Skipping.")
            return

        await self.text_queue.put(text)

    async def interrupt(self) -> None:
        self.stop_requested = True
        sd.stop()
        
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self.stop_requested = False
    
    async def flush(self) -> None:
        await self.text_queue.join()
        await self.audio_queue.join()
        
        print("Queue flushed.")

    async def close(self) -> None:    
        await self.interrupt()
        self.stop_requested = False
        self.is_running = False

        for _ in range(self.num_workers):
            await self.text_queue.put(None)
        

        for task in self.worker_tasks:
            task.cancel()
        
        if self.playback_task:
            self.playback_task.cancel()

        await asyncio.gather(
            *self.worker_tasks,
            self.playback_task,
            return_exceptions=True,
        )

        print("TTS shutdown complete.")
        

  

    
        