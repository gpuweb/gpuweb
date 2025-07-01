#!/bin/bash
set -euo pipefail

source /dependency-versions.sh # Source dependency versions
if [ -d "./wgsl/grammar" ]; then
  rm -rf "./wgsl/grammar"
fi
if [ -d "/grammar" ]; then
  cp -r "/grammar" "./wgsl/"
fi
python3 -m pip install --break-system-packages  --ignore-installed --upgrade \
  bikeshed==$PIP_BIKESHED_VERSION
export PATH="$(python3 -m site --user-base)/bin:${PATH}"
bikeshed update
node "/usr/local/lib/node_modules/puppeteer/install.mjs"
