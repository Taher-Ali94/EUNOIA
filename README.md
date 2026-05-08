# EUNOIA

Local assistant runtime with text and voice interfaces.

## Run

```bash
python /home/runner/work/EUNOIA/EUNOIA/main.py --mode text
python /home/runner/work/EUNOIA/EUNOIA/main.py --mode voice
```

Voice mode supports existing voice pipeline options:

```bash
python /home/runner/work/EUNOIA/EUNOIA/main.py --mode voice --record-mode auto --device cpu --model-size small
```

Exit with `exit` / `quit` (or `Ctrl+C`).

## Environment

Create `.env` from `.env.example` and set values as needed:

- `LLM_KEEP_ALIVE`
- `LLM_NUM_PREDICT`
- `LLM_TEMPERATURE`
- `TOOL_BASE_PATH`
- `MAX_REASONING_STEPS`
- `MEMORY_ENABLED`
- `MEMORY_USER_ID`
- `MONGO_CHECKPOINTER_ENABLED`
- `MONGO_URI`
- `MONGO_DB_NAME`
- `MONGO_THREAD_ID`

The assistant expects a local Ollama runtime/model configured in `source/config/settings.py` defaults.
