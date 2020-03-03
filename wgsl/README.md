# WebGPU Shading Language Specification

## Design Criteria

There are several constraints driving the development of WGSL. The ones related
to the language itself are found in the [Goals](https://gpuweb.github.io/gpuweb//wgsl#goals)
section of the specification. Criteria which guide our development of the language are:

 * The burden for adding constructs to the language is to show why the construct
   is needed, not to show why it should not be added


## Generating the specification

The specification is written using [Bikeshed](https://tabatkins.github.io/bikeshed).

If you have bikeshed installed locally, you can generate the specification with:

```
make
```

This simply runs bikeshed on the `index.bs` file.

Otherwise, you can use the bikeshed Web API:

```
make online
```
