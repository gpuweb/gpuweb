#!/bin/bash
set -e # Exit with nonzero exit code if anything fails

echo 'Building spec'
make -C spec
echo 'Building wgsl'
make -C wgsl
echo 'Building explainer'
make -C explainer

if [ -d out ]; then
  mkdir out/wgsl out/explainer

  echo 'Copying spec/index.html spec/webgpu.idl -> out/'
  cp spec/index.html spec/webgpu.idl out/

  echo 'Copying wgsl/index.html -> out/wgsl/'
  cp wgsl/index.html out/wgsl/
  echo '<meta http-equiv="refresh" content="0;url=wgsl/" />' > out/wgsl.html

  echo 'Copying explainer/index.html -> out/explainer/'
  cp explainer/index.html out/explainer/
fi
