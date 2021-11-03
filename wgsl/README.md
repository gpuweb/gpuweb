# WebGPU Shading Language Specification

## Dependencies

The specification is written using [Bikeshed](https://tabatkins.github.io/bikeshed). \
The WGSL grammar in the specification is validated using [Tree-sitter](https://tree-sitter.github.io/tree-sitter/).

To install both `Bikeshed` and `Tree-sitter`, type:

```bash
python3 -m pip install bikeshed==3.0.3 tree_sitter==0.19.0
```

## Generating both the specification and validating grammar (recommended)

With both `Bikeshed` and `Tree-sitter` locally installed, type:

```bash
make
```

The rendered specification will be written to `index.html`.

## Generating the specification only

With `Bikeshed` locally installed, type:

```bash
make index.html
```

Alternatively, if you do not have `Bikeshed` locally installed, you can use the Bikeshed Web API to generate the specification (slower):

```bash
make online
```

Either approach will write the rendered specification to `index.html`.

## Validating grammar only

With `Tree-sitter` installed, type:

```bash
make grammar/grammar.js
```

