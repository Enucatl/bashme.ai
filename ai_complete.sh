_bashme_ai_fzf_live_reload() {
    # Prerequisite checks
    if ! command -v fzf &> /dev/null; then
        echo "fzf is not installed. Please install it to use this feature." >&2
        return 1
    fi

    local python_executable="/opt/home/user/venv/bashme/bin/python"
    local cli_script="/home/user/src/bashme.ai/src/bashme/cli.py"

    # The command construction is now simpler as it calls the new CLI
    local initial_command
    printf -v initial_command \
      '%q %q --current-command %q --cursor-position %q --pwd %q 2>/dev/null' \
      "$python_executable" "$cli_script" "$READLINE_LINE" "$READLINE_POINT" "$PWD"

    local reload_command
    printf -v reload_command \
      'bash -c "%s %s --current-command %q --cursor-position %q --pwd %q --fzf-query %q" 2>/dev/null' \
      "$python_executable" "$cli_script" "$READLINE_LINE" "$READLINE_POINT" "$PWD" "{q}"

    # FZF invocation and insertion logic remain exactly the same
    local choice
    choice=$(eval "$initial_command" | fzf \
        --reverse \
        --prompt="AI Command> " \
        --bind "change:reload($reload_command)" \
        --preview 'echo {}' \
        --preview-window 'up,1,border-top')

    if [[ -n "$choice" ]]; then
        READLINE_LINE="$choice"
        READLINE_POINT="${#choice}"
    fi
}

bind -x '"\ec": _bashme_ai_fzf_live_reload'
