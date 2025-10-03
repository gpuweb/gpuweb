SHELL := /bin/bash

.PHONY: all clean nfkc validate lalr validate-examples

all: index.html nfkc validate test diagrams
validate: lalr tspath_tests unit_tests validate-examples

clean:
	rm -f index.html index.bs.pre index.pre.html wgsl.recursive.bs.include.pre grammar/grammar.js grammar/grammar.js.pre wgsl.lalr.txt
	rm -rf grammar/build


# Generate spec HTML from Bikeshed source.
WGSL_SOURCES:=index.bs ./grammar/src/scanner.c wgsl.recursive.bs.include wgsl.reserved.bs.include $(wildcard syntax/*.syntax.bs.include) $(wildcard img/*.svg)
index.pre.html: $(WGSL_SOURCES)
	DIE_ON=everything bash ../tools/invoke-bikeshed.sh $@ $(WGSL_SOURCES)

wgsl.reserved.bs.include: Makefile tools/generate-reserved-words.py
	python3 tools/generate-reserved-words.py >$@
wgsl.reserved.plain: Makefile tools/generate-reserved-words.py
	python3 tools/generate-reserved-words.py --plain >$@

GHC=https://github.com/gpuweb/gpuweb/blob
index.html: index.pre.html nfkc
	@echo 'Inserting source permalink: index.pre.html -> index.html'
	@sed -e "s,gpuweb/wgsl/</a>,gpuweb/wgsl/</a><br><a href=\"$(GHC)/$(shell git rev-parse HEAD)/wgsl/index.bs\">$(GHC)/$(shell git rev-parse HEAD)/wgsl/index.bs</a>," <index.pre.html >index.html

# Generate diagrams from source. You can rebuild these without rebuilding the spec.
MERMAID_OUTPUTS := $(patsubst diagrams/%.mmd,img/%.mmd.svg,$(wildcard diagrams/*.mmd))
diagrams: $(MERMAID_OUTPUTS)
img/%.mmd.svg: diagrams/%.mmd ../tools/invoke-mermaid.sh ../tools/mermaid.json
	bash ../tools/invoke-mermaid.sh -i $< -o $@

TREESITTER_GRAMMAR_INPUT := grammar/grammar.js

# A file used to signal the WGSL parser was successfully installed.
TREESITTER_PARSER_STAMP := grammar/build.stamp

# Extract WGSL grammar from the spec
$(TREESITTER_GRAMMAR_INPUT): index.bs ./grammar/src/scanner.c ./tools/extract-grammar.py wgsl.reserved.plain
	bash -c ' \
	  if [ -f ../tools/custom-action/dependency-versions.sh ]; then \
	    source ../tools/custom-action/dependency-versions.sh; \
	  else \
	    source /dependency-versions.sh; \
	  fi && \
	  python3 ./tools/extract-grammar.py --flow x'

# Build a Treesitter parser to validate grammar extract and later examples in spec
$(TREESITTER_PARSER_STAMP): $(TREESITTER_GRAMMAR_INPUT)
	source ../tools/custom-action/dependency-versions.sh && python3 ./tools/extract-grammar.py --spec index.bs --scanner ./grammar/src/scanner.c --tree-sitter-dir grammar --flow b

.PHONY: validate-examples
# Use Treesitter to parse many code examples in the spec.
validate-examples: $(TREESITTER_PARSER_STAMP)
	source ../tools/custom-action/dependency-versions.sh && python3 ./tools/extract-grammar.py --flow e

.PHONY: tspath_tests
tspath_tests: ./tools/TSPath.py
	python3 ./tools/TSPath.py

.PHONY: unit_tests
# Use Treesitter to parse code samples
unit_tests: $(TREESITTER_PARSER_STAMP) ./tools/wgsl_unit_tests.py
	python3 ./tools/wgsl_unit_tests.py

# The grammar in JSON form, emitted by Treesitter.
WGSL_GRAMMAR=grammar/src/grammar.json
$(WGSL_GRAMMAR) : $(TREESITTER_PARSER_STAMP)

.PHONY: nfkc
nfkc:
	python3 ../tools/check-nfkc.py

#### Grammar analyzer materials below here.
#### You probably only want 'make validate'

.PHONY: test
test: analyze_test

# The grammar anlyzer consumes the Treesitter JSON representation of the grammar.
# So Treesitter has to succeed first.
ANALYZE_SCRIPT=./tools/analyze/lalr.py
ANALYZER=$(ANALYZE_SCRIPT) ./tools/analyze/Grammar.py ./tools/analyze/ObjectRegistry.py

# Compute and print LALR(1) parse table for the WGSL grammar
.PHONY: lalr
lalr: wgsl.lalr.txt

# Print a simple (uncanonicalized form) of the grammar
.PHONY: simple
simple: wgsl.simple.txt

# A human-readable LALR(1) parse table, in an ad hoc format.
wgsl.lalr.txt : $(ANALYZER) $(WGSL_GRAMMAR)
	python3 $(ANALYZE_SCRIPT) -lalr grammar/src/grammar.json >$@

wgsl.simple.txt : $(ANALYZER) $(WGSL_GRAMMAR)
	python3 $(ANALYZE_SCRIPT) -simple grammar/src/grammar.json >$@

# Print a simple (uncanonicalized form) of the grammar
.PHONY: recursive
recursive : $(ANALYZER) $(WGSL_GRAMMAR)
	@python3 $(ANALYZE_SCRIPT) -recursive grammar/src/grammar.json
.PHONY: recursive_bs
recursive_bs : $(ANALYZER) $(WGSL_GRAMMAR)
	@python3 $(ANALYZE_SCRIPT) -recursive -bs grammar/src/grammar.json

wgsl.recursive.bs.include : $(ANALYZER) $(WGSL_GRAMMAR)
	python3 $(ANALYZE_SCRIPT) -recursive -bs grammar/src/grammar.json >$@.pre
	bash ../tools/copy-if-different.sh $@.pre $@

# Print a simple (uncanonicalized form) of the grammar and check LL(1)
.PHONY: recursive_ll
recursive_ll : $(ANALYZER) $(WGSL_GRAMMAR)
	@python3 $(ANALYZE_SCRIPT) -recursive -ll grammar/src/grammar.json

## The following targets are used when developing the grammar analyzer


# Unit tests for the grammar analyzer.
# These are by no means exhaustive!
.PHONY: analyze_test
analyze_test: $(ANALYZER)
	python3 ./tools/analyze/test.py 2>&1

# Profile LALR analysis
.PHONY: profile
profile wgsl.lalr.profile : $(ANALYZER) $(WGSL_GRAMMAR)
	python3 -m cProfile -o wgsl.lalr.profile $(ANALYZE_SCRIPT) -lalr grammar/src/grammar.json

# Compute LR(1) item sets
.PHONY: lr
lr: $(ANALYZER) $(WGSL_GRAMMAR)
	python3 $(ANALYZE_SCRIPT) -lr grammar/src/grammar.json

# Compute LL(1) parse table
.PHONY: ll
ll: $(ANALYZER) $(WGSL_GRAMMAR)
	python3 $(ANALYZE_SCRIPT) -ll grammar/src/grammar.json


# Produce LALR(1) parse tables for small sample languages

.PHONY: lalr_simple
lalr_simple: $(ANALYZER) analyze/test/firsts.json
	python3 $(ANALYZE_SCRIPT) -lalr analyze/test/firsts.json

.PHONY: lalr_star
lalr_star: $(ANALYZER) analyze/test/star.json
	python3 $(ANALYZE_SCRIPT) -lalr analyze/test/star.json

# Example 4.42 from the Dragon book, i.e.
# Compilers: Principles, Techniques, and Tools.
# Aho, Sethi, Ullman, 1986, reprint with corrections 1988
.PHONY: lalr_442
lalr_442: $(ANALYZER) analyze/test/ex442.json
	python3 $(ANALYZE_SCRIPT) -lalr analyze/test/ex442.json
