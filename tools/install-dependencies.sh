#!/bin/bash
set -euo pipefail
source ./tools/custom-action/dependency-versions.sh # Source dependency versions

code=1
for opt in "$@"; do
    case "$opt" in
        bikeshed)
            # Note we pin a version of Bikeshed so that `build-validate-publish` will be stable,
            # but spec-prod (used in `publish-TR-webgpu`) always uses the latest.
            python3 -m pip install --upgrade bikeshed==$PIP_BIKESHED_VERSION
            bikeshed update
            code=0
            ;;
        wgsl)
            python3 -m pip install --upgrade build==$PIP_BUILD_VERSION tree_sitter==$PIP_TREE_SITTER_VERSION setuptools==$PIP_SETUPTOOLS_VERSION
            code=0
            ;;
        diagrams)
            npx --yes -- @mermaid-js/mermaid-cli@$NPM_MERMAID_CLI_VERSION --version
            code=0
            ;;
    esac
done

exit "$code"
