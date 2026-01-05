import shlex
from dataclasses import dataclass

from alias_suggest import alias_parser


@dataclass
class MatchCandidate:
    alias: alias_parser.Alias
    confidence: float
    match_type: str


def tokenize_command(cmd: str) -> list[str]:
    try:
        return shlex.split(cmd)
    except ValueError:
        return cmd.split()


def calculate_similarity(cmd_tokens: list[str], expansion_tokens: list[str]) -> float:
    if not expansion_tokens:
        return 0.0
    if expansion_tokens == cmd_tokens[: len(expansion_tokens)]:
        return 1.0
    matching = sum(1 for t in expansion_tokens if t in cmd_tokens)
    return matching / len(expansion_tokens)


def find_matches(
    command: str, aliases: list[alias_parser.Alias]
) -> list[MatchCandidate]:
    cmd_tokens = tokenize_command(command)
    if not cmd_tokens:
        return []

    candidates = []
    is_git_cmd = cmd_tokens[0] == "git"

    for alias in aliases:
        exp_tokens = tokenize_command(alias.expansion)
        if not exp_tokens:
            continue

        if alias.source == "git config":
            if not is_git_cmd or len(cmd_tokens) < 2:
                continue
            git_subcmd = " ".join(cmd_tokens[1:])
            git_subcmd_tokens = cmd_tokens[1:]

            if alias.expansion == git_subcmd:
                candidates.append(MatchCandidate(alias, 1.0, "exact_git"))
                continue

            if git_subcmd.startswith(alias.expansion):
                confidence = len(alias.expansion) / len(git_subcmd)
                if confidence >= 0.5:
                    candidates.append(MatchCandidate(alias, confidence, "prefix_git"))
                continue

            exp_git_tokens = tokenize_command(alias.expansion)
            if exp_git_tokens == git_subcmd_tokens[: len(exp_git_tokens)]:
                remaining_args = len(git_subcmd_tokens) - len(exp_git_tokens)
                confidence = 1.0 - (remaining_args * 0.1)
                candidates.append(
                    MatchCandidate(alias, max(0.5, confidence), "prefix_git_tokens")
                )
                continue
        else:
            if alias.expansion == command:
                candidates.append(MatchCandidate(alias, 1.0, "exact"))
                continue

            if command.startswith(alias.expansion + " "):
                confidence = len(alias.expansion) / len(command)
                if confidence >= 0.3:
                    candidates.append(
                        MatchCandidate(alias, min(0.95, confidence + 0.3), "prefix")
                    )
                continue

            if command.startswith(alias.expansion):
                confidence = len(alias.expansion) / len(command)
                if confidence >= 0.5:
                    candidates.append(MatchCandidate(alias, confidence, "starts_with"))
                continue

            if exp_tokens == cmd_tokens[: len(exp_tokens)]:
                remaining_args = len(cmd_tokens) - len(exp_tokens)
                confidence = 1.0 - (remaining_args * 0.05)
                candidates.append(
                    MatchCandidate(alias, max(0.5, confidence), "prefix_tokens")
                )
                continue

            similarity = calculate_similarity(cmd_tokens, exp_tokens)
            if similarity >= 0.8:
                candidates.append(MatchCandidate(alias, similarity * 0.9, "similar"))

    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return candidates[:5]


def get_best_match(
    command: str,
    aliases: list[alias_parser.Alias],
    min_confidence: float = 0.8,
) -> MatchCandidate | None:
    matches = find_matches(command, aliases)
    if matches and matches[0].confidence >= min_confidence:
        return matches[0]
    return None
