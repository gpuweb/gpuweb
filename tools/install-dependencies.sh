#!/bin/bash
set -eo pipefail

code=1
for opt in "$@"; do
    case "$opt" in
        bikeshed)
            pip3 install bikeshed==3.13.1
            bikeshed update
            code=0
            ;;
        wgsl)
            pip3 install tree_sitter==0.20.1
            code=0
            ;;
        diagrams)
            npx --yes -- @mermaid-js/mermaid-cli@10.2.2 --version
            code=0
            ;;
    esac
done

exit "$code"
