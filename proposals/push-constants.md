# ImmediateData

**Roadmap:** This proposal is **under active development, but has not been standardized for inclusion in the WebGPU specification. The proposal is likely to change before it is standardized.** WebGPU implementations **must not** expose this functionality; doing so is a spec violation. Note however, an implementation might provide an option (e.g. command line flag) to enable a draft implementation, for developers who want to test this proposal.

Last modified: 2024-05-30

Issue: #75

# Requirements

No special requirements.

# WGSL


## Address Spaces

| Address space | Sharing among invocations | Default access mode | Notes |
| --- | --- | --- | --- |
| `immediate_data` | Invocations in [shader stage](https://www.w3.org/TR/WGSL/#shader-stages) | [read](https://www.w3.org/TR/WGSL/#access-read) | For [uniform buffer](https://www.w3.org/TR/WGSL/#uniform-buffer) variables exclude [array types](https://www.w3.org/TR/WGSL/#array-types) variable or [structure types](https://www.w3.org/TR/WGSL/#struct-types) variable contains [array types](https://www.w3.org/TR/WGSL/#array-types) attributes |


## Variable and Value Declarations

| Declaration | Mutability | Scope | Effective-value-type | Initializer Support | Initializer Expression | Part of Resource Interface |
| --- | --- | --- | --- | --- | --- | --- |
| `var<immediate_data>` | Immutable | [Module](https://www.w3.org/TR/WGSL/#module-scope) | [Concrete](https://www.w3.org/TR/WGSL/#type-concrete) [constructible](https://www.w3.org/TR/WGSL/#constructible) [host-shareable](https://www.w3.org/TR/WGSL/#host-shareable) excludes [array types](https://www.w3.org/TR/WGSL/#array-types) and [structure types](https://www.w3.org/TR/WGSL/#struct-types) contains array members | Disallowed	| | Yes. [uniform buffer](https://www.w3.org/TR/WGSL/#uniform-buffer) |

NOTE: Each [entry point](https://www.w3.org/TR/WGSL/#entry-point) can statically use at most one immediate data variable.

# API

## Limits

One new limits:

| Limit name | Description | Type | Limit class | Default |
| --- | --- | --- | --- | --- |
| immediateDataRangeMaxByteSize | The maximum bytes allowed value for the immediateDataRangeMaxSize | [GPUSize32](https://www.w3.org/TR/webgpu/#typedefdef-gpusize32) | [maximum](https://www.w3.org/TR/webgpu/#limit-class-maximum) | 64 |

NOTE: 64 bytes is the sizeof(mat4x4).

## Pipeline Layouts
One new member in `GPUPipelineLayoutDescriptor`.

```javascript
dictionary GPUPipelineLayoutDescriptor
         : GPUObjectDescriptorBase {
    required sequence<GPUBindGroupLayout> bindGroupLayouts;
    uint32_t immediateDataRangeByteSize = 0;
};
```
`immediateDataRangeByteSize`: Size of immediate data range used in pipeline, type is bytes.

NOTE: `immediateDataRangeByteSize` = sizeof(variables) + sizeof(paddings). Follow [ Aligment rules ](https://www.w3.org/TR/WGSL/#alignment-and-size) in wgsl spec.

NOTE: two pipeline layouts are defined to be “compatible for immediate data” if they were created with identical immediate data byte size. It means immediate data values can share between pipeline layouts that are compatible for immediate data.

NOTE: Immediate data range follow [out-of-bounds access](https://www.w3.org/TR/WGSL/#out-of-bounds-access) rules in wgsl spec.

## GPUCommandEncoder

Four new functions in `GPUCommandEncoder`.

```javascript
interface mixin GPUBindingCommandsMixin {
        void setImmeidateDataU32(uint32_t offset, uint32_t value);
        void setImmediateDataI32(uint32_t offset, int32_t value);
        void setImmediateDataF32(uin32_t offset, float32_t value);
        void setImmediateDataRange(uint32_t rangeOffset, AllowSharedBufferSource data, optional dataOffset, optional size);
}
```
NOTE: rangeOffset: Offset in bytes into immediate data range to begin writing at. Requires multiple of 4 bytes.
NOTE: dataOffset: Offset in into data to begin writing from. Given in elements if data is a TypedArray and bytes otherwise.
