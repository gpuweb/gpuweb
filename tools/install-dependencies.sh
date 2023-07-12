#!/bin/bash
set -eo pipefail
. ./tools/.env

code=1
for opt in "$@"; do
    case "$opt" in
        bikeshed)
            pip3 install bikeshed
            bikeshed update
            code=0
            ;;
        wgsl)
            pip3 install tree_sitter==$PIP_TREE_SITTER_VERSION
            code=0
            ;;
        diagrams)
            npx --yes -- @mermaid-js/mermaid-cli@$NPM_MERMAID_CLI_VERSION --version
            code=0
            ;;
    esac
done

exit "$code"
