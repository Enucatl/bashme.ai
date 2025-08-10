# Place this in your ~/.bashrc or a sourced file

_bashme_ai_fzf_live_reload() {
    # Prerequisite checks
    if ! command -v fzf &> /dev/null; then
        echo "fzf is not installed. Please install it to use this feature." >&2
        return 1
    fi
    if [[ -z "$BASHME_API_KEY" ]]; then
        echo "BASHME_API_KEY environment variable is not set." >&2
        return 1
    fi

    # Use a local variable for the python interpreter path for clarity
    local python_executable="/opt/home/user/venv/bashme/bin/python"
    local client_script="/home/user/src/bashme.ai/src/bashme/client.py"

    # --- THE FIX ---
    # Construct the base command that will be run by fzf.
    # Note the use of double quotes to allow variable expansion.
    # We escape the inner double quotes for the command-line arguments.
    # We use printf with %q to safely quote the variables against shell interpretation.
    local initial_command
    printf -v initial_command \
      '%s %s --current-command %q --cursor-position %q --pwd %q --api-key %q 2>/dev/null' \
      "$python_executable" "$client_script" "$READLINE_LINE" "$READLINE_POINT" "$PWD" "$BASHME_API_KEY"

    # The reload command is almost identical, but includes the fzf query `{q}`.
    # We wrap the whole thing in `bash -c "..."` for robust execution.
    local reload_command
    printf -v reload_command \
      'bash -c "%s %s --current-command %q --cursor-position %q --pwd %q --api-key %q --fzf-query %q" 2>/dev/null' \
      "$python_executable" "$client_script" "$READLINE_LINE" "$READLINE_POINT" "$PWD" "$BASHME_API_KEY" "{q}"

    # --- THE FZF INVOCATION ---
    local choice
    #
    # 1. We pipe the output of the *initial_command* into fzf to populate it on startup.
    # 2. The --bind "change:reload(...)" now uses the correctly quoted reload_command.
    #
    choice=$(eval "$initial_command" | fzf --reverse --bind "change:reload($reload_command)")

    # The logic for inserting the choice back into the command line is correct and remains the same.
    if [[ -n "$choice" ]]; then
        # This part of your code was already correct.
        local token_to_replace
        token_to_replace=$(echo "${READLINE_LINE:0:$READLINE_POINT}" | grep -o '[^ ]*$')
        local start_pos=$((READLINE_POINT - ${#token_to_replace}))

        READLINE_LINE="${READLINE_LINE:0:$start_pos}${choice} ${READLINE_LINE:$READLINE_POINT}"
        READLINE_POINT=$((start_pos + ${#choice} + 1))
    fi
}

# Bind it to a key (this part was correct)
# Ensure your BASHME_API_KEY is exported in .bashrc: export BASHME_API_KEY="..."
bind -x '"\ec": _bashme_ai_fzf_live_reload'
