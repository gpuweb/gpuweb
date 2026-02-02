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


Note that on Vulkan we need `computeFullSubgroups == VK_TRUE` because we should set `VK_PIPELINE_SHADER_STAGE_CREATE_REQUIRE_FULL_SUBGROUPS_BIT` when creating the compute pipelien to ensure the subgroup sizes must be launched with all invocations active in the compute stage.

TODO: Shall we support this extension on the newer Apple silicons with a single acceptable subgroup size?

2. Three new limitations for the WGSL attribute `subgroup_size`.

(1) `minExplicitComputeSubgroupSize` specifies the minimum value that can be used as the attribute `subgroup_size`.

| Platform | Implementation |
|----------|------|
|Vulkan|`VkPhysicalDeviceSubgroupSizeControlPropertiesEXT::minSubgroupSize` |
|D3D12|`D3D12_FEATURE_DATA_D3D12_OPTIONS1::waveLaneCountMin` |

(2) `maxExplicitComputeSubgroupSize` specifies the maximum value that can be used as the attribute `subgroup_size`.

| Platform | Implementation |
|----------|------|
|Vulkan|`VkPhysicalDeviceSubgroupSizeControlPropertiesEXT::maxSubgroupSize` |
|D3D12|`D3D12_FEATURE_DATA_D3D12_OPTIONS1::waveLaneCountMax` |

(3) `maxComputeWorkgroupSubgroups` limits the total workgroup size when the attribute `subgroup_size` is used.

| Platform | Implementation |
|----------|------|
|Vulkan|`VkPhysicalDeviceSubgroupSizeControlProperties.maxComputeWorkgroupSubgroups` |
|D3D12| Not supported |

Note that we need new limitations instead of the existing `subgroupMinSize` and `subgroupMaxSize` is because:
1. D3D12 runtime validates `[WaveSize]` with `waveLaneCountMin` and `waveLaneCountMax`
2. On D3D12 we don't always use `waveLaneCountMin` as `subgroupMinSize` because on some Intel GPUs, it is possible to run some pixel shaders with wave lane count 8, while on that platform `waveLaneCountMin` is 16, meaning in compute shaders the wave lane count will always be at least 16.
3. On D3D12 we don't always use `waveLaneCountMax` as `subgroupMaxSize` because in [D3D12 document](https://github.com/Microsoft/DirectXShaderCompiler/wiki/Wave-Intrinsics#:~:text=UINT%20WaveLaneCountMax) "the WaveLaneCountMax queried from D3D12 API is not reliable and the meaning is unclear.


# Behavior
 * The attribute `subgroup_size` is restricted to `compute` shaders (in HLSL `[WaveSize()]` is [only supported in compute shaders](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_WaveSize.html#hlsl-attribute)).
 * The parameter must be a const-expression or an override-expression that resolves to an `i32` or `u32`.
 * The parameter must be must be a power-of-two (required by [D3D12](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_WaveSize.html#allowed-wave-sizes)).
 * The parameter must be greater than or equal to the `minExplicitComputeSubgroupSize` on the current adapter (required by [D3D12](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_WaveSize.html#runtime-validation)).
 * The parameter must be less than or equal to the `maxExplicitComputeSubgroupSize` on the current adapter (required by [D3D12](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_WaveSize.html#runtime-validation)).
 * The total workgroup size (`workgroupSize.x * workgroupsize.y * workgroupsize.z`) must be less than or equal to the product of the attribute `subgroup_size` and `maxComputeWorkgroupSubgroups` (required by [Vulkan](https://docs.vulkan.org/refpages/latest/refpages/source/VkPipelineShaderStageCreateInfo.html#VUID-VkPipelineShaderStageCreateInfo-pNext-02756)).
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
