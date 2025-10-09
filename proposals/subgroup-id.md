# Subgroup ID


* Status: **Draft**
* Last modified: 2025-10-02
* Issue: [#5365](https://github.com/gpuweb/gpuweb/issues/5365)

# Overview

This proposal intends to add a new built-in value: `subgroup_id`.
`subgroup_id` represents the value of the invocation's subgroup's id within the
workgroup.
This built-in value was originally omitted from the subgroups feature because
it was not available on D3D12 implementations.
It is currently planned to be added to [HLSL](https://github.com/microsoft/hlsl-specs/issues/645).

# Built-in Value

| Built-in | Stage | Type | Direction | Description |
| -------- | ----- | ---- | --------- | ----------- |
| `subgroup_id` | compute | u32 | Input | The invocation's subgroup's id within the workgroup |

Ideally this built-in would be considered subgroup uniform, but our uniformity
analysis occurs at the workgroup level.

**TODO**: Do we want to try and introduce subgroup uniformity?
APIs speak little of the guarantees and testing shows that guarantees do not
match user expectations.

# Language vs Enable Extension

There are two options to expose the built-in: as language extension or as an
enable extension.

**TODO**: Decide on the type of extension.

## Language Extension

In this option the built-in is exposed as a language extension under the
`subgroups` enable extension.
It is worth noting, this would be the first language extension to an
enable extension.
Both Vulkan and Metal expose this built-in natively (as `SubgroupId` in SPIR-V
and `simdgroup_index_in_threadgroup` in MSL).
D3D12 does not currently expose this built-in so, instead, implementations
would be expected to polyfill it.

Example HLSL polyfill:
```
groupshared uint subgroup_id_gen;

[numthreads(32, 1, 1)]
void main() {
  uint sid = 0;
  if (WaveIsFirstLane()) {
    InterlockedAdd(subgroup_id_gen, 1, sid);
  }
  sid = WaveReadLaneFirst(sid);

  // sid is used as subgroup_id from here in the shader
}

```

This is the simplest polyfill, though there are potentially multiple strategies
to polyfill.
The downsides to a polyfill are that:
1. It is unlikely to generate the equivalent values to what the hardware would
   natively generate.
2. It uses a groupshared variable and likely eats into the groupshared memory
   budget.

## Enable Extension

In this option, the built-in value is exposed under a new enable extension
`subgroup_id`.
This option would rely on the native implementations to provide the value.
This means implementations would not expose the value in D3D12 implementations
until it is available in a future shader model.

The downside to an enable extension is that the built-in would not be available
on all platforms for some time.

