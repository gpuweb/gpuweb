# WebGPU Compatibility Mode

This proposal is **under active development, but has not been standardized for inclusion in the WebGPU specification**. WebGPU implementations **must not** expose this functionality; doing so is a spec violation. Note however, an implementation might provide an option (e.g. command line flag) to enable a draft implementation, for developers who want to test this proposal.

The changes merged into this document are those for which the GPU for the Web Community Group has achieved **tentative** consensus prior to official standardization of the whole proposal. New items will be added to this doc as tentative consensus on further issues is achieved.

## Problem

WebGPU is a good match for modern explicit graphics APIs such as Vulkan, Metal and D3D12. However, there are a large number of devices which do not yet support those APIs. In particular, on Chrome on Windows, 31% of Chrome users do not have D3D11.1 or higher. On Android, [23% of Android users do not have Vulkan 1.1 (15% do not have Vulkan at all)](https://developer.android.com/about/dashboards). On ChromeOS, Vulkan penetration is still quite low, while OpenGL ES 3.1 is ubiquitous.

## Goals

The primary goal of WebGPU Compatibility mode is to increase the reach of WebGPU by providing an opt-in, slightly restricted subset of WebGPU which will run on older APIs such as D3D11 and OpenGL ES. The set of restrictions in Compatibility mode should be kept to a minimum in order to make it easy to port existing WebGPU applications. This will increase adoption of WebGPU applications via a wider userbase.

Since WebGPU Compatibility mode is a subset of WebGPU, all valid Compatibility mode applications are also valid WebGPU applications. Consequently, Compatibility mode applications will also run on user agents which do not support Compatibility mode. Such user agents will simply ignore the option requesting a Compatibility mode Adapter and return a Core WebGPU Adapter instead.

## WebGPU Spec Changes

Terms:

- Compatibility-defaulting adapter: an adapter on which `requestDevice()` defaults to a Compatibility Mode device.
- Core-defaulting adapter: an adapter on which `requestDevice()` defaults to a Core device.
- Core-capable adapter: an adapter which can provide a Core device if requested.
- Core-only implementation: a User Agent implementation which does not implement Compatibility Mode validation.

### Capabilities

Compatibility Mode introduces a new baseline "feature level" for WebGPU.
From this baseline, the "core" feature level is a collection of capability upgrades from "compatibility":

- Core requires some better limits which are optional in Compatibility Mode. See [10. Lower Limits](#10-lower-limits).
- Core requires some features which are optional in Compatibility Mode.

The `"webgpu-core"` feature enables **all features and limits** that are allowed in Core.
On Core-defaulting adapters, it is always available and enabled by default (including in Core-only implementations).
On Compatibility-defaulting adapters, may be enabled if available.

As always, the capabilities of the resulting device are enforced on all calls to the API.

EXTENSIBILITY:
Incremental capabilities between Compatibility Mode and Core can be exposed as limits or features which are optional on Compatibility-defaulting adapters.
They would be similarly always available and enabled by default on Core-requested adapters
(including in Core-only implementations).

### Initialization

No IDL changes.

The core spec already allows `featureLevel: "compatibility"`, which is currently ignored.
When an application passes `"compatibility"`, it indicates that it can handle (and hopefully use) an adapter with capabilities lower than the `"core"` defaults. In this case:

- If a User Agent supporting Compatibility Mode is running on a Core-*incapable* system, it returns a Compatibility-defaulting Core-incapable adapter (or null).
- If a User Agent supporting Compatibility Mode is running on a Core-*capable*, it **may** return a Compatibility Mode-defaulting Core-capable adapter, or **may** return a Core-defaulting adapter.
    - ALTERNATIVE: "require" (non-normatively encourage) UAs to go one way or the other - either always emulate Compatibility Mode or always upgrade to Core. This is probably not necessary.
- As already in the current spec, Core-only implementations must still recognize `"compatibility"` but ignore it (automatically upgrade the request) and return a Core-defaulting adapter (or null).

The `GPUAdapter` does not expose whether it is Core-defaulting or Compat-defaulting.
Most applications shouldn't need to check that compat is enforced, instead requesting the capabilities they want and only using those capabilities.
Applications that do need to check that compat is enforced (such as tests) should create a device and then check whether the `"webgpu-core"` feature is enabled on the device.

#### Example

```js
const adapter = await navigator.gpu.requestAdapter()
const device = await adapter.requestDevice();
```

and

```js
const adapter = await navigator.gpu.requestAdapter({ featureLevel: 'compatibility' });
const device = await adapter.requestDevice({ requiredFeatures: ['webgpu-core'] });
```

have the same result. Both will succeed if core is available and fail if not.

Using `requestAdapter({ featureLevel: 'compatibility' })` provides a way to upgrade the functionality at runtime, while still getting Compatibility Mode if available:

```js
const adapter = await navigator.gpu.requestAdapter({ featureLevel: 'compatibility' });
const hasCore = adapter.features.has('webgpu-core');
const requiredFeatures = [];
if (hasCore) {
   requiredFeatures.push('webgpu-core');
}
const device = await adapter.requestDevice({ requiredFeatures });

...

// enable fancier rendering if `hasCore` is true.
```

### Texture Creation

```webidl
partial dictionary GPUTextureDescriptor {
    GPUTextureViewDimension textureBindingViewDimension;
}
```

See "Texture view dimension may be specified", below.

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

**Justification**: OpenGL ES 3.1 does not support texture views.

### 2. Color blending state may not differ between color attachments in a `GPUFragmentState`.

Each `GPUColorTargetState` in a `GPUFragmentState` must have the same `blend.alpha`, `blend.color` and `writeMask`, or else a validation error will occur on render pipeline creation.

**Justification**: OpenGL ES 3.1 does not support indexed draw buffer state.

### 3. Disallow `CommandEncoder.copyTextureToBuffer()` and `CommandEncoder.copyTextureToTexture()` for compressed texture formats
`CommandEncoder.copyTextureToBuffer()` and `CommandEncoder.copyTextureToTexture()` of a compressed texture are disallowed, and will result in a validation error.

**Justification**: Compressed texture formats are non-renderable in OpenGL ES, and `glReadPixels()` requires a framebuffer-complete FBO, preventing `copyTextureToBuffer()`. Additionally, because ES 3.1 does not support `glCopyImageSubData()`, texture-to-texture copies must be worked around with `glBlitFramebuffer()`. Since compressed textures are not renderable, they cannot use the `glBlitFramebuffer()` workaround, preventing implementation of `copyTextureToTexture()`.

### 4. Disallow `GPUTextureViewDimension` `"CubeArray"` via validation

**Justification**: OpenGL ES does not support Cube Array textures.

### 5. Views of the same texture used in a single draw may not differ in aspect or mip levels.

A draw call may not bind two views of the same texture differing in `aspect`, `baseMipLevel`, or `mipLevelCount`. Only a single aspect and mip level range per texture is supported. This is enforced via validation at draw time.

**Justification**: OpenGL ES does not support texture views, but one set of these parameters per texture is supported via glTexParameteri(). In particular, one depth/stencil aspect may be specified via `GL_DEPTH_STENCIL_TEXTURE_MODE`, and one mip level subset via the `GL_TEXTURE_BASE_LEVEL` and `GL_TEXTURE_MAX_LEVEL` parameters.

### 6. Array texture views used in bind groups must consist of the entire array. That is, `baseArrayLayer` must be zero, and `arrayLayerCount` must be equal to the size of the texture array.

A bind group may not reference a subset of array layers. Only views of the entire array are supported for sampling or storage bindings. This is enforced via validation at bind group creation time.

**Justification**: OpenGL ES does not support texture views.

### 7. Disallow `sample_mask` and `sample_index` builtins in WGSL.

Use of the `sample_mask` or `sample_index` builtins would cause a validation error at shader module creation time.

**Justification**: OpenGL ES 3.1 does not support `gl_SampleMask`, `gl_SampleMaskIn`, or `gl_SampleID`.

### 8. Disallow two-component (RG) texture formats in storage texture bindings.

The `rg32uint`, `rg32sint`, and `rg32float` texture formats no longer support the `"write-only" or "read-only" STORAGE_BINDING` capability by default.

Calls to `createTexture()` or `createBindGroupLayout()` with this combination cause a validation error. Calls to `createShaderModule()` will fail if these formats are referenced as storage textures.

**Justification**: GLSL ES 3.1 (section 4.4.7, "Format Layout Qualifiers") does not permit any two-component (RG) texture formats in a format layout qualifier.

### 9. Depth bias clamp must be zero.

During `createRenderPipeline()` and `createRenderPipelineAsync()`, `GPUDepthStencilState.depthBiasClamp` must be zero, or a validation error occurs.

**Justification**: GLSL ES 3.1 does not support `glPolygonOffsetClamp()`.

### 10. Lower limits.

The differences in limits between compatibility mode and standard WebGPU
are as follows


| limit                               | compat  | standard  | gl limit                                     |
| :---------------------------------- | ------: | --------: | :------------------------------------------- |
| `maxColorAttachments`               |       4 |         8 | min(MAX_COLOR_ATTACHMENTS, MAX_DRAW_BUFFERS) |
| `maxComputeInvocationsPerWorkgroup` |     128 |       256 | MAX_COMPUTE_WORK_GROUP_INVOCATIONS           |
| `maxComputeWorkgroupSizeX`          |     128 |       256 | MAX_COMPUTE_WORK_GROUP_SIZE                  |
| `maxComputeWorkgroupSizeY`          |     128 |       256 | MAX_COMPUTE_WORK_GROUP_SIZE                  |
| `maxInterStageShaderVariables`      |      15 |        16 | MAX_VARYING_VECTORS                          |
| `maxStorageBuffersPerShaderStage`   |       4 |         8 | min(GL_MAX_SHADER_STORAGE_BUFFER_BINDINGS, GL_MAX_VERTEX_SHADER_STORAGE_BLOCKS, GL_MAX_FRAGMENT_SHADER_STORAGE_BLOCKS, GL_MAX_COMPUTE_SHADER_STORAGE_BLOCKS) |
| `maxTextureDimension1D`             |    4096 |      8192 | MAX_TEXTURE_SIZE                             |
| `maxTextureDimension2D`             |    4096 |      8192 | MAX_TEXTURE_SIZE                             |
| `maxUniformBufferBindingSize`       |   16384 |     65536 | MAX_UNIFORM_BLOCK_SIZE                       |
| `maxVertexAttributes`        | 16<sup>a</sup> |        16 | MAX_VERTEX_ATTRIBS                           |

(a) In compatibility mode, using `@builtin(vertex_index)`
and/or `@builtin(instance_index)` each count as an
attribute.

Note: Some of the limits are derived from a survey of OpenGL ES 3.1 devices
and are higher than the limit specified in the OpenGL ES 3.1 spec.

For example, in OpenGL ES 3.1, GL_MAX_FRAGMENT_IMAGE_UNIFORMS and GL_MAX_VERTEX_IMAGE_UNIFORMS can be
zero but `maxStorageTexturesPerShaderStage` is 4 above as all 3.1 devices support at
least 4 of each.

Similar limits include GL_MAX_TEXTURE_SIZE (2048) and GL_MAX_3D_TEXTURE_SIZE (256) but actual
devices support the values above.

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

## 15. Disallow bgra8unorm-srgb textures

**Justification**: OpenGL ES 3.1 does not support bgra8unorm-srgb textures.

## 16. Disallow `textureLoad` with `texture_depth?` textures

If a `texture_depth`, `texture_depth_2d_array`, or `texture_depth_cube` are used in a `textureLoad` call
in code passed to `createShaderModule` a validation error is generated.

**Justification**: OpenGL ES 3.1 does not support `texelFetch` for depth textures.

Note: this does not affect textures made with depth formats bound to `texture_2d<f32>`.

## 17. Disallow `@interpolation(flat)` and `@interpolation(flat, first)`

If code is passed to `createShaderModule` that uses `@interpolation(flat)` or `@interpolation(flat, first)`
generate a validation error.

**Justification**: OpenGL ES 3.1 only supports the last vertex as the provoking vertex where as 
other APIs only support the first vertex so only `@interpolation(flat, either)` is supported in
compatibility mode.

## Issues

Q: OpenGL ES does not have "coarse" and "fine" variants of the derivative instructions (`dFdx()`, `dFdy()`, `fwidth()`). Should WGSL's "fine" derivatives (`dpdxFine()`, `dpdyFine()`, and `fwidthFine()`) be required to deliver high precision results? See [Issue 4325](https://github.com/gpuweb/gpuweb/issues/4325).

A: Unclear. In SPIR-V, Fine variants must include the value of P for the local fragment, while Coarse variants do not. WGSL is less constraining, and simply says that Coarse "may result in fewer unique positions than `dpdxFine(e)`."
