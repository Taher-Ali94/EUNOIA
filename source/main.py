import time
from .core.llm_manager import LLMManager
from .voice.voice_manager import VoiceManager
import asyncio


# def main():
#     llm = LLMManager(
#         model_name="Eunoia",
#         keep_alive="15m",
#         num_predict=100,
#         temperature=0.7,
#     )

#     wake_time1 = time.time()

#     print("Warming up model...")
#     response , _ = llm.wake_llm()
#     print(f"Wake-up response: {response.content}\n")
#     print("Model is ready.\n")

#     wake_time2 = time.time()
#     print(f"Model wake-up time: {wake_time2 - wake_time1:.2f} seconds\n")
#     messages = []

#     while True:
#         user_input = input("You: ").strip()

#         if user_input.lower() in {"exit", "quit"}:
#             print("Goodbye.")
#             break

#         messages.append(
#             {
#                 "role": "user",
#                 "content": user_input,
#             }
#         )

#         llm_response1 = time.time()
#         result , _ = llm.call_llm(messages)

#         if result is None:
#             print("Assistant: Something went wrong.\n")
#             continue

#         llm_response2 = time.time()
#         print(f"LLM response time: {llm_response2 - llm_response1:.2f} seconds\n")
#         print(f"Assistant: {result.content}\n")
#         print(f"Current step: {result.step}\n")


#         messages.append(
#             {
#                 "role": "assistant",
#                 "content": result.content,
#             }
#         )

async def main():
    vm = VoiceManager()

    await vm.start_tts()
    await vm.speak("Hello, how are you?")
    await vm.flush_tts()
    await vm.speak("This is a test of the text-to-speech system.")
    await vm.flush_tts()
    await vm.speak("Goodbye!")
    await vm.flush_tts()

    await vm.shutdown()


if __name__ == "__main__":
    asyncio.run(main())