#!/bin/bash --login
set -eo pipefail

. /.env # Source the environment variables
cp -r /grammar ./wgsl/
python3 -m pip install --break-system-packages
export PATH="$(python3 -m site --user-base)/bin:${PATH}"
bikeshed update
