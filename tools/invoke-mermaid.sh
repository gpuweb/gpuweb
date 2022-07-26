#!/bin/sh

cfg_file=$(dirname "$0")/mermaid.json

# This script is meant to be run in parallel with itself, so it uses --no to
# disable the prompt to install new packages (and avoid npx racing with itself).
# Use tools/install-dependencies.sh to install the package explicitly.
npx --no -- @mermaid-js/mermaid-cli@9.1.4 --backgroundColor black --configFile "$cfg_file" "$@"
ret=$?

if [ "$ret" != 0 ]; then
        echo '**************** Mermaid is not installed. *****************'
        echo '*** Please run `tools/install-dependencies.sh diagrams`. ***'
    if [ -n "$REQUIRE_DIAGRAM_GENERATION" ]; then
        echo '**** Failing because REQUIRE_DIAGRAM_GENERATION is set. ****'
        exit "$ret"
    else
        echo '********** Skipping mermaid diagram regeneration. **********'
    fi
fi
