Shell Alias Suggestion Tool

Overview

A tool that monitors shell commands and suggests existing aliases that could have been
used instead. Works with both bash and zsh, uses Claude API (Haiku) for intelligent
suggestions.

Requirements

- Run after every command in bash (dev containers) and zsh (macOS host)
- Analyze command against existing shell aliases and git aliases
- Use Claude Haiku API for fast, inexpensive suggestions
- Support both shells with minimal configuration
- Python implementation using Anthropic SDK
- API key from $ANTHROPIC_API_KEY environment variable
- Conservative suggestion mode (>80% confidence, max 3 suggestions per hour)
- Easy one-line installation via pipx or uv

Installation

Quick Install (Recommended)

Using pipx (works everywhere):
    pipx install git+https://github.com/YOUR_USERNAME/shell-alias-suggestions.git
    alias-suggest install

Using uv (faster):
    uv tool install git+https://github.com/YOUR_USERNAME/shell-alias-suggestions.git
    alias-suggest install

Then restart your shell or run:
    source ~/.bashrc  # or ~/.zshrc

Dev Container Installation

Add to your devcontainer.json postCreateCommand or Dockerfile:
    pipx install git+https://github.com/YOUR_USERNAME/shell-alias-suggestions.git && alias-suggest install --bash

Or add to devcontainer.json features (after publishing):
    "features": {
        "ghcr.io/YOUR_USERNAME/shell-alias-suggestions:1": {}
    }

Local Development Install

    cd shell-alias-suggestions
    pipx install -e .
    alias-suggest install

Architecture

Project Structure

    shell-alias-suggestions/
    ├── pyproject.toml              # Package configuration
    ├── src/
    │   └── alias_suggest/
    │       ├── __init__.py
    │       ├── cli.py              # CLI entry points
    │       ├── analyzer.py         # Main analysis logic
    │       ├── alias_parser.py     # Parse shell/git aliases
    │       ├── pattern_matcher.py  # Fast local matching
    │       ├── llm.py              # Claude API integration
    │       ├── config.py           # Configuration management
    │       ├── hooks.py            # Shell hook generation/installation
    │       └── hook.sh             # Shell hook script (bundled)
    ├── tests/
    │   ├── test_analyzer.py
    │   ├── test_alias_parser.py
    │   ├── test_pattern_matcher.py
    │   └── test_llm.py
    └── README.md

Components

1. CLI Tool (alias-suggest)
   - Entry point installed globally via pipx/uv
   - Subcommands: install, uninstall, analyze, config, test
   - Handles shell hook installation/removal

2. Shell Hook (bundled hook.sh)
   - Lightweight shell script bundled with the package
   - Integrates with both bash and zsh
   - Captures last executed command from history
   - Calls the analyzer asynchronously to avoid blocking terminal

3. Analyzer Module
   - Parses shell aliases and git aliases
   - Performs fast local pattern matching
   - Calls Claude Haiku API when potential match found
   - Returns suggestion to display

4. Data Storage
   - Uses ~/.local/share/alias-suggest/ for data files
   - cache.json - Cached parsed aliases (auto-updated)
   - suggestions.log - Rate limiting tracker (auto-generated)
   - Config via environment variables (no config file needed)

Data Flow

    Command executed
        ↓
    Shell hook triggered (PROMPT_COMMAND/precmd)
        ↓
    hook.sh captures command from history
        ↓
    hook.sh calls `alias-suggest analyze` in background
        ↓
    Analyzer checks cache for aliases (or rebuilds if stale)
        ↓
    Fast local pattern matching
        ↓
    If potential match → Call Claude Haiku API
        ↓
    Display friendly suggestion to user

CLI Commands

alias-suggest install
    Install shell hooks into ~/.bashrc and/or ~/.zshrc
    Options:
      --bash      Only install bash hook
      --zsh       Only install zsh hook
      --force     Overwrite existing hooks

alias-suggest uninstall
    Remove shell hooks from shell config files

alias-suggest analyze "git status"
    Manually analyze a command (for testing)

alias-suggest config
    Show current configuration (from env vars)

alias-suggest test
    Run a self-test to verify installation

alias-suggest cache --clear
    Clear the alias cache to force refresh

Implementation Plan

Step 1: Create Package Structure

Create pyproject.toml:
    [project]
    name = "alias-suggest"
    version = "0.1.0"
    description = "Shell alias suggestion tool powered by Claude"
    requires-python = ">=3.9"
    dependencies = [
        "anthropic>=0.18.0",
        "click>=8.0.0",
    ]

    [project.scripts]
    alias-suggest = "alias_suggest.cli:main"

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = ["src/alias_suggest"]

Step 2: Build CLI with Click

Create src/alias_suggest/cli.py:
- Main entry point using Click
- install subcommand to add hooks to shell configs
- uninstall subcommand to remove hooks
- analyze subcommand for manual testing
- config subcommand to show settings
- test subcommand for self-verification

Step 3: Build Alias Parser

Create src/alias_suggest/alias_parser.py:
- Extract aliases from:
  - Shell configs: ~/.bashrc, ~/.zshrc, ~/.bash_aliases, ~/.zsh_aliases
  - Oh-my-zsh plugins if present
  - Git config: git config --global --list | grep '^alias\.'
- Cache parsed aliases with file modification timestamps
- Auto-refresh cache when config files change
- Store cache in ~/.local/share/alias-suggest/cache.json

Step 4: Build Pattern Matcher

Create src/alias_suggest/pattern_matcher.py:
- Fast local matching algorithm:
  - Check if command starts with git and matches any git alias expansion
  - Check if command matches any shell alias expansion
  - Build candidate list of potential aliases
- Return top candidates for LLM analysis
- Calculate confidence score for each match

Step 5: Integrate Claude API

Create src/alias_suggest/llm.py:
- Use anthropic Python SDK
- Read API key from $ANTHROPIC_API_KEY environment variable
- Call with Haiku model (claude-3-5-haiku-20241022)
- Only call API if local pattern matching confidence > 80%
- Prompt template:
    The user ran this command: {command}

    Available aliases:
    {relevant_aliases}

    Could they have used an alias instead? If yes, respond with ONLY:
    ALIAS: <alias_name>
    EXPANSION: <what_it_expands_to>
    
    If no good match, respond with: NO_SUGGESTION
- Parse response and format for display
- Cache recent suggestions to avoid duplicate LLM calls

Step 6: Create Shell Hook

Create src/alias_suggest/hook.sh (bundled with package):
    # Shell Alias Suggestions Hook
    # Installed by: alias-suggest install

    __alias_suggest_check() {
        local last_cmd
        if [ -n "$ZSH_VERSION" ]; then
            last_cmd=$(fc -ln -1 2>/dev/null | sed 's/^[[:space:]]*//')
        else
            last_cmd=$(HISTTIMEFORMAT= history 1 2>/dev/null | sed 's/^[[:space:]]*[0-9]*[[:space:]]*//')
        fi
        
        [ -z "$last_cmd" ] && return
        [ "$last_cmd" = "$__ALIAS_SUGGEST_LAST_CMD" ] && return
        export __ALIAS_SUGGEST_LAST_CMD="$last_cmd"
        
        # Run in background to not block prompt
        (alias-suggest analyze "$last_cmd" 2>/dev/null &)
    }

    # Install hook based on shell type
    if [ -n "$ZSH_VERSION" ]; then
        autoload -Uz add-zsh-hook
        add-zsh-hook precmd __alias_suggest_check
    elif [ -n "$BASH_VERSION" ]; then
        PROMPT_COMMAND="__alias_suggest_check${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
    fi

Step 7: Shell Hook Installation

Create src/alias_suggest/hooks.py:
- Function to locate shell config files
- Function to inject hook source line
- Function to remove hook source line
- Support for both bash and zsh
- Idempotent installation (don't add duplicates)

Hook injection (added to ~/.bashrc or ~/.zshrc):
    # Alias Suggest - Shell alias suggestions powered by Claude
    eval "$(alias-suggest hook)"

Step 8: Display Formatting

- Show suggestions in a distinct color (cyan)
- Format: 💡 Tip: Use 'gst' instead → git status
- Option to disable via $ALIAS_SUGGEST_DISABLED=1
- Respect terminal width for formatting

Step 9: Performance Optimizations

- Cache parsed aliases with file timestamps
- Only call LLM if local pattern matching confidence > 80%
- Timeout after 2 seconds if LLM call is slow
- Add rate limiting (max 3 suggestions per hour by default)
- Track suggestion timestamps in ~/.local/share/alias-suggest/suggestions.log
- Skip common simple commands (cd, ls, clear, pwd, exit)

Configuration

All configuration via environment variables (no config file needed):

    ANTHROPIC_API_KEY          # Required: Your Anthropic API key
    ALIAS_SUGGEST_DISABLED=1   # Disable suggestions temporarily
    ALIAS_SUGGEST_MODEL        # Model to use (default: claude-3-5-haiku-20241022)
    ALIAS_SUGGEST_MAX_HOURLY   # Max suggestions per hour (default: 3)
    ALIAS_SUGGEST_TIMEOUT      # API timeout in seconds (default: 2)
    ALIAS_SUGGEST_MIN_CONF     # Minimum confidence threshold (default: 0.8)
    ALIAS_SUGGEST_DEBUG=1      # Enable debug output

Files Created at Runtime

    ~/.local/share/alias-suggest/
    ├── cache.json              # Alias cache (auto-generated)
    └── suggestions.log         # Rate limiting tracker

Edge Cases to Handle

- Commands with pipes, redirects, and complex syntax
- Multi-line commands
- Commands run via sudo
- Git aliases that themselves use other aliases
- Aliases with arguments vs exact matches
- Shell-specific syntax differences (bash vs zsh)
- Missing ANTHROPIC_API_KEY (graceful degradation)
- Network timeouts

Testing Strategy

1. Unit tests for alias parser (test_alias_parser.py)
2. Unit tests for pattern matcher (test_pattern_matcher.py)
3. Unit tests for LLM integration with mocking (test_llm.py)
4. Integration tests for CLI commands
5. Test with common git aliases (gst, gco, gp, etc.)
6. Test with shell aliases (ll, la, ..., etc.)
7. Test in both bash and zsh environments
8. Test API error handling (rate limits, network issues)

Dev Container Feature (Optional)

For easier dev container integration, create a Dev Container Feature:

    devcontainer-feature.json:
    {
        "id": "shell-alias-suggestions",
        "version": "1.0.0",
        "name": "Shell Alias Suggestions",
        "description": "AI-powered shell alias suggestions",
        "options": {
            "shell": {
                "type": "string",
                "enum": ["both", "bash", "zsh"],
                "default": "bash",
                "description": "Which shell(s) to install hooks for"
            }
        }
    }

    install.sh:
    #!/bin/bash
    pipx install alias-suggest
    alias-suggest install --${SHELL:-bash}

Future Enhancements

- Support for fish shell
- Machine learning to learn user patterns over time
- Suggest creating NEW aliases for frequently used long commands
- Integration with popular alias frameworks (oh-my-zsh, bash-it)
- Publish to PyPI for easier installation (pip install alias-suggest)
- Create Homebrew formula for macOS
- Web dashboard to view alias usage statistics
