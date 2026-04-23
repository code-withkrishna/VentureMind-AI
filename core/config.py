from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency in test envs
    def load_dotenv(*args, **kwargs) -> bool:
        return False

ROOT_DIR = Path(__file__).resolve().parent.parent

PRODUCT_BRIEF = {
    "name": "VentureMind AI – Multi-Agent Startup Validation System",
    "problem_statement": (
        "Founders waste weeks validating startup ideas through scattered research, "
        "gut feel, and low-confidence AI outputs before they know if demand is real."
    ),
    "target_users": [
        "Founders",
        "Startup studio teams",
        "Accelerator operators",
        "Angel investors",
    ],
    "why_it_matters": (
        "Weak startup validation burns time, cash, and conviction. Teams need a fast, "
        "investor-style decision engine that makes demand, competition, and risk visible."
    ),
}


def _load_environment() -> None:
    load_dotenv()
    load_dotenv(dotenv_path=ROOT_DIR / "api.env", override=True)


def _get_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def _get_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _get_str(name: str, default: str) -> str:
    value = (os.getenv(name) or "").strip()
    return value if value else default


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    serper_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.2
    groq_max_tokens: int = 1400
    search_results: int = 5
    search_language: str = "en"
    search_country: str = "us"
    max_reasoning_loops: int = 2
    llm_retries: int = 3
    tool_retries: int = 3
    confidence_threshold: int = 76
    request_timeout_seconds: int = 45
    app_name: str = "VentureMind AI – Multi-Agent Startup Validation System"
    data_dir: Path = ROOT_DIR / "data"
    logs_dir: Path = ROOT_DIR / "logs"

    @property
    def trace_dir(self) -> Path:
        return self.logs_dir / "traces"

    @property
    def memory_db_path(self) -> Path:
        return self.data_dir / "agent_memory.sqlite"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "Settings":
        _load_environment()

        groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
        serper_api_key = (os.getenv("SERPER_API_KEY") or "").strip()

        if not groq_api_key:
            raise RuntimeError(
                "Missing GROQ_API_KEY. Add it to api.env or your environment before starting the app."
            )

        if not serper_api_key:
            raise RuntimeError(
                "Missing SERPER_API_KEY. Add it to api.env or your environment before starting the app."
            )

        groq_model = (os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile").strip()
        if groq_model.startswith("groq/"):
            groq_model = groq_model.split("/", 1)[1]

        settings = cls(
            groq_api_key=groq_api_key,
            serper_api_key=serper_api_key,
            groq_model=groq_model,
            groq_temperature=_get_float("GROQ_TEMPERATURE", 0.2),
            groq_max_tokens=_get_positive_int("GROQ_MAX_TOKENS", 1400),
            search_results=_get_positive_int(
                "SEARCH_RESULTS",
                _get_positive_int("SERPER_RESULTS", 5),
            ),
            search_language=_get_str("SEARCH_LANGUAGE", "en"),
            search_country=_get_str("SEARCH_COUNTRY", "us"),
            max_reasoning_loops=_get_positive_int("MAX_REASONING_LOOPS", 2),
            llm_retries=_get_positive_int("LLM_RETRIES", 3),
            tool_retries=_get_positive_int("TOOL_RETRIES", 3),
            confidence_threshold=_get_positive_int("CONFIDENCE_THRESHOLD", 76),
            request_timeout_seconds=_get_positive_int("REQUEST_TIMEOUT_SECONDS", 45),
        )
        settings.ensure_directories()
        return settings
