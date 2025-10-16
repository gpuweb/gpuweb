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

Some build steps for the WGSL spec modify the Python environment.
If this is undesirable or not allowed in your situation, then create and use
a [venv](https://docs.python.org/3/library/venv.html) virtual Python environment:

* As a one-time setup step, create a `venv` environment in a subdirectory:

    # Run this from the root directory of the repository. Creates a subdir named `myenv`
    python -m venv myenv

* Then enter the virtual environment before running the WGSL build:

    . myenv/bin/activate
    # Now you can build the WGSL spec in this shell

## Building the specification

When the specification is generated, it is written to `index.html`.

### Generating specification, validating the grammar and code samples (recommended)

```bash
. myenv/bin/activate   # Required only if using a Python virtual environment
make
```

### Generating the specification only

To generate the specification only, run:

```bash
. myenv/bin/activate   # Required only if using a Python virtual environment
make index.html
```

### Validating the code samples can be parsed

```bash
. myenv/bin/activate   # Required only if using a Python virtual environment
make validate-examples
```

This extracts the grammar from the specification source in `index.bs`, creates a Tree-sitter parser from the
grammar, and then ensures that code samples from the specification can be parsed correctly.

### Validating the grammar is LALR(1)

```bash
. myenv/bin/activate   # Required only if using a Python virtual environment
make lalr
```

This produces an LALR(1) parse table for the WGSL grammar in an ad-hoc textual format.
It will fail if it finds a conflict.

Tree-sitter's JSON representation of the WGSL grammar is used as an input to this step,
so this step will execute the Tree-sitter step if required.
