#!/usr/bin/env python3

# Checks if all normative and informative
# WGSL spec sources are NFKC normal
# Note: Filters sources by the working directory,
# any other directory can benefit as well as WGSL

import unicodedata
import subprocess
import sys

files = subprocess.run(
    ["git", "ls-files"], check=True, capture_output=True
).stdout.splitlines()

fix = "--fix" in [unicodedata.normalize("NFKC", i) for i in sys.argv]

for file in files:
    contents = open(file).read()
    normalized = unicodedata.normalize("NFKC", contents)
    if contents != normalized:
        if fix:
            open(file, "w").write(normalized)
        else:
            raise SystemExit("Error: Source files are not NFKC normalized.")
