SHELL := /bin/bash

.PHONY: all clean diagrams

all: index.html webgpu.idl diagrams

clean:
	rm -f index.html index.pre.html webgpu.idl

# Generate spec HTML from Bikeshed source.
index.pre.html: *.bs sections/*.bs
	DIE_ON=everything bash ../tools/invoke-bikeshed.sh index.pre.html *.bs sections/*.bs

GHC=https://github.com/gpuweb/gpuweb/blob
index.html: index.pre.html
	@echo 'Inserting source permalink: index.pre.html -> index.html'
	@sed -e "s,gpuweb.github.io/gpuweb/</a>,gpuweb.github.io/gpuweb/</a><br><a href=\"$(GHC)/$(shell git rev-parse HEAD)/spec/index.bs\">$(GHC)/$(shell git rev-parse HEAD)/spec/index.bs</a>," <index.pre.html >index.html

# Generate diagrams from source. You can rebuild these without rebuilding the spec.
MERMAID_OUTPUTS := $(patsubst diagrams/%.mmd,img/%.mmd.svg,$(wildcard diagrams/*.mmd))
diagrams: $(MERMAID_OUTPUTS)
img/%.mmd.svg: diagrams/%.mmd ../tools/invoke-mermaid.sh ../tools/mermaid.json
	bash ../tools/invoke-mermaid.sh -i $< -o $@

# Extract webgpu.idl from the spec.
webgpu.idl: index.html ../tools/extract-idl-index.py
	python3 ../tools/extract-idl-index.py index.html > webgpu.idl
