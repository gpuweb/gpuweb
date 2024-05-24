#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ] ; then
    echo "Usage: $0 output.html SOURCE_FILES..."
    echo
    echo "Invokes the locally-installed 'bikeshed' if available, and falls back to the"
    echo "Bikeshed API (api.csswg.org/bikeshed) if not. One of the source files must be"
    echo "'index.bs'."
    echo
    echo 'Set the $DIE_ON environment variable to use the --die-on option, e.g.:'
    echo "DIE_ON=everything $0 index.bs included1.bs"
    echo
    echo 'Set $BIKESHED_DISALLOW_LOCAL to skip the locally-installed Bikeshed.'
    echo 'Set $BIKESHED_DISALLOW_ONLINE to prevent fallback to the Bikeshed API.'
    exit 1
fi
output="$1"
shift
# now $@ is the list of input files

if type bikeshed >/dev/null && [ -z "${BIKESHED_DISALLOW_LOCAL:=}" ] ; then
    # Build using locally-installed bikeshed.
    # Always build using the tarfile build, to ensure that it never breaks.

    opts=()
    if [ "${DIE_ON:=}" ] ; then
        opts+=("--die-on=$DIE_ON")
    fi

    # Use a temporary file because Bikeshed won't check for tarfiles on stdin.
    tmp_tar=$(mktemp)
    trap 'rm -f -- "$tmp_tar"' EXIT

    tar cf "$tmp_tar" "$@"
    bikeshed "${opts[@]}" spec "$tmp_tar" "$output"
    exit
elif [ -z "${BIKESHED_DISALLOW_ONLINE:=}" ] ; then
    # Build using Bikeshed API.
    echo 'Local bikeshed not found. Falling back to Bikeshed API.'

    tmp_body=$(mktemp) # Contains response body
    tmp_headers=$(mktemp) # Contains response headers
    trap 'rm -f -- "$tmp_body" "$tmp_headers"' EXIT

    opts=()
    if [ "${DIE_ON:=}" ] ; then
        opts+=("--form" "die-on=$DIE_ON")
    fi
    tar c "$@" | curl --silent https://api.csswg.org/bikeshed/ --form "file=@-" "${opts[@]}" --output "$tmp_body" --dump-header "$tmp_headers"

    if head --lines=1 "$tmp_headers" | grep --quiet '\<200\>' ; then
        # If successful, write to output file
        cat "$tmp_body" > "$output"
        exit
    else
        cat "$tmp_headers"
        # If unsuccessful, print the errors on stdout
        cat "$tmp_body" >&2
        exit 1
    fi
fi

echo 'Error: Local bikeshed not found, and $BIKESHED_DISALLOW_ONLINE is set'
exit 1
