#!/bin/bash
set -e # Exit with nonzero exit code if anything fails

# Compile specs by default, unless told to only copy static files
if [ $1 == 'static' ]; then
  echo 'Extracting IDL from WebGPU spec'
  make -C spec webgpu.idl
else
  echo 'Building spec'
  make -C spec
  echo 'Building wgsl'
  make -C wgsl
  echo 'Building explainer'
  make -C explainer
fi

if [ -d out ]; then
  mkdir -p out/wgsl out/explainer out/samples

  echo 'Copying wgsl/* -> out/wgsl/'
  cp -r wgsl/* out/wgsl/
  rm out/wgsl/{Makefile,*.bs}

  echo 'Copying explainer/* -> out/explainer/'
  cp -r explainer/* out/explainer/
  rm out/explainer/{Makefile,*.bs}

  echo 'Copying spec/* -> out/'
  cp spec/* out/
  rm out/{README.md,Makefile,*.py,*.bs}

  echo 'Copying samples/* -> out/samples/'
  cp samples/* out/samples/

  echo '<meta http-equiv="refresh" content="0;url=wgsl/" />' > out/wgsl.html
fi
