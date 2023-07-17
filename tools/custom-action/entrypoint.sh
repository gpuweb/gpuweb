#!/bin/bash --login
set -eo pipefail

source /prepare.sh # Execute the prepare script
git init # To ensure subsequent git commands pick the workspace
git config --global --add safe.directory /github/workspace
BIKESHED_DISALLOW_ONLINE=1 REQUIRE_DIAGRAM_GENERATION=1 make -j out
if [[ "$1" == "ON" ]]; then
  echo "Checking if repo is clean"
  bash tools/check-repo-clean.sh
fi
chmod --recursive 777 out # For subsequent steps
