# 64 Bit atomics

Status: **Draft**

Last modified: 2025-03-10

Issue: [#5071](https://github.com/gpuweb/gpuweb/issues/5071)

**The 64 bit question**:
The WGSL spec does not have a 64 bit integer type and there are no near term plans to do support it. If we want to support 64 bit atomic operations we must use a surrogate type.

The alignment and size  of vec2u (vec2<u32>) is specified (https://www.w3.org/TR/WGSL/#alignment-and-size) as 8 bytes. This allows us to use the vec2< u32 > as a composite type for the unsigned 64 bit integer. 

Since all atomic operations in WGSL [operate only on atomic types](https://www.w3.org/TR/WGSL/#atomic-types) the declaration Atomic< vec2u > will actually map to a u64 in all backends.

*msl
Typed resources used in 64-bit integer operations must be declared with HLSL type int64_t or uint64_t and have format R32G32_UINT.


# Requirements

**Vulkan**:
* VK_KHR_shader_atomic_int64  (device extension) or Vulkan 1.2 with support bits.
* [VK_KHR_shader_atomic_int64](https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VK_KHR_shader_atomic_int64.html)
* [Spirv Enviroment for 64 bit integers ](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#spirvenv-capabilities-table-Int64Atomics)

According to [this query](https://vulkan.gpuinfo.org/listfeaturescore12.php),
The 1.2 feature "shaderBufferInt64Atomics" has 87.7% support on Linux and 31% support on Android.
As an extension  [this query](https://vulkan.gpuinfo.org/displayextensiondetail.php?extension=VK_KHR_shader_atomic_int64),
has 69% support on Linux but only 4.66% support on android.


"The supported operations include OpAtomicMin, OpAtomicMax, OpAtomicAnd, OpAtomicOr, OpAtomicXor, OpAtomicAdd, OpAtomicExchange, and OpAtomicCompareExchange." on signed/unsigned integer


**Metal**:
* Metal 2.4 for all OS

According to the Metal
[feature table](https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf), this
includes the following families: Apple 9

https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf p251

We only get min/max but min/max is useful if one is doing software (compute) GPU rendering.
See the [requirement for atomic 64 bit support](https://jms55.github.io/posts/2024-11-14-virtual-geometry-bevy-0-15/#hardware-rasterization-and-atomicmax) for software rendering of virtual geometry.


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
| **atomic_64_ops** | Adds functions with broader set of 64 bit atomics |

**NOTE**: The atomic_64_min_max should be limited to storage buffers. 

**NOTE**: The atomic_64_ops should be limited to workgroup and storage buffers.


## Built-in Functions


Functions made availible via **atomic_64_min_max** 

All built-in function can only be used in `compute` or `fragment` shader stages. `T` as uvec2
| Function | Preconditions | Description |
| --- | --- | --- |
| `fn atomicStoreMax(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T)` | | Atomically stores the value v in the atomic object pointed to by atomic_ptr.|
| `fn atomicStoreMin(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T)` | | Atomically stores the value v in the atomic object pointed to by atomic_ptr. |

Functions additional functions made availible via **atomic_64_ops** 

Atomic sub is not available in HLSL. 

All built-in function can only be used in `compute` or `fragment` shader stages. `T` as uvec2
| Function | Preconditions | Description |
| --- | --- | --- |
| `fn atomicLoad(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Returns the atomically loaded the value pointed to by atomic_ptr. It does not modify the object. |
| `fn atomicStore(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically stores the value v in the atomic object pointed to by atomic_ptr. |
| `fn atomicAdd(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs an addition operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicMax(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a maximum operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicMin(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a minimum operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicAnd(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a bitwise AND operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicOr(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a bitwise OR operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |
| `fn atomicXor(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically performs a bitwise XOR operation on the atomic object pointed to by atomic_ptr with the value v, and returns the original value stored in the atomic object before the operation. |


| `fn atomicExchange(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` | | Atomically stores the value v in the atomic object pointed to by atomic_ptr and returns the original value stored in the atomic object before the operation. |
| `fn atomicCompareExchangeWeak(atomic_ptr: ptr<AS, atomic<T>, read_write>, cmp: T, v: T) ->  __atomic_compare_exchange_result<T>` | | Performs a compare and exchange of value v for atomic object pointed to by atomic_ptr if cmp is equal. Returns compare and exchange result. |

### `atomicCompareExchangeWeak` ### {#atomic-compare-exchange-weak}


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
| **atomic_64_min_max** | Allows the WGSL feature|
| **atomic_64_ops** | Allows the WGSL feature |



**TODO**: 

# Appendix A: WGSL Built-in Function Mappings

| Built-in | SPIR-V |  HLSL| MSL|
| --- | --- | --- | --- |
| `atomicStoreMin` | OpAtomicUMin | InterlockedMax | atomic_min_explicit |
| `atomicStoreMax` | OpAtomicUMax | InterlockedMin | atomic_max_explicit |


# Appendix B: WGSL Built-in Function Mappings

| Built-in | SPIR-V | HLSL| MSL |
| --- | --- | --- | --- |
| `atomicLoad` | OpAtomicUMin | InterlockedMax |  NA <sup>1</sup> |
| `atomicStore` | OpAtomicUMax | InterlockedMin |   NA <sup>1</sup> |
| `atomicAdd` | OpAtomicUMin | InterlockedAdd |  NA <sup>1</sup>  |
| `atomicMin` | OpAtomicUMin | InterlockedMin | NA <sup>1</sup>   |
| `atomicMax` | OpAtomicUMax | InterlockedMax |  NA <sup>1</sup>  |
| `atomicAnd` | OpAtomicUAnd | InterlockedMin |   NA <sup>1</sup> |
| `atomicOr` | OpAtomicUOr | InterlockedMax |  NA <sup>1</sup>  |
| `atomicXor` | OpAtomicUXor | InterlockedMax |  NA <sup>1</sup>  |
| `atomicExchange` | OpAtomicUExchange | InterlockedMax |  NA <sup>1</sup>  |
| `atomicCompareExchangeWeak` | OpAtomicUMax | InterlockedMax |  NA <sup>1</sup>  |





1. No known msl function for these extended atomic 64 opts.
