# Shell Alias Suggestions

A tool that monitors shell commands and suggests existing aliases that could have been used instead. Works with both bash and zsh, uses Claude API (Haiku) for intelligent suggestions.

## Features

- Automatically detects when you could have used an alias
- Works with both shell aliases and git aliases
- Uses Claude Haiku for smart, context-aware suggestions
- Rate-limited to avoid being annoying (max 3 suggestions/hour by default)
- Non-blocking: runs in background, doesn't slow down your shell
- Easy one-line installation

## Quick Install

Using pipx (recommended):

```bash
pipx install git+https://github.com/YOUR_USERNAME/shell-alias-suggestions.git
alias-suggest install
```

Using uv (faster):

```bash
uv tool install git+https://github.com/YOUR_USERNAME/shell-alias-suggestions.git
alias-suggest install
```

Then restart your shell or run:

```bash
source ~/.bashrc  # or ~/.zshrc
```

## Configuration

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

All configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `ALIAS_SUGGEST_DISABLED` | `false` | Disable suggestions temporarily |
| `ALIAS_SUGGEST_MODEL` | `claude-3-5-haiku-20241022` | Claude model to use |
| `ALIAS_SUGGEST_MAX_HOURLY` | `3` | Max suggestions per hour |
| `ALIAS_SUGGEST_TIMEOUT` | `2` | API timeout in seconds |
| `ALIAS_SUGGEST_MIN_CONF` | `0.8` | Minimum confidence threshold |
| `ALIAS_SUGGEST_DEBUG` | `false` | Enable debug output |

## Usage

Once installed, the tool runs automatically after each command. When it detects a command that could have used an alias, you'll see:

```
💡 Tip: Use 'gst' instead → git status
```

### CLI Commands

```bash
# Install shell hooks
alias-suggest install
alias-suggest install --bash  # bash only
alias-suggest install --zsh   # zsh only

# Remove shell hooks
alias-suggest uninstall

# Manually analyze a command
alias-suggest analyze "git status"

# Show configuration
alias-suggest config

# Run self-test
alias-suggest test

# Manage alias cache
alias-suggest cache show
alias-suggest cache clear
```

## How It Works

1. Shell hook captures each command after execution
2. Fast local pattern matching checks for potential alias matches
3. If confidence > 80%, Claude Haiku API confirms the suggestion
4. Suggestion displayed in cyan with the alias and its expansion

## Dev Container Installation

Add to your `devcontainer.json` postCreateCommand:

```json
{
  "postCreateCommand": "pipx install git+https://github.com/YOUR_USERNAME/shell-alias-suggestions.git && alias-suggest install --bash"
}
```

## Development

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/shell-alias-suggestions.git
cd shell-alias-suggestions

# Install in development mode
pipx install -e .

# Run tests
pip install pytest pytest-mock
pytest
```

## License

MIT

