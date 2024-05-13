#!/bin/bash
# This is called from the repository root. Populates out/ with everything to
# publish on GitHub Pages and PR previews.
set -euo pipefail

mkdir -p out/{wgsl,wgsl/grammar,explainer,correspondence,operations}

cp -r spec/{index.html,webgpu.idl,img} out/
cp spec/webgpu.idl out/webgpu.idl.txt

cp -r wgsl/{index.html,wgsl.lalr.txt,img} out/wgsl/
cp wgsl/grammar/grammar.js out/wgsl/grammar/

cp explainer/index.html out/explainer/
cp -r explainer/img/ out/explainer/

cp correspondence/index.html out/correspondence/

cp operations/index.html out/operations/

# Redirect wgsl.html to wgsl/
echo '<meta http-equiv="refresh" content="0;url=wgsl/" />' > out/wgsl.html
