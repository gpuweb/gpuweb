# Variable Rasterization Rate

* Status: [Draft](README.md#status-draft)
* Created: 2026-05-27
* Issue: [#450](https://github.com/gpuweb/gpuweb/issues/450)

## Motivation

Variable rasterization rate lets an application vary the density of rasterization across a render
target. A common use case is foveated rendering: the application renders the region near the user's
gaze at full density and renders peripheral regions at lower density. This can reduce fragment
shader invocations and attachment traffic while keeping the highest quality in the most important
part of the image.

The feature is useful for XR, high-resolution displays, and other workloads where a uniform
one-fragment-per-pixel rate spends significant work in areas where the user is less sensitive to
detail.

This proposal uses the name "variable rasterization rate" because the intended portable behavior is
to change rasterization density. This is distinct from variable rate shading, which changes fragment
shading rate while preserving full-rate rasterization.

## Scope

This proposal adds an optional render pass attachment that provides a two-dimensional rasterization
density map. Each texel in the map controls the requested horizontal and vertical density for a tile
of the render target.

The initial proposal does not add:

* per-draw rasterization rate state
* per-primitive shader outputs such as `SV_ShadingRate`
* Vulkan-style shading rate palettes
* D3D12-style shading rate combiners
* WGSL built-ins or enable directives

Those features are related, but they are not equivalent to variable rasterization rate and are better
considered separately.

## Native API Availability

**Vulkan**:

* [`VK_EXT_fragment_density_map`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_fragment_density_map.html)
  exposes a render pass fragment density map attachment.
* [`VK_EXT_fragment_density_map2`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_fragment_density_map2.html)
  exposes additional capabilities, including dynamic density maps and non-subsampled image support.
* Fragment density map images use `VK_IMAGE_USAGE_FRAGMENT_DENSITY_MAP_BIT_EXT`.
* A fragment density map image contains normalized `(x, y)` float component values for framebuffer
  regions. Each component is in `(0.0, 1.0]`, with `1.0` meaning full density along that axis.
* Implementations use the density values as hints to optimize low-density regions. Vulkan also
  allows subpass color and depth attachments to be subsampled for further optimization.

**Metal**:

* [`MTLRasterizationRateMap`](https://developer.apple.com/documentation/metal/mtlrasterizationratemap)
  exposes rasterization rate maps through render pass descriptors.
* Metal represents the map using horizontal and vertical rate arrays rather than an arbitrary 2D
  texture. A Metal implementation may expose this WebGPU feature if it can translate the WebGPU map
  to the supported native representation, or if the WebGPU API is revised to use a separable map.

**D3D12**:

* D3D12 Variable Rate Shading controls shading rate, not rasterization rate. It preserves full-rate
  rasterization and writes the full framebuffer.
* D3D12 VRS is not considered a faithful implementation of this feature unless the specification
  explicitly allows a VRS approximation.

## API

### Feature

Add a new feature name:

```webidl
partial enum GPUFeatureName {
    "variable-rasterization-rate",
};
```

### Texture Usage

Add a new texture usage for rasterization rate map textures:

```webidl
partial namespace GPUTextureUsage {
    const GPUFlagsConstant VARIABLE_RASTERIZATION_RATE = 0x80;
};
```

The exact bit value is provisional and should be assigned with the rest of the WebGPU texture usage
bits.

### Limits

Add limits describing the supported size of the render-target region controlled by one map texel.

| Limit name | Type | Limit class | Default |
| --- | --- | --- | --- |
| `minVariableRasterizationRateTileWidth` | `GPUSize32` | minimum | 1 |
| `minVariableRasterizationRateTileHeight` | `GPUSize32` | minimum | 1 |
| `maxVariableRasterizationRateTileWidth` | `GPUSize32` | maximum | 1 |
| `maxVariableRasterizationRateTileHeight` | `GPUSize32` | maximum | 1 |

If `"variable-rasterization-rate"` is supported, the maximum tile dimensions must be at least the
minimum tile dimensions. A larger maximum allows a lower-resolution map to cover a larger render
target.

### Render Pass Descriptor

Add an optional rasterization rate map view to `GPURenderPassDescriptor`:

```webidl
partial dictionary GPURenderPassDescriptor {
    GPUTextureView? variableRasterizationRateMap = null;
};
```

If `variableRasterizationRateMap` is `null`, the render pass uses the normal full rasterization
rate.

## Rasterization Rate Map

The rasterization rate map is a 2D texture view whose first two color components contain normalized
`(x, y)` floating-point density values. The API should define the supported map formats separately
from the density-value semantics. A compact unsigned-normalized two-component format such as
`rg8unorm` is a plausible MVP baseline, but Vulkan's fragment density map model is described in
terms of normalized component values rather than as a requirement that WebGPU expose exactly that
format. Implementations may expose additional uncompressed, non-sRGB, two-or-more-component
unsigned-normalized or floating-point color formats if they are supported natively as rasterization
rate maps.

For each texel:

* the red channel is the requested horizontal rasterization density
* the green channel is the requested vertical rasterization density
* `1.0` requests full density
* values greater than `0.0` and less than `1.0` request lower density

Each map texel applies to a rectangular tile of the render pass. Given render pass dimensions
`renderWidth` and `renderHeight`, and map dimensions `mapWidth` and `mapHeight`:

```text
tileWidth = ceil(renderWidth / mapWidth)
tileHeight = ceil(renderHeight / mapHeight)
```

`tileWidth` and `tileHeight` must be within the device's variable rasterization rate tile size
limits.

Implementations may clamp or quantize the requested density to native supported rates. The map
values are hints: implementations may choose the effective rasterization density for correctness,
quality, security, or native API constraints. A component value of `0.0` is invalid as a fragment
density value; implementations must reject, sanitize, clamp, or otherwise avoid passing invalid zero
density values to native APIs.

## Validation

If `descriptor.variableRasterizationRateMap` is not `null`:

* The `"variable-rasterization-rate"` feature must be enabled on the device.
* `descriptor.variableRasterizationRateMap` must be a valid `GPUTextureView`.
* The texture view's format must be a supported rasterization rate map format with at least two
  uncompressed, non-sRGB, unsigned-normalized or floating-point color components.
* The texture view's texture usage must include `GPUTextureUsage.VARIABLE_RASTERIZATION_RATE`.
* The texture view must reference exactly one mip level.
* The texture view's texture sample count must be `1`.
* The texture view dimension must be `"2d"` for a single-view render pass.
* The texture view's map tile size must be within the device limits described above.
* The texture subresource used as the map must not overlap any color, depth/stencil, or resolve
  attachment in the same render pass.
* The texture subresource used as the map must not be used for another purpose in the same render
  pass.

When this proposal is combined with multi-view rendering:

* If the render pass `viewCount` is `1`, a `"2d"` map view is used for the single view.
* If the render pass `viewCount` is greater than `1`, the map view must be a `"2d-array"` view with
  `arrayLayerCount == viewCount`; array layer `i` controls view `i`.

## Behavior

Variable rasterization rate affects the density of rasterization and fragment processing within the
render pass. It may reduce the number of fragment shader invocations and may cause one fragment
shader result to cover multiple framebuffer pixels. It does not change the logical render target
dimensions.

Existing shader inputs and outputs keep their existing meanings:

* `@builtin(position)` is still expressed in framebuffer coordinates.
* Fragment shader derivatives are computed using the implementation's effective rasterization rate.
* Depth, stencil, blending, and attachment stores apply to the covered framebuffer pixels according
  to the effective rasterization rate.

The map is read-only for the duration of the render pass. Its contents are consumed at render pass
execution time. Implementations that cannot read a GPU-produced map at render pass execution time
must either avoid exposing this feature, restrict the allowed usages, or insert implementation
workarounds that preserve the specified behavior.

## WGSL

No WGSL changes are required.

This proposal intentionally avoids adding a shader-visible rate built-in in the initial version. A
future extension could expose the effective rasterization rate or tile information if applications
need it.

## JavaScript Example

```js
const adapter = await navigator.gpu.requestAdapter();
if (!adapter.features.has("variable-rasterization-rate")) {
  throw new Error("Variable rasterization rate is not available");
}

const device = await adapter.requestDevice({
  requiredFeatures: ["variable-rasterization-rate"],
});

const rateMap = device.createTexture({
  size: [64, 64],
  format: "rg8unorm",
  usage:
    GPUTextureUsage.COPY_DST |
    GPUTextureUsage.TEXTURE_BINDING |
    GPUTextureUsage.VARIABLE_RASTERIZATION_RATE,
});

// Upload an rg8unorm map. Red and green values of 255 request full density.
// Lower non-zero values request lower horizontal or vertical density.
device.queue.writeTexture(
  { texture: rateMap },
  rateMapData,
  { bytesPerRow: 64 * 2 },
  [64, 64],
);

const pass = encoder.beginRenderPass({
  colorAttachments: [{
    view: colorTexture.createView(),
    loadOp: "clear",
    storeOp: "store",
    clearValue: [0, 0, 0, 1],
  }],
  variableRasterizationRateMap: rateMap.createView(),
});
```

## Security and Robustness

The map contents are ordinary texture data and cannot be fully validated at API call time.
Implementations must sanitize, clamp, or otherwise safely handle map values that are not accepted by
the native backend. Invalid map contents must not cause undefined behavior, memory disclosure, or
device loss.

Because variable rasterization rate changes rendering quality and can affect timing, applications
should treat it as an optional performance feature. User agents may clamp requested rates upward or
disable the feature in contexts where exposing it is not appropriate.

## Open Questions

* Should the WebGPU API expose a full 2D texture map, as proposed here, or a separable horizontal and
  vertical map that more closely matches Metal?
* Should WebGPU require one MVP map format such as `rg8unorm`, or should adapters expose a set of
  supported rasterization rate map formats?
* Should GPU-generated maps in the same command buffer be required? On Vulkan this likely requires
  `fragmentDensityMapDynamic` or an implementation workaround.
* What exact robustness behavior should be required for `0.0` map values, which are outside the
  native Vulkan fragment density value range?
* Should render target restrictions from Vulkan subsampled images be exposed to applications, or
  must implementations hide them by requiring native non-subsampled image support or using internal
  intermediate images?
* Should D3D12 VRS be allowed as an approximation, or should VRS remain a separate WebGPU feature?
* How should render bundles declare compatibility with render passes that use a rasterization rate
  map?

## Resources

* https://github.com/gpuweb/gpuweb/issues/450
* https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_fragment_density_map.html
* https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_fragment_density_map2.html
* https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_fragment_shading_rate.html
* https://developer.apple.com/documentation/metal/mtlrasterizationratemap
* https://learn.microsoft.com/en-us/windows/win32/direct3d12/vrs
* https://github.com/KhronosGroup/Vulkan-Samples/tree/main/samples/extensions/fragment_density_map
