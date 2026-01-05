import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from alias_suggest import config


@dataclass
class Alias:
    name: str
    expansion: str
    source: str


@dataclass
class AliasCache:
    aliases: list[Alias]
    file_mtimes: dict[str, float]


def get_shell_config_files() -> list[Path]:
    home = Path.home()
    candidates = [
        home / ".bashrc",
        home / ".zshrc",
        home / ".bash_aliases",
        home / ".zsh_aliases",
        home / ".bash_profile",
        home / ".profile",
    ]
    zsh_custom = home / ".oh-my-zsh" / "custom"
    if zsh_custom.exists():
        candidates.extend(zsh_custom.glob("*.zsh"))
        candidates.extend(zsh_custom.glob("**/*.zsh"))
    return [f for f in candidates if f.exists()]


def parse_shell_aliases(content: str) -> list[tuple[str, str]]:
    aliases = []
    alias_pattern = re.compile(
        r"""^\s*alias\s+([^=]+)=(['"]?)(.+?)\2\s*$""", re.MULTILINE
    )
    for match in alias_pattern.finditer(content):
        name = match.group(1).strip()
        expansion = match.group(3).strip()
        if expansion.startswith(("'", '"')) and expansion.endswith(expansion[0]):
            expansion = expansion[1:-1]
        aliases.append((name, expansion))
    return aliases


def parse_shell_config_file(path: Path) -> list[Alias]:
    try:
        content = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    return [Alias(name, exp, str(path)) for name, exp in parse_shell_aliases(content)]


def get_git_aliases() -> list[Alias]:
    try:
        result = subprocess.run(
            ["git", "config", "--global", "--list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    aliases = []
    for line in result.stdout.splitlines():
        if line.startswith("alias."):
            parts = line.split("=", 1)
            if len(parts) == 2:
                name = parts[0][6:]
                expansion = parts[1]
                aliases.append(Alias(name, expansion, "git config"))
    return aliases


def load_cache() -> AliasCache | None:
    if not config.CACHE_FILE.exists():
        return None
    try:
        data = json.loads(config.CACHE_FILE.read_text())
        aliases = [Alias(**a) for a in data["aliases"]]
        return AliasCache(aliases=aliases, file_mtimes=data["file_mtimes"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save_cache(cache: AliasCache) -> None:
    config.ensure_data_dir()
    data = {
        "aliases": [
            {"name": a.name, "expansion": a.expansion, "source": a.source}
            for a in cache.aliases
        ],
        "file_mtimes": cache.file_mtimes,
    }
    config.CACHE_FILE.write_text(json.dumps(data, indent=2))


def is_cache_valid(cache: AliasCache) -> bool:
    config_files = get_shell_config_files()
    current_mtimes = {}
    for f in config_files:
        try:
            current_mtimes[str(f)] = f.stat().st_mtime
        except OSError:
            continue
    return cache.file_mtimes == current_mtimes


def get_all_aliases(force_refresh: bool = False) -> list[Alias]:
    if not force_refresh:
        cache = load_cache()
        if cache and is_cache_valid(cache):
            return cache.aliases

    all_aliases = []
    file_mtimes = {}

    config_files = get_shell_config_files()
    for config_file in config_files:
        try:
            file_mtimes[str(config_file)] = config_file.stat().st_mtime
        except OSError:
            continue
        all_aliases.extend(parse_shell_config_file(config_file))

    all_aliases.extend(get_git_aliases())

    cache = AliasCache(aliases=all_aliases, file_mtimes=file_mtimes)
    save_cache(cache)

    return all_aliases


def clear_cache() -> bool:
    if config.CACHE_FILE.exists():
        config.CACHE_FILE.unlink()
        return True
    return False
