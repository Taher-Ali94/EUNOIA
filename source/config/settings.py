from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_model_name: str = "Eunoia"
    llm_keep_alive: str = "10m"
    llm_num_predict: int = 200
    llm_temperature: float = 0.0

    tool_base_path: str = "."
    max_reasoning_steps: int = 6

    memory_enabled: bool = True
    memory_user_id: str = "EunoiaUser"

    mongo_checkpointer_enabled: bool = False
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "eunoia"
    mongo_thread_id: str = "EunoiaUser"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()