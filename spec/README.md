# WebGPU Specification

## Dependencies

The specification is written using [Bikeshed](https://tabatkins.github.io/bikeshed)
with diagrams generated using [Mermaid](https://mermaid-js.github.io/mermaid/).

To install the necessary tools, run:

```bash
./tools/install-dependencies.sh bikeshed diagrams wgsl
```

Alternatively, invoke `pip3`/`npx` directly, using the commands in [that script](../tools/install-dependencies.sh).

## Building this spec

If Bikeshed is not installed locally, the Bikeshed API will be used to generate the specification
(this is generally slower).

To generate the specification and `webgpu.idl`, type:

```bash
make
```

When the specification is generated, it is written to `index.html`.
