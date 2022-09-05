#!/bin/sh
set -e

code=1
for opt in "$@"; do
    case "$opt" in
        bikeshed)
            pip3 install bikeshed==3.7.0
            bikeshed update
            code=0
            ;;
        wgsl)
            pip3 install tree_sitter==0.20.0
            code=0
            ;;
        diagrams)
            npx --yes -- @mermaid-js/mermaid-cli@9.1.4 --version
            code=0
            ;;
    esac
done

exit "$code"
