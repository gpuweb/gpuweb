#!/bin/bash
set -euo pipefail
source ../tools/custom-action/dependency-versions.sh # Source dependency versions

cfg_file=$(dirname "$0")/mermaid.json
cfg_puppeteer_file=$(dirname "$0")/mermaid-puppeteer.json

# This script is meant to be run in parallel with itself, so it uses --no to
# disable the prompt to install new packages (and avoid npx racing with itself).
# Use tools/install-dependencies.sh to install the package explicitly.
npx --no -- @mermaid-js/mermaid-cli@$NPM_MERMAID_CLI_VERSION --puppeteerConfigFile "$cfg_puppeteer_file" --backgroundColor black --configFile "$cfg_file" "$@" || {
    echo
    echo '**************** Mermaid is not installed. *****************'
    echo '*** Please run `tools/install-dependencies.sh diagrams`. ***'
    if [ -n "${REQUIRE_DIAGRAM_GENERATION:=}" ]; then
        echo '**** Failing because REQUIRE_DIAGRAM_GENERATION is set. ****'
        exit 1
    else
        echo '********** Skipping mermaid diagram regeneration. **********'
    fi
    echo
}
