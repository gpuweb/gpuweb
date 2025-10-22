# ImmediateData

**Roadmap:** This proposal is **under active development, but has not been standardized for inclusion in the WebGPU specification. The proposal is likely to change before it is standardized.** WebGPU implementations **must not** expose this functionality; doing so is a spec violation. Note however, an implementation might provide an option (e.g. command line flag) to enable a draft implementation, for developers who want to test this proposal.

Last modified: 2025-10-20

Issue: #75

# Requirements

No special requirements.

# WGSL


## Address Spaces

| Address space | Sharing among invocations | Default access mode | Notes |
| --- | --- | --- | --- |
| `immediate` | Invocations in [shader stage](https://www.w3.org/TR/WGSL/#shader-stages) | [read](https://www.w3.org/TR/WGSL/#access-read) | For [uniform buffer](https://www.w3.org/TR/WGSL/#uniform-buffer) variables exclude [array types](https://www.w3.org/TR/WGSL/#array-types) variable or [structure types](https://www.w3.org/TR/WGSL/#struct-types) variable contains [array types](https://www.w3.org/TR/WGSL/#array-types) attributes |


## Variable and Value Declarations

| Declaration | Mutability | Scope | Effective-value-type | Initializer Support | Initializer Expression | Part of Resource Interface |
| --- | --- | --- | --- | --- | --- | --- |
| `var<immediate>` | Immutable | [Module](https://www.w3.org/TR/WGSL/#module-scope) | [Concrete](https://www.w3.org/TR/WGSL/#type-concrete) [constructible](https://www.w3.org/TR/WGSL/#constructible) [host-shareable](https://www.w3.org/TR/WGSL/#host-shareable) excludes [array types](https://www.w3.org/TR/WGSL/#array-types) and [structure types](https://www.w3.org/TR/WGSL/#struct-types) contains array members | Disallowed	| | Yes. [uniform buffer](https://www.w3.org/TR/WGSL/#uniform-buffer) |

NOTE: Each [entry point](https://www.w3.org/TR/WGSL/#entry-point) can statically use at most one immediate variable.

Sample Code:
```
struct S {
  i : i32,
}

var<immediate> a : S;
var<immediate> b : i32;
var<immediate> c : i32; // unused

fn uses_a() {
  let foo = a.i;
}

fn uses_uses_a() {
  uses_a();
}

fn uses_b() {
  let foo = b;
}

// Each entry point can statically use at most one immediate variable.
@compute @workgroup_size(1)
fn main1() {
  uses_a();
}

@compute @workgroup_size(1)
fn main2() {
  uses_uses_a();
}

@compute @workgroup_size(1)
fn main3() {
  uses_b();
}

@compute @workgroup_size(1)
fn main4() {
}
```

# API

## Limits

One new limits:

| Limit name | Description | Type | Limit class | Default |
| --- | --- | --- | --- | --- |
| maxImmediateSize | The maximum bytes allowed value for the immediateSize | [GPUSize32](https://www.w3.org/TR/webgpu/#typedefdef-gpusize32) | [maximum](https://www.w3.org/TR/webgpu/#limit-class-maximum) | 64 |

NOTE: 64 bytes is the sizeof(mat4x4).

## Pipeline Layouts
One new member in `GPUPipelineLayoutDescriptor`.

```javascript
dictionary GPUPipelineLayoutDescriptor
         : GPUObjectDescriptorBase {
    required sequence<GPUBindGroupLayout> bindGroupLayouts;
    uint32_t immediateSize = 0;
};
```
`immediateSize`: Size of immediate data range used in pipeline, type is bytes.

NOTE: `immediateSize` = sizeof(variables) + sizeof(paddings). Follow [ Alignment rules ](https://www.w3.org/TR/WGSL/#alignment-and-size) in wgsl spec.

NOTE: two pipeline layouts are defined to be “compatible for immediate data” if they were created with identical immediate data byte size. It means immediate data values can share between pipeline layouts that are compatible for immediate data.

NOTE: Immediate data range follow [out-of-bounds access](https://www.w3.org/TR/WGSL/#out-of-bounds-access) rules in wgsl spec.

## GPUCommandEncoder

One new function in `GPUBindingCommandsMixin`.

```javascript
interface mixin GPUBindingCommandsMixin {
        void setImmediateData(uint32_t rangeOffset, AllowSharedBufferSource data, optional dataOffset, optional size);
}
```

- `rangeOffset`: Offset in bytes into immediate data range to begin writing at. Requires multiple of 4 bytes.
- `dataOffset` and `size` work like in [writeBuffer](https://gpuweb.github.io/gpuweb/#dom-gpuqueue-writebuffer): "Given in elements if data is a TypedArray and bytes otherwise."
- The immediate data is stored in an internal slot `[[immediate data]]` in `GPUBindingCommandsMixin`, which is shared across `GPUComputePassEncoder`, `GPURenderPassEncoder`, and `GPURenderBundleEncoder`. See issue [#5117](https://github.com/gpuweb/gpuweb/issues/5117).

## Per-Stage Immediate Data

This proposal does **NOT** support per-stage immediate data ranges. The immediate data range is unified across all shader stages (vertex, fragment, compute). This decision is based on:

- Vulkan and D3D12 use unified immediate data ranges (push constants and root constants respectively)
- Metal supports per-stage ranges but can easily implement unified ranges by calling set*Bytes() multiple times
- Unified ranges simplify the API and implementation

See issue [#5116](https://github.com/gpuweb/gpuweb/issues/5116) for detailed discussion.

## Render Bundle Support

The `setImmediateData()` function is available in `GPURenderBundleEncoder` through `GPUBindingCommandsMixin`.

**Behavior:**
- When encoding a render bundle (as when encoding a render pass), calls to `setImmediateData()` snapshot the immediate data content at encoding time. The immediate values used by draw calls in a bundle cannot be changed.
- Immediate data is cleared/reset before and after executing each individual bundle (similar to bind group state).

**Example:**
```javascript
// Create bundle with immediate data
const bundleEncoder = device.createRenderBundleEncoder(descriptor);
bundleEncoder.setImmediateData(0, new Uint32Array([1, 2, 3, 4]));
bundleEncoder.setPipeline(pipeline);
bundleEncoder.draw(3);
const bundle = bundleEncoder.finish();

// Use in render pass
const passEncoder = commandEncoder.beginRenderPass(descriptor);
passEncoder.setImmediateData(0, new Uint32Array([5, 6, 7, 8]));
passEncoder.draw(3); // Uses [5, 6, 7, 8]
passEncoder.executeBundles([bundle]); // Uses snapshotted [1, 2, 3, 4]
passEncoder.draw(3); // Uses [] - immediate data cleared after executeBundles
passEncoder.end();
```

See issue [#5118](https://github.com/gpuweb/gpuweb/issues/5118) for detailed discussion.
