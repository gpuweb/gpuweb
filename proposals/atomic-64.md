# 64 Bit atomics

Status: **Draft**

Last modified: 2025-02-14

Issue: [#4306](https://github.com/gpuweb/gpuweb/issues/5071)

# Requirements

**Vulkan**:
* VK_KHR_shader_atomic_int64  (device extension) or Vulkan 1.2 with support bits.
* (https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VK_KHR_shader_atomic_int64.html)
* (https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#spirvenv-capabilities-table-Int64Atomics)

According to [this query](https://vulkan.gpuinfo.org/listfeaturescore12.php),
The 1.2 feature "shaderBufferInt64Atomics" has 87.7% support on Linux and 31% support on Android.
As an extension  [this query](https://vulkan.gpuinfo.org/displayextensiondetail.php?extension=VK_KHR_shader_atomic_int64),
has 69% support on Linux but only 4.66% support on android.


" The supported operations include OpAtomicMin, OpAtomicMax, OpAtomicAnd, OpAtomicOr, OpAtomicXor, OpAtomicAdd, OpAtomicExchange, and OpAtomicCompareExchange." on signed/unsigned integer


**Metal**:
* Metal 2.4 for all OS

According to the Metal
[feature table](https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf), this
includes the following families: Apple 9

https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf p251

We only get min/max but min/max is useful if you are doing software (compute) GPU rendering.


**D3D12**:
* SM6.6 support (https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_Int64_and_Float_Atomics.html), and
* `D3D12_FEATURE_D3D12_OPTIONS1` supports `Int64ShaderOps`

typedef struct D3D12_FEATURE_DATA_D3D12_OPTIONS9 {
    ...
    BOOL AtomicInt64OnTypedResourceSupported;
    BOOL AtomicInt64OnGroupSharedSupported;
} D3D12_FEATURE_DATA_D3D12_OPTIONS9;


# WGSL

## Enable Extension

Add two new enable extensions.
| Enable | Description |
| --- | --- |
| **atomic_64_min_max** | Adds functions for only min and max ops 64 bit atomics |
| **atomic_64_ops** | Adds functions a broader set of 64 bit atomics |

**TODO**: The atomic_64_min_max should be limited to storage buffers.
**TODO**: Can we include 64 bit atomics for workgroups and probably should for the atomic_64_ops

## Usage


* The alignment and size  of vec2<u32> is specified (https://www.w3.org/TR/WGSL/#alignment-and-size) as 8 bytes. This allows us to use the vec2<u32> as a surragate for the u64.



## Built-in Functions

### `atomicCompareExchangeWeak` ### {#atomic-compare-exchange-weak}

Functions made availible via **atomic_64_min_max** 

All built-in function can only be used in `compute` or `fragment` shader stages. `T` as uvec2
| Function | Preconditions | Description |
| --- | --- | --- |
| `fn atomicStoreMax(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T)` | | Atomically stores the value v in the atomic object pointed to by atomic_ptr.|
| `fn atomicStoreMin(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T)` | | Atomically stores the value v in the atomic object pointed to by atomic_ptr. |

Functions made availible via **atomic_64_ops** 

All built-in function can only be used in `compute` or `fragment` shader stages. `T` as uvec2
| Function | Preconditions | Description |
| --- | --- | --- |
| `fn atomicLoad(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Returns the atomically loaded the value pointed to by atomic_ptr. It does not modify the object. |
| `fn atomicStore(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically stores the value v in the atomic object pointed to by atomic_ptr. |
| `fn atomicAdd(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs an addition operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicSub(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a subtraction operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicMax(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a maximum operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicMin(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a minimum operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicAnd(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a bitwise AND operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicOr(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a bitwise OR operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicXor(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a bitwise XOR operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |


| `fn atomicExchange(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically stores the value v in the atomic object pointed to by atomic_ptr and returns the original value stored in the atomic object before the operation. |
| `fn atomicCompareExchangeWeak(atomic_ptr: ptr<AS, atomic<T>, read_write>, cmp: T, v: T) ->  __atomic_compare_exchange_result<T>` | | Performs a compare and exchange of value v for atomic object pointed to by atomic_ptr if cmp is equal. Returns compare and exchange result. |



```wgsl
fn atomicCompareExchangeWeak(
      atomic_ptr: ptr<AS, atomic<T>, read_write>,
      cmp: T,
      v: T) -> __atomic_compare_exchange_result<T>

struct __atomic_compare_exchange_result<T> {
  old_value : T,   // old value stored in the atomic
  exchanged : bool // true if the exchange was done
}
```

# API

## GPU Feature

New GPU features:
| Feature | Description |
| --- | --- |
| **subgroups** | Allows the WGSL feature and adds new limits |


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


# Appendix B: WGSL Built-in Function Mappings

| Built-in | SPIR-V<sup>1</sup> | HLSL | MSL |
| --- | --- | --- | --- |
| `atomicStoreMin` | OpAtomicSMin | atomic_min_explicit | WaveIsFirstInterlockedMinLane |
| `atomicStoreMax` | OpAtomicSMax | atomic_max_explicit | WaveIsFirstInterlockedMaxLane |



1. All group non-uniform instructions use the `Subgroup` scope.
2. To avoid constant-expression requirement, use SPIR-V 1.5 or OpGroupNonUniformShuffle.
