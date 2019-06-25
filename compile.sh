#!/bin/bash
set -e # Exit with nonzero exit code if anything fails

make -C spec

if [ -d out ]; then
  echo Copy spec/index.html into out/index.html
  cp spec/index.html out/index.html
fi
