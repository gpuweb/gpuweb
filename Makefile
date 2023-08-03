# This should be invoked with make -j for full parallelism.
SHELL := /bin/bash

targets := spec wgsl explainer correspondence

.PHONY: all out $(targets) clean

# Build everything
all: $(targets)

# Build everything, and copy it to out/
out: all
	bash ./tools/populate-out.sh

$(targets):
	make -j -C $@

# Clean up all (or at least most) generated files
clean:
	echo $(targets) | xargs -n1 make clean -C
	rm -rf out/
