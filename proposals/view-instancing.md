# View Instancing

* Status: [Draft](README.md#status-draft)
* Created: 2026-04-29
* Issue: [#4109](https://github.com/gpuweb/gpuweb/issues/4109)

## Motivation

Many rendering workloads draw the same scene into multiple views with only small per-view
differences, such as stereo XR rendering, layered shadow rendering, or cascaded camera views.
Today, WebGPU applications must encode a separate render pass and duplicate draw calls for each
view. This increases CPU overhead, command memory usage, and state management complexity.

Native graphics APIs already expose view instancing or multiview mechanisms that let a single draw
be broadcast to multiple render-target array layers while still giving shaders access to the
current view index. WebGPU should expose a similarly small, portable feature.

This proposal adds an opt-in view instancing feature for render passes:

* A render pass can target multiple views at once.
* Rasterization is broadcast across all views in the pass.
* Shaders can optionally read the current `view_index`.

The proposal intentionally uses a dense `viewCount` rather than a sparse `viewMask`. The primary
target is stereo and other contiguous layered rendering use cases, while keeping the API simple.

## Native API Availability

**Vulkan**:

* [`VK_KHR_multiview`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_multiview.html)
  (promoted to Vulkan 1.1), exposed through
  [`VkPhysicalDeviceMultiviewFeatures::multiview`](https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceMultiviewFeatures.html)
* [`VK_KHR_dynamic_rendering`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_dynamic_rendering.html)
  for dynamic-rendering multiview via
  [`VkRenderingInfo::viewMask`](https://docs.vulkan.org/refpages/latest/refpages/source/VkRenderingInfo.html)
* The SPIR-V `ViewIndex` built-in

**D3D12**:

* View Instancing
  ([`D3D12_VIEW_INSTANCING_TIER`](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ne-d3d12-d3d12_view_instancing_tier),
  [`D3D12_VIEW_INSTANCING_DESC`](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_view_instancing_desc))
* The HLSL
  [`SV_ViewID`](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-semantics)
  system value

**Metal**:

* [Vertex Amplification](https://developer.apple.com/documentation/metal/improving-rendering-performance-with-vertex-amplification)
* Layered render-target rendering via
  [`[[render_target_array_index]]`](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf)
* Per-view selection via
  [`[[amplification_id]]`](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf)

## WGSL

### Enable Extension

Add a new enable extension.

| Enable | Description |
| --- | --- |
| `view_instancing` | Adds the `view_index` built-in input for render pipelines used with view-instanced render passes. |

### Built-in Values

| Built-in | Stage | Type | Direction | Description |
| --- | --- | --- | --- | --- |
| `view_index` | vertex, fragment | `u32` | Input | The active view for the current invocation. Values are in `[0, viewCount)`. |

`view_index` is only valid in render pipelines used with a view-instanced render pass.

### Example usage

```wgsl
enable view_instancing;

struct VSOut {
  @builtin(position) position : vec4f,
  @location(0) tint : vec3f,
};

@vertex
fn vsMain(@builtin(vertex_index) vertex_index : u32,
          @builtin(view_index) view_index : u32) -> VSOut {
  var positions = array(
    vec2f(-0.8, -0.8),
    vec2f( 0.8, -0.8),
    vec2f( 0.0,  0.8),
  );

  var out : VSOut;
  out.position = vec4f(positions[vertex_index], 0.0, 1.0);
  out.tint = select(vec3f(1.0, 0.3, 0.2), vec3f(0.2, 0.8, 1.0), view_index == 1u);
  return out;
}

@fragment
fn fsMain(@location(0) tint : vec3f) -> @location(0) vec4f {
  return vec4f(tint, 1.0);
}
```

## API

### Feature

Add a new feature name:

* `"view-instancing"`

### Limits

Add a new supported limit:

| Limit name | Type | Limit class | Default |
| --- | --- | --- | --- |
| `maxViewInstanceCount` | `GPUSize32` | maximum | 1 |

If `"view-instancing"` is supported, `maxViewInstanceCount` must be at least `2`.

### Render Pass Descriptor

Add a new field to `GPURenderPassDescriptor`:

```webidl
partial dictionary GPURenderPassDescriptor {
    GPUSize32 viewCount = 1;
}
```

### Behavior

* `viewCount == 1` preserves existing behavior.
* `viewCount > 1` creates a view-instanced render pass and requires the `"view-instancing"` feature to be
  enabled on the device.
* `viewCount` must be less than or equal to `device.limits.maxViewInstanceCount`.
* For view `i`, rendering targets array layer `baseArrayLayer + i` of each attachment view.
* Rasterization and fragment processing happen once per view for each primitive in the pass.
* A pipeline used in a view-instanced render pass renders to all views even if it does not read
  `view_index`. `view_index` is only needed when shader behavior differs per view.

### Validation

When `viewCount > 1`:

* each color attachment view must be a `2d-array` view with `arrayLayerCount == viewCount`
* the depth/stencil attachment view, if present, must be a `2d-array` view with
  `arrayLayerCount == viewCount`
* each resolve target, if present, must be a `2d-array` view with `arrayLayerCount == viewCount`
* `viewCount` must be at least `1`

### Example usage

```js
const colorView = viewInstancingTexture.createView({
  dimension: "2d-array",
  baseArrayLayer: 0,
  arrayLayerCount: 2,
});

const pass = encoder.beginRenderPass({
  colorAttachments: [{
    view: colorView,
    loadOp: "clear",
    storeOp: "store",
    clearValue: { r: 0, g: 0, b: 0, a: 1 },
  }],
  viewCount: 2,
});
```

## Open Questions

* Should `@builtin(view_index)` be allowed when `viewCount == 1`, implicitly producing `0`, or
  should it remain invalid outside view-instanced passes?
* Do render bundles need an explicit view-instancing compatibility bit, or can they always inherit the
  enclosing render pass's `viewCount`?
* Is `viewCount` sufficient, or is there any compelling use case that requires sparse view masks in
  the initial API surface?
* Are there any extension interactions that should be explicitly disallowed in the initial version
  of this feature?

## Resources

* https://github.com/gpuweb/gpuweb/issues/4109
* https://registry.khronos.org/vulkan/specs/1.3-extensions/html/chap8.html#renderpass-multiview
* https://learn.microsoft.com/en-us/windows/win32/direct3d12/view-instancing
