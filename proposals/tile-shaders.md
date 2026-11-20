# Tile Shaders

* Status: [Draft](README.md#status-draft)
* Created: 2026-11-02
* Issue: [#11086](https://github.com/gpuweb/gpuweb/issues/11086)
* Point of contact: Mike Wyrzykowski (mwyrzykowski)

## Summary

This proposal adds an optional **tile shader** stage to WebGPU render passes. A tile shader is a compute-like kernel that is dispatched once per implementation-defined region (a "tile", for example NxM pixels) of the render target, instead of once per fragment. It runs at a specified point in the render pass, after the preceding draws have completed, and can read and write the per-pixel state of its region.

This allows algorithms that today require multiple passes and extra device-memory-resident buffers (order-independent transparency, deferred lighting / G-buffers, custom MSAA resolve, programmable blending, depth peeling, etc.) to instead be expressed as a single render pass that keeps its intermediate per-pixel state local to the pass, where the hardware allows, reducing the associated bandwidth and extra pass overhead.

## Problem / Motivation

WebGPU render passes currently model the framebuffer purely as a set of textures. Every fragment shader invocation writes its output through the fixed-function blend stage, and there is no way for:

- A fragment shader to read back arbitrary per-pixel intermediate state that other draws wrote earlier in the same pass (beyond fixed blending), without first ending the pass and starting a new one that samples/loads a device-memory texture.
- Any shader to run "per tile" rather than "per fragment" or "per compute workgroup", to do bulk per-pixel work (sort, resolve, composite) once all relevant draws for a region of the framebuffer have completed, without that data making a round trip through device memory.

Some GPU architectures can keep per-pixel state in fast local storage while a region of the framebuffer is being rendered. WebGPU already partially acknowledges this via limits like `maxColorAttachmentBytesPerSample`, but currently gives applications no way to *use* that storage for anything beyond ordinary attachment storage + fixed blending.

Several common rendering techniques are naturally expressed as "accumulate per-pixel data across draws, then run a resolve step per pixel/tile", and today have to be implemented either:
- With multiple passes and device-memory-resident intermediate buffers (e.g. classic A-buffer OIT, deferred shading G-buffers), which costs bandwidth and pass-switch overhead, or
- Not at all, if they rely on ordering guarantees within a tile that a portable multi-pass emulation can't easily provide.

## Background: Tile shading concepts

This proposal builds on three concepts:

- **Custom per-pixel render pass state (imageblocks)**: a render pipeline can declare a custom per-pixel data layout (an "imageblock") that persists for the duration of a render pass, in addition to (or instead of) the normal color/depth attachments. Fragment shaders can read and write their pixel's slot.
- **Ordered per-pixel access (raster order groups)**: a way to serialize read-modify-write access to per-pixel state across fragment invocations that land on the same pixel (e.g. from overlapping triangles), so that per-pixel accumulation is well-defined.
- **Per-region compute-like stage (tile shaders)**: a pipeline stage that is dispatched once per region of the render target, with one thread (or a small fixed group of threads) per pixel in the region, rather than per vertex or fragment of a draw call. It runs interleaved with render commands in the same pass (e.g. to initialize per-pixel state before the first draw, or to sort and composite accumulated fragments after the last relevant draw) and can read and write the per-pixel state and the attachments directly.

## Implementation details across platforms

- **D3D12**: no on-chip tile-memory feature. The semantics can be expressed using **Rasterizer Ordered Views (ROVs)** in fragment shaders for the ordered per-pixel accumulation, plus a **compute shader** for the tile-shader resolve step, backed by a device-memory per-pixel buffer. Requires ROV support; unsupported on adapters lacking it. See "Implementing the semantics on D3D12" below for an example mapping.
- **GL/GLES / Compatibility mode**: available only where an interlock equivalent exists; otherwise `"tile-shaders"` is unsupported.
- **Metal**: provides native tile memory, imageblocks, and raster order groups.
- **Vulkan**: no single direct equivalent, but related pieces exist. `VK_EXT_shader_tile_image` lets fragment shaders read the current tile's attachment values directly (more similar to "programmable blending" than to a general tile-shader stage). `VK_EXT_fragment_shader_interlock` provides a pixel-ordered critical section that can be used in place of ROVs to approximate raster order groups, following a similar strategy to D3D12. `VK_HUAWEI_subpass_shading` provides a compute-like shader that runs over subpass/tile data, most similar in function to tile shaders, but is vendor-specific.

Applications targeting broad hardware support are expected to feature-detect and fall back to a conventional multi-pass technique (e.g. a device-memory A-buffer for OIT) when `"tile-shaders"` is unavailable, the same way they already branch on other optional features today.

## Implementing the semantics on D3D12

Here is an example mapping illustrating one way the feature could be expressed there using existing functionality. The strategy is: **imageblock -> device-memory per-pixel buffer indexed by pixel coordinate; raster order group -> Rasterizer Ordered View; tile shader dispatch -> a compute pass reading that buffer.**

### 1. Imageblock storage

The per-pixel struct in the `imageblock` address space could be lowered to a structured buffer sized `width * height * bytesPerPixel`, indexed by `pixelIndex = y * width + x`. On D3D12 this would be a UAV over a structured buffer:

```hlsl
struct OITFragment { float4 color; float depth; };
struct OITImageblock { uint count; OITFragment fragments[8]; };

// Declared as a Rasterizer Ordered UAV so that per-pixel read-modify-write
// from overlapping fragments is serialized in primitive order.
RasterizerOrderedStructuredBuffer<OITImageblock> ImageblockBuffer : register(u0);
```

### 2. Raster order group -> Rasterizer Ordered View

The `@raster_order_group(n)` attribute maps onto the `RasterizerOrdered*` resource types. Any fragment shader that touches the imageblock would be compiled with the ordered UAV, which is intended to provide the "fragments landing on the same pixel are serialized in draw order" behavior that Metal's raster order groups provide:

```hlsl
// Lowered from `@fragment fn fs_accumulate(...)`
void fs_accumulate(float4 pos : SV_Position, FragIn in) {
  uint idx = uint(pos.y) * FramebufferWidth + uint(pos.x);
  // ROV is intended to order this read-modify-write across overlapping frags.
  uint n = ImageblockBuffer[idx].count;
  if (n < 8) {
    ImageblockBuffer[idx].fragments[n].color = shade(in);
    ImageblockBuffer[idx].fragments[n].depth = pos.z;
    ImageblockBuffer[idx].count = n + 1;
  }
}
```

### 3. Tile shader dispatch -> compute pass

`dispatchTileShader()` could be lowered to a compute dispatch over the framebuffer once the accumulating draws have completed. The implicit barrier the API inserts would become a UAV barrier between the render draws and the compute dispatch:

```hlsl
// Lowered from `@tile fn ts_resolve(...)`
RWStructuredBuffer<OITImageblock> ImageblockBuffer : register(u0);
RWTexture2D<float4> ColorTarget : register(u1);

[numthreads(8, 8, 1)]
void ts_resolve(uint2 pixel : SV_DispatchThreadID) {
  if (any(pixel >= FramebufferSize)) return;
  uint idx = pixel.y * FramebufferWidth + pixel.x;
  OITImageblock ib = ImageblockBuffer[idx];
  // sort ib.fragments[0..ib.count] by depth, blend back-to-front...
  float4 color = 0;
  for (uint i = 0; i < ib.count; ++i)
    color = blend(color, ib.fragments[i].color);
  ColorTarget[pixel] = color;
}
```

### 4. Command-stream lowering

An implementation could record this within a single WebGPU render pass as follows:
- On `beginRenderPass` with an `imageblock` layout, allocate (or recycle from a per-device pool) the backing structured buffer and, if `loadOp`-like initialization is requested, clear it.
- Draws using imageblock-writing pipelines bind it as a Rasterizer Ordered UAV.
- `dispatchTileShader()` ends the current render sub-pass, inserts a UAV barrier, records the compute dispatch, and (if the tile shader writes attachments) copies/leaves results in the color target. On D3D12 this would mean splitting what the app sees as one render pass into a render segment + compute segment internally.
- On `endRenderPass`, the backing buffer is returned to the pool.

### Caveats of the D3D12 path

- **ROV availability**: Rasterizer Ordered Views require the ROV capability, which is a hardware feature tier and not guaranteed on every D3D12 adapter WebGPU may run on. Adapters without ROVs may not be able to provide the ordering guarantee.
- **Memory and bandwidth**: the backing buffer is `width * height * bytesPerPixel` in device memory. At 3840x2160 with a 40-byte imageblock that is ~330 MB, versus little or no device memory with native support. This is the fundamental performance-portability gap.
- **No local-storage residency**: the emulation does not provide the bandwidth-saving benefit of the feature; it is intended to produce equivalent results but is not performance-representative.

A similar approach may apply to desktop Vulkan (`VK_EXT_fragment_shader_interlock` in place of ROVs) and to GL/GLES where an interlock equivalent exists.

## Optional feature

This proposal frames tile shaders as an **optional** feature, for three reasons:

1. **The ordering guarantee is not universally available.** Correct raster-order-group behavior depends on ROVs (D3D12), `VK_EXT_fragment_shader_interlock` (Vulkan), or a tile-image / interlock equivalent. These are not present on all adapters WebGPU targets, particularly in the GLES 3.1-class baseline and Compatibility mode. Mandating the feature would require conformance on hardware that may not be able to provide it.
2. **The performance cliff is invisible to applications.** With native support, imageblock storage can stay local to the pass at little or no device-memory cost; on an emulated path it is hundreds of MB of device memory and full bandwidth. If the feature were always present, an application would have no signal distinguishing the fast path from a large memory/bandwidth regression. Keeping it optional (and feature-detected) makes that tradeoff explicit, consistent with how WebGPU already gates features with performance cliffs such as `timestamp-query` and `shader-f16`.
3. **Memory budget on low-end devices.** The `width * height * bytesPerPixel` backing allocation can exceed the budget of the weak devices in WebGPU's baseline, so mandating it may not be viable there.

## Proposed API sketch

### New device limits

```
maxImageblockBytesPerPixel: 64   // example default; imageblock storage
                                  // consumed per pixel by a render pipeline
maxTileShaderWorkgroupSize: ...  // max threads per tile-shader dispatch
```

### New optional feature

```js
const adapter = await navigator.gpu.requestAdapter();
if (adapter.features.has('tile-shaders')) {
  device = await adapter.requestDevice({ requiredFeatures: ['tile-shaders'] });
}
```

### WGSL: imageblock address space

A new address space, `imageblock`, for per-pixel structured data that persists for the life of a render pass and is addressed implicitly by the current fragment's / tile-shader-invocation's pixel position:

```wgsl
struct OITFragment {
  color: vec4<f32>,
  depth: f32,
}

struct OITImageblock {
  count: u32,
  fragments: array<OITFragment, 8>,
}

var<imageblock> oit_data: OITImageblock;
```

Fragment shaders and tile shaders sharing the same imageblock layout can read/write `oit_data` for "their" pixel. Because multiple fragment invocations (from overlapping triangles) may target the same pixel in the same tile, a `@raster_order_group(n)` attribute is proposed to make read-modify-write ordering well-defined:

```wgsl
@raster_order_group(0) var<imageblock> oit_data: OITImageblock;

@fragment
fn fs_accumulate(@builtin(position) pos: vec4<f32>, in: FragIn) {
  let c = shade(in);
  let n = oit_data.count;
  if (n < 8u) {
    oit_data.fragments[n] = OITFragment(c, pos.z);
    oit_data.count = n + 1u;
  }
}
```

### WGSL: tile shader stage

A new shader stage attribute, `@tile`, for entry points dispatched once per tile with a fixed number of invocations (typically one per pixel in the tile):

```wgsl
@raster_order_group(0) var<imageblock> oit_data: OITImageblock;

@tile @workgroup_size(1)
fn ts_resolve(@builtin(tile_position) pixel: vec2<u32>) -> @location(0) vec4<f32> {
  var frags = oit_data.fragments;
  // sort `frags[0..oit_data.count]` by depth (back to front)...
  var color = vec4<f32>(0.0);
  for (var i = 0u; i < oit_data.count; i = i + 1u) {
    color = blend(color, frags[i].color);
  }
  return color;
}
```

### JS API: pipeline and encoder additions

```js
// Render pipeline gains an optional imageblock layout description.
const pipeline = device.createRenderPipeline({
  layout: pipelineLayout,
  vertex: { module, entryPoint: 'vs_main' },
  fragment: {
    module,
    entryPoint: 'fs_accumulate',
    targets: [{ format: 'bgra8unorm' }],
  },
  imageblock: {
    // mirrors the WGSL struct layout used by `var<imageblock>` declarations
    bytesPerPixel: 40,
  },
});

// A separate tile-shader pipeline, sharing the render pass's imageblock.
const tileShaderPipeline = device.createTileShaderPipeline({
  layout: pipelineLayout,
  tile: { module, entryPoint: 'ts_resolve' },
  imageblock: { bytesPerPixel: 40 },
});

const pass = encoder.beginRenderPass({
  colorAttachments: [{ view, loadOp: 'clear', storeOp: 'store' }],
  imageblock: { bytesPerPixel: 40 }, // reserve imageblock storage for the pass
});

pass.setPipeline(opaquePipeline);
// ... draw opaque geometry ...

pass.setPipeline(oitAccumulatePipeline);
// ... draw transparent geometry, accumulating into imageblock ...

// New: dispatch a tile shader over the current render pass's tiles.
pass.dispatchTileShader(tileShaderPipeline);

pass.end();
```

`dispatchTileShader()` would be validated to only run within a render pass that declared a compatible `imageblock` layout, and would insert an implicit barrier ensuring all preceding draws in the pass have completed their imageblock writes before the tile shader reads them. On immediate-mode backends this barrier could lower to a UAV barrier between the render draws and the emulating compute dispatch (see "Implementing the semantics on D3D12").

## References

- [WebGPU specification](https://www.w3.org/TR/webgpu/)
- D3D12: [Rasterizer Order Views](https://learn.microsoft.com/en-us/windows/win32/direct3d12/rasterizer-ordered-views)
- [Metal: Tile shaders and resource preparation commands](https://developer.apple.com/documentation/metal/tile-shaders-resource-preparation-commands)
- [Metal: Implementing order-independent transparency with image blocks](https://developer.apple.com/documentation/metal/implementing-order-independent-transparency-with-image-blocks)
- Vulkan: [VK_EXT_fragment_shader_interlock](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_EXT_fragment_shader_interlock.html)
- Vulkan: [VK_EXT_shader_tile_image](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_EXT_shader_tile_image.html)
- Vulkan: [VK_HUAWEI_subpass_shading](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_HUAWEI_subpass_shading.html)
