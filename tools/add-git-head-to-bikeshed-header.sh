#!/bin/bash
# Append another line to the "This version:" metadata at the top.

if [ $# -ne 1 ] ; then
    echo "Usage: $0 index.pre.html > index.html"
    exit 1
fi

ghc="https://github.com/gpuweb/gpuweb/blob"
head=$(git rev-parse HEAD)
sed -e "s,gpuweb.github.io/gpuweb/</a>,gpuweb.github.io/gpuweb/</a><br><a href=\"$ghc/$head/spec/index.bs\">$ghc/$head/spec/index.bs</a>," "$1"
