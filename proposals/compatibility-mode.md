# WebGPU Compatibility Mode

* Status: [Merged](README.md#status-merged)
* Created: 2023-10-10
* Issue: [#4266](https://github.com/gpuweb/gpuweb/issues/4266),
  [label:compat](https://github.com/gpuweb/gpuweb/issues?q=label%3Acompat)

This proposal is **under active development, but has not been standardized for inclusion in the WebGPU specification**. WebGPU implementations **must not** expose this functionality; doing so is a spec violation. Note however, an implementation might provide an option (e.g. command line flag) to enable a draft implementation, for developers who want to test this proposal.

The changes merged into this document are those for which the GPU for the Web Community Group has achieved **tentative** consensus prior to official standardization of the whole proposal. New items will be added to this doc as tentative consensus on further issues is achieved.

## Problem

WebGPU is a good match for modern explicit graphics APIs such as Vulkan, Metal and D3D12. However, there are a large number of devices which do not yet support those APIs. In particular, on Chrome on Windows, 31% of Chrome users do not have D3D11.1 or higher. On Android, [23% of Android users do not have Vulkan 1.1 (15% do not have Vulkan at all)](https://developer.android.com/about/dashboards). On ChromeOS, Vulkan penetration is still quite low, while OpenGL ES 3.1 is ubiquitous.

## Goals

The primary goal of WebGPU Compatibility mode is to increase the reach of WebGPU by providing an opt-in, slightly restricted subset of WebGPU which will run on older APIs such as D3D11 and OpenGL ES. The set of restrictions in Compatibility mode should be kept to a minimum in order to make it easy to port existing WebGPU applications. This will increase adoption of WebGPU applications via a wider userbase.

Since WebGPU Compatibility mode is a subset of WebGPU, all valid Compatibility mode applications are also valid WebGPU applications. Consequently, Compatibility mode applications will also run on user agents which do not support Compatibility mode. Such user agents will simply ignore the option requesting a Compatibility mode Adapter and return a Core WebGPU Adapter instead.

# WebGPU Spec Changes

Spec changes are described in the following subsections.

## Validation

As always, API calls which are unsupported by a Device will result in validation errors.
Even if a Device is backed by a fully WebGPU-capable hardware adapter, such as D3D12, Metal or Vulkan, it validates all subsequent API calls made on the Adapter and the objects it vends according the set of features enabled on the device, including Compatibility mode validation when `"core-features-and-limits"` is not enabled.

Note there are currently no "Compatibility features", features that would provide incremental capabilities _between_ Compatibility and Core modes.
See [discussion](https://github.com/gpuweb/gpuweb/issues/4987#issuecomment-2625791411).

## `"core-features-and-limits"` Feature

A new feature `"core-features-and-limits"`, when enabled on a device, lifts all Compatibility mode restrictions (features and limits). See below for details.

## Initialization

When calling `GPU.requestAdapter()`, passing `featureLevel: "compatibility"` in the `GPURequestAdapterOptions` will indicate to the User Agent a request to select the Compatibility subset of WebGPU, which is detailed in later sections.

- If the request is honored by the User Agent, the resulting adapter will be a "Compatibility-defaulting" Adapter.

  If not, the resulting adapter will be "Core-defaulting" (the same as what you would get from `featureLevel: "core"` if the system supports it).

- `adapter.requestDevice()` with no arguments requests a device that has `adapter`'s default capabilities.

  `adapter.requestDevice(desc)` can request additional capabilities over the `adapter`'s defaults.

- Core-defaulting adapters *always* support the `"core-features-and-limits"` feature. It is *automatically enabled* on devices created from such adapters.

  Compatibility-defaulting adapters *may* support the `"core-features-and-limits"` feature. It *may be requested* on devices created from such adapters.

  Both *may* support features like `"float32-blendable"`, which is optional in both modes.

### Usage

Applications should `requestAdapter()` with a `featureLevel` that is below or equal to their minimum requirements.
Then they can inspect the available features and enable features, including `"core-features-and-limits"` if they can optionally take advantage of Core features.

Example code for an application which:

- Requires `"float32-blendable"`
- Supports using Core features if available
- Supports using only Compatibility features otherwise
- Supports fallback if WebGPU is not available at all

```js
const adapter = await navigator.gpu.requestAdapter({ featureLevel: "compatibility" });
if (adapter === null || !adapter.features.has("float32-blendable")) {
  return app.init_fallback_no_webgpu();
}

const requiredFeatures = [];
if (adapter.features.has("core-features-and-limits")) {
  requiredFeatures.push("core-features-and-limits");
}

const device = await adapter.requestDevice({ requiredFeatures });
return app.init(device);
```

The capabilities of a device can be determined from the device alone, allowing the device to be passed into other parts of the code (or into libraries) without sidecar information:

```js
const haveCore = device.features.has("core-features-and-limits");
```

## Compatibility mode restrictions

### 1. Texture view dimension may be specified

When specifying a texture, a `textureBindingViewDimension` property determines the views which can be bound from that texture for sampling (see "Proposed IDL changes", above). Binding a view of a different dimension for sampling than specified at texture creation time will cause a validation error. If `textureBindingViewDimension` is unspecified, use [the same algorithm as `createView()`](https://gpuweb.github.io/gpuweb/#abstract-opdef-resolving-gputextureviewdescriptor-defaults):

```
if desc.dimension is "1d":
    set textureBindingViewDimension to "1d"
if desc.dimension is "2d":
  if desc.size.depthOrArrayLayers is 1:
    set textureBindingViewDimension to "2d"
  else:
    set textureBindingViewDimension to "2d-array"
if desc.dimension is "3d":
  set textureBindingViewDimension to "3d"
```

The WebIDL change:

```webidl
partial dictionary GPUTextureDescriptor {
    GPUTextureViewDimension textureBindingViewDimension;
}
```

**Justification**: OpenGL ES 3.1 does not support texture views.

### 2. Color blending state may not differ between color attachments in a `GPUFragmentState`.

Each `GPUColorTargetState` in a `GPUFragmentState` must have the same `blend.alpha`, `blend.color` and `writeMask`, or else a validation error will occur on render pipeline creation.

**Justification**: OpenGL ES 3.1 does not support indexed draw buffer state.

### 3. Disallow `CommandEncoder.copyTextureToBuffer()` and `CommandEncoder.copyTextureToTexture()` for compressed texture formats
`CommandEncoder.copyTextureToBuffer()` and `CommandEncoder.copyTextureToTexture()` of a compressed texture are disallowed, and will result in a validation error.

**Justification**: Compressed texture formats are non-renderable in OpenGL ES, and `glReadPixels()` requires a framebuffer-complete FBO, preventing `copyTextureToBuffer()`. Additionally, because ES 3.1 does not support `glCopyImageSubData()`, texture-to-texture copies must be worked around with `glBlitFramebuffer()`. Since compressed textures are not renderable, they cannot use the `glBlitFramebuffer()` workaround, preventing implementation of `copyTextureToTexture()`.

### 4. Disallow `GPUTextureViewDimension` `"CubeArray"` via validation

**Justification**: OpenGL ES does not support Cube Array textures.

### 5. Views of the same texture used in a single draw may not differ in aspect, mip levels, or swizzle.

A draw call may not bind two views of the same texture differing in `aspect`, `baseMipLevel`, `mipLevelCount`, or `swizzle`. Only a single aspect, a mip level range, and a swizzle per texture is supported. This is enforced via validation at draw time.

**Justification**: OpenGL ES does not support texture views, but one set of these parameters per texture is supported via glTexParameteri(). In particular, one depth/stencil aspect may be specified via `GL_DEPTH_STENCIL_TEXTURE_MODE`, and one mip level subset via the `GL_TEXTURE_BASE_LEVEL` and `GL_TEXTURE_MAX_LEVEL` parameters.

### 6. Array texture views used in bind groups must consist of the entire array. That is, `baseArrayLayer` must be zero, and `arrayLayerCount` must be equal to the size of the texture array.

A bind group may not reference a subset of array layers. Only views of the entire array are supported for sampling or storage bindings. This is enforced via validation at bind group creation time.

**Justification**: OpenGL ES does not support texture views.

### 7. Disallow `sample_mask` and `sample_index` builtins in WGSL.

Use of the `sample_mask` or `sample_index` builtins would cause a validation error at pipeline creation time.

**Justification**: OpenGL ES 3.1 does not support `gl_SampleMask`, `gl_SampleMaskIn`, or `gl_SampleID`.

### 8. Disallow two-component (RG) texture formats in storage texture bindings.

The `rg32uint`, `rg32sint`, and `rg32float` texture formats no longer support the `"write-only" or "read-only" STORAGE_BINDING` capability by default.

Calls to `createTexture()` or `createBindGroupLayout()` with this combination cause a validation error.

**Justification**: GLSL ES 3.1 (section 4.4.7, "Format Layout Qualifiers") does not permit any two-component (RG) texture formats in a format layout qualifier.

### 9. Depth bias clamp must be zero.

During `createRenderPipeline()` and `createRenderPipelineAsync()`, `GPUDepthStencilState.depthBiasClamp` must be zero, or a validation error occurs.

**Justification**: GLSL ES 3.1 does not support `glPolygonOffsetClamp()`.

### 10. Lower limits.

The differences in limits between compatibility mode and standard WebGPU
are as follows:

| limit                               | compat  | standard  | gl limit                                     |
| :---------------------------------- | ------: | --------: | :------------------------------------------- |
| `maxColorAttachments`               |       4 |         8 | min(MAX_COLOR_ATTACHMENTS, MAX_DRAW_BUFFERS) |
| `maxComputeInvocationsPerWorkgroup` |     128 |       256 | MAX_COMPUTE_WORK_GROUP_INVOCATIONS           |
| `maxComputeWorkgroupSizeX`          |     128 |       256 | MAX_COMPUTE_WORK_GROUP_SIZE                  |
| `maxComputeWorkgroupSizeY`          |     128 |       256 | MAX_COMPUTE_WORK_GROUP_SIZE                  |
| `maxInterStageShaderVariables`      |      15 |        16 | MAX_VARYING_VECTORS                          |
| `maxTextureDimension1D`             |    4096 |      8192 | MAX_TEXTURE_SIZE                             |
| `maxTextureDimension2D`             |    4096 |      8192 | MAX_TEXTURE_SIZE                             |
| `maxUniformBufferBindingSize`       |   16384 |     65536 | MAX_UNIFORM_BLOCK_SIZE                       |
| `maxVertexAttributes`        | 16<sup>a</sup> |        16 | MAX_VERTEX_ATTRIBS                           |

(a) In compatibility mode, using `@builtin(vertex_index)`
and/or `@builtin(instance_index)` each count as an
attribute.

Note: Some of the limits are derived from a survey of OpenGL ES 3.1 devices
and are higher than the limit specified in the OpenGL ES 3.1 spec. For example:

- `MAX_COMPUTE_SHADER_STORAGE_BLOCKS` can be 4, but all devices support at least 8.
  `maxStorageBuffersPerShaderStage` is not lowered.
- `MAX_TEXTURE_SIZE` can be 2048, but all ES3.1+ devices support at least 4096.
  `maxTextureDimension1D` and `maxTextureDimension2D` are lowered accordingly.
- `MAX_3D_TEXTURE_SIZE` can be 256, but all ES3.1+ devices support at least 2048.
  `maxTextureDimension3D` is not lowered.

### 11. Disallow `linear` and `sample` interpolation options.

In WGSL, an inter-stage variable can be marked with one of three interpolation types: `'perspective'`,
`'linear'`, `'flat'`, and one of three interpolation sampling modes: `'center'`, `'centroid'`, `'sample'`

In compatibility mode, `'linear'` type and sampling mode `'sample'` are disallowed.
If either are used in the code passed to `createShaderModule` a validation error is generated.

**Justification**: OpenGL ES 3.1 does not support `linear` interpolation nor `sample` sampling.

### 12. Disallow copying multisample textures.

`copyTextureToTexture` will generate a validation error if the sampleCount of the textures is not 1.

**Justification**: OpenGL ES 3.1 does not support copying of multisample textures.

### 13. Disallow texture format reinterpretation

When calling `createTexture`, the `viewFormats`, if specified, must be the same format as the texture.

**Justification**: OpenGL ES 3.1 does not support texture format reinterpretation.

### 14. Require `depthOrArrayLayers` to be compatible with `textureBindingViewDimension` in `createTexture`.

When creating a texture you can pass in a `textureBindingViewDimension`.

* If `textureBindingViewDimension` is `"2d"` and `depthOrArrayLayers` is not 1, a validation error is generated.

* If `textureBindingViewDimension` is `"cube"` and `depthOrArrayLayers` is not 6, a validation error is generated.

**Justification**: OpenGL ES 3.1 cannot create 2d textures with more than 1 layer nor can it
create cube maps that are not exactly 6 layers.

### 15. Disallow bgra8unorm-srgb textures

**Justification**: OpenGL ES 3.1 does not support bgra8unorm-srgb textures.

### 16. Disallow `textureLoad` with `texture_depth?` textures

If a `texture_depth`, `texture_depth_2d_array`, or `texture_depth_cube` are used in a `textureLoad` call
in code passed to `createShaderModule` a validation error is generated.

**Justification**: OpenGL ES 3.1 does not support `texelFetch` for depth textures.

Note: this does not affect textures made with depth formats bound to `texture_2d<f32>`.

### 17. Disallow `@interpolation(flat)` and `@interpolation(flat, first)`

If code is passed to `createShaderModule` that uses `@interpolation(flat)` or `@interpolation(flat, first)`
generate a validation error.

**Justification**: OpenGL ES 3.1 only supports the last vertex as the provoking vertex where as
other APIs only support the first vertex so only `@interpolation(flat, either)` is supported in
compatibility mode.

### 18. Introduce new `maxStorageBuffersInVertexStage` and `maxStorageTexturesInVertexStage` limits.

In `createBindGroupLayout` and `createPipelineLayout` (including `"auto"` layout creation), if the number of `"storage"`/`"read-only-storage"` buffer bindings with visibility bit `VERTEX` exceeds the `maxStorageBuffersInVertexStage` limit, a validation error will occur.

In `createBindGroupLayout`, `createPipelineLayout` (including "auto" layout creation), if the number of `storageTexture` bindings with visibility bit `VERTEX` exceeds the `maxStorageTexturesInVertexStage` limit, a validation error will occur.

In addition to the new limits, the existing `maxStorageBuffersPerShaderStage` and `maxStorageTexturesPerShaderStage` limits continue to apply to all stages. E.g., the effective storage buffer limit in the vertex stage is `min(maxStorageBuffersPerShaderStage, maxStorageBuffersInVertexStage)`.

In Compatibility mode, these new limits will have a default of zero. In Core mode, `maxStorageBuffersInVertexStage` will default to the same value as `maxStorageBuffersPerShaderStage` and `maxStorageTexturesInVertexStage` will default to the same value as `maxStorageTexturesPerShaderStage`.

In both Compatibility Mode and Core, at device creation time, if the requested limit for `maxStorageBuffersInVertexStage` exceeds the effective requested limit for `maxStorageBuffersPerShaderStage`, then the requested limit for `maxStorageBuffersPerShaderStage` is raised to the
value requested for `maxStorageBuffersInVertexStage`. If the requested limit for `maxStorageTexturesInVertexStage` exceeds the effective requested limit for `maxStorageTexturesPerShaderStage`, then the requested limit for `maxStorageTexturesPerShaderStage` is raised to the
value requested for `maxStorageTexturesInVertexStage`.

In Core mode, at device creation time, and after application of the previous rule, `maxStorageBuffersInVertexStage` is set to the effective requested limit for `maxStorageBuffersPerShaderStage`, and `maxStorageTexturesInVertexStage` is set to the effective limit for `maxStorageTexturesPerShaderStage`.

**Justification**: OpenGL ES 3.1 allows `MAX_VERTEX_SHADER_STORAGE_BLOCKS` and `MAX_VERTEX_IMAGE_UNIFORMS` to be zero, and there are a significant number of devices in the field with that value.

### 19. Introduce new `maxStorageBuffersInFragmentStage` and `maxStorageTexturesInFragmentStage` limits.

In `createBindGroupLayout`, `createPipelineLayout` (including `"auto"` layout creation), if the number of `"storage"`/`"read-only-storage"` buffer bindings with visibility bit `FRAGMENT` exceeds the `maxStorageBuffersInFragmentStage` limit, a validation error will occur.

In `createBindGroupLayout`, `createPipelineLayout` (including `"auto"` layout creation), if the number of `storageTexture` bindings with visibility bit `FRAGMENT` exceeds the `maxStorageTexturesInFragmentStage` limit, a validation error will occur.

In addition to the new limits, the existing `maxStorageBuffersPerShaderStage` and `maxStorageTexturesPerShaderStage` limits continue to apply to all stages. E.g., the effective storage buffer limit in the fragment stage is `min(maxStorageBuffersPerShaderStage, maxStorageBuffersInFragmentStage)`.

In Compatibility mode, these new limits will have a default of four. In Core mode, `maxStorageBuffersInFragmentStage` will default to the same value as `maxStorageBuffersPerShaderStage`, and `maxStorageTexturesInFragmentStage` will default to the same value as `maxStorageTexturesPerShaderStage`.

In both Compatibility Mode and Core, at device creation time, if the requested limit for `maxStorageBuffersInFragmentStage` exceeds the effective requested limit for `maxStorageBuffersPerShaderStage`, then the requested limit for `maxStorageBuffersPerShaderStage` will be raised to the
value requested for `maxStorageBuffersInFragmentStage`. If the requested limit for `maxStorageTexturesInFragmentStage` exceeds the effective limit for `maxStorageTexturePerShaderStage`, then the requested limit for `maxStorageTexturesPerShaderStage` will be raised to the
value requested for `macStorageTexturesInFragmentStage`.

In Core mode, at device creation time, and after application of the previous rule, `maxStorageBuffersInFragmentStage` is set to the effective limit for `maxStorageBuffersPerShaderStage` and, `maxStorageTexturesInFragmentStage` is set to the effective limit for `maxStorageTexturesPerShaderStage`.

**Justification**: Although OpenGL ES 3.1 allows `MAX_FRAGMENT_SHADER_STORAGE_BLOCKS` and `MAX_FRAGMENT_IMAGE_UNIFORMS` to be zero the
population of devices with less than 4 of each limit is around 5% and falling. The remaining devices support 4 or more of each.

### 20. Disallow using a depth texture with a non-comparison sampler

Using a depth texture `texture_depth_2d`, `texture_depth_cube`, `texture_depth_2d_array` with a non-comparison
sampler in a shader will generate a validation error at pipeline creation time.

**Justification**: OpenGL ES 3.1 says such usage has undefined behavior.

### 21. Limit the number of texture+sampler combinations in a stage.

If the number of texture+sampler combinations used a in single stage in a pipeline exceeds
`maxSampledTexturesPerShaderStage` or `maxSamplersPerShaderStage`, a validation error is generated.

The validation occurs as follows:

```
for each stage of the pipeline:
  sum = 0
  for each unique texture or external texture binding that is used in any call to a texture builtin in the shader call graph reachable from the shader entry point:
    numPairs = max(1, number of unique texture sampler combos for that texture binding)
    if it's an external texture binding,
      numPairs = 1 + 3 * numPairs // for LUT texture/sampler and Y+U+V
    sum = sum + numPairs
  if sum > maxSampledTexturesPerShaderStage or sum > maxSamplersPerShaderStage
    generate a validation error.
```

**Justification**: In OpenGL ES 3.1 does not support more combinations. Sampler units and texture units are bound together, and are limited by GL_MAX_TEXTURE_IMAGE_UNITS and GL_MAX_VERTEX_TEXTURE_IMAGE_UNITS. Texture unit X uses sampler unit X.

### 22. Disallow multisampled `rgba16float` and `r32float` textures.

`rgba16float` and `r32float` support multisampling in Core, but not in Compatibility mode.
A validation error is produced by `createTexture()` for unsupported combinations.

Comparison with WebGPU Core and OpenGL ES 3.1:

<table>
  <tr><th>sampleCount <th style=text-align:right>Format
    <th>Core
    <th>OpenGL ES 3.1
    <th>Compatibility
  <tr><td rowspan=6>1 <td style=text-align:right>r16float
    <td>render/blend
    <td rowspan=3>(render/blend with (GL_EXT_color_buffer_half_float or GL_EXT_color_buffer_float))
    <td>same as core
  <tr><td style=text-align:right>rg16float
    <td>render/blend
    <td>same as core
  <tr><td style=text-align:right>rgba16float
    <td>render/blend
    <td>same as core
  <tr><td style=text-align:right>r32float
    <td>render,<br>(blend with float32-blendable)
    <td rowspan=3>(render with GL_EXT_color_buffer_float),<br>(blend with EXT_float_blend)
    <td>same as core
  <tr><td style=text-align:right>rg32float
    <td>render,<br>(blend with float32-blendable)
    <td>same as core
  <tr><td style=text-align:right>rgba32float
    <td>render,<br>(blend with float32-blendable)
    <td>same as core

  <tr><th>sampleCount <th style=text-align:right>Format
    <th>Core
    <th>OpenGL ES 3.1
    <th>Compatibility
  <tr><td rowspan=6>4 <td style=text-align:right>r16float
    <td>render/resolve/blend
    <td rowspan=2>(render/resolve/blend with GL_EXT_color_buffer_float)
    <td>same as core
  <tr><td style=text-align:right>rg16float
    <td>render/resolve/blend
    <td>same as core
  <tr><td style=text-align:right>rgba16float
    <td>render/resolve/blend
    <td>&cross;
    <td>&cross;
  <tr><td style=text-align:right>r32float
    <td>render,<br>(blend with float32-blendable)
    <td>&cross;
    <td>&cross;
  <tr><td style=text-align:right>rg32float
    <td>&cross;
    <td>&cross;
    <td>same as core
  <tr><td style=text-align:right>rgba32float
    <td>&cross;
    <td>&cross;
    <td>same as core

  <tr><th>sampleCount <th style=text-align:right>Format
    <th>Core
    <th>OpenGL ES 3.1
    <th>Compatibility
  <tr><td>1 or 4 <td style=text-align:right>rg11b10ufloat
    <td>(render/resolve/blend with rg11b10ufloat-renderable)
    <td>(render/resolve/blend with GL_EXT_color_buffer_float)
    <td>same as core
</table>

**Justification**: See OpenGL ES 3.1 column.
Implementing Compatibility mode on OpenGL ES 3.1 requires `GL_EXT_color_buffer_float`.
Only a small number of devices (most recently produced in 2018) lack support for this extension.

### 23. Disallow all multisampled integer textures.

Integer texture formats allow multisampling in Core, but not in Compatibility mode.
(The formats are `r8uint`, `r8sint`, `rg8uint`, `rg8sint`, `rgba8uint`, `rgba8sint`, `r16uint`, `r16sint`, `rg16uint`, `rg16sint`, `rgba16uint`, `rgba16sint`, `rgb10a2uint`.)

If `createTexture()` is called with any of these formats and `sampleCount > 1`, a validation error is produced.

**Justification**: OpenGL ES 3.1 does not require multisampling to be supported on integer texture formats. The minimum value for GL_MAX_INTEGER_SAMPLES is 1, and [94.7% of reports on gpuinfo have that value](https://opengles.gpuinfo.org/displaycapability.php?name=GL_MAX_INTEGER_SAMPLES&esversion=31).

### 24. Disallow "Fine" variants of derivative functions (`dpdxFine()`, `dpdyFine()`, `fwidthFine()`).

These functions must not be referenced from the from the call graph rooted at a shader entry point or else a validation error will occur at pipeline creation time.

**Justification**: OpenGL ES does not support "Coarse" and "Fine" variants of the derivative functions (`dfdx()`, `dfdy()`, `fwidth()`).
