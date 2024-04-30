# Subgroups

Status: **Draft**

Last modified: 2024-04-30

Issue: #75

# Requirements

No special requirements.

# WGSL


## Address Spaces

| Address space | Sharing among invocations | Default access mode | Notes |
| --- | --- | --- | --- |
| `push_constant` | Invocations in [shader stage](https://www.w3.org/TR/WGSL/#shader-stages) | [read](https://www.w3.org/TR/WGSL/#access-read) | For [uniform buffer](https://www.w3.org/TR/WGSL/#uniform-buffer) variables exclude [array types](https://www.w3.org/TR/WGSL/#array-types) variable or [structure types](https://www.w3.org/TR/WGSL/#struct-types) variable contains [array types](https://www.w3.org/TR/WGSL/#array-types) attributes |


## Variable and Value Declarations

| Declaration | Mutability | Scope | Effective-value-type | Initializer Support | Initializer Expression | Part of Resource Interface |
| --- | --- | --- | --- | --- | --- | --- |
| `var<push_constant>` | Immutable | [Module](https://www.w3.org/TR/WGSL/#module-scope) | [Concrete](https://www.w3.org/TR/WGSL/#type-concrete) [constructible](https://www.w3.org/TR/WGSL/#constructible) [host-shareable](https://www.w3.org/TR/WGSL/#host-shareable) excludes [array types](https://www.w3.org/TR/WGSL/#array-types) and [structure types](https://www.w3.org/TR/WGSL/#struct-types) contains array members | Disallowed	| | Yes. [uniform buffer](https://www.w3.org/TR/WGSL/#uniform-buffer) |

NOTE: Each [entry point](https://www.w3.org/TR/WGSL/#entry-point) can statically use at most one push constant variable.

# API

## Limits

One new limits:

| Limit name | Description | Type | Limit class | Default |
| --- | --- | --- | --- | --- |
| pushConstantMaxSize | The maximum allowed value for the pushconstantsSize | [GPUSize32](https://www.w3.org/TR/webgpu/#typedefdef-gpusize32) | [maximum](https://www.w3.org/TR/webgpu/#limit-class-maximum) | 64 |

NOTE: 64 bytes is the sizeof(mat4x4).

## Pipeline Layouts
One new member in `GPUPipelineLayoutDescriptor`.

```javascript
dictionary GPUPipelineLayoutDescriptor
         : GPUObjectDescriptorBase {
    required sequence<GPUBindGroupLayout> bindGroupLayouts;
    uint32_t pushConstantsSize = 0;
};
```
two pipeline layouts are defined to be “compatible for push constants” if they were created with identical push constant size. It means push constants values can share between pipeline layouts that are compatible for push constants.

## GPUCommandEncoder

Four new functions in `GPUCommandEncoder`.

```javascript
interface GPUCommandEncoder {
        void setPushConstantU32(uint32_t offset, uint32_t value);
        void setPushConstantI32(uint32_t offset, int32_t value);
        void setPushConstantF32(uin32_t offset, float32_t value);
        void setPushConstants(uint32_t offset, uint32_t count, ArrayBuffer data);
}
```
