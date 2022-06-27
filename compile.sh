#!/bin/bash
set -e # Exit with nonzero exit code if anything fails

export BIKESHED_DISALLOW_ONLINE=1

echo 'Building spec and webgpu.idl'
make -C spec index.html webgpu.idl
echo 'Building wgsl'
make -C wgsl index.html wgsl.lalr.txt
echo 'Building explainer'
make -C explainer index.html
echo 'Building correspondence'
make -C correspondence index.html

if [ -d out ]; then
  echo 'Populating out/'

  mkdir -p out/wgsl out/explainer out/correspondence out/samples
  cp -r spec/{index.html,webgpu.idl} out/
  cp -r wgsl/{index.html,wgsl.lalr.txt} out/wgsl/
  cp -r explainer/{index.html,img} out/explainer/
  cp -r correspondence/index.html out/correspondence/
  cp -r samples/* out/samples/

  # Redirect wgsl.html to wgsl/
  echo '<meta http-equiv="refresh" content="0;url=wgsl/" />' > out/wgsl.html
fi
