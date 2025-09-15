# 64 Bit atomics (storage buffers)

Status: **Draft**

Last modified: 2025-09-15

Issue: [#5071](https://github.com/gpuweb/gpuweb/issues/5071)

## The 64 bit question

The WGSL spec does not have a 64 bit integer type and there are no near term plans to do support it. If we want to support 64 bit atomic operations we must use a surrogate type.

The alignment and size of `vec2u` (`vec2<u32>`) is specified as 8 bytes. This allows us to use the `vec2<u32>` as a composite type for the unsigned 64 bit integer. See the [WGSL specification on alignment and size](https://www.w3.org/TR/WGSL/#alignment-and-size).

Since all atomic operations in WGSL [operate only on atomic types](https://www.w3.org/TR/WGSL/#atomic-types) the declaration `Atomic<vec2u>` will actually map to a `u64` in all backends.

# Requirements

## Vulkan

*   `VK_KHR_shader_atomic_int64` (device extension) or Vulkan 1.2 with support bits.
*   [VK_KHR_shader_atomic_int64](https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VK_KHR_shader_atomic_int64.html)
*   [Spirv Enviroment for 64 bit integers](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#spirvenv-capabilities-table-Int64Atomics)

According to [this query](https://vulkan.gpuinfo.org/listfeaturescore12.php), the 1.2 feature `"shaderBufferInt64Atomics"` has 87.7% support on Linux and 31% support on Android. As an extension, [this query](https://vulkan.gpuinfo.org/displayextensiondetail.php?extension=VK_KHR_shader_atomic_int64) has 69% support on Linux but only 4.66% support on android.

> "The supported operations include `OpAtomicMin`, `OpAtomicMax`, `OpAtomicAnd`, `OpAtomicOr`, `OpAtomicXor`, `OpAtomicAdd`, `OpAtomicExchange`, and `OpAtomicCompareExchange`." on signed/unsigned integer

## Metal

*   Metal 2.4 for all OSx

Metal is very restrictive on support for atomic 64. It restricts all operations to simply `max`/`min` of the c++ `uint64_t`. For a complete summary see 6.15.4.6 Atomic Modify Functions (64 Bits).

According to the Metal [feature table](https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf), this includes the following families: Apple 9

See page 251 of the [Metal Shading Language Specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf).

While we only get `min`/`max` but `min`/`max` is useful if one is doing software (compute) GPU rendering. See the [requirement for atomic 64 bit support](https://jms55.github.io/posts/2024-11-14-virtual-geometry-bevy-0-15/#hardware-rasterization-and-atomicmax) for software rendering of virtual geometry.

## D3D12

*   SM6.6 support ([HLSL SM 6.6 Int64 and Float Atomics](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_Int64_and_Float_Atomics.html)), and
*   `D3D12_FEATURE_D3D12_OPTIONS1` supports `Int64ShaderOps`

```c
typedef struct D3D12_FEATURE_DATA_D3D12_OPTIONS9 {
    ...
    BOOL AtomicInt64OnTypedResourceSupported;
    BOOL AtomicInt64OnGroupSharedSupported;
} D3D12_FEATURE_DATA_D3D12_OPTIONS9;
```
Atomic sub is not available in HLSL.

> Typed resources used in 64-bit integer operations must be declared with HLSL type `int64_t` or `uint64_t` and have format `R32G32_UINT`.

# WGSL

## Enable Extension

Add a single new enable extension:

| Enable                  | Description                                          |
| ----------------------- | ---------------------------------------------------- |
| `atomic_64_min_max`     | Adds functions for only min and max ops 64 bit atomics |

> **NOTE**: The `atomic_64_min_max` should be limited to storage buffers. This does not include textures/images.

## Built-in Functions

### Functions made availible via `atomic_64_min_max`

All built-in function can only be used in `compute` or `fragment` shader stages. `T` as `uvec2`.

| Function                                                          | Preconditions | Description                                                              |
| ----------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------ |
| `fn atomicStoreMax(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T)` |               | Atomically stores the value v in the atomic object pointed to by atomic_ptr. |
| `fn atomicStoreMin(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T)` |               | Atomically stores the value v in the atomic object pointed to by atomic_ptr. |

### Functions additional functions made availible via `atomic_64_ops`



All built-in function can only be used in `compute` or `fragment` shader stages. `T` as `uvec2`.

| Function                                                          | Preconditions | Description                                                                      |
| ----------------------------------------------------------------- | ------------- | -------------------------------------------------------------------------------- |
| `fn atomicLoad(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` |               | Returns the atomically loaded the value pointed to by atomic_ptr. It does not modify the object. |
| `fn atomicStore(atomic_ptr: ptr<AS, atomic<T>, read_write>, v: T) -> T` |               | Atomically stores the value v in the atomic object pointed to by atomic_ptr.     |

# API

## GPU Feature

New GPU features:

| Feature             | Description                                                          |
| ------------------- | -------------------------------------------------------------------- |
| `atomic_64_min_max` | Allows the WGSL feature predicated on support for these 64 bit operations |

# Appendix

## Appendix A: WGSL Built-in Function Mappings

| Built-in         | SPIR-V         | HLSL           | MSL                 |
| ---------------- | -------------- | -------------- | ------------------- |
| `atomicStoreMin` | `OpAtomicUMin` | `InterlockedMax` | `atomic_min_explicit` |
| `atomicStoreMax` | `OpAtomicUMax` | `InterlockedMin` | `atomic_max_explicit` |

