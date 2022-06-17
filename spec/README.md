# WebGPU Specification

## Dependencies

The specification is written using [Bikeshed](https://tabatkins.github.io/bikeshed).

To install Bikeshed, type:

```bash
python3 -m pip install bikeshed==3.7.0
```

## Building this spec

If Bikeshed is not installed locally, the Bikeshed API will be used to generate the specification
(this is generally slower).

To generate the specification and `webgpu.idl`, type:

```bash
make
```

When the specification is generated, it is written to `index.html`.
