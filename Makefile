# This should be invoked with make -j for full parallelism.
SHELL := /bin/bash

# TODO: Include wgsl as a target once dependencies respect wgsl.so creation
# and until then, execute make without -j
targets := spec explainer correspondence operations

.PHONY: all out $(targets) wgsl clean

# Build everything
all: $(targets) wgsl

# Build everything, and copy it to out/
out: all
	bash ./tools/populate-out.sh

$(targets):
	make -j -C $@

wgsl:
	make -C wgsl

# Clean up all (or at least most) generated files
clean:
	echo $(targets) | xargs -n1 make clean -C
	rm -rf out/
