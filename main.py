import argparse
import asyncio
import contextlib
import importlib.util
import signal

from langgraph.checkpoint.mongodb import MongoDBSaver

from source.config.settings import get_settings
from source.core.llm_manager import LLMManager
from source.graph.builder import build_graph
from source.graph.nodes import AssistantNodes
from source.memory.long_term_mem0.mem_client import MemoryClient
from source.tools.registry import ToolRegistry


EXIT_COMMANDS = {"exit", "quit"}


def voice_dependencies_available():
    return not missing_voice_dependencies()


def missing_voice_dependencies():
    required = ("sounddevice", "kokoro", "faster_whisper")
    return [name for name in required if importlib.util.find_spec(name) is None]


def parse_args(default_mode: str):
    parser = argparse.ArgumentParser(description="Run EUNOIA assistant in text or voice mode.")
    parser.add_argument("--mode", choices=["voice", "text"], default=default_mode)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--record-mode", choices=["auto", "manual"], default="auto")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--model-size", default="small")
    parser.add_argument("--compute-type", default="int8")
    parser.add_argument("--language", default="en")
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--silence-duration", type=float, default=2.0)
    parser.add_argument("--silence-threshold", type=float, default=0.01)
    parser.add_argument("--tts-lang-code", default="a")
    parser.add_argument("--tts-voice", default="af_bella")
    parser.add_argument("--tts-speed", type=float, default=1.0)
    parser.add_argument("--tts-sample-rate", type=int, default=24000)
    parser.add_argument("--tts-num-workers", type=int, default=2)
    return parser.parse_args()


async def build_runtime(debug: bool = False):
    settings = get_settings()
    llm_manager = LLMManager(
        model_name=settings.llm_model_name,
        keep_alive=settings.llm_keep_alive,
        num_predict=settings.llm_num_predict,
        temperature=settings.llm_temperature,
    )
    tool_registry = ToolRegistry(base_path=settings.tool_base_path)

    memory_client = None
    if settings.memory_enabled:
        candidate = MemoryClient(user_id=settings.memory_user_id)
        await candidate.initialize_memory()
        if candidate.memory is not None:
            memory_client = candidate
        elif debug:
            print("Memory initialization failed. Continuing without memory.")

    nodes = AssistantNodes(
        llm_manager=llm_manager,
        tool_registry=tool_registry,
        memory_client=memory_client,
        max_reasoning_steps=settings.max_reasoning_steps,
    )

    checkpointer_stack = contextlib.ExitStack()
    checkpointer = None
    config = None
    if settings.mongo_checkpointer_enabled:
        try:
            checkpointer = checkpointer_stack.enter_context(
                MongoDBSaver.from_conn_string(settings.mongo_uri, settings.mongo_db_name)
            )
            checkpointer.setup()
            config = {"configurable": {"thread_id": settings.mongo_thread_id}}
        except Exception as e:
            checkpointer_stack.close()
            checkpointer_stack = contextlib.ExitStack()
            checkpointer = None
            config = None
            if debug:
                print(f"MongoDB checkpointer initialization failed: {e}. Continuing without checkpointing.")

    app = build_graph(nodes).compile(checkpointer=checkpointer)
    return app, tool_registry, memory_client, checkpointer_stack, config


async def ask_assistant(app, messages: list[dict[str, str]], user_input: str, config: dict | None = None):
    result = await app.ainvoke({"messages": messages, "current_user_input": user_input}, config=config)
    messages[:] = list(result.get("messages", messages))
    return result.get("final_response") or "I ran into an issue generating a response."

async def run_text_mode(app, messages: list[dict[str, str]], stop_event: asyncio.Event, config: dict | None = None):
    while not stop_event.is_set():
        try:
            user_input = input("You: ").strip()
        except EOFError:
            break

        if not user_input:
            continue
        if user_input.lower() in EXIT_COMMANDS:
            break

        response = await ask_assistant(app, messages, user_input, config=config)
        print(f"Eunoia: {response}")


async def run_voice_mode(args: argparse.Namespace, app, messages: list[dict[str, str]], stop_event: asyncio.Event, config: dict | None = None):
    from source.voice.voice_manager import VoiceManager

    voice_manager = VoiceManager(
        model_size=args.model_size,
        device=args.device,
        compute_type=args.compute_type,
        language=args.language,
        sample_rate=args.sample_rate,
        silence_duration=args.silence_duration,
        silence_threshold=args.silence_threshold,
        tts_lang_code=args.tts_lang_code,
        tts_voice=args.tts_voice,
        tts_speed=args.tts_speed,
        tts_sample_rate=args.tts_sample_rate,
        tts_num_workers=args.tts_num_workers,
    )

    await voice_manager.start_tts()
    try:
        while not stop_event.is_set():
            user_input = await (
                voice_manager.record_auto()
                if args.record_mode == "auto"
                else voice_manager.record_manual()
            )
            user_input = (user_input or "").strip()

            if not user_input:
                continue

            if args.debug:
                print(f"[debug] transcribed: {user_input}")

            if user_input.lower() in EXIT_COMMANDS:
                break

            response = await ask_assistant(app, messages, user_input, config=config)
            print(f"Eunoia: {response}")
            await voice_manager.speak(response)

        await voice_manager.flush_tts()
    finally:
        await voice_manager.shutdown()


async def async_main(args: argparse.Namespace):
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    app, tool_registry, memory_client, checkpointer_stack, config = await build_runtime(debug=args.debug)
    messages: list[dict[str, str]] = []
    try:
        if args.mode == "voice":
            await run_voice_mode(args=args, app=app, messages=messages, stop_event=stop_event, config=config)
        else:
            await run_text_mode(app=app, messages=messages, stop_event=stop_event, config=config)
        return 0
    finally:
        await tool_registry.close()
        if memory_client is not None:
            await memory_client.stop()
        checkpointer_stack.close()


def main() -> int:
    default_mode = "voice" if voice_dependencies_available() else "text"
    args = parse_args(default_mode=default_mode)

    missing_deps = missing_voice_dependencies()
    if args.mode == "voice" and missing_deps:
        if args.debug:
            print(f"Missing voice dependencies: {', '.join(missing_deps)}")
        print("Voice dependencies are unavailable. Falling back to text mode.")
        args.mode = "text"

    try:
        return asyncio.run(async_main(args))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())