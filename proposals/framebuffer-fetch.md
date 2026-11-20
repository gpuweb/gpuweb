# Framebuffer Fetch

* Status: [Draft](README.md#status-draft)
* Created: 2026-11-04
* Issue: [#11089](https://github.com/gpuweb/gpuweb/issues/11089)
* Point of contact: Mike Wyrzykowski (mwyrzykowski)

## Summary

This proposal adds **framebuffer fetch** to WebGPU render passes: a fragment shader can read the current value of a color attachment at the location of its own fragment. It is the smallest useful subset of the [tile-shaders](tile-shaders.md) proposal and is modeled on Vulkan's [`VK_EXT_shader_tile_image`](https://docs.vulkan.org/features/latest/features/proposals/VK_EXT_shader_tile_image.html). There are no custom per-pixel layouts, no new shader stage, no new commands and no new resource types: what is read is the color attachment itself.

It has two parts, and only the second is optional hardware functionality:

- **Framebuffer fetch**, a WGSL language extension (`framebuffer_fetch`) with no device feature: a fragment shader reads a color attachment that its draw does not write. On D3D12 this needs nothing beyond an ordinary texture read and a resource transition, so it could reasonably be supported on any WebGPU implementation, which is what WGSL language extensions are for.
- `"framebuffer-fetch-coherent"`, an optional device feature: a fragment shader also writes the attachment it reads, for example to implement a custom blend, and each read observes the writes of all earlier fragments on that pixel in primitive order. On D3D12 this maps to Rasterizer Ordered Views (ROVs), which not every adapter supports.

On tile-based GPUs the reads are served from on-chip tile memory, and with `TRANSIENT_ATTACHMENT` textures an intermediate attachment such as a G-buffer never has to be written to memory. On other GPUs the results are identical but there is no on-chip benefit.

## Motivation

A render pass cannot currently read back anything it produced earlier in the same pass, other than through fixed-function blending. To use an attachment's contents, an application has to end the pass (storing the attachment), begin a new pass, and sample the texture. On tile-based GPUs this forces the data out of tile memory and back in, costs bandwidth and memory, and adds a pass boundary.

- **Deferred shading**: write a G-buffer with one set of draws and light it with the next draws of the same pass. With `TRANSIENT_ATTACHMENT` textures the G-buffer can stay entirely on-chip.
- **Programmable blending** (`"framebuffer-fetch-coherent"`): blend modes that fixed-function blending cannot express (overlay, soft light, custom tone mapping applied on store) in a single draw.
- **Multi-input passes**: read several attachments and write one, such as compositing or post-processing steps, without leaving the render pass.

The [tile-shaders](tile-shaders.md) proposal covers these and more, but its imageblock and tile shader concepts map natively only to Metal; on other APIs they require emulation with large device-memory buffers and compute passes (see the D3D12 section of that proposal). Reading the current attachment value exists in every major graphics API in some form (Metal `[[color(n)]]`, Vulkan `VK_EXT_shader_tile_image` and input attachments, GLES framebuffer fetch, D3D12 SRVs and ROVs), so it is the part of tile shading that can be specified portably first. It is also a building block for the rest: a later proposal can add more on top of framebuffer fetch without changing what is specified here.

## Background: Vulkan's tile images

Framebuffer fetch is the name used by OpenGL ES (`GL_EXT_shader_framebuffer_fetch`) and by Dawn's experimental implementation. The Vulkan proposal for `VK_EXT_shader_tile_image` describes the same capability in terms of the *tile image*: the framebuffer is logically divided into tiles, and a tile image is a view of a framebuffer attachment restricted to the tile being processed. For GPUs that support it, it replaces many uses of subpasses, which are not available with Vulkan's dynamic rendering. It is deliberately narrow:

- A fragment shader only reads its own location, never a neighborhood or the whole tile.
- The tile image has the attachment's format. There is no reinterpretation, no additional storage and no descriptors; the shader names the attachment by its color attachment index.
- Output is still written through ordinary fragment outputs.
- Color reads are in rasterization order (coherent).
- Depth and stencil reads are separate feature bits, and an optional non-coherent mode with explicit barriers is described separately.

WebGPU has no subpasses either, so the same concept fills the same gap here.

## What is kept and what is left out

| Capability | `VK_EXT_shader_tile_image` | This proposal |
| --- | --- | --- |
| Read a color attachment at the fragment's own location | Yes (`shaderTileImageColorReadAccess`, always available with the extension) | Yes: the `framebuffer_fetch` language extension, for attachments the draw does not write |
| Read an attachment in rasterization order while writing it | Yes (color reads are coherent) | Yes, as a separate optional feature: `"framebuffer-fetch-coherent"` |
| Fixed-function blending on a fetched attachment | Works as normal | Not allowed on attachments that are read |
| Depth and stencil reads | Yes (`shaderTileImageDepthReadAccess`, `shaderTileImageStencilReadAccess`) | No |
| Multisampled attachments (`sample` operand) | Yes | No, single-sampled only |
| Non-coherent reads with explicit barriers | Optional mode (section 6 of the Vulkan proposal) | No |
| Format reinterpretation, access beyond the fragment's own pixel | Left to future extensions | No (see [tile-shaders](tile-shaders.md)) |

## Implementation details across platforms

- **Metal**: native on Apple GPUs, which support programmable blending: `[[color(n)]]` fragment function inputs read the current value of color attachment `n` and cover both parts, and reads of memoryless (`TRANSIENT_ATTACHMENT`) attachments come from tile memory. Intel and AMD Mac GPUs do not support programmable blending (Apple's feature set tables list it only for Apple GPU families). For framebuffer fetch there, an implementation can sample the attachment as a texture and insert the render-target memory barrier (`memoryBarrier(scope: .renderTargets, ...)`, macOS only and not supported by Apple GPUs) between the draws that write it and the draws that read it. `"framebuffer-fetch-coherent"` there would need a raster order group on a read-write texture, which is a per-device capability (`rasterOrderGroupsSupported`).
- **Vulkan**: `VK_EXT_shader_tile_image` is the direct counterpart: per its proposal, color read access is mandatory in the extension, reads are in rasterization order, and no descriptors are needed. Without it, `VK_KHR_dynamic_rendering_local_read` (core in Vulkan 1.4) provides input attachment reads inside dynamic rendering for framebuffer fetch, and subpass input attachments, which every Vulkan implementation has, can serve older drivers. `VK_EXT_rasterization_order_attachment_access` or `VK_EXT_fragment_shader_interlock` can provide `"framebuffer-fetch-coherent"`; the interlock path follows the D3D12 ROV strategy below.
- **D3D12**: no native framebuffer fetch, but both parts can be expressed with existing functionality and without additional memory: framebuffer fetch works on every adapter, and `"framebuffer-fetch-coherent"` needs ROVs. See "Implementing the semantics on D3D12" below.
- **GL/GLES / Compatibility mode**: `GL_EXT_shader_framebuffer_fetch` provides both parts and `GL_EXT_shader_framebuffer_fetch_non_coherent` provides the base part. This draft does not support either in Compatibility mode, and rejects `@color` inputs at pipeline creation there, like the existing Compatibility mode restriction on `dpdxFine`. The reason is that Compatibility mode requires all color targets to share one `writeMask`, which conflicts with reading one attachment (`writeMask: 0`) while writing another.

Applications detect framebuffer fetch with `navigator.gpu.wgslLanguageFeatures.has('framebuffer_fetch')` plus a check that the device is not in Compatibility mode (`device.features.has('core-features-and-limits')`), and detect `"framebuffer-fetch-coherent"` like any other feature. Without them, applications fall back to a conventional multi-pass technique: end the pass and sample the attachment in the next one.

## Implementing the semantics on D3D12

The strategy is: **framebuffer fetch -> read the attachment through an SRV; `"framebuffer-fetch-coherent"` -> access the attachment through a Rasterizer Ordered View.** Both use the application's own attachment texture, so unlike the imageblock mapping in [tile-shaders](tile-shaders.md) there is no `width * height * bytesPerPixel` side buffer, no compute pass and no splitting of the render pass.

### Framebuffer fetch: SRV

For a draw whose pipeline has `@color(n)` inputs and `writeMask: 0` for those targets:

- The pipeline state has no render target in slot `n`, and the attachment texture is transitioned to `D3D12_RESOURCE_STATE_PIXEL_SHADER_RESOURCE` and bound as an SRV for the draw. Nothing writes the attachment during the draw, so the read cannot race with the output merger.
- `@color(n)` lowers to a load at the fragment's pixel. The transition between draws that write the attachment and draws that read it also provides the ordering and visibility, so applications write no barriers.

```hlsl
// Lowered from `@color(0) albedo: vec4f`; attachment 0 is not written by this draw.
Texture2D<float4> FramebufferFetch0 : register(t0);

float4 fs_light(float4 pos : SV_Position) : SV_Target2 {
  float4 albedo = FramebufferFetch0.Load(int3(int2(pos.xy), 0));
  // ...
}
```

This path needs no optional D3D12 capability: no ROVs, no UAV-capable texture and no typed UAV format support. Any renderable color format works, and sRGB attachments decode on read as for any texture.

### `"framebuffer-fetch-coherent"`: ROV

For a draw that both reads and writes attachment `n`:

- The attachment is bound as a UAV and declared as a `RasterizerOrdered*` resource instead of being bound as a render target. `@color(n)` lowers to a load at the start of the shader and the `@location(n)` output to a store at the end (merged with the loaded value when `writeMask` is partial).
- Per the [D3D ROV documentation](https://learn.microsoft.com/en-us/windows/win32/direct3d11/rasterizer-order-views), ROVs "guarantee the order of UAV accesses for any pair of overlapping pixel shader invocations", in the order the geometry was submitted: a read "must reflect writes by a previous invocation and must not reflect writes by a subsequent invocation". That is the coherent framebuffer fetch.

```hlsl
// Lowered from `@color(0) dst: vec4f` and `@location(0)`; attachment 0 is read and written.
RasterizerOrderedTexture2D<float4> FramebufferFetch0 : register(u0);

[earlydepthstencil]
void fs_overlay(float4 pos : SV_Position, float2 uv : TEXCOORD0) {
  uint2 pixel = uint2(pos.xy);
  float4 dst = FramebufferFetch0[pixel];
  float4 result = /* body of fs_overlay */;
  FramebufferFetch0[pixel] = result;
}
```

### Caveats of the D3D12 path

- **Availability**: the ROV path needs `ROVsSupported` and typed UAV loads and stores for the attachment's format (`TypedUAVLoadAdditionalFormats` for formats beyond the 32-bit single-channel ones), which is the set of formats with `"read-write"` storage texture access. Typed UAVs cannot use sRGB formats. Adapters without ROVs do not expose `"framebuffer-fetch-coherent"` but support framebuffer fetch like any other adapter.
- **No fixed-function output merger for that attachment**: it is a UAV, not a render target, so blending and write masks are not applied by the hardware. This is why a read target must not have a `blend` state, and why the implementation applies `writeMask` itself.
- **Depth/stencil tests**: UAV writes are performed by the shader, so to keep fragments that fail the depth/stencil tests from writing, the shader is compiled with early depth/stencil testing. That cannot honor `discard`, `frag_depth` or `sample_mask`, so those are not allowed in a fragment shader of a pipeline that writes an attachment it reads (see "Pipeline validation").
- **Single-sampled only**: ROV resource types exist for buffers and for 1D, 2D (including arrays) and 3D textures, but not for multisampled textures.
- **Ordering across draws**: the ROV guarantee is stated for invocations "generated by the same draw calls", so the implementation separates draws that touch the same attachment with a UAV barrier.
- **Performance**: there is no on-chip storage; the attachment lives in device memory like any texture. ROVs serialize overlapping fragments, so the cost grows with overdraw (as with ROV-based order-independent transparency). Framebuffer fetch costs a transition between writing and reading draws, which is comparable to the pass boundary the fallback would use. The results are identical to those of native tile-based implementations but not performance-representative.

## Proposed API changes

### Features

Framebuffer fetch needs no device feature; see "WGSL" below. There is one new `GPUFeatureName`:

- `"framebuffer-fetch-coherent"`: allows a pipeline to write a color target that it reads through `@color`.

```js
const adapter = await navigator.gpu.requestAdapter();
if (adapter.features.has('framebuffer-fetch-coherent')) {
  device = await adapter.requestDevice({ requiredFeatures: ['framebuffer-fetch-coherent'] });
}
```

### WGSL

A new language extension, `framebuffer_fetch`, which is available automatically if the implementation supports it and is listed in `navigator.gpu.wgslLanguageFeatures`. A `requires framebuffer_fetch;` directive documents the use and makes shader creation fail on implementations without it:

| WGSL language extension | Description |
| --- | --- |
| `framebuffer_fetch` | Adds the `@color(n)` fragment shader input attribute, which reads a color attachment at the fragment's own location. |

A new attribute, `@color(n)`, valid on a parameter of a `@fragment` entry point or on a member of a structure-typed parameter, like `@location`:

- `n` is a non-negative `const-expression` of type `i32` or `u32` and names the color attachment (the `GPUFragmentState.targets` index) to read. Each `n` can be used at most once per entry point.
- The type must be `vec4<f32>`, `vec4<i32>` or `vec4<u32>`, matching the sample type of the target's format. Components that the format does not have read as 0 (green, blue) and 1 (alpha), as for `textureLoad`.
- `@color` inputs do not count against `maxInterStageShaderVariables`.
- The value is the one `textureLoad` would return for the fragment's pixel from the attachment's texture view: an 8-bit unorm attachment returns the quantized value that was stored, and an sRGB attachment returns linear values.
- A read executed by a helper invocation (including after `discard`) returns an indeterminate value, as atomics do.

### Pipeline validation

In `createRenderPipeline()` and `createRenderPipelineAsync()`, for a fragment entry point that has `@color` inputs:

- `multisample.count` must be 1, and the device must not be in Compatibility mode (it must have `"core-features-and-limits"` enabled).
- For each `@color(n)`:
  - `targets[n]` must exist and be non-null, and the input's type must match the sample type of its format.
  - `targets[n].blend` must be `undefined`.
  - If `targets[n].writeMask` is 0 the target is only read. Otherwise the device must have `"framebuffer-fetch-coherent"` enabled, the format must support the `"read-write"` storage texture access (baseline: `r32float`, `r32sint`, `r32uint`; more with `"texture-formats-tier2"`), and the entry point must not contain a `discard` statement or use `@builtin(frag_depth)` or `@builtin(sample_mask)` as an output.

### Semantics

**Framebuffer fetch.** The pipeline must have `writeMask: 0` for every target it reads, so no fragment of the draw modifies those attachments. The value read is the attachment's content immediately before the draw: the result of its load operation and of every earlier draw in the render pass, in submission order. This is the value a `textureLoad` at the fragment's pixel would return in a new render pass begun at this point; implementations are free to avoid the pass boundary, and applications write no barriers.

**`"framebuffer-fetch-coherent"`.** The pipeline may also write the targets it reads. Fragments that cover the same pixel are ordered by *primitive order*: draws in the order encoded, instances in order, and primitives within an instance in the order submitted, which is the order fixed-function blending would apply. A read observes the writes of every earlier fragment on that pixel, including earlier fragments of the same draw, with their write masks and depth/stencil results applied, and never observes the writes of later fragments. A fragment's own write happens after its read and is not observed by it.

## Examples

### Deferred lighting in one render pass

Depth/stencil is omitted for brevity.

```wgsl
requires framebuffer_fetch;

struct GBuffer {
  @location(0) albedo: vec4f,
  @location(1) normal: vec4f,
}

@fragment
fn fs_gbuffer(in: SurfaceInput) -> GBuffer {
  return GBuffer(vec4f(in.albedo, 1), vec4f(normalize(in.normal), 0));
}

@fragment
fn fs_light(
  @builtin(position) pos: vec4f,
  @color(0) albedo: vec4f,
  @color(1) normal: vec4f,
) -> @location(2) vec4f {
  return vec4f(shade(albedo.rgb, normalize(normal.xyz), pos.xy), 1);
}
```

```js
const transient = (format) => device.createTexture({
  size: [width, height],
  format,
  usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TRANSIENT_ATTACHMENT,
});
const albedo = transient('rgba8unorm');
const normal = transient('rgba16float');

const gbufferPipeline = device.createRenderPipeline({
  layout: 'auto',
  vertex: { module, entryPoint: 'vs_main', buffers },
  fragment: {
    module,
    entryPoint: 'fs_gbuffer',
    targets: [
      { format: 'rgba8unorm' },
      { format: 'rgba16float' },
      { format: 'bgra8unorm', writeMask: 0 },
    ],
  },
});

const lightPipeline = device.createRenderPipeline({
  layout: 'auto',
  vertex: { module, entryPoint: 'vs_fullscreen' },
  fragment: {
    module,
    entryPoint: 'fs_light',
    targets: [
      { format: 'rgba8unorm', writeMask: 0 },   // read as @color(0)
      { format: 'rgba16float', writeMask: 0 },  // read as @color(1)
      { format: 'bgra8unorm' },
    ],
  },
});

const pass = encoder.beginRenderPass({
  colorAttachments: [
    { view: albedo.createView(), loadOp: 'clear', storeOp: 'discard' },
    { view: normal.createView(), loadOp: 'clear', storeOp: 'discard' },
    { view: context.getCurrentTexture().createView(), loadOp: 'clear', storeOp: 'store' },
  ],
});
pass.setPipeline(gbufferPipeline);
// ... draw scene geometry ...
pass.setPipeline(lightPipeline);
pass.draw(3);
pass.end();
```

### Custom blending (`"framebuffer-fetch-coherent"`)

```wgsl
requires framebuffer_fetch;

@group(0) @binding(0) var layer_sampler: sampler;
@group(0) @binding(1) var layer_texture: texture_2d<f32>;

fn overlay(dst: vec3f, src: vec3f) -> vec3f {
  return select(1.0 - 2.0 * (1.0 - dst) * (1.0 - src), 2.0 * dst * src, dst < vec3f(0.5));
}

@fragment
fn fs_overlay(@location(0) uv: vec2f, @color(0) dst: vec4f) -> @location(0) vec4f {
  let src = textureSample(layer_texture, layer_sampler, uv);
  return vec4f(mix(dst.rgb, overlay(dst.rgb, src.rgb), src.a), dst.a);
}
```

```js
const device = await adapter.requestDevice({
  requiredFeatures: ['framebuffer-fetch-coherent', 'texture-formats-tier2'],
});

// `blend` is left undefined: the shader does the blending.
const overlayPipeline = device.createRenderPipeline({
  layout: 'auto',
  vertex: { module, entryPoint: 'vs_layer' },
  fragment: { module, entryPoint: 'fs_overlay', targets: [{ format: 'rgba8unorm' }] },
});
```

## Left out

- **Depth and stencil reads.** Vulkan exposes them as separate features because implementations manage depth/stencil differently from color. Metal fragment functions read color attachments only, and D3D12 could express only read-only depth (a read-only depth-stencil view plus an SRV).
- **Multisampled attachments.** Vulkan's `sample` operand has no counterpart here. On D3D12, per-sample reads would be straightforward for framebuffer fetch (`Texture2DMS::Load`) but impossible on the ROV path, which has no multisampled resource types.
- **Non-coherent read-modify-write with explicit barriers.** Vulkan's optional mode lets a shader read an attachment that it also writes, without ordering, with application-inserted barriers inside the render pass. Most backends have a matching barrier (the macOS-only render-target memory barrier on non-Apple GPUs, UAV barriers on D3D12), and it would be a no-op where reads are already ordered, such as tile-memory reads on Apple GPUs. It is left out because it needs an application-visible barrier command and leaves overlapping fragments racy, and the two parts above already cover the use cases.
- **Format reinterpretation, custom per-pixel data and access beyond the fragment's own pixel.** These are the imageblock and tile shader parts of [tile-shaders](tile-shaders.md), which can build on framebuffer fetch later.

## Open questions

- **Universal support.** As a language extension, framebuffer fetch has to be implementable on every backend an implementation supports. This draft argues that it is: D3D12 through SRVs and transitions, Vulkan through `VK_EXT_shader_tile_image`, local read or subpass input attachments, and Metal through programmable blending on Apple GPUs and through a render-target memory barrier plus a texture read on Intel and AMD Macs, where the SDK documents the barrier as making framebuffer writes readable by the following fragment shaders. None of this has been verified on hardware, in particular on Vulkan drivers without local read and on Intel and AMD Macs. If it does not hold, the fallback is a `GPUFeatureName` with an `enable` directive.
- **Explicit texture usage.** The D3D12 ROV path needs a UAV-capable texture (`D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS`), and a Vulkan implementation without `VK_EXT_shader_tile_image` needs `VK_IMAGE_USAGE_INPUT_ATTACHMENT_BIT` for framebuffer fetch; Metal needs nothing on Apple GPUs but `MTLTextureUsageShaderRead` on Intel and AMD Macs. This draft adds no usage and lets implementations add these capabilities to eligible render attachments: the D3D12 UAV flag when `"framebuffer-fetch-coherent"` is enabled, but the Vulkan input attachment bit and the Metal shader-read usage unconditionally, since framebuffer fetch has no device feature to key off. The UAV flag can have a hidden cost on D3D12 (for example, lost color compression), and the input attachment and shader-read bits now apply to every color attachment on implementations that need them. An explicit `GPUTextureUsage` would make the cost visible and local, at the price of relaxing the "only and exactly" usage rule of [transient-attachments](transient-attachments.md); requiring `STORAGE_BINDING` instead would exclude transient attachments.
- **Format support for `"framebuffer-fetch-coherent"`.** The `"read-write"` storage format requirement comes only from D3D12's typed UAV loads. Metal and Vulkan could support every renderable color format, so the set could instead be defined per backend capability.
- **Blending on read targets.** Disallowed so that the ROV lowering stays exact. It could be allowed if implementations apply the blend state in the shader on that path.
- **Conversion behavior.** Reads are defined as `textureLoad` equivalents (linear values for sRGB attachments). How `[[color(n)]]` and the Vulkan paths behave for sRGB and other converting formats needs to be verified against that definition.
- **`discard`, `frag_depth` and `sample_mask`.** The restriction exists only because of early depth/stencil testing on the D3D12 ROV path, and it applies only to pipelines that write an attachment they read. It could be relaxed for pipelines that disable depth/stencil writes.

## References

- Vulkan: [VK_EXT_shader_tile_image proposal](https://docs.vulkan.org/features/latest/features/proposals/VK_EXT_shader_tile_image.html) and [reference page](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_EXT_shader_tile_image.html)
- Vulkan: [VK_KHR_dynamic_rendering_local_read](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_KHR_dynamic_rendering_local_read.html)
- Vulkan: [VK_EXT_rasterization_order_attachment_access](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_EXT_rasterization_order_attachment_access.html)
- Vulkan: [VK_EXT_fragment_shader_interlock](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_EXT_fragment_shader_interlock.html)
- D3D12: [Rasterizer Order Views](https://learn.microsoft.com/en-us/windows/win32/direct3d12/rasterizer-ordered-views)
- D3D11.3: [Rasterizer Order Views](https://learn.microsoft.com/en-us/windows/win32/direct3d11/rasterizer-order-views)
- Metal: [Metal Shading Language Specification](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf) (fragment function input `[[color(m)]]`)
- Metal: [Metal Feature Set Tables](https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf) (programmable blending by GPU family, and which GPU families support render-target memory barriers)
- OpenGL ES: [GL_EXT_shader_framebuffer_fetch](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_shader_framebuffer_fetch.txt) and [GL_EXT_shader_framebuffer_fetch_non_coherent](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_shader_framebuffer_fetch_non_coherent.txt)
- This repository: [tile-shaders](tile-shaders.md), [transient-attachments](transient-attachments.md)
