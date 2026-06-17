# Multisampled Array Textures

* Status: [Draft](README.md#status-draft)
* Created: 2026-04-30
* Issue: [#6277](https://github.com/gpuweb/gpuweb/issues/6277)

## Motivation

WebGPU currently forbids creating multisampled 2D textures with more than one
array layer. That restriction makes XR, stereo, layered rendering, and other
multi-target MSAA workflows awkward even on platforms that natively support
multisampled array textures.

Applications that want per-layer MSAA today must either:

* allocate a separate multisampled texture per layer
* resolve each layer early into a single-sampled array texture
* avoid custom resolve and per-sample shader reads entirely

These workarounds increase resource management complexity, make native API
interop harder, and block shader patterns that are already available in Vulkan,
D3D12, and Metal.

This proposal adds core WebGPU support that allows WebGPU to:

* create multisampled 2D array textures
* create multisampled `2d-array` texture views
* bind them in shaders as `texture_multisampled_2d_array<T>`

This proposal does not add layered rendering by itself. Outside of multiview or
another future layered-rendering feature, render attachments must still target a
single array layer per attachment view.

## Native API Availability

**Vulkan**:

* [`VkImageCreateInfo`](https://registry.khronos.org/vulkan/specs/latest/man/html/VkImageCreateInfo.html)
  supports 2D images with `arrayLayers > 1` and
  `samples != VK_SAMPLE_COUNT_1_BIT`
* [`VkImageViewCreateInfo`](https://registry.khronos.org/vulkan/specs/latest/man/html/VkImageViewCreateInfo.html)
  supports `VK_IMAGE_VIEW_TYPE_2D_ARRAY`
* SPIR-V supports multisampled array image types

**D3D12**:

* [`D3D12_RESOURCE_DESC`](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_resource_desc)
  covers multisampled array texture allocation
* [`Texture2DMSArray`](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/sm5-object-texture2dmsarray)
  and the broader
  [`Texture` type documentation](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-texture)
* SRV / RTV / DSV bindings for multisampled array textures are part of the
  D3D12 texture/view model

**Metal**:

* [`MTLTextureType.type2DMultisampleArray`](https://developer.apple.com/documentation/metal/mtltexturetype/type2dmultisamplearray)
* [Metal Shading Language Specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf)
  for `texture2d_ms_array<T>`

## WGSL

### Language Extension

Add a new WGSL language extension name.

| WGSL language extension | Description |
| --- | --- |
| `multisampled_array_textures` | Adds the `texture_multisampled_2d_array<T>` texture type for multisampled 2D array textures. |

A WGSL module may use a `requires multisampled_array_textures;` directive to
document that it depends on this language extension. The directive does not
enable the extension; the type is available when the implementation supports the
language extension.

### Texture Types

| Texture type | Description |
| --- | --- |
| `texture_multisampled_2d_array<T>` | Read-only multisampled 2D array texture. Matches the existing `texture_multisampled_2d<T>` semantics, with an explicit array layer in `textureLoad`. |

### Builtin Functions

Add overloads for:

* `textureLoad(t: texture_multisampled_2d_array<ST>, coords: vec2<C>, array_index: A, sample_index: S) -> vec4<ST>`
* `textureDimensions(t: texture_multisampled_2d_array<ST>) -> vec2<u32>`
* `textureNumLayers(t: texture_multisampled_2d_array<ST>) -> u32`
* `textureNumSamples(t: texture_multisampled_2d_array<ST>) -> u32`

### Example usage

```wgsl
requires multisampled_array_textures;

@group(0) @binding(0) var color_msaa : texture_multisampled_2d_array<f32>;

fn resolvePixel(coord : vec2<i32>, layer : i32) -> vec4f {
  var sum = vec4f(0.0);
  for (var sample = 0; sample < 4; sample++) {
    sum += textureLoad(color_msaa, coord, layer, sample);
  }
  return sum * 0.25;
}
```

## API

### Feature

No new `GPUFeatureName` is added. Multisampled array textures are part of core
WebGPU. The WGSL type is exposed through the `multisampled_array_textures` WGSL
language extension.

### Limits

No new limits are required.

Existing limits such as `maxTextureArrayLayers` and existing sample-count
validation continue to apply.

### Texture Creation

`GPUDevice.createTexture()` may create a multisampled 2D texture with more than
one array layer.

No new fields are added. The change is to validation and allowed combinations:

* `dimension` must remain `"2d"`
* `sampleCount > 1` may be combined with `size.depthOrArrayLayers > 1`

### Texture Views

* a multisampled 2D array texture may create `dimension: "2d"` views selecting
  a single array layer
* a multisampled 2D array texture may create `dimension: "2d-array"` views

### Binding Model

* `GPUTextureBindingLayout.multisampled == true` may be used with
  `viewDimension: "2d-array"`
* WGSL shaders may declare `texture_multisampled_2d_array<T>` when the
  implementation supports the `multisampled_array_textures` WGSL language
  extension

### Behavior

* Multisampled array textures are valid resources for both render-target
  allocation and shader reads.
* Render attachments outside multiview still use one layer per attachment view.
* Resolve targets remain single-sampled and follow the existing array-view
  rules of the enclosing render pass.
* This feature composes naturally with multiview, but does not depend on it.
* No additional validation is needed for multisampled-array textures when
  multiview is also enabled.
* `GPUTextureUsage.TRANSIENT_ATTACHMENT` may be used with multisampled array
  textures. Transient attachment usage remains a hint; implementations may
  still allocate backing storage.

### Validation

* multisampled textures may have `depthOrArrayLayers > 1`
* multisampled texture views may be either `"2d"` or `"2d-array"`
* multisampled texture bindings may use `viewDimension: "2d-array"`
* `texture_multisampled_2d_array<T>` is valid when the implementation supports
  the `multisampled_array_textures` WGSL language extension

In compatibility mode:

* `GPUDevice.createTexture()` rejects multisampled textures with
  `depthOrArrayLayers > 1`
* `GPUDevice.createBindGroupLayout()` rejects
  `GPUTextureBindingLayout.multisampled == true` with
  `viewDimension: "2d-array"`

## Example usage

```js
const adapter = await navigator.gpu.requestAdapter();
if (!adapter) {
  throw new Error("WebGPU is not supported");
}

const device = await adapter.requestDevice();

const texture = device.createTexture({
  size: { width: 1024, height: 1024, depthOrArrayLayers: 2 },
  sampleCount: 4,
  format: "rgba8unorm",
  usage:
      GPUTextureUsage.RENDER_ATTACHMENT |
      GPUTextureUsage.TEXTURE_BINDING,
});

const arrayView = texture.createView({
  dimension: "2d-array",
});

const layer0View = texture.createView({
  dimension: "2d",
  baseArrayLayer: 0,
  arrayLayerCount: 1,
});
```

## Resources

* https://registry.khronos.org/vulkan/specs/latest/man/html/VkImageCreateInfo.html
* https://registry.khronos.org/vulkan/specs/latest/man/html/VkImageViewCreateInfo.html
* https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_resource_desc
* https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/texture2dmsarray
* https://developer.apple.com/documentation/metal/mtltexturetype/type2dmultisamplearray
* https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf
