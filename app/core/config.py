from dataclasses import dataclass
import os


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "VibeSport")
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = _to_bool(os.getenv("DEBUG"), default=True)
    exercises_data_path: str = os.getenv("EXERCISES_DATA_PATH", "data/exercises.json")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    ollama_timeout: float = float(os.getenv("OLLAMA_TIMEOUT", "60"))
    # AJOUT DE LA SIMPLE AUTH
    api_token: str = os.getenv("API_TOKEN", "vibe-sport-secret-key-123")


settings = Settings()
