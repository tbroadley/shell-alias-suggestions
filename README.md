# Shell Alias Suggestions

A tool that monitors shell commands and suggests existing aliases that could have been used instead. Works with both bash and zsh.

## Features

- Automatically detects when you could have used an alias
- Works with both shell aliases and git aliases
- Chains shell + git aliases (e.g., suggests `g s` if you have `g=git` and git alias `s=status`)
- Fast: uses local pattern matching with caching
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

All configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ALIAS_SUGGEST_DISABLED` | `false` | Disable suggestions temporarily |
| `ALIAS_SUGGEST_MIN_CONF` | `0.8` | Minimum confidence threshold |
| `ALIAS_SUGGEST_DEBUG` | `false` | Enable debug output |

## Usage

Once installed, the tool runs automatically after each command. When it detects a command that could have used an alias, you'll see:

```
💡 Tip: Use 'g s' instead → git status
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
2. Fast local pattern matching checks for alias matches
3. If confidence > 80%, suggestion is displayed
4. Suggestion shows the alias and its expansion

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
uv tool install -e .

# Run tests
uv run pytest
```

## License

MIT
