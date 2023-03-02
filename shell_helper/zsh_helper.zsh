yc_widget () {
    setopt localoptions pipefail no_aliases 2> /dev/null
    zle -I
    _YC_PIPE=$(mktemp -u /tmp/yc_pipe.XXXXXX)
    (_YC_PIPE=$_YC_PIPE yc) < /dev/tty
    if [ -f "$_YC_PIPE" ]; then
        BUFFER=$(cat $_YC_PIPE)
        rm $_YC_PIPE
    fi
}
