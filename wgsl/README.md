# WebGPU Shading Language Specification

**For general instructions on building, see [CONTRIBUTING.md](../CONTRIBUTING.md).**

## Dependencies

The following tools are used:
* For building the specification HTML from source: [Bikeshed](https://tabatkins.github.io/bikeshed)
  * If Bikeshed is not installed locally, the Bikeshed web API will be used to generate the specification.
      This is generally slower, and requires a connection to the internet.
* For building diagrams from source: [Mermaid](https://mermaid-js.github.io/mermaid/)
  * The generated files are checked in. If Mermaid is not installed, regeneration will be skipped.
* For validating the grammar and code samples:
  * [Python 3](https://www.python.org)
  * [Tree-sitter](https://tree-sitter.github.io/tree-sitter)
  * [py-tree-sitter](https://github.com/tree-sitter/py-tree-sitter)
  * [npm](https://www.npmjs.com/)
  * [node.js](https://nodejs.org/)
  * A C/C++ compiler

To install the necessary tools, run:

```bash
./tools/install-dependencies.sh bikeshed diagrams wgsl
```

Alternatively, invoke `pip3`/`npx` directly, using the commands in [that script](../tools/install-dependencies.sh).

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
grammar, and then ensures that code samples from the specification can be parsed correctly.

### Validating the grammar is LALR(1)

```bash
make lalr
```

This produces an LALR(1) parse table for the WGSL grammar in an ad-hoc textual format.
It will fail if it finds a conflict.

Tree-sitter's JSON representation of the WGSL grammar is used as an input to this step,
so this step will execute the Tree-sitter step if required.
