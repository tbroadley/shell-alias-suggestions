import sys
from dataclasses import dataclass

from alias_suggest import alias_parser
from alias_suggest import config
from alias_suggest import pattern_matcher

CYAN = "\033[96m"
RESET = "\033[0m"


@dataclass
class Suggestion:
    alias_name: str
    expansion: str
    git_prefix: str | None = None


def should_skip_command(command: str) -> bool:
    if not command or not command.strip():
        return True
    first_word = command.split()[0]
    return first_word in config.SKIP_COMMANDS


def find_git_prefix_alias(aliases: list[alias_parser.Alias]) -> str | None:
    for alias in aliases:
        if alias.source != "git config" and alias.expansion.strip() == "git":
            return alias.name
    return None


def format_suggestion(suggestion: Suggestion) -> str:
    if suggestion.git_prefix:
        return f"{CYAN}💡 Tip: Use '{suggestion.git_prefix} {suggestion.alias_name}' instead → git {suggestion.expansion}{RESET}"
    return f"{CYAN}💡 Tip: Use '{suggestion.alias_name}' instead → {suggestion.expansion}{RESET}"


def analyze_command(command: str) -> str | None:
    if config.is_disabled():
        return None

    if should_skip_command(command):
        return None

    aliases = alias_parser.get_all_aliases()
    if not aliases:
        if config.is_debug():
            print("DEBUG: No aliases found")
        return None

    min_conf = config.get_min_confidence()
    best_match = pattern_matcher.get_best_match(command, aliases, min_conf)

    if not best_match:
        if config.is_debug():
            print(f"DEBUG: No match above {min_conf} confidence")
        return None

    if config.is_debug():
        print(f"DEBUG: Best match: {best_match.alias.name} ({best_match.confidence:.2f}, {best_match.match_type})")

    is_git = best_match.alias.source == "git config"
    suggestion = Suggestion(
        alias_name=best_match.alias.name,
        expansion=best_match.alias.expansion,
        git_prefix=find_git_prefix_alias(aliases) if is_git else None,
    )

    return format_suggestion(suggestion)


def run_analysis(command: str) -> int:
    result = analyze_command(command)
    if result:
        print(result, file=sys.stderr)
    return 0
