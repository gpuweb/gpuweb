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

**TODO**: Should this be two built-in functions or a single parameterized function?
We could go the route of `subgroup_matrix` and make a templated version of the
built-in function, but we'd have to introduce a new predeclared enum for the
scopes.
It is unclear whether there should be two scope or three (as described in the
spec).
Another alternative could be to wait for the [enums](enums.md) proposal to resolve
and allow enums as function parameters (it would have to be a `@const` parameter).

