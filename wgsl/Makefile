.PHONY: all clean validate lalr validate-examples

all: index.html validate test
validate: lalr validate-examples
validate-examples: grammar/grammar.js

clean:
	rm -f index.html index.pre.html grammar/grammar.js wgsl.lalr.txt

# Generate spec HTML from Bikeshed source.
index.pre.html: index.bs
	DIE_ON=everything bash ../tools/invoke-bikeshed.sh index.pre.html index.bs

index.html: index.pre.html
	bash ../tools/add-git-head-to-bikeshed-header.sh index.pre.html > index.html

# Extract WGSL grammar from the spec, validate it with Treesitter,
# and use Treesitter to parse many code examples in the spec.
grammar/grammar.js: index.bs extract-grammar.py
	python3 ./extract-grammar.py index.bs grammar/grammar.js

# The grammar in JSON form, emitted by Treesitter.
WGSL_GRAMMAR=grammar/src/grammar.json
$(WGSL_GRAMMAR) : grammar/grammar.js


#### Grammar analyzer materials below here.
#### You probably only want 'make validate'

.PHONY: test
test: analyze_test

# The grammar anlyzer consumes the Treesitter JSON representation of the grammar.
# So Treesitter has to succeed first.
ANALYZE_SCRIPT=analyze/lalr.py
ANALYZER=$(ANALYZE_SCRIPT) analyze/Grammar.py analyze/ObjectRegistry.py

# Compute and print LALR(1) parse table for the WGSL grammar
.PHONY: lalr
lalr: wgsl.lalr.txt


# A human-readable LALR(1) parse table, in an ad hoc format.
wgsl.lalr.txt : $(ANALYZER) $(WGSL_GRAMMAR)
	python3 $(ANALYZE_SCRIPT) -lalr grammar/src/grammar.json >$@


## The following targets are used when developing the grammar analyzer


# Unit tests for the grammar analyzer.
# These are by no means exhaustive!
.PHONY: analyze_test
analyze_test: $(ANALYZER)
	python3 analyze/test.py 2>&1

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

