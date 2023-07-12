#!/bin/bash
set -eo pipefail

export $(cat /dependency-versions.env | xargs) # Source the .env file
cp -r /grammar ./wgsl/
python3 -m pip install --break-system-packages --upgrade \
  bikeshed
export PATH="$(python3 -m site --user-base)/bin:${PATH}"
bikeshed update
