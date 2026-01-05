import pytest

from alias_suggest import alias_parser
from alias_suggest import pattern_matcher


@pytest.fixture
def sample_aliases() -> list[alias_parser.Alias]:
    return [
        alias_parser.Alias("ll", "ls -la", "/home/user/.bashrc"),
        alias_parser.Alias("la", "ls -A", "/home/user/.bashrc"),
        alias_parser.Alias("gst", "git status", "/home/user/.bashrc"),
        alias_parser.Alias("st", "status", "git config"),
        alias_parser.Alias("co", "checkout", "git config"),
        alias_parser.Alias("cb", "checkout -b", "git config"),
    ]


class TestTokenizeCommand:
    @pytest.mark.parametrize(
        ("cmd", "expected"),
        [
            ("ls -la", ["ls", "-la"]),
            ("git status", ["git", "status"]),
            ("echo 'hello world'", ["echo", "hello world"]),
            ('echo "hello world"', ["echo", "hello world"]),
            ("", []),
        ],
    )
    def test_tokenize_command(self, cmd: str, expected: list[str]):
        assert pattern_matcher.tokenize_command(cmd) == expected

    def test_tokenize_unbalanced_quotes(self):
        result = pattern_matcher.tokenize_command("echo 'unbalanced")
        assert result == ["echo", "'unbalanced"]


class TestFindMatches:
    def test_exact_shell_alias_match(self, sample_aliases):
        matches = pattern_matcher.find_matches("ls -la", sample_aliases)
        assert len(matches) > 0
        assert matches[0].alias.name == "ll"
        assert matches[0].confidence == 1.0

    def test_exact_git_alias_match(self, sample_aliases):
        matches = pattern_matcher.find_matches("git status", sample_aliases)
        assert len(matches) > 0
        git_matches = [m for m in matches if m.alias.source == "git config"]
        assert any(m.alias.name == "st" for m in git_matches)

    def test_prefix_match(self, sample_aliases):
        matches = pattern_matcher.find_matches("ls -la /tmp", sample_aliases)
        assert len(matches) > 0
        assert any(m.alias.name == "ll" for m in matches)

    def test_git_prefix_match(self, sample_aliases):
        matches = pattern_matcher.find_matches(
            "git checkout -b feature", sample_aliases
        )
        assert len(matches) > 0
        assert any(m.alias.name == "cb" for m in matches)

    def test_no_match(self, sample_aliases):
        matches = pattern_matcher.find_matches("echo hello", sample_aliases)
        assert len(matches) == 0

    def test_empty_command(self, sample_aliases):
        matches = pattern_matcher.find_matches("", sample_aliases)
        assert len(matches) == 0


class TestGetBestMatch:
    def test_high_confidence_match(self, sample_aliases):
        result = pattern_matcher.get_best_match(
            "ls -la", sample_aliases, min_confidence=0.8
        )
        assert result is not None
        assert result.alias.name == "ll"

    def test_low_confidence_filtered(self, sample_aliases):
        result = pattern_matcher.get_best_match(
            "ls -la /very/long/path/to/somewhere",
            sample_aliases,
            min_confidence=0.95,
        )
        assert result is None or result.confidence >= 0.95

    def test_no_match_returns_none(self, sample_aliases):
        result = pattern_matcher.get_best_match(
            "echo hello", sample_aliases, min_confidence=0.8
        )
        assert result is None
