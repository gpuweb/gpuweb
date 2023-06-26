#!/bin/bash
set -eo pipefail

status=$(git status -s)
diffs=$(git diff)

if [ -n "$status" ] ; then
  echo "$status"
  echo "$diffs"
  exit 1
fi
