import importlib.resources
from pathlib import Path

HOOK_MARKER_START = "# >>> alias-suggest initialize >>>"
HOOK_MARKER_END = "# <<< alias-suggest initialize <<<"
HOOK_LINE = 'eval "$(alias-suggest hook)"'


def get_hook_script() -> str:
    return importlib.resources.files("alias_suggest").joinpath("hook.sh").read_text()


def get_shell_config_path(shell: str) -> Path:
    home = Path.home()
    if shell == "bash":
        bashrc = home / ".bashrc"
        if bashrc.exists():
            return bashrc
        return home / ".bash_profile"
    elif shell == "zsh":
        return home / ".zshrc"
    raise ValueError(f"Unsupported shell: {shell}")


def is_hook_installed(config_path: Path) -> bool:
    if not config_path.exists():
        return False
    content = config_path.read_text()
    return HOOK_MARKER_START in content or "alias-suggest" in content


def install_hook(shell: str, force: bool = False) -> tuple[bool, str]:
    config_path = get_shell_config_path(shell)

    if is_hook_installed(config_path) and not force:
        return False, f"Hook already installed in {config_path}"

    if force and is_hook_installed(config_path):
        uninstall_hook(shell)

    hook_block = f"""
{HOOK_MARKER_START}
{HOOK_LINE}
{HOOK_MARKER_END}
"""

    if config_path.exists():
        content = config_path.read_text()
        if not content.endswith("\n"):
            content += "\n"
    else:
        content = ""

    content += hook_block
    config_path.write_text(content)

    return True, f"Installed hook in {config_path}"


def uninstall_hook(shell: str) -> tuple[bool, str]:
    config_path = get_shell_config_path(shell)

    if not config_path.exists():
        return False, f"Config file not found: {config_path}"

    content = config_path.read_text()

    if HOOK_MARKER_START not in content:
        if "alias-suggest" in content:
            return (
                False,
                f"Found alias-suggest references but not in expected format in {config_path}",
            )
        return False, f"No hook found in {config_path}"

    lines = content.splitlines()
    new_lines = []
    in_block = False

    for line in lines:
        if HOOK_MARKER_START in line:
            in_block = True
            continue
        if HOOK_MARKER_END in line:
            in_block = False
            continue
        if not in_block:
            new_lines.append(line)

    while new_lines and new_lines[-1] == "":
        new_lines.pop()

    config_path.write_text("\n".join(new_lines) + "\n" if new_lines else "")

    return True, f"Removed hook from {config_path}"


def detect_available_shells() -> list[str]:
    shells = []
    home = Path.home()

    if (home / ".bashrc").exists() or (home / ".bash_profile").exists():
        shells.append("bash")
    if (home / ".zshrc").exists():
        shells.append("zsh")

    return shells if shells else ["bash"]
