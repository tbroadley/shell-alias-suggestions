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

