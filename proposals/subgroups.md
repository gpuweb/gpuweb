# Subgroups

Status: **Draft**

Last modified: 2024-12-12

Issue: [#4306](https://github.com/gpuweb/gpuweb/issues/4306)

Spec PR: [#4963](https://github.com/gpuweb/gpuweb/pulls/4963)

# Requirements

**Vulkan**:
* SPIR-V 1.3, and
* Vulkan 1.1, and
* subgroupSupportedStages includes compute and fragment bit, and
* subgroupSupportedOperations includes the following bits: basic, vote, ballot, shuffle, shuffle relative, arithmetic, quad, and
* Vulkan 1.3 or VK_EXT_subgroup_size_control

According to [this query](https://vulkan.gpuinfo.org/displaycoreproperty.php?core=1.1&name=subgroupSupportedOperations&platform=all),
~84% of devices are captured.
Dropping quad would only grab another ~1%.

**Metal**:
* Quad-scoped permute, and
* Simd-scoped permute, and
* Simd-scoped reduction, and
* Metal 2.1 for macOS or Metal 2.3 for iOS

According to the Metal
[feature table](https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf), this
includes the following families: Metal3, Apple7+, Mac2.


**D3D12**:
* SM6.0 support, and
* `D3D12_FEATURE_DATA_D3D12_OPTIONS1` permits `WaveOps`

# WGSL

## Enable Extension

Add two new enable extensions.
| Enable | Description |
| --- | --- |
| **subgroups** | Adds built-in values and functions for subgroups |
| ~subgroups_f16~ | Allows f16 to be used in subgroups operations |

Note: Metal can always provide subgroups_f16, Vulkan requires
VK_KHR_shader_subgroup_extended_types
([~61%](https://vulkan.gpuinfo.org/listdevicescoverage.php?extension=VK_KHR_shader_subgroup_extended_types&platform=all)
of devices), and D3D12 requires SM6.2.

**TODO**: Can we drop **subgroups_f16**?
According to this [analysis](https://github.com/teoxoy/gpuinfo-vulkan-query/blob/8681e0074ece1b251177865203d18b018e05d67a/subgroups.txt#L1071-L1466)
Only 4% of devices that support both f16 and subgroups could not support
subgroup extended types.
**RESOLVED** at F2F: remove subgroups_f16

**TODO**: Should this feature be broken down further?
According to [gpuinfo.org](https://vulkan.gpuinfo.org/displaycoreproperty.php?core=1.1&name=subgroupSupportedOperations&platform=all),
this feature set captures ~84% of devices.
Splitting the feature does not grab a significant portion of devices.
Splitting out simd-scoped reduction adds the Apple6 family which includes
iPhone11, iPhone SE, and iPad (9th gen).

**TODO**: Should there be additional enables for extra functionality?
Some possibilities:
* MSL and HLSL (SM6.7) support `any` and `all` operations at quad scope
* SPIR-V and HLSL (SM6.5) could support more exclusive/inclusive, clustered, and partitioned operations
* Inclusive sum and product could be done with multi-prefix SM6.5 operations in HLSL or through emulation

## Built-in Values

| Built-in | Type | Direction | Description |
| --- | --- | --- | --- |
| `subgroup_size` | u32 | Input | The size of the current subgroup |
| `subgroup_invocation_id` | u32 | Input | The index of the invocation in the current subgroup |

When used in `compute` shader stage, `subgroup_size` should be considered uniform for uniformity analysis.

Note: HLSL does not expose a subgroup_id or num_subgroups equivalent.

**TODO**: Can subgroup_id and/or num_subgroups be emulated efficiently and portably?

## Built-in Functions

All built-in function can only be used in `compute` or `fragment` shader stages.
Using f16 as a parameter in any of these functions requires `subgroups_f16` to be enabled.

| Function | Preconditions | Description |
| --- | --- | --- |
| `fn subgroupElect() -> bool` | | Returns true if this invocation has the lowest subgroup_invocation_id among active invocations in the subgroup |
| `fn subgroupAll(e : bool) -> bool` | | Returns true if `e` is true for all active invocations in the subgroup |
| `fn subgroupAny(e : bool) -> bool` | | Returns true if `e` is true for any active invocation in the subgroup |
| `fn subgroupBroadcast(e : T, id : I) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types<br>`I` must be i32 or u32 | Broadcasts `e` from the invocation whose subgroup_invocation_id matches `id`, to all active invocations. <br>`id` must be a constant-expression. Use `subgroupShuffle` if you need a non-constant `id`. |
| `fn subgroupBroadcastFirst(e : T) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types | Broadcasts `e` from the active invocation with the lowest subgroup_invocation_id in the subgroup  to all other active invocations |
| `fn subgroupBallot(pred : bool) -> vec4<u32>` | | Returns a set of bitfields where the bit corresponding to subgroup_invocation_id is 1 if `pred` is true for that active invocation and 0 otherwise. |
| `fn subgroupShuffle(v : T, id : I) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types<br>`I` must be u32 or i32 | Returns `v` from the active invocation whose subgroup_invocation_id matches `id` |
| `fn subgroupShuffleXor(v : T, mask : u32) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types | Returns `v` from the active invocation whose subgroup_invocation_id matches `subgroup_invocation_id ^ mask`.<br>`mask` must be dynamically uniform<sup>1</sup> |
| `fn subgroupShuffleUp(v : T, delta : u32) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types | Returns `v` from the active invocation whose subgroup_invocation_id matches `subgroup_invocation_id - delta`<br>`delta` must be dynamically uniform<sup>1</sup> |
| `fn subgroupShuffleDown(v : T, delta : u32) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types | Returns `v` from the active invocation whose subgroup_invocation_id matches `subgroup_invocation_id + delta`<br>`delta` must be dynamically uniform<sup>1</sup> |
| `fn subgroupAdd(e : T) -> T` | `T` must be u32, i32, f32, or a vector of those types | Reduction<br>Adds `e` among all active invocations and returns that result |
| `fn subgroupExclusiveAdd(e : T) -> T)` | `T` must be u32, i32, f32, f16 or a vector of those types | Exclusive scan<br>Returns the sum of `e` for all active invocations with subgroup_invocation_id less than this invocation |
| `fn subgroupInclusiveAdd(e : T) -> T)` | `T` must be u32, i32, f32, f16 or a vector of those types | Inclusive scan<br>Returns the sum of `e` for all active invocations with subgroup_invocation_id less than or equal to this invocation |
| `fn subgroupMul(e : T) -> T` | `T` must be u32, i32, f32, or a vector of those types | Reduction<br>Multiplies `e` among all active invocations and returns that result |
| `fn subgroupExclusiveMul(e : T) -> T)` | `T` must be u32, i32, f32, f16 or a vector of those types | Exclusive scan<br>Returns the product of `e` for all active invocations with subgroup_invocation_id less than this invocation |
| `fn subgroupInclusiveMul(e : T) -> T)` | `T` must be u32, i32, f32, f16 or a vector of those types | Inclusive scan<br>Returns the product of `e` for all active invocations with subgroup_invocation_id less than or equal to this invocation |
| `fn subgroupAnd(e : T) -> T` | `T` must be u32, i32, or a vector of those types | Reduction<br>Performs a bitwise and of `e` among all active invocations and returns that result |
| `fn subgroupOr(e : T) -> T` | `T` must be u32, i32, or a vector of those types | Reduction<br>Performs a bitwise or of `e` among all active invocations and returns that result |
| `fn subgroupXor(e : T) -> T` | `T` must be u32, i32, or a vector of those types | Reduction<br>Performs a bitwise xor of `e` among all active invocations and returns that result |
| `fn subgroupMin(e : T) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types | Reduction<br>Performs a min of `e` among all active invocations and returns that result |
| `fn subgroupMax(e : T) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types | Reduction<br>Performs a max of `e` among all active invocations and returns that result |
| `fn quadBroadcast(e : T, id : I)` | `T` must be u32, i32, f32, f16 or a vector of those types<br>`I` must be u32 or i32 | Broadcasts `e` from the quad invocation with id equal to `id`<br>`id` must be a constant-expression<sup>2</sup> |
| `fn quadSwapX(e : T) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types | Swaps `e` between invocations in the quad in the X direction |
| `fn quadSwapY(e : T) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types | Swaps `e` between invocations in the quad in the Y direction |
| `fn quadSwapDiagonal(e : T) -> T` | `T` must be u32, i32, f32, f16 or a vector of those types | Swaps `e` between invocations in the quad diagnoally |
1. This is the first instance of dynamic uniformity. See the portability and uniformity section for more details.
2. Unlike `subgroupBroadcast`, there is no alternative if the author wants a non-constant `id`: SPIR-V does not have a quad shuffle operation to fall back on.

**TODO**: Are quad operations worth it?
Quad operations present even less portability than subgroup operations due to
factors like helper invocations and multiple draws being packed into a
subgroup.
SM6.7 adds an attribute to require helpers be active.

**TODO**: Can we spec the builtins to improve portability without hurting performance?
E.g. shuffle up or down when delta is clearly out of range.
Need to consider the affect or active vs inactive invocations.

## Portability and Uniformity

Unfortunately,
[testing](https://github.com/gpuweb/gpuweb/issues/4306#issuecomment-1795498468)
indicates that behavior is not widely portable across devices.
Even requiring that the subgroup operations only be used in uniform control
flow (at workgroup scope) is insufficient to produce portable behavior.
For example, compilers make aggressive opimizations that do not preserve the
correct active invocations.
This leaves us in an awkward situation where portability cannot be guaranteed,
but these operations provide significant performance improvements in many
circumstances.

Suggest allowing these operations anywhere and provide guidance on how to
achieve portable behavior.
From testing, it seems all implementations are able to produce portable results
when the workgroup never diverges.
While this may seem obvious, it still provides significant benefit in many
cases (for example, by reducing overall memory bandwidth).

Not requiring any particular uniformity also makes providing these operations
in fragment shaders more palatable.
Normally, there would be extra portability hazards in fragment shaders (e.g.
due to helper invocations).

## Diagnostics

Add new diagnostic controls:

| Filterable Triggering Rule | Default Severity | Triggering Location | Description |
| --- | --- | --- | --- |
| **subgroup_uniformity** | Error | Call site of a subgroup builtin function | A call to a subgroup builtin that the uniformity analysis cannot prove occurs in uniform control flow (or with uniform parameter values in some cases) |
| ~subgroup_branching~ | Error | Call site of a subgroup builtin function | A call to a subgroup builtin that uniformity analysis cannot prove is preceeded only by uniform branches |

**TODO**: Are these defaults appropriate?
They attempt to default to the most portable behavior, but that means it would
be an error to have a subgroup operation preceeded by divergent control flow.

Issue: after internal testing, we found subgroup_branching to be very onerous.
Disabling subgroup_uniformity on a builtin would require also disabling subgroup_branching in
almost all cases.
Additionally, simple, extremely common patterns would be rejected by the diagnostic
(e.g. initializing a workgroup variable with a subset of invocations).

# API

## GPU Feature

New GPU features:
| Feature | Description |
| --- | --- |
| **subgroups** | Allows the WGSL feature and adds new limits |
| ~subgroups-f16~ | Allows WGSL feature. Requires **subgroups** and **shader-f16** |

**TODO**: Can we expose a feature to require a specific subgroup size?
No facility exists in Metal so it would have to be a separate feature.
In SM6.6 HLSL adds a required wave size attribute for shaders.
In Vulkan, pipelines can specify a required size between min and max using
subgroup size control.
This is a requested feature (see #3950).

## Adapter Info

Two new entries in GPUAdapterInfo:
| Limit | Description | Vulkan | Metal | D3D12
| --- | --- | --- | --- | --- |
| subgroupMinSize | Minimum subgroup size | minSubgroupSize from VkPhysicalDeviceSubgroupSizeProperties[EXT] | 4 | WaveLaneCountMin from D3D12_FEATURE_DATA_D3D12_OPTIONS1 |
| subgroupMaxSize | Maximum subgroup size | maxSubgroupSize from VkPhysicalDeviceSubgroupSizeProperties[EXT] | 64 | 128 |

Major requirement is that no shader will be launched where the `subgroup_size`
built-in value is less than `subgroupMinSize` or greater than
`subgroupMaxSize`.

**TODO**: I have been unable to find a more accurate query for Metal subgroup
sizes before pipeline compilation.

**TODO**: More testing is required to verify the reliability of D3D12 WaveLaneCountMin.

**TODO**: We could consider adding a limit for which stages support subgroup
operations for future expansion, but it is not necessary now.

# Pipelines

Note: Vulkan backends should either pass
VkShaderRequiredSubgroupSizeCreateInfoEXT or the ALLOW_VARYING flag to pipeline
creation to ensure the subgroup size built-in value works correctly.

**TODO**: Can we add a pipeline parameter to require full subgroups in compute shaders?
Validate that workgroup size x dimension is a multiple of max subgroup size.
For Vulkan, this would set the FULL_SUBGROUPS pipeline creation bit.
For Metal, this would use threadExecutionWidth.
D3D12 would have to be proven empricially.

# Appendix A: WGSL Built-in Value Mappings

| Built-in | SPIR-V | MSL | HLSL |
| --- | --- | --- | --- |
| `subgroup_size` | SubgroupSize | threads_per_simdgroup | WaveGetLaneCount |
| `subgroup_invocation_id` | SubgroupLocalInvocationId | thread_index_in_simdgroup | WaveGetLaneIndex |

# Appendix B: WGSL Built-in Function Mappings

| Built-in | SPIR-V<sup>1</sup> | MSL | HLSL |
| --- | --- | --- | --- |
| `subgroupElect` | OpGroupNonUniformElect | simd_is_first | WaveIsFirstLane |
| `subgroupAll` | OpGroupNonUniformAll | simd_all | WaveActiveAllTrue |
| `subgroupAny` | OpGroupNonUniformAny | simd_any | WaveActiveAnyTrue |
| `subgroupBroadcast` | OpGroupNonUniformBroadcast<sup>2</sup> | simd_broadcast | WaveReadLaneAt |
| `subgroupBroadcastFirst` | OpGroupNonUniformBroadcastFirst | simd_broadcast_first | WaveReadLaneFirst |
| `subgroupBallot` | OpGroupNonUniformBallot | simd_ballot | WaveActiveBallot |
| `subgroupShuffle` | OpGroupNonUniformShuffle | simd_shuffle | WaveReadLaneAt with non-uniform index |
| `subgroupShuffleXor` | OpGroupNonUniformShuffleXor | simd_shuffle_xor | WaveReadLaneAt with index equal `subgroup_invocation_id ^ mask` |
| `subgroupShuffleUp` | OpGroupNonUniformShuffleUp | simd_shuffle_up | WaveReadLaneAt with index equal `subgroup_invocation_id - delta` |
| `subgroupShuffleDown` | OpGroupNonUniformShuffleDown | simd_shuffle_down | WaveReadLaneAt with index equal `subgroup_invocation_id + delta` |
| `subgroupAdd` | OpGroupNonUniform[IF]Add with Reduce operation | simd_sum | WaveActiveSum |
| `subgroupExclusiveAdd` | OpGroupNonUniform[IF]Add with ExclusiveScan operation | simd_prefix_exclusive_sum | WavePrefixSum |
| `subgroupInclusiveAdd` | OpGroupNonUniform[IF]Add with InclusiveScan operation | simd_prefix_inclusive_sum | WavePrefixSum(x) + x |
| `subgroupMul` | OpGroupNonUniform[IF]Mul with Reduce operation | simd_product | WaveActiveProduct |
| `subgroupExclusiveMul` | OpGroupNonUniform[IF]Add with ExclusiveScan operation | simd_prefix_exclusive_product | WavePrefixProduct |
| `subgroupInclusiveMul` | OpGroupNonUniform[IF]Add with InclusiveScan operation | simd_prefix_inclusive_product | WavePrefixProduct(x) * x |
| `subgroupAnd` | OpGroupNonUniformBitwiseAnd with Reduce operation | simd_and | WaveActiveBitAnd |
| `subgroupOr` | OpGroupNonUniformBitwiseOr with Reduce operation | simd_or | WaveActiveBitOr |
| `subgroupXor` | OpGroupNonUniformBitwiseXor with Reduce operation | simd_xor | WaveActiveBitXor |
| `subgroupMin` | OpGroupNonUniform[SUF]Min with Reduce operation | simd_min | WaveActiveMin |
| `subgroupMax` | OpGroupNonUniform[SUF]Max with Reduce operation | simd_max | WaveActiveMax |
| `quadBroadcast` | OpGroupNonUniformQuadBroadcast | quad_broadcast | QuadReadLaneAt |
| `quadSwapX` | OpGroupNonUniformQuadSwap with Direction=0 | quad_shuffle with `quad_lane_id=thread_index_in_quad_group ^ 1` (xor bits `01`) | QuadReadAcrossX |
| `quadSwapY` | OpGroupNonUniformQuadSwap with Direction=1 | quad_shuffle with `quad_lane_id=thread_index_in_quad_group ^ 2` (xor bits `10`) | QuadReadAcrossY |
| `quadSwapDiagonal` | OpGroupNonUniformQuadSwap with Direction=2 | quad_shuffle with `quad_lane_id=thread_index_in_quad_group ^ 3` (xor bits `11`)  | QuadReadAcrossDiagonal |


1. All group non-uniform instructions use the `Subgroup` scope.
2. To avoid constant-expression requirement, use SPIR-V 1.5 or OpGroupNonUniformShuffle.

# Appendix C: CTS Status

Last updated: 2024-12-18

| Built-in value | Validation | Compute | Fragment |
| --- | --- | --- | --- |
| `subgroup_invocation_id` | &check; | &check; | &check; |
| `subgroup_size` | &check; | &check; | &check; |

| Built-in function | Validation | Compute | Fragment |
| --- | --- | --- | --- |
| `subgroupElect` | &check; | &check; | &check; |
| `subgroupAll` | &check; | &check; | &check; |
| `subgroupAny` | &check; | &check; | &check; |
| `subgroupBroadcast` | &check; | &check; | &check; |
| `subgroupBroadcastFirst` | &check; | &check; | &check; |
| `subgroupBallot` | &check; | &check; | &check; |
| `subgroupShuffle` | &check; | &check; | &check; |
| `subgroupShuffleXor` | &check; | &check; | &check; |
| `subgroupShuffleUp` | &check; | &check; | &check; |
| `subgroupShuffleDown` | &check; | &check; | &check; |
| `subgroupAdd` | &check; | &check; | &check; |
| `subgroupExclusiveAdd` | &check; | &check; | &check; |
| `subgroupInclusiveAdd` | &check; | &check; | &check; |
| `subgroupMul` | &check; | &check; | &check; |
| `subgroupExclusiveMul` | &check; | &check; | &check; |
| `subgroupInclusiveMul` | &check; | &check; | &check; |
| `subgroupAnd` | &check; | &check; | &check; |
| `subgroupOr` | &check; | &check; | &check; |
| `subgroupXor` | &check; | &check; | &check; |
| `subgroupMin` | &check; | &check; | &check; |
| `subgroupMax` | &check; | &check; | &check; |
| `quadBroadcast` | &check; | &check; | &check; |
| `quadSwapX` | &check; | &check; | &check; |
| `quadSwapY` | &check; | &check; | &check; |
| `quadSwapDiagonal` | &check; | &check; | &check; |

| Diagnostic | Validation |
| --- | --- |
| `subgroup_uniformity` | &check; |

| Uniformity analysis | Validation |
| --- | --- |
| `subgroup_size` uniform in compute | &check; |
| Built-in functions require uniformity | &check; |
| Shuffle delta/mask params require uniformity | &check; |
