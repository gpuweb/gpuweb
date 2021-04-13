# GPULimits Explainer

This document lists the citations for the "limits" in the WebGPU API that decide the minimum capabilities of a compliant WebGPU implementation.

## The GPULimits Dictionary (last updated 2021-04-13)

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
    unsigned long maxVertexBuffers = 8;
    unsigned long maxVertexAttributes = 16;
    unsigned long maxVertexArrayStride = 2048;
    unsigned long maxTextureDimension1D = 8192;
    unsigned long maxTextureDimension2D = 8192;
    unsigned long maxTextureDimension3D = 2048;
    unsigned long maxTextureArrayLayers = 2048;
};
```

Limit | API Doc | gpuweb issue/PR | Notes
--- | --- | --- | ---
`maxBindGroups = 4;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxBoundDescriptorSets` | |
`maxDynamicUniformBuffersPerPipelineLayout = 8;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxDescriptorSetUniformBuffersDynamic` | [#406](https://github.com/gpuweb/gpuweb/issues/406) |
`maxDynamicStorageBuffersPerPipelineLayout = 4;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxDescriptorSetStorageBuffersDynamic` | [#406](https://github.com/gpuweb/gpuweb/issues/406) |
`maxSampledTexturesPerShaderStage = 16;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxPerStageDescriptorSampledImages` | [#409](https://github.com/gpuweb/gpuweb/issues/409) |
`maxSamplersPerShaderStage = 16;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxPerStageDescriptorSamplers` | [#409](https://github.com/gpuweb/gpuweb/issues/409) |
`maxStorageBuffersPerShaderStage = 4;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxPerStageDescriptorStorageBuffers` | [#409](https://github.com/gpuweb/gpuweb/issues/409) |
`maxStorageTexturesPerShaderStage = 4;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxPerStageDescriptorStorageImages` | [#409](https://github.com/gpuweb/gpuweb/issues/409) |
`maxUniformBuffersPerShaderStage = 12;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxPerStageDescriptorUniformBuffers` | [#409](https://github.com/gpuweb/gpuweb/issues/409) |
`maxVertexBuffers = 8;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxVertexInputBindings` | [#693](https://github.com/gpuweb/gpuweb/issues/693) |
`maxVertexAttributes = 16;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxVertexInputAttributes` | [#693](https://github.com/gpuweb/gpuweb/issues/693) |
`maxVertexArrayStride = 2048;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxVertexInputBindingStride` | [#693](https://github.com/gpuweb/gpuweb/issues/693) |
`maxTextureDimension1D = 8192;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxImageDimension1D` | [#1327](https://github.com/gpuweb/gpuweb/issues/1327) | Vulkan's limit is 4096. We expand the limit to 8192 because [the vast majority of devices in market can support 8192 or a higher limit](https://vulkan.gpuinfo.org/displaydevicelimit.php?name=maxImageDimension1D). The devices that cannot support this limit are pretty rare and old.
`maxTextureDimension2D = 8192;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxImageDimension2D` | [#1327](https://github.com/gpuweb/gpuweb/issues/1327) | Vulkan's limit is 4096. We expand the limit to 8192 because [the vast majority of devices in market can support 8192 or a higher limit](https://vulkan.gpuinfo.org/displaydevicelimit.php?name=maxImageDimension2D). The devices that cannot support this limit are pretty rare and old.
`maxTextureDimension3D = 2048;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxImageDimension3D` | [#1327](https://github.com/gpuweb/gpuweb/issues/1327) | Vulkan's limit is 256. We expand the limit to 2048 because [the vast majority of devices in market can support 2048 or a higher limit](https://vulkan.gpuinfo.org/displaydevicelimit.php?name=maxImageDimension3D). The devices that cannot support this limit are pretty rare and old.
`maxTextureArrayLayers = 2048;` | [Vulkan](https://vulkan.lunarg.com/doc/view/1.2.170.0/linux/chunked_spec/chap42.html#limits) `maxImageArrayLayers` | [#1327](https://github.com/gpuweb/gpuweb/issues/1327) | Vulkan's limit is 256. We expand the limit to 2048 because [the vast majority of devices in market can support 2048 or a higher limit](https://vulkan.gpuinfo.org/displaydevicelimit.php?name=maxImageArrayLayers). The devices that cannot support this limit are pretty rare and old.
