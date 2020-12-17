#!/bin/bash
set -e # Exit with nonzero exit code if anything fails

make -C spec
make -C wgsl

if [ -d out ]; then
  echo Copy spec/index.html into out/index.html
  cp spec/index.html out/index.html
  echo Copy spec/webgpu.idl into out/webgpu.idl
  cp spec/webgpu.idl out/webgpu.idl
  echo Copy wgsl/index.html into out/wgsl.html
  cp wgsl/index.html out/wgsl.html
fi
