import pytest

from alias_suggest import analyzer


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


class TestFindGitPrefixAlias:
    def test_finds_git_alias(self):
        from alias_suggest import alias_parser

        aliases = [
            alias_parser.Alias("g", "git", "/home/user/.bashrc"),
            alias_parser.Alias("ll", "ls -la", "/home/user/.bashrc"),
        ]
        assert analyzer.find_git_prefix_alias(aliases) == "g"

    def test_no_git_alias(self):
        from alias_suggest import alias_parser

        aliases = [
            alias_parser.Alias("ll", "ls -la", "/home/user/.bashrc"),
        ]
        assert analyzer.find_git_prefix_alias(aliases) is None

    def test_ignores_git_config_aliases(self):
        from alias_suggest import alias_parser

        aliases = [
            alias_parser.Alias("st", "status", "git config"),
        ]
        assert analyzer.find_git_prefix_alias(aliases) is None


class TestFormatSuggestion:
    def test_format_shell_suggestion(self):
        suggestion = analyzer.Suggestion(alias_name="ll", expansion="ls -la")
        result = analyzer.format_suggestion(suggestion)

        assert "ll" in result
        assert "ls -la" in result
        assert "💡" in result

    def test_format_git_suggestion_with_prefix(self):
        suggestion = analyzer.Suggestion(alias_name="st", expansion="status", git_prefix="g")
        result = analyzer.format_suggestion(suggestion)

        assert "'g st'" in result
        assert "git status" in result
        assert "💡" in result


class TestAnalyzeCommand:
    def test_disabled_returns_none(self, mocker):
        mocker.patch("alias_suggest.config.is_disabled", return_value=True)
        assert analyzer.analyze_command("git status") is None

    def test_skip_command_returns_none(self, mocker):
        mocker.patch("alias_suggest.config.is_disabled", return_value=False)
        assert analyzer.analyze_command("cd /tmp") is None
