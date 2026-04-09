# Subgroup Size Control

* Status: [Draft](README.md#status-draft)
* Created: 2026-01-28
* Issue: [#5545](https://github.com/gpuweb/gpuweb/issues/5545)

# Motivation

Current WebGPU specification doesn't provide a way to manually specify the subgroup size when creating a compute pipeline. We can only query the actual subgroup size in the WGSL shader through the built-in variable `subgroup_size`. Then when targeting the platforms that support multiple subgroup sizes, we have to prepare multiple code paths for all the possible subgroup sizes for the correctness of the computation, which may cause below issues:
1. It's difficult to test against every the possible subgroup sizes on such platforms because the actual subgroup size in use is not in our control.
2. The subgroup size chosen by the GPU driver may not always be the best one when handling different shader inputs.
3. Many parameters inside the compute shader (for example, workgroup sizes and array sizes in workgroup memory) can only follow the requirements of the largest possible subgroup size, which may not be the best ones for the smaller subgroup sizes.

The WebGPU feature `subgroup-size-control` introduces the ability to use the attribute `subgroup_size` in compute shaders in WGSL.
When the attribute `subgroup_size` is declared, the compute pipeline will only be executed with the specified subgroup size, and the built-in value `subgroup_size` will always be the the value of the attribute `subgroup_size`.

# Status
This feature has not been approved by the working group yet.

# Native API Availability
1. The WGSL attribute `subgroup_size`

| Platform | Implementation | Note |
|----------|------|-------|
| SPIR-V | `requiredSubgroupSize` in `VkPipelineShaderStageRequiredSubgroupSizeCreateInfo` on the API side | [`VK_EXT_subgroup_size_control`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_subgroup_size_control.html) or Vulkan 1.3 <br> `VkPhysicalDeviceSubgroupSizeControlFeatures.subgroupSizeControl` = `VK_TRUE`<br>`VkPhysicalDeviceSubgroupSizeControlFeatures.computeFullSubgroups` = `VK_TRUE` |
| HLSL | HLSL attribute [`[WaveSize()]`](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_WaveSize.html) | `Shader Model 6.6` |
| Metal | Not Supported | According to [Metal document](https://developer.apple.com/documentation/apple-silicon/porting-your-metal-code-to-apple-silicon#Determine-the-SIMD-Group-Size-at-Runtime): <br>"The size of a SIMD group varies between different GPUs, particularly Mac GPUs. Don't assume the size of SIMD groups." |


Note that
* On Vulkan we need `computeFullSubgroups == VK_TRUE` because we should set `VK_PIPELINE_SHADER_STAGE_CREATE_REQUIRE_FULL_SUBGROUPS_BIT` when creating the compute pipeline to ensure the subgroup sizes must be launched with all invocations active in the compute stage.
* Metal does not natively support controlling subgroup size, but the browsers may choose to expose the feature on Metal at their own risk.

2. No additional explicit limits are exposed on `GPUAdapterInfo`.

Previously, three limits were proposed (`explicitComputeSubgroupMinSize`, `explicitComputeSubgroupMaxSize`, `maxComputeWorkgroupSubgroups`) to expose the range of valid subgroup sizes and workgroup subgroup counts. The working group decided not to expose them ([#6241](https://github.com/gpuweb/gpuweb/issues/6241)). The reasons:
 * Most users of this feature are expert developers coding for a specific architecture who already know which subgroup sizes to use.
 * The native API limits do not always accurately represent the range of usable sizes (e.g. on Intel Gen12, `waveLaneCountMin` is 8 but the minimum requestable compute subgroup size is 16; on D3D12, `waveLaneCountMax` is not reliable).
 * `maxComputeWorkgroupSubgroups` only exists on Vulkan and has no D3D12 equivalent.

Instead, if the implementation cannot create a pipeline with the requested subgroup size (e.g. due to the size being outside the supported range, register pressure, or hardware-specific workgroup subgroup count limits), it results in an **uncategorized error** during pipeline creation. The implementation must support at least one power-of-two subgroup size between `subgroupMinSize` and `subgroupMaxSize` (from `GPUAdapterInfo`).


# Behavior
 * The attribute `subgroup_size` is restricted to `compute` shaders (in HLSL `[WaveSize()]` is [only supported in compute shaders](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_WaveSize.html#hlsl-attribute)).
 * The parameter must be a const-expression or an override-expression that resolves to an `i32` or `u32`.
 * The parameter must be must be a power-of-two (required by [D3D12](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_WaveSize.html#allowed-wave-sizes)).
 * If the implementation cannot create a pipeline with the requested subgroup size (e.g. due to the size being outside the supported range, register pressure, or hardware-specific workgroup subgroup count limits), it results in an uncategorized error during pipeline creation. The implementation must support at least one power-of-two subgroup size between `subgroupMinSize` and `subgroupMaxSize`.
 * `workgroupSize.x` must be a multiple of the attribute `subgroup_size` (required by [Vulkan](https://docs.vulkan.org/refpages/latest/refpages/source/VkPipelineShaderStageCreateInfo.html#VUID-VkPipelineShaderStageCreateInfo-pNext-02757)).

# WGSL Specification

## Enable Extension

Add a new `enable` extension.
| Enable | Description |
| --- | --- |
| **subgroup_size_control** | Adds WGSL attribute `subgroup_size` for `compute` shaders |

## New WGSL feature

This extension adds a new `subgroup_size_attr` entry for `subgroup_size`.
An entry is added to the _attribute_ list:
```
subgroup_size_attr :
 '@' 'subgroup_size' '(' expression ',' ? ')'
```

| Item | Content |
|----------|------|
|Description|Specifies the explicit subgroup size for the compute shader. <br> Must only be applied to a compute shader entry point function. Must not be applied to any other object.|
|Parameters| Takes one parameter which must be:<br>a const-expression or an override-expression; <br>an `i32` or `u32`;<br>a power of two.|

# Example usage

Enabling the `subgroup-size-control` feature for a `GPUDevice`:

```js
const adapter = await navigator.gpu.requestAdapter();

const requestedFeatures = [];
if (adapter.features.has('subgroup-size-control')) {
    requestedFeatures.push('subgroup-size-control');
} else {
    // Use an alternate code path or communicate error to user.
}

const device = await adapter.requestDevice({ requestedFeatures });
```

Using `subgroup_size` attribute in a WGSL shader:

```wgsl
enable subgroups;
enable subgroup_size_control;

@compute @workgroup_size(64, 1, 1) @subgroup_size(32)
fn main(@builtin(subgroup_invocation_id) sg_id : u32,
        @builtin(subgroup_size) sg_size : u32) {
    // ...
}
```

# References
 * [HLSL `WaveSize` attribute](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_WaveSize.html)
 * [Vulkan `VK_EXT_subgroup_size_control` extension](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_subgroup_size_control.html)
 * [Vulkan validations on `VkPipelineShaderStageCreateInfo`](https://docs.vulkan.org/refpages/latest/refpages/source/VkPipelineShaderStageCreateInfo.html)
 * [Metal documentation `porting-your-metal-code-to-apple-silicon`](https://developer.apple.com/documentation/apple-silicon/porting-your-metal-code-to-apple-silicon#Determine-the-SIMD-Group-Size-at-Runtime)
