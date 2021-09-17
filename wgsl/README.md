# WebGPU Shading Language Specification

## Dependencies

The specification is written using [Bikeshed](https://tabatkins.github.io/bikeshed).
The WGSL grammar in the specification is validated using [Tree-sitter](https://tree-sitter.github.io/tree-sitter/).

To install both Bikeshed and Tree-sitter, run:

```bash
python3 -m pip install bikeshed==3.7.0 tree_sitter==0.19.0
```

## Building this spec

If Bikeshed is not installed locally, the Bikeshed API will be used to generate the specification
(this is generally slower).

When the specification is generated, it is written to `index.html`.

### Generating both the specification and validating grammar (recommended)

With Tree-sitter locally installed, type:

```bash
make
```

### Generating the specification only

To generate the specification only, type:

```bash
make index.html
```

### Validating grammar only

With Tree-sitter locally installed, type:

```bash
make grammar/grammar.js
```

## Checking that WGSL code samples parse correctly

To check that the WGSL source code samples in the specification parse correctly, run:

```
make grammar/grammar.js
```

This uses:
* [node.js](https://nodejs.org/)
* [npm](https://www.npmjs.com/)
* [Python 3](https://www.python.org/)
* The [tree-sitter](https://github.com/tree-sitter/tree-sitter) Python module: `pip3 install tree-sitter`
* A C/C++ compiler

## Building and checking everything

To generate the specification and check the examples, run:

```
make
```

