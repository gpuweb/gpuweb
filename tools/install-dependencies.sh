#!/bin/bash
set -eo pipefail
export $(cat ./tools/custom-action/.env | xargs) # Source the .env file

code=1
for opt in "$@"; do
    case "$opt" in
        bikeshed)
            # Always use the latest bikeshed because that's what spec-prod uses.
            pip3 install --upgrade bikeshed
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
