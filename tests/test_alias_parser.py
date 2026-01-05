import pytest

from alias_suggest import alias_parser


class TestParseShellAliases:
    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            ("alias ll='ls -la'", [("ll", "ls -la")]),
            ('alias ll="ls -la"', [("ll", "ls -la")]),
            ("alias ll=ls", [("ll", "ls")]),
            ("  alias ll='ls -la'  ", [("ll", "ls -la")]),
            ("alias gst='git status'", [("gst", "git status")]),
            (
                "alias ll='ls -la'\nalias la='ls -A'",
                [("ll", "ls -la"), ("la", "ls -A")],
            ),
            ("# alias commented='out'", []),
            ("echo 'alias inside=string'", []),
            ("", []),
        ],
    )
    def test_parse_shell_aliases(self, content: str, expected: list[tuple[str, str]]):
        result = alias_parser.parse_shell_aliases(content)
        assert result == expected

    def test_parse_complex_alias(self):
        content = "alias gc='git commit -m'"
        result = alias_parser.parse_shell_aliases(content)
        assert result == [("gc", "git commit -m")]


class TestAliasCache:
    def test_save_and_load_cache(self, tmp_path, mocker):
        mocker.patch("alias_suggest.config.CACHE_FILE", tmp_path / "cache.json")
        mocker.patch("alias_suggest.config.DATA_DIR", tmp_path)

        aliases = [
            alias_parser.Alias("ll", "ls -la", "/home/user/.bashrc"),
            alias_parser.Alias("gst", "git status", "git config"),
        ]
        cache = alias_parser.AliasCache(
            aliases=aliases, file_mtimes={"/home/user/.bashrc": 12345.0}
        )

        alias_parser.save_cache(cache)
        loaded = alias_parser.load_cache()

        assert loaded is not None
        assert len(loaded.aliases) == 2
        assert loaded.aliases[0].name == "ll"
        assert loaded.aliases[1].name == "gst"
        assert loaded.file_mtimes == {"/home/user/.bashrc": 12345.0}

    def test_load_cache_missing_file(self, tmp_path, mocker):
        mocker.patch("alias_suggest.config.CACHE_FILE", tmp_path / "nonexistent.json")
        assert alias_parser.load_cache() is None

    def test_load_cache_invalid_json(self, tmp_path, mocker):
        cache_file = tmp_path / "cache.json"
        cache_file.write_text("not valid json")
        mocker.patch("alias_suggest.config.CACHE_FILE", cache_file)
        assert alias_parser.load_cache() is None


class TestGetGitAliases:
    def test_parse_git_aliases(self, mocker):
        mock_result = mocker.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "alias.st=status\nalias.co=checkout\nuser.name=Test"
        mocker.patch("subprocess.run", return_value=mock_result)

        aliases = alias_parser.get_git_aliases()

        assert len(aliases) == 2
        assert aliases[0].name == "st"
        assert aliases[0].expansion == "status"
        assert aliases[1].name == "co"
        assert aliases[1].expansion == "checkout"

    def test_git_not_found(self, mocker):
        mocker.patch("subprocess.run", side_effect=FileNotFoundError())
        aliases = alias_parser.get_git_aliases()
        assert aliases == []
