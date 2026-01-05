import json
import time

import pytest

from alias_suggest import analyzer
from alias_suggest import config


class TestShouldSkipCommand:
    @pytest.mark.parametrize(
        ("cmd", "expected"),
        [
            ("cd /tmp", True),
            ("ls", True),
            ("clear", True),
            ("pwd", True),
            ("exit", True),
            ("git status", False),
            ("docker ps", False),
            ("", True),
            ("   ", True),
        ],
    )
    def test_should_skip_command(self, cmd: str, expected: bool):
        assert analyzer.should_skip_command(cmd) == expected


class TestRateLimiting:
    def test_rate_limit_allows_when_under_limit(self, tmp_path, mocker):
        mocker.patch.object(config, "DATA_DIR", tmp_path)
        mocker.patch.object(config, "SUGGESTIONS_LOG", tmp_path / "suggestions.log")
        mocker.patch("alias_suggest.config.get_max_hourly", return_value=3)

        assert analyzer.check_rate_limit() is True

    def test_rate_limit_blocks_when_over_limit(self, tmp_path, mocker):
        mocker.patch.object(config, "DATA_DIR", tmp_path)
        log_file = tmp_path / "suggestions.log"
        mocker.patch.object(config, "SUGGESTIONS_LOG", log_file)
        mocker.patch("alias_suggest.config.get_max_hourly", return_value=3)

        recent_timestamps = [time.time() - 60 * i for i in range(3)]
        log_file.write_text(json.dumps(recent_timestamps))

        assert analyzer.check_rate_limit() is False

    def test_rate_limit_ignores_old_suggestions(self, tmp_path, mocker):
        mocker.patch.object(config, "DATA_DIR", tmp_path)
        log_file = tmp_path / "suggestions.log"
        mocker.patch.object(config, "SUGGESTIONS_LOG", log_file)
        mocker.patch("alias_suggest.config.get_max_hourly", return_value=3)

        old_timestamps = [time.time() - 7200]
        log_file.write_text(json.dumps(old_timestamps))

        assert analyzer.check_rate_limit() is True

    def test_record_suggestion(self, tmp_path, mocker):
        mocker.patch.object(config, "DATA_DIR", tmp_path)
        log_file = tmp_path / "suggestions.log"
        mocker.patch.object(config, "SUGGESTIONS_LOG", log_file)

        analyzer.record_suggestion()

        timestamps = json.loads(log_file.read_text())
        assert len(timestamps) == 1
        assert time.time() - timestamps[0] < 5


class TestFormatSuggestion:
    def test_format_shell_suggestion(self):
        from alias_suggest import llm

        suggestion = llm.Suggestion(alias_name="ll", expansion="ls -la")
        result = analyzer.format_suggestion(suggestion, is_git=False)

        assert "ll" in result
        assert "ls -la" in result
        assert "💡" in result

    def test_format_git_suggestion(self):
        from alias_suggest import llm

        suggestion = llm.Suggestion(alias_name="st", expansion="status")
        result = analyzer.format_suggestion(suggestion, is_git=True)

        assert "git st" in result
        assert "git status" in result
        assert "💡" in result


class TestAnalyzeCommand:
    def test_disabled_returns_none(self, mocker):
        mocker.patch("alias_suggest.config.is_disabled", return_value=True)
        assert analyzer.analyze_command("git status") is None

    def test_skip_command_returns_none(self, mocker):
        mocker.patch("alias_suggest.config.is_disabled", return_value=False)
        assert analyzer.analyze_command("cd /tmp") is None

    def test_rate_limited_returns_none(self, mocker, tmp_path):
        mocker.patch("alias_suggest.config.is_disabled", return_value=False)
        mocker.patch("alias_suggest.config.is_debug", return_value=False)
        mocker.patch.object(config, "DATA_DIR", tmp_path)
        log_file = tmp_path / "suggestions.log"
        mocker.patch.object(config, "SUGGESTIONS_LOG", log_file)
        mocker.patch("alias_suggest.config.get_max_hourly", return_value=0)
        log_file.write_text(json.dumps([time.time()]))

        assert analyzer.analyze_command("git status") is None
