# Subgroup ID

* Status: [Draft](README.md#status-draft)
* Created: 2025-10-01
* Issue: [#5365](https://github.com/gpuweb/gpuweb/issues/5365)

# Overview

This proposal intends to add two new built-in values: `subgroup_id` and `num_subgroups`.
`subgroup_id` represents the value of the invocation's subgroup's id within the
workgroup.
This built-in value was originally omitted from the subgroups feature because
it was not available on D3D12 implementations.
It is currently planned to be added to [HLSL](https://github.com/microsoft/hlsl-specs/issues/645).
`num_subgroups` reports the number of subgroups in the workgroup.

# Built-in Value

| Built-in | Stage | Type | Direction | Description |
| -------- | ----- | ---- | --------- | ----------- |
| `num_subgroups` | compute | u32 | Input | The number of subgroups in this invocation's workgroup. |
| `subgroup_id` | compute | u32 | Input | The invocation's subgroup's id within the workgroup. Values are densely packed in the range [0, `num_subgroups`). |

Ideally these built-ins would be considered subgroup uniform, but our uniformity
analysis occurs at the workgroup level.

**RESOLVED**: Subgroup uniformity will be introduced as a separate language feature.

# Language vs Enable Extension

There are two options to expose the built-ins: as language extension or as an
enable extension.

**RESOLVED**: Language extension

## Language Extension

In this option the built-ins are exposed as a language extension under the
`subgroups` enable extension.
It is worth noting, this would be the first language extension to an
enable extension.
Both Vulkan and Metal expose this built-in natively.
`subgroup_id` is avalable as `SubgroupId` in SPIR-V and `simdgroup_index_in_threadgroup` in MSL.
`num_subgroups` is available as `NumSubgroups` in SPIR-V and `simdgroups_per_threadgroup` in MSL.
D3D12 does not currently expose these built-ins so, instead, implementations
would be expected to polyfill it.

Example HLSL polyfill:
```
groupshared uint subgroup_id_gen;

[numthreads(32, 1, 1)]
void main() {
  // subgroup_id polyfill
  uint sid = 0;
  if (WaveIsFirstLane()) {
    InterlockedAdd(subgroup_id_gen, 1, sid);
  }
  sid = WaveReadLaneFirst(sid);

  // sid is used as subgroup_id from here in the shader

  // num_subgroups polyfill (depends on subgroup_id)
  GroupMemoryBarrierWithGroupSync();
  uint num_sgs = 0;
  if (WaveIsFirstLane()) {
    num_sgs = subgroup_id_gen;
  }
  num_sgs = WaveReadLaneFirst(num_sgs);

  // num_sgs is used as num_subgroups from here in the shader
}

```

This is the simplest polyfill, though there are potentially multiple strategies
to polyfill.
The downsides to a polyfill are that:
1. It is unlikely to generate the equivalent values to what the hardware would
   natively generate.
2. It uses a groupshared variable and likely eats into the groupshared memory
   budget.

