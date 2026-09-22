# Assert Uniform

* Status: [Draft](README.md#status-draft)
* Created: 2026-09-21
* Issue: [#6955](https://github.com/gpuweb/gpuweb/issues/6955)

## Overview

A WGSL language feature that adds a new built-in function: `assertUniform`.
The input to the built-in function must be uniform.
It allows users to statically check whether some code is interpreted as uniform
by the implementation.
There can be performance impacts when accessing resources using a non-uniform
index with [bindless](bindless.md).

## WGSL

### Language Extension

| Name | Description |
| ---- | ----------- |
| `assert_uniform` | Allows the use of the `assertUniform` built-in function. |

### `assertUniform` Built-in Function

```wgsl
@const fn assertUniform(x : E) -> E
```

Returns `x`.

Note: Would be considered a bit-preserving function for floating-point purposes
(i.e. no flushing denorms), but no implementation would have to generate
backend code for it.

Triggers a uniformity diagnostic if the uniformity analysis cannot prove that
`x` is a uniform value.
Triggers a uniformity diagnostic if the uniformity analysis cannot prove the
call is in uniform control flow.
The uniformity scope is workgroup/draw call.

The passthrough semantics of the function allow users to test the uniformity
within a larger expression seamlessly.

The function is not annotated with `@must_use` so that is can be easily used as
a function call statement.

Examples:
```wgsl
// A shader author can annotate the exact location they wish to assert
// uniformity without a separate statement.
let res = getResource<texture_2d<f32>>(assertUniform(index));

// Possible, but unnecessary.
assertUniform(index);
let res2 = getResource<texture_2d<f32>>(index);

// Here, the uniformity of the control depends on the uniformity of a, it would
// not be equivalent to move the assertion to its own statement without
// incorporating a.
let cond = a || assertUniform(dpdx(b)).x > threshold;

// Equivalent alternative:
assertUniform(a && b);
let cond2 = a || dpdx(b).x > threshold;
```

### `assertSubgroupUniform` Built-in Function

```wgsl
@const fn assertSubgroupUniform(x : E) -> E
```

The same as `assertUniform` except that the scope is of uniformity is subgroup.

Requires that the `subgroup_uniformity` language feature is supported.

## Issues

1. Should the proposal include attributes to facilitate library writers?

Attributes (e.g. `@uniform`) could be added to be allowed in limited locations:
* Function declarations: must be called from uniform control flow
* Function parameters: value must be uniform
* Function return values: return value is uniform

The first two represent a contract about calling the function.
The attribute on the return declaration is a simplification if the function has multiple return statements.

2. How should uniformity scope be handled?

Currently the scope is included in the name.
It could also be encoded as a template parameter similar to subgroup matrix
load/store, but would require a new pre-declared enum.
It is not clear what the values of that enum would be since the larger
uniformity scope depends on the surrounding entry point context.
It could also be an enum parameter (const requirement) if this depended on the
[enums](enums.md) proposal, but that sort of goes against the decision made for
subgroup matrix.

If the attributes are added, templating would make sense for them.
So either as part of the name (`@uniform` for full uniformity or
`@subgroup_uniform` for subgroup uniformity) or as an optional parameter (e.g.
`@uniform or `@uniform(subgroup)`).

3. Should control and value semantics be separated in the built-in functions?

For use with [bindless](bindless.md) there is potential value is not requiring
both uniform control flow and uniform values.
Should we introduce a parameter-less version for control flow only?
Should the parameter version only imply uniform value?
Or, should there be a `assertUniformValue` variant for just the value?

