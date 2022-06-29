# WebGPU Shading Language Specification

## Dependencies

The following tools are used:
* For building the specification HTML from source: [Bikeshed](https://tabatkins.github.io/bikeshed)
  * If Bikeshed is not installed locally, the Bikeshed web API will be used to generate the specification.
      This is generally slower, and requires a connection to the internet.
* For validating the grammar and code samples:
  * [Python 3](https://www.python.org)
  * [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
  * [npm](https://www.npmjs.com/)
  * [node.js](https://nodejs.org/)
  * A C/C++ compiler

To install Bikeshed and Tree-sitter, run:

```bash
python3 -m pip install bikeshed==3.7.0 tree_sitter==0.19.0
```

## Building the specification

When the specification is generated, it is written to `index.html`.

### Generating specification, validating the grammar and code samples (recommended)

```bash
make
```

### Generating the specification only

To generate the specification only, run:

```bash
make index.html
```

### Validating the code samples can be parsed

```bash
make validate-examples
```

This extracts the grammar from the specification source in `index.bs`, creates a Tree-sitter parser from the
grammar, and then ensures that code samples from the specification can be parsd correctly.

### Validating the grammar is LALR(1)

```bash
make lalr
```

This produces an LALR(1) parse table for the WGSL grammarin an ad-hoc textual format.
It will fail if it finds a conflict.

Tree-sitter's JSON representation of the WGSL grammar is used as an input to this step,
so this step will execute the Tree-sitter step if required.
