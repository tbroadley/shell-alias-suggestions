import re
from dataclasses import dataclass

from alias_suggest import config
from alias_suggest import pattern_matcher


@dataclass
class Suggestion:
    alias_name: str
    expansion: str


PROMPT_TEMPLATE = """The user ran this command: {command}

Available aliases:
{aliases}

Could they have used an alias instead? If yes, respond with ONLY:
ALIAS: <alias_name>
EXPANSION: <what_it_expands_to>

If no good match, respond with: NO_SUGGESTION"""


def format_aliases_for_prompt(candidates: list[pattern_matcher.MatchCandidate]) -> str:
    lines = []
    for c in candidates:
        source_info = " (git alias)" if c.alias.source == "git config" else ""
        lines.append(f"- {c.alias.name} = {c.alias.expansion}{source_info}")
    return "\n".join(lines)


def parse_llm_response(response: str) -> Suggestion | None:
    if "NO_SUGGESTION" in response:
        return None

    alias_match = re.search(r"ALIAS:\s*(\S+)", response)
    expansion_match = re.search(r"EXPANSION:\s*(.+?)(?:\n|$)", response)

    if alias_match:
        alias_name = alias_match.group(1)
        expansion = expansion_match.group(1).strip() if expansion_match else ""
        return Suggestion(alias_name=alias_name, expansion=expansion)

    return None


def get_suggestion(
    command: str,
    candidates: list[pattern_matcher.MatchCandidate],
) -> Suggestion | None:
    api_key = config.get_api_key()
    if not api_key:
        if config.is_debug():
            print("DEBUG: No ANTHROPIC_API_KEY set, skipping LLM call")
        return _fallback_suggestion(candidates)

    import anthropic

    prompt = PROMPT_TEMPLATE.format(
        command=command,
        aliases=format_aliases_for_prompt(candidates),
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=config.get_model(),
            max_tokens=100,
            timeout=config.get_timeout(),
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text
        if config.is_debug():
            print(f"DEBUG: LLM response: {response_text}")
        return parse_llm_response(response_text)
    except anthropic.APITimeoutError:
        if config.is_debug():
            print("DEBUG: LLM call timed out")
        return _fallback_suggestion(candidates)
    except anthropic.APIError as e:
        if config.is_debug():
            print(f"DEBUG: LLM API error: {e}")
        return _fallback_suggestion(candidates)


def _fallback_suggestion(
    candidates: list[pattern_matcher.MatchCandidate],
) -> Suggestion | None:
    if candidates and candidates[0].confidence >= 0.95:
        best = candidates[0]
        return Suggestion(alias_name=best.alias.name, expansion=best.alias.expansion)
    return None
