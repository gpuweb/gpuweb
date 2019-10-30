# GPULimits Explainer

This document lists the citations for the "limits" in the WebGPU API that decide the minimum capabilities of a compliant WebGPU implementation.

## The GPULimits Dictionary (last updated 2019-10-29)

```javascript
dictionary GPULimits {
    unsigned long maxBindGroups = 4;
    unsigned long maxDynamicUniformBuffersPerPipelineLayout = 8;
    unsigned long maxDynamicStorageBuffersPerPipelineLayout = 4;
    unsigned long maxSampledTexturesPerShaderStage = 16;
    unsigned long maxSamplersPerShaderStage = 16;
    unsigned long maxStorageBuffersPerShaderStage = 4;
    unsigned long maxStorageTexturesPerShaderStage = 4;
    unsigned long maxUniformBuffersPerShaderStage = 12;
};
```

Limit | API Doc | gpuweb issue/PR
--- | --- | ---
`maxBindGroups = 4;` | [Vulkan](https://www.khronos.org/registry/vulkan/specs/1.1-extensions/html/vkspec.html#limits-minmax) `maxBoundDescriptorSets` |
`maxDynamicUniformBuffersPerPipelineLayout = 8;` | [Vulkan](https://www.khronos.org/registry/vulkan/specs/1.1-extensions/html/vkspec.html#limits-minmax) `maxDescriptorSetUniformBuffersDynamic` | [#406](https://github.com/gpuweb/gpuweb/issues/406)
`maxDynamicStorageBuffersPerPipelineLayout = 4;` | [Vulkan](https://www.khronos.org/registry/vulkan/specs/1.1-extensions/html/vkspec.html#limits-minmax) `maxDescriptorSetStorageBuffersDynamic` | [#406](https://github.com/gpuweb/gpuweb/issues/406)
`maxSampledTexturesPerShaderStage = 16;` | [Vulkan](https://www.khronos.org/registry/vulkan/specs/1.1-extensions/html/vkspec.html#limits-minmax) `maxPerStageDescriptorSampledImages` | [#409](https://github.com/gpuweb/gpuweb/issues/409)
`maxSamplersPerShaderStage = 16;` | [Vulkan](https://www.khronos.org/registry/vulkan/specs/1.1-extensions/html/vkspec.html#limits-minmax) `maxPerStageDescriptorSamplers` | [#409](https://github.com/gpuweb/gpuweb/issues/409)
`maxStorageBuffersPerShaderStage = 4;` | [Vulkan](https://www.khronos.org/registry/vulkan/specs/1.1-extensions/html/vkspec.html#limits-minmax) `maxPerStageDescriptorStorageBuffers` | [#409](https://github.com/gpuweb/gpuweb/issues/409)
`maxStorageTexturesPerShaderStage = 4;` | [Vulkan](https://www.khronos.org/registry/vulkan/specs/1.1-extensions/html/vkspec.html#limits-minmax) `maxPerStageDescriptorStorageImages` | [#409](https://github.com/gpuweb/gpuweb/issues/409)
`maxUniformBuffersPerShaderStage = 12;` | [Vulkan](https://www.khronos.org/registry/vulkan/specs/1.1-extensions/html/vkspec.html#limits-minmax) `maxPerStageDescriptorUniformBuffers` | [#409](https://github.com/gpuweb/gpuweb/issues/409)
