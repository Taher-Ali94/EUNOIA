# Eunoia Assistant

A local-first AI assistant with both text and voice interfaces.

## What It Does

Eunoia is a personal assistant runtime that runs entirely on your local machine, supporting chat via text or voice with optional tool integrations and persistent memory.

## Architecture

### LangGraph Pipeline Overview

- **Nodes:** Each LangGraph node represents a functional block (LLM inference, tool use, memory ops, observation).
- **State Flow:** Messages and context are routed step-by-step according to conversation history and tool output.
- **Tool System:** Pluggable tool registry for local filesystem/web/data APIs, invoked via structured JSON.
- **Memory System:** (Optional) Persistent long-term memory backed by MongoDB and Chroma for retrieval-augmented interaction.
- **Voice Pipeline:** Uses local speech-to-text and text-to-speech (optional), with automatic or manual recording.

## Tech Stack


| Library                             | Purpose/Reason Used                        |
| ----------------------------------- | ------------------------------------------ |
| Python (>=3.10)                     | Core runtime                               |
| LangGraph                           | Stepwise orchestration and graph execution |
| Pydantic                            | Config/data validation                     |
| Ollama Python SDK                   | Local LLM inference client                 |
| sounddevice, kokoro, faster_whisper | Voice input/output pipeline                |
| MongoDB, Chroma                     | Memory/checkpoint storage                  |

## Project Structure

```
EUNOIA/
│
├── main.py               # CLI entrypoint, mode parsing
├── readme.md             # Project overview and docs
├── .env.example          # Example environment configuration
├── source/
│   ├── config/
│   │   ├── settings.py           # All project settings
│   │   ├── model.py              # LLM system prompt and model config
│   │   └── mem0_config.py        # Memory backend config
│   ├── core/
│   │   └── llm_manager.py        # LLM invocation and output parsing
│   ├── graph/
│   │   ├── builder.py            # Graph construction
│   │   └── nodes.py              # Nodes for main assistant loop
│   ├── memory/
│   │   └── long_term_mem0/
│   │       └── mem_client.py     # Mongo/Chroma memory client
│   └── tools/
│       └── registry.py           # Tool invocation/registration logic
│
├── docker-compose.yaml   # (Optional) Chroma/Mongo stack
```

## Setup & Installation

### Prerequisites

- Python >= 3.10
- [Ollama](https://ollama.com/) installed and at least one local compatible model pulled
- MongoDB instance (local or docker)
- (optional) ChromaDB for vector memory

### Steps

1. Clone the repo
   `git clone ...`
2. Create a virtualenv and install requirements
   `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3. Pull your Ollama model
   `ollama pull llama3:8b`
4. Copy `.env.example` to `.env` and set all values
5. Run in text mode:
   `python main.py --mode text`
6. Run in voice mode:
   `python main.py --mode voice [--record-mode auto|manual] ...`

## Configuration

Each setting in `settings.py`:  


| Name                       | Default                                     | Purpose                          |
| -------------------------- | ------------------------------------------- | -------------------------------- |
| LLM_MODEL_NAME             | "YOUR_MODEL_NAME"                           | Which Ollama model to use        |
| LLM_KEEP_ALIVE             | "10m"                                       | How long to keep LLM in memory   |
| LLM_NUM_PREDICT            | 200                                         | Max tokens per generation        |
| LLM_TEMPERATURE            | 0.0                                         | Sampling temperature             |
| TOOL_BASE_PATH             | "./sandbox"                                 | Root for file/tool ops           |
| MAX_REASONING_STEPS        | 6                                           | Max reasoning hops before answer |
| MEMORY_ENABLED             | True                                        | Toggle long-term memory          |
| MEMORY_USER_ID             | "YOUR_USER_ID"                              | ID/key for memory separation     |
| MONGO_CHECKPOINTER_ENABLED | True                                        | Use MongoDB for checkpointing    |
| MONGO_URI                  | "mongodb://YOUR_MONGO_HOST:YOUR_MONGO_PORT" | Mongo connection                 |
| MONGO_DB_NAME              | "YOUR_DB_NAME"                              | Mongo DB for memory/checkpoints  |
| MONGO_THREAD_ID            | "YOUR_THREAD_ID"                            | MongoDB thread collection key    |

## Available Tools


| Tool Name          | Description              | Input Format Example                              |
| ------------------ | ------------------------ | ------------------------------------------------- |
| web_search         | Does a web search        | `{"query":"string","max_results":5}`              |
| search_news        | News search              | `{"query":"string","max_results":5}`              |
| get_page_content   | Fetches web page content | `{"url":"https://..."}`                           |
| read_file          | Reads a local file       | `{"path":"relative/path"}`                        |
| write_file         | Writes content           | `{"path":"file","content":"text","append":false}` |
| list_files         | Lists files in a folder  | `{"path":".","recursive":false}`                  |
| get_directory_info | Folder metadata          | `{"path":"."}`                                    |
| create_directory   | Make directory           | `{"path":"..."} `                                 |
| delete_directory   | Remove directory         | `{"path":"..."} `                                 |
| rename_directory   | Rename directory         | `{"old_path":"...","new_path":"..."}`             |

## Voice Mode

- Run with `--mode voice`
- Requires `sounddevice`, `faster_whisper`, `kokoro`
- Supports `--record-mode`, `--device`, `--model-size`, etc.

## CLI Flags


| Flag                | Default  | Description                        |
| ------------------- | -------- | ---------------------------------- |
| --mode              | text     | Run in text or voice mode          |
| --debug             | False    | Extra debug logging                |
| --record-mode       | auto     | Voice: auto or manual record       |
| --device            | cpu      | Voice: hardware target             |
| --model-size        | small    | Voice: model size                  |
| --compute-type      | int8     | Voice: quantization                |
| --language          | en       | Voice: input lang                  |
| --sample-rate       | 16000    | Voice: sample rate                 |
| --silence-duration  | 2.0      | Voice: silence timeout (sec)       |
| --silence-threshold | 0.01     | Voice: silence amplitude threshold |
| --tts-lang-code     | a        | Voice: tts language                |
| --tts-voice         | af_bella | Voice: tts voice type              |
| --tts-speed         | 1.0      | Voice: tts speed                   |
| --tts-sample-rate   | 24000    | Voice: tts sample rate             |
| --tts-num-workers   | 2        | Voice: tts worker processes        |

## Example Usage

**Text:**

```
User: What's the weather in Berlin?
Assistant: [web_search tool used]
User: Can you remember I like chess?
Assistant: [memory tool used]
User: exit
```

**Voice:**

```
$ python main.py --mode voice --device cpu
(Speak: "What's the news?" — [assistant responds])
```

## Known Limitations

- Only supports local models (Ollama)
- No cloud or push-notification integrations
- Voice mode depends on local Python libraries and mic configuration
- Memory features require always-on Mongo and Chroma

## License

MIT
