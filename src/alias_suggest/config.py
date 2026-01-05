import os
from pathlib import Path

DATA_DIR = Path.home() / ".local" / "share" / "alias-suggest"
CACHE_FILE = DATA_DIR / "cache.json"
SUGGESTIONS_LOG = DATA_DIR / "suggestions.log"

SKIP_COMMANDS = frozenset({"cd", "ls", "clear", "pwd", "exit", "history", "fg", "bg", "jobs"})


def get_api_key() -> str | None:
    return os.environ.get("ANTHROPIC_API_KEY")


def is_disabled() -> bool:
    return os.environ.get("ALIAS_SUGGEST_DISABLED", "").lower() in ("1", "true", "yes")


def get_model() -> str:
    return os.environ.get("ALIAS_SUGGEST_MODEL", "claude-3-5-haiku-20241022")


def get_max_hourly() -> int:
    return int(os.environ.get("ALIAS_SUGGEST_MAX_HOURLY", "3"))


def get_timeout() -> float:
    return float(os.environ.get("ALIAS_SUGGEST_TIMEOUT", "2"))


def get_min_confidence() -> float:
    return float(os.environ.get("ALIAS_SUGGEST_MIN_CONF", "0.8"))


def is_debug() -> bool:
    return os.environ.get("ALIAS_SUGGEST_DEBUG", "").lower() in ("1", "true", "yes")


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

