import sys

import click

from alias_suggest import alias_parser
from alias_suggest import analyzer
from alias_suggest import config
from alias_suggest import hooks


@click.group()
@click.version_option()
def main():
    """Shell alias suggestion tool powered by Claude."""
    pass


@main.command()
@click.option("--bash", "shell", flag_value="bash", help="Only install bash hook")
@click.option("--zsh", "shell", flag_value="zsh", help="Only install zsh hook")
@click.option("--force", is_flag=True, help="Overwrite existing hooks")
def install(shell: str | None, force: bool):
    """Install shell hooks into shell config files."""
    if shell:
        shells = [shell]
    else:
        shells = hooks.detect_available_shells()

    success = False
    for sh in shells:
        installed, message = hooks.install_hook(sh, force=force)
        if installed:
            click.echo(click.style(f"✓ {message}", fg="green"))
            success = True
        else:
            click.echo(click.style(f"• {message}", fg="yellow"))

    if success:
        click.echo()
        click.echo("Restart your shell or run:")
        for sh in shells:
            config_file = "~/.bashrc" if sh == "bash" else "~/.zshrc"
            click.echo(f"  source {config_file}")


@main.command()
@click.option("--bash", "shell", flag_value="bash", help="Only uninstall bash hook")
@click.option("--zsh", "shell", flag_value="zsh", help="Only uninstall zsh hook")
def uninstall(shell: str | None):
    """Remove shell hooks from shell config files."""
    if shell:
        shells = [shell]
    else:
        shells = hooks.detect_available_shells()

    for sh in shells:
        removed, message = hooks.uninstall_hook(sh)
        if removed:
            click.echo(click.style(f"✓ {message}", fg="green"))
        else:
            click.echo(click.style(f"• {message}", fg="yellow"))


@main.command()
@click.argument("command")
def analyze(command: str):
    """Analyze a command for alias suggestions."""
    sys.exit(analyzer.run_analysis(command))


@main.command()
def hook():
    """Output the shell hook script for eval."""
    click.echo(hooks.get_hook_script())


@main.command("config")
def show_config():
    """Show current configuration."""
    click.echo("Configuration (from environment variables):")
    click.echo()

    api_key = config.get_api_key()
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        click.echo(f"  ANTHROPIC_API_KEY:        {masked}")
    else:
        click.echo(click.style("  ANTHROPIC_API_KEY:        (not set)", fg="red"))

    click.echo(f"  ALIAS_SUGGEST_DISABLED:   {config.is_disabled()}")
    click.echo(f"  ALIAS_SUGGEST_MODEL:      {config.get_model()}")
    click.echo(f"  ALIAS_SUGGEST_MAX_HOURLY: {config.get_max_hourly()}")
    click.echo(f"  ALIAS_SUGGEST_TIMEOUT:    {config.get_timeout()}s")
    click.echo(f"  ALIAS_SUGGEST_MIN_CONF:   {config.get_min_confidence()}")
    click.echo(f"  ALIAS_SUGGEST_DEBUG:      {config.is_debug()}")
    click.echo()
    click.echo(f"Data directory: {config.DATA_DIR}")
    click.echo(f"Cache file:     {config.CACHE_FILE}")


@main.command()
def test():
    """Run a self-test to verify installation."""
    click.echo("Running self-test...")
    click.echo()

    click.echo("1. Checking API key...", nl=False)
    if config.get_api_key():
        click.echo(click.style(" OK", fg="green"))
    else:
        click.echo(click.style(" MISSING", fg="red"))
        click.echo("   Set ANTHROPIC_API_KEY environment variable")

    click.echo("2. Loading aliases...", nl=False)
    aliases = alias_parser.get_all_aliases()
    click.echo(click.style(f" {len(aliases)} found", fg="green"))

    shell_aliases = [a for a in aliases if a.source != "git config"]
    git_aliases = [a for a in aliases if a.source == "git config"]
    click.echo(f"   - Shell aliases: {len(shell_aliases)}")
    click.echo(f"   - Git aliases: {len(git_aliases)}")

    click.echo("3. Testing pattern matcher...", nl=False)
    from alias_suggest import pattern_matcher

    test_cmd = "git status"
    matches = pattern_matcher.find_matches(test_cmd, aliases)
    if matches:
        click.echo(click.style(f" OK ({len(matches)} matches for '{test_cmd}')", fg="green"))
    else:
        click.echo(click.style(" No matches (normal if no git aliases)", fg="yellow"))

    click.echo("4. Checking shell hooks...", nl=False)
    installed_shells = []
    for shell in ["bash", "zsh"]:
        try:
            config_path = hooks.get_shell_config_path(shell)
            if hooks.is_hook_installed(config_path):
                installed_shells.append(shell)
        except (ValueError, FileNotFoundError):
            pass
    if installed_shells:
        click.echo(click.style(f" Installed: {', '.join(installed_shells)}", fg="green"))
    else:
        click.echo(click.style(" Not installed", fg="yellow"))
        click.echo("   Run 'alias-suggest install' to install hooks")

    click.echo()
    click.echo("Self-test complete!")


@main.group()
def cache():
    """Manage the alias cache."""
    pass


@cache.command("clear")
def cache_clear():
    """Clear the alias cache to force refresh."""
    if alias_parser.clear_cache():
        click.echo(click.style("✓ Cache cleared", fg="green"))
    else:
        click.echo("Cache file not found (nothing to clear)")


@cache.command("show")
def cache_show():
    """Show cached aliases."""
    aliases = alias_parser.get_all_aliases()

    shell_aliases = [a for a in aliases if a.source != "git config"]
    git_aliases = [a for a in aliases if a.source == "git config"]

    if shell_aliases:
        click.echo(click.style("Shell Aliases:", bold=True))
        for alias in shell_aliases[:20]:
            click.echo(f"  {alias.name} = {alias.expansion}")
        if len(shell_aliases) > 20:
            click.echo(f"  ... and {len(shell_aliases) - 20} more")
        click.echo()

    if git_aliases:
        click.echo(click.style("Git Aliases:", bold=True))
        for alias in git_aliases[:20]:
            click.echo(f"  git {alias.name} = git {alias.expansion}")
        if len(git_aliases) > 20:
            click.echo(f"  ... and {len(git_aliases) - 20} more")

    if not aliases:
        click.echo("No aliases found")


if __name__ == "__main__":
    main()

