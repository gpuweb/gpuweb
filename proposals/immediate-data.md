# ImmediateData

**Roadmap:** This proposal is **under active development, but has not been standardized for inclusion in the WebGPU specification. The proposal is likely to change before it is standardized.** WebGPU implementations **must not** expose this functionality; doing so is a spec violation. Note however, an implementation might provide an option (e.g. command line flag) to enable a draft implementation, for developers who want to test this proposal.

Last modified: 2025-10-28

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

**`immediateSize`**: Size of immediate data range used in pipeline, in bytes.

### Immediate Slots

Each pipeline defines a set of **immediate slots** based on the `var<immediate>` variables used by its shaders:
- Each 32-bit word (4 bytes) in the immediate data range corresponds to one slot
- `immediateSize` must be at least `SizeOf(the immediate variable)`, like [minimum buffer binding size](https://gpuweb.github.io/gpuweb/#minimum-buffer-binding-size)
- For struct types, padding bytes **are included** in the size but slots corresponding to padding **are not included** in the set of slots that must be set by the API
- Example: `var<immediate> s : struct { a : f32, b : vec4<f32> }` requires `immediateSize = 32` (4 bytes for `a` at offset 0, 12 bytes padding at offsets 4-15 to align `b` to a 16-byte boundary, 16 bytes for `b` at offsets 16-31). Only slots 0, 4, 5, 6, 7 (the 32-bit words containing actual data: word 0 for `a`, words 4-7 for `b`) need to be set via `setImmediateData()`

**Compatibility:** Two pipeline layouts are "compatible for immediate data" if they were created with identical `immediateSize`. Immediate data values can be shared between pipelines with compatible layouts.

**Out-of-bounds:** Immediate data range follows [out-of-bounds access](https://www.w3.org/TR/WGSL/#out-of-bounds-access) rules in WGSL spec.

## GPUCommandEncoder

One new function in `GPUBindingCommandsMixin`.

```javascript
interface mixin GPUBindingCommandsMixin {
        void setImmediateData(uint32_t rangeOffset, AllowSharedBufferSource data, optional dataOffset, optional size);
}
```

- `rangeOffset`: Offset in bytes into immediate data range to begin writing at. Must be a multiple of 4 bytes.
- `dataOffset` and `size` work like in [writeBuffer](https://gpuweb.github.io/gpuweb/#dom-gpuqueue-writebuffer): "Given in elements if data is a TypedArray and bytes otherwise." The actual byte size copied must be a multiple of 4 bytes.
- The immediate data is stored in an internal slot `[[immediate data]]` in `GPUBindingCommandsMixin`, which is shared across `GPUComputePassEncoder`, `GPURenderPassEncoder`, and `GPURenderBundleEncoder`. See issue [#5117](https://github.com/gpuweb/gpuweb/issues/5117).

## Validation

Immediate values must be set before they can be used in draw or dispatch operations.

**Validation rules:**

1. **At draw/dispatch time:** A validation error is generated if any immediate slot (see [Immediate Slots](#immediate-slots)) used by the current pipeline has not been set since:
   - The beginning of the encoder (for `GPURenderPassEncoder` or `GPUComputePassEncoder`), or
   - The last `executeBundles()` call (for `GPURenderPassEncoder`)

   For pipelines with multiple shader stages, the union of slots from all stages must be set.

2. **Initial state:** At the beginning of an encoder, no immediate slots are considered set.

3. **After executeBundles():** After `executeBundles()` completes, all immediate slots are cleared (no slots are considered set).

4. **Setting slots:** When `setImmediateData(rangeOffset, data, ...)` is called, the 32-bit word slots at byte offsets `[rangeOffset, rangeOffset + actualSize)` are marked as set, where `actualSize` is the actual byte size of the data being copied. Since both `rangeOffset` and `actualSize` must be multiples of 4 bytes, this marks complete 32-bit word slots as set.

**Example validation:**

```javascript
// Pipeline uses slots 0-3 (16 bytes of immediate data)
const pipeline = device.createComputePipeline({
  layout: device.createPipelineLayout({ immediateSize: 16 }),
  compute: { module, entryPoint: "main" } // uses var<immediate> data : vec4<f32>
});

const encoder = commandEncoder.beginComputePass();
encoder.setPipeline(pipeline);

// ERROR: Immediate slots 0-3 have not been set
// encoder.dispatchWorkgroups(1);

encoder.setImmediateData(0, new Float32Array([1, 2, 3, 4])); // Sets slots 0-3

// OK: All required slots are now set
encoder.dispatchWorkgroups(1);

encoder.end();
```

See issue [#5318](https://github.com/gpuweb/gpuweb/issues/5318) for detailed discussion.

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
// After executeBundles, immediate data is cleared - would need to call setImmediateData again
passEncoder.setImmediateData(0, new Uint32Array([9, 10, 11, 12]));
passEncoder.draw(3); // Uses [9, 10, 11, 12]
passEncoder.end();
```

See issue [#5118](https://github.com/gpuweb/gpuweb/issues/5118) for detailed discussion.

# Resolved Questions:

- **Per-stage immediate data?** No, unified range across all stages. (Issue [#5116](https://github.com/gpuweb/gpuweb/issues/5116))
- **Internal slot location?** `[[immediate data]]` is in `GPUBindingCommandsMixin`. (Issue [#5117](https://github.com/gpuweb/gpuweb/issues/5117))
- **RenderBundle support?** Yes, with snapshot behavior and state reset after execution. (Issue [#5118](https://github.com/gpuweb/gpuweb/issues/5118))
- **Validation for unset immediates?** Yes, validation error at draw/dispatch if required immediate slots have not been set. (Issue [#5318](https://github.com/gpuweb/gpuweb/issues/5318))
