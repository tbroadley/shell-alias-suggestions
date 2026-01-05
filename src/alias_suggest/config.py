import os
from pathlib import Path

DATA_DIR = Path.home() / ".local" / "share" / "alias-suggest"
CACHE_FILE = DATA_DIR / "cache.json"

SKIP_COMMANDS = frozenset({"cd", "ls", "clear", "pwd", "exit", "history", "fg", "bg", "jobs"})


def is_disabled() -> bool:
    return os.environ.get("ALIAS_SUGGEST_DISABLED", "").lower() in ("1", "true", "yes")


def get_min_confidence() -> float:
    return float(os.environ.get("ALIAS_SUGGEST_MIN_CONF", "0.8"))


def is_debug() -> bool:
    return os.environ.get("ALIAS_SUGGEST_DEBUG", "").lower() in ("1", "true", "yes")


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
