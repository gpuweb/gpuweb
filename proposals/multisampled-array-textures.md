# Multisampled Array Textures

* Status: [Draft](README.md#status-draft)
* Created: 2026-04-30
* Issue: TBD

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

This proposal adds an opt-in feature that allows WebGPU to:

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

### Enable Extension

Add a new enable extension.

| Enable | Description |
| --- | --- |
| `multisampled_array_textures` | Adds the `texture_multisampled_2d_array<T>` texture type for multisampled 2D array textures. |

### Texture Types

| Texture type | Description |
| --- | --- |
| `texture_multisampled_2d_array<T>` | Read-only multisampled 2D array texture. Matches the existing `texture_multisampled_2d<T>` semantics, with an explicit array layer in `textureLoad`. |

### Example usage

```wgsl
enable multisampled_array_textures;

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

Add a new feature name:

* `"multisampled-array-textures"`

### Limits

No new limits are required.

Existing limits such as `maxTextureArrayLayers` and existing sample-count
validation continue to apply.

### Texture Creation

When `"multisampled-array-textures"` is enabled, `GPUDevice.createTexture()`
may create a multisampled 2D texture with more than one array layer.

No new fields are added. The change is to validation and allowed combinations:

* `dimension` must remain `"2d"`
* `sampleCount > 1` may be combined with `size.depthOrArrayLayers > 1`

### Texture Views

When `"multisampled-array-textures"` is enabled:

* a multisampled 2D array texture may create `dimension: "2d"` views selecting
  a single array layer
* a multisampled 2D array texture may create `dimension: "2d-array"` views

### Binding Model

When `"multisampled-array-textures"` is enabled:

* `GPUTextureBindingLayout.multisampled == true` may be used with
  `viewDimension: "2d-array"`
* WGSL shaders may declare `texture_multisampled_2d_array<T>`

### Behavior

* If the feature is not enabled, current behavior is preserved.
* If the feature is enabled, multisampled array textures become valid resources
  for both render-target allocation and shader reads.
* Render attachments outside multiview still use one layer per attachment view.
* Resolve targets remain single-sampled and follow the existing array-view
  rules of the enclosing render pass.
* This feature composes naturally with multiview, but does not depend on it.

### Validation

Without `"multisampled-array-textures"`:

* multisampled textures must continue to have exactly one array layer
* multisampled texture views must continue to be `dimension: "2d"`

With `"multisampled-array-textures"`:

* multisampled textures may have `depthOrArrayLayers > 1`
* multisampled texture views may be either `"2d"` or `"2d-array"`
* multisampled texture bindings may use `viewDimension: "2d-array"`
* `texture_multisampled_2d_array<T>` is valid only when the WGSL extension is
  enabled

## Example usage

```js
const feature = "multisampled-array-textures";

const adapter = await navigator.gpu.requestAdapter();
if (!adapter || !adapter.features.has(feature)) {
  throw new Error("Multisampled array textures are not supported");
}

const device = await adapter.requestDevice({
  requiredFeatures: [feature],
});

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

## Open Questions

* Should `texture_multisampled_2d_array<T>` require a WGSL `enable` extension,
  or should the device feature alone make it available?
* Should this feature remain fully independent from multiview, or are there any
  layered-rendering interactions that should be specified together?
* Are there backends that support multisampled array render targets but not
  multisampled array texture reads, requiring finer-grained capability
  reporting?
* Do we need any additional validation around resolve targets when
  multisampled-array textures and multiview are both enabled?

## Resources

* https://registry.khronos.org/vulkan/specs/latest/man/html/VkImageCreateInfo.html
* https://registry.khronos.org/vulkan/specs/latest/man/html/VkImageViewCreateInfo.html
* https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_resource_desc
* https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/texture2dmsarray
* https://developer.apple.com/documentation/metal/mtltexturetype/type2dmultisamplearray
* https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf
