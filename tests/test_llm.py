import pytest

from alias_suggest import alias_parser
from alias_suggest import llm
from alias_suggest import pattern_matcher


class TestParseLlmResponse:
    @pytest.mark.parametrize(
        ("response", "expected_alias", "expected_expansion"),
        [
            ("ALIAS: gst\nEXPANSION: git status", "gst", "git status"),
            ("ALIAS: ll\nEXPANSION: ls -la", "ll", "ls -la"),
            ("ALIAS: co\nEXPANSION: checkout", "co", "checkout"),
        ],
    )
    def test_parse_valid_response(self, response: str, expected_alias: str, expected_expansion: str):
        result = llm.parse_llm_response(response)
        assert result is not None
        assert result.alias_name == expected_alias
        assert result.expansion == expected_expansion

    def test_parse_no_suggestion(self):
        result = llm.parse_llm_response("NO_SUGGESTION")
        assert result is None

    def test_parse_no_suggestion_with_explanation(self):
        result = llm.parse_llm_response("NO_SUGGESTION - the command doesn't match any alias")
        assert result is None

    def test_parse_invalid_response(self):
        result = llm.parse_llm_response("I think you could use gst")
        assert result is None


class TestFormatAliasesForPrompt:
    def test_format_shell_alias(self):
        candidates = [
            pattern_matcher.MatchCandidate(
                alias=alias_parser.Alias("ll", "ls -la", "/home/user/.bashrc"),
                confidence=1.0,
                match_type="exact",
            )
        ]
        result = llm.format_aliases_for_prompt(candidates)
        assert "ll = ls -la" in result
        assert "(git alias)" not in result

    def test_format_git_alias(self):
        candidates = [
            pattern_matcher.MatchCandidate(
                alias=alias_parser.Alias("st", "status", "git config"),
                confidence=1.0,
                match_type="exact_git",
            )
        ]
        result = llm.format_aliases_for_prompt(candidates)
        assert "st = status" in result
        assert "(git alias)" in result


class TestFallbackSuggestion:
    def test_high_confidence_fallback(self):
        candidates = [
            pattern_matcher.MatchCandidate(
                alias=alias_parser.Alias("ll", "ls -la", "/home/user/.bashrc"),
                confidence=0.98,
                match_type="exact",
            )
        ]
        result = llm._fallback_suggestion(candidates)
        assert result is not None
        assert result.alias_name == "ll"

    def test_low_confidence_no_fallback(self):
        candidates = [
            pattern_matcher.MatchCandidate(
                alias=alias_parser.Alias("ll", "ls -la", "/home/user/.bashrc"),
                confidence=0.7,
                match_type="prefix",
            )
        ]
        result = llm._fallback_suggestion(candidates)
        assert result is None

    def test_empty_candidates_no_fallback(self):
        result = llm._fallback_suggestion([])
        assert result is None


class TestGetSuggestion:
    def test_no_api_key_uses_fallback(self, mocker):
        mocker.patch("alias_suggest.config.get_api_key", return_value=None)
        mocker.patch("alias_suggest.config.is_debug", return_value=False)

        candidates = [
            pattern_matcher.MatchCandidate(
                alias=alias_parser.Alias("ll", "ls -la", "/home/user/.bashrc"),
                confidence=0.98,
                match_type="exact",
            )
        ]

        result = llm.get_suggestion("ls -la", candidates)
        assert result is not None
        assert result.alias_name == "ll"

    def test_api_timeout_uses_fallback(self, mocker):
        import anthropic

        mocker.patch("alias_suggest.config.get_api_key", return_value="test-key")
        mocker.patch("alias_suggest.config.is_debug", return_value=False)
        mocker.patch("alias_suggest.config.get_model", return_value="claude-3-5-haiku-20241022")
        mocker.patch("alias_suggest.config.get_timeout", return_value=2.0)

        mock_client = mocker.Mock()
        mock_client.messages.create.side_effect = anthropic.APITimeoutError(request=mocker.Mock())
        mocker.patch("anthropic.Anthropic", return_value=mock_client)

        candidates = [
            pattern_matcher.MatchCandidate(
                alias=alias_parser.Alias("ll", "ls -la", "/home/user/.bashrc"),
                confidence=0.98,
                match_type="exact",
            )
        ]

        result = llm.get_suggestion("ls -la", candidates)
        assert result is not None
        assert result.alias_name == "ll"

