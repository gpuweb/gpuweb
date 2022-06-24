#!/bin/bash
# This is called from the repository root. Populates out/ with everything to
# publish on GitHub Pages and PR previews.
set -e

mkdir -p out/{wgsl,explainer,correspondence,samples}
cp -r spec/{index.html,webgpu.idl} out/
cp -r wgsl/{index.html,wgsl.lalr.txt} out/wgsl/
cp -r explainer/{index.html,img/} out/explainer/
cp -r correspondence/index.html out/correspondence/
cp -r samples/* out/samples/

# Redirect wgsl.html to wgsl/
echo '<meta http-equiv="refresh" content="0;url=wgsl/" />' > out/wgsl.html
