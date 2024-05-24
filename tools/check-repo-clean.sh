#!/bin/bash
set -euo pipefail

status=$(git status -s)

if [ -n "$status" ] ; then
  echo "$status"
  exit 1
fi
