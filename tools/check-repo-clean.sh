#!/bin/bash
set -eo pipefail

status=$(git status -s)

if [ -n "$status" ] ; then
  echo "$status"
  git diff
  exit 1
fi
