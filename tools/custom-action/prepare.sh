#!/bin/bash
set -eo pipefail

export $(cat /.env | xargs) # Source the .env file
cp -r /grammar ./wgsl/
sudo python3 -m pip install --break-system-packages \
  bikeshed
export PATH="$(python3 -m site --user-base)/bin:${PATH}"
sudo bikeshed update
