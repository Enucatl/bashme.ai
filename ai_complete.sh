_bashme_ai_fzf_live_reload() {
    # The command that fzf will run every time the user types a new character
    # The '{q}' placeholder is replaced by fzf with the current query text.
    local reload_command="
      /opt/home/user/venv/bashme/bin/python /home/user/src/bashme.ai/src/bashme/client.py \
        --current-command '$READLINE_LINE' \
        --cursor-position '$READLINE_POINT' \
        --pwd '$PWD' \
        --api-key '$API_KEY' \
        --fzf-query {q}"

    # We use fzf's 'reload' feature, bound to the 'change' event
    local choice
    choice=$(fzf --reverse --bind "change:reload($reload_command)" --preview 'echo {}')

    if [[ -n "$choice" ]]; then
        local token_to_replace
        token_to_replace=$(echo "${READLINE_LINE:0:$READLINE_POINT}" | grep -o '[^ ]*$')
        local start_pos=$((READLINE_POINT - ${#token_to_replace}))

        READLINE_LINE="${READLINE_LINE:0:$start_pos}${choice} ${READLINE_LINE:$READLINE_POINT}"
        READLINE_POINT=$((start_pos + ${#choice} + 1))
    fi
}

# Bind it to a key
bind -x '"\ec": _bashme_ai_fzf_live_reload'
