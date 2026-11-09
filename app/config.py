import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class ModelSettings:
    provider: str
    model: str
    api_key: str | None
    base_url: str | None
    temperature: float


@dataclass
class Settings:
    main: ModelSettings
    router: ModelSettings
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR.parent / 'haqdaar.db'}")
    history_turns: int = int(os.getenv("HISTORY_TURNS") or 8)
    max_guard_retries: int = int(os.getenv("MAX_GUARD_RETRIES") or 1)


def _model(prefix: str, fallback: ModelSettings | None = None) -> ModelSettings:
    def pick(name: str, default):
        value = os.getenv(f"{prefix}_{name}")
        if value:
            return value
        if fallback is not None:
            return getattr(fallback, name.lower())
        return default

    return ModelSettings(
        provider=pick("PROVIDER", "groq").lower(),
        model=pick("MODEL", "openai/gpt-oss-120b"),
        api_key=pick("API_KEY", None),
        base_url=pick("BASE_URL", None),
        temperature=float(pick("TEMPERATURE", 0.2)),
    )


def load_settings() -> Settings:
    main = _model("LLM")
    router = _model("ROUTER", fallback=main)
    return Settings(main=main, router=router)
