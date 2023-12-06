#!/bin/bash
set -eo pipefail

source /dependency-versions.sh # Source dependency versions
cp -r /grammar ./wgsl/
python3 -m pip install --break-system-packages --upgrade \
  bikeshed
export PATH="$(python3 -m site --user-base)/bin:${PATH}"
bikeshed update
node "/usr/local/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/puppeteer/install.js"
