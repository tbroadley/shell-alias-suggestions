import json
import sys
import time

from alias_suggest import alias_parser
from alias_suggest import config
from alias_suggest import llm
from alias_suggest import pattern_matcher

CYAN = "\033[96m"
RESET = "\033[0m"


def should_skip_command(command: str) -> bool:
    if not command or not command.strip():
        return True
    first_word = command.split()[0]
    return first_word in config.SKIP_COMMANDS


def check_rate_limit() -> bool:
    config.ensure_data_dir()
    log_path = config.SUGGESTIONS_LOG

    if not log_path.exists():
        return True

    try:
        timestamps = json.loads(log_path.read_text())
    except (json.JSONDecodeError, OSError):
        timestamps = []

    hour_ago = time.time() - 3600
    recent = [t for t in timestamps if t > hour_ago]

    return len(recent) < config.get_max_hourly()


def record_suggestion() -> None:
    config.ensure_data_dir()
    log_path = config.SUGGESTIONS_LOG

    try:
        timestamps = json.loads(log_path.read_text()) if log_path.exists() else []
    except (json.JSONDecodeError, OSError):
        timestamps = []

    hour_ago = time.time() - 3600
    timestamps = [t for t in timestamps if t > hour_ago]
    timestamps.append(time.time())

    log_path.write_text(json.dumps(timestamps))


def format_suggestion(suggestion: llm.Suggestion, is_git: bool = False) -> str:
    if is_git:
        return f"{CYAN}💡 Tip: Use 'git {suggestion.alias_name}' instead → git {suggestion.expansion}{RESET}"
    return f"{CYAN}💡 Tip: Use '{suggestion.alias_name}' instead → {suggestion.expansion}{RESET}"


def analyze_command(command: str) -> str | None:
    if config.is_disabled():
        return None

    if should_skip_command(command):
        return None

    if not check_rate_limit():
        if config.is_debug():
            print("DEBUG: Rate limit reached, skipping suggestion")
        return None

    aliases = alias_parser.get_all_aliases()
    if not aliases:
        if config.is_debug():
            print("DEBUG: No aliases found")
        return None

    min_conf = config.get_min_confidence()
    candidates = pattern_matcher.find_matches(command, aliases)

    if not candidates:
        if config.is_debug():
            print("DEBUG: No pattern matches found")
        return None

    high_conf_candidates = [c for c in candidates if c.confidence >= min_conf]
    if not high_conf_candidates:
        if config.is_debug():
            print(
                f"DEBUG: No candidates above {min_conf} confidence. Best: {candidates[0].confidence:.2f}"
            )
        return None

    if config.is_debug():
        print(f"DEBUG: Found {len(high_conf_candidates)} high-confidence candidates")
        for c in high_conf_candidates:
            print(f"  - {c.alias.name} ({c.confidence:.2f}, {c.match_type})")

    suggestion = llm.get_suggestion(command, high_conf_candidates)

    if suggestion:
        record_suggestion()
        is_git = any(
            c.alias.source == "git config" and c.alias.name == suggestion.alias_name
            for c in candidates
        )
        return format_suggestion(suggestion, is_git)

    return None


def run_analysis(command: str) -> int:
    result = analyze_command(command)
    if result:
        print(result, file=sys.stderr)
    return 0
