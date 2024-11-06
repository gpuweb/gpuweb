# Texel Buffers

**Roadmap:** This proposal is **under active development, but has not been standardized for inclusion in the WebGPU specification. The proposal is likely to change before it is standardized.** WebGPU implementations **must not** expose this functionality; doing so is a spec violation. Note however, an implementation might provide an option (e.g. command line flag) to enable a draft implementation, for developers who want to test this proposal.

Last modified: 2024-10-07

Issue: [#162](https://github.com/gpuweb/gpuweb/issues/162)

# WGSL


## Extension Names

Add `'texel_buffer'` as a new language extension name.


## Language Extensions

[[Add new table entry to *Language-extensions*]]

| WGSL language extension | Description                                                              |
| ----------------------- | ------------------------------------------------------------------------ |
| **texel_buffer**        | Allows the use of the `texel_buffer` type and related builtin functions. |


## Texel Buffer Types

[[New subsection of **Texture and Sampler Types**]]

A **texel buffer** supports accessing texels stored in a 1D buffer using texture load and store functions.

Unlike other WGSL texture types, the texels of a texel buffer are stored in a `GPUBuffer`, and bound to the pipeline via a `GPUTexelBufferView`.
Additionally, the maximum number of texels in a texel buffer is often much larger than for storage textures. See https://gpuweb.github.io/gpuweb/#supported-limits

A texel buffer type must be parameterized by one of the [texel formats](https://w3.org/TR/WGSL/#texel-formats) for storage textures.
The texel format determines the conversion function as specified in [Texel Formats](https://w3.org/TR/WGSL/#texel-formats).

For a `textureStore` operation, the inverse of the conversion function is used to convert the shader value to the stored texel.

| Type                                 | Description                    |
| ------------------------------------ | ------------------------------ |
| **texel_buffer**<_Format_, _Access_> | A texel buffer type that accesses buffer data using texture functions. |

- _Format_ must be an enumerant for one of the texel formats for storage textures
- _Access_ must be `read` or `read_write`

Writes to texel buffers are visible to the same invocation, and can be synchronized with other invocations from the same workgroup using a `textureBarrier`.


## Restrictions on Functions

Add `texel_buffer` to the list of valid function parameter types.


## Texture Built-in Functions

[[Add new overloads]]

| Parameterization               | Overload                 |
| ------------------------------ | ------------------------ |
| _AM_ is `read` or `read_write` | `@must_use fn textureDimensions(t : texel_buffer<F, AM>) -> u32` |
| _C_ is `i32` or `u32`<br/>_AM_ is `read` or `read_write`<br/>_CF_ depends on the storage texel format _F_. [See the texel format table](https://w3.org/TR/WGSL/#storage-texel-formats) for the mapping of texel format to channel format. | `@must_use fn textureLoad(t : texel_buffer<F, AM>, coords : C) -> vec4<CF>` |
| _C_ is `i32` or `u32`<br/>_CF_ depends on the storage texel format _F_. [See the texel format table](https://w3.org/TR/WGSL/#storage-texel-formats) for the mapping of texel format to channel format. | `@must_use fn textureStore(t : texel_buffer<F, read_write>, coords : C, value: vec4<CF>)` |


# API


## Limits

| Limit name             | Type        | Limit class | Default                   |
| ---------------------- | ----------- | ----------- | ------------------------- |
| **maxTexelBufferSize** | `GPUSize64` | maximum     | 134217728 bytes (128 MiB) |


## Adapter Capability Guarantees

Add "`maxTexelBufferSize` must be <= `maxBufferSize`".


## Resource Usages

[[Modify description of internal usages]]

**storage**<br/>
Read/write storage resource binding. Allowed by buffer `STORAGE`, texture `STORAGE_BINDING`, or buffer `TEXEL_BUFFER`.

**storage-read**<br/>
Read-only storage resource bindings. Preserves the contents. Allowed by buffer `STORAGE`, texture `STORAGE_BINDING`, or buffer `TEXEL_BUFFER`.


## Buffer Usages

[[Add new const to `GPUBufferUsage` namespace]]

```javascript
  const GPUFlagsConstant TEXEL_BUFFER = 0x0400;
```


## GPUTexelBufferView

[[New subsection of **Textures and Texture Views**]]

A `GPUTexelBufferView` is a view onto some subset of the buffer subresources defined by a particular `GPUBuffer`.

```javascript
[Exposed=(Window, Worker), SecureContext]
interface GPUTexelBufferView {
};
GPUTexelBufferView includes GPUObjectBase;
```

`GPUTexelBufferView` has the following immutable properties:

> **[[buffer]], readonly**<br/>
> The `GPUBuffer` into which this is a view.
>
> **[[descriptor]], readonly**<br/>
> The `GPUTexelBufferViewDescriptor` describing this texel buffer view.
>
> All optional fields of `GPUTexelBufferViewDescriptor` are defined.


### Texel Buffer View Creation

```javascript
dictionary GPUTexelBufferViewDescriptor : GPUObjectDescriptorBase {
    GPUTextureFormat format;
    GPUSize64 offset = 0;
    GPUSize64 size;
};
```

`GPUTexelBufferViewDescriptor` has the following members:

> **format, of type GPUTextureFormat**<br/>
> The format of the texel buffer view.
>
> **offset, of type GPUSize64, defaulting to 0**<br/>
> The offset, in bytes, from the beginning of the buffer to the range exposed by the texel buffer view.
>
> **size, of type GPUSize64**<br/>
> The size, in bytes, of the texel buffer view. If not provided, specifies the range starting at `offset` and ending at the end of the buffer.

**createView(descriptor)**<br/>
Creates a `GPUTexelBufferView`.

> **Called on:** `GPUBuffer` _this_.
>
> **Arguments:**
>
> | Parameter    | Type                           | `Nullable` | `Optional` | Description      |
> | ------------ | ------------------------------ | ---------- | ---------- | ---------------- |
> | `descriptor` | `GPUTexelBufferViewDescriptor` | ✘          | ✔          | Description of the `GPUTexelBufferView` to create. |
>
> **Returns:** _view_, of type `GPUTexelBufferView`.
>
> [Content timeline](https://w3.org/TR/WGSL/#content-timeline) steps:
>
> 1. ? Validate
> 2. Let _view_ be ! [create a new WebGPU object](https://w3.org/TR/WGSL/#abstract-opdef-create-a-new-webgpu-object)(_this_, `GPUTexelBufferView`, _descriptor_)
> 3. Issue the _initialization steps_ on the Device timeline of _this_.
> 4. Return _view_.
>
> [Device timeline](https://w3.org/TR/WGSL/#device-timeline) steps:
>
> 1. If any of the following conditions are unsatisfied generate a validation error, invalidate _view_ and return.
>    - _this_ is valid to use with _this_.[[device]].
>    - _this_.usage must contain the `TEXEL_BUFFER` bit
>    - _descriptor_.`offset` + _descriptor_.`size` must be <= _this_.`size`
>    - _descriptor_.`size` must be <= _limits_.`maxTexelBufferSize`.
>    - _descriptor_.`size` must be a multiple of the texel size of _descriptor_.`format`.
>    - _descriptor_.`offset` must be a multiple of `256`.
> 2. Let _view_ be a new `GPUTexelBufferView` object.
> 3. Set _view_.[[buffer]] to _this_.
> 4. Set _view_.[[descriptor]] to _descriptor_.


## Bind Group Layout Creation

[[Add new field to **GPUBindGroupLayoutEntry**]]

```javascript
GPUTexelBufferBindingLayout texelBuffer;
```

**texelBuffer, of type [GPUTexelBufferBindingLayout]**<br/>
When provided, indicates the binding resource type for this `GPUBindGroupLayoutEntry` is `GPUTexelBufferBindingLayout`.

[[Add new entry to table of `GPUBindGroupLayoutEntry` members]]

| Binding member | Resource type          | Binding type                      | Binding usage |
| -------------- | ---------------------- | --------------------------------- | ------------- |
| texelBuffer    | `GPUTexelBufferView`   | `storage`<br/>`read-only-storage` | storage<br/>storage-read |

**TODO:** Do these use buffer slots, texture slots, storage texture slots, or a new type of slot?

[[Add new enum and dictionary]]

```javascript
enum GPUTexelBufferAccess {
    "read-only",
    "read-write",
};

dictionary GPUTexelBufferBindingLayout {
    GPUTexelBufferAccess access = "read-write";
    GPUTextureFormat format;
};
```

`GPUTexelBufferBindingLayout` dictionaries have the following members:

**access, of type GPUTexelBufferAccess, defaulting to "read-write"**<br/>
Indicates the access mode that will be used for texel buffer views bound to this binding.
**format, of type GPUTextureFormat**<br/>
The required format of texel buffer views bound to this binding.


## Bind Group Creation

[[Add new validation rules for `GPUBindGroupEntry` in `createBindGroup`]]

**texelBuffer**

- _resource_ is a `GPUTexelBufferView`.
- _resource_ is valid to use with _this_.
- _layoutBinding_.texelBuffer.format is equal to _resource_.format.
- _resource_.[[buffer]].usage includes `TEXEL_BUFFER`.


## Default Pipeline Layout

[[Add new steps for creating default pipeline layout]]

> If _resource_ is for a texel buffer binding:
>
> - Let _texelBufferLayout_ be a new `GPUTexelBufferBindingLayout`.
> - Set _texelBufferLayout_.format to _resource_’s format.
> - If the access mode is:<br/>
>   -> **read**<br/>
>   Set _texelBufferLayout_.access to `"read-only"`.<br/>
>   -> **read_write**<br/>
>   Set _texelBufferLayout_.access to `"read-write"`.
> - Set _entry_.texelBuffer to _texelBufferLayout_.


## Bind Groups

[[Add new aliasing limitations for texel buffers]]

**Replace:** “writable buffer binding range” with “writable buffer binding range or texel buffer view”

**Replace:** “of the same buffer” with “of the same buffer or texel buffer view”


## Plain color formats

[[Add new column to format table for `TEXEL_BUFFER`]]

| Format                    | `TEXEL_BUFFER` |
| ------------------------- | -------------- |
| **8-bit per component**   |                |
| `r8unorm`                 |                |
| `r8snorm`                 |                |
| `r8uint`                  |                |
| `r8sint`                  |                |
| `rg8unorm`                |                |
| `rg8snorm`                |                |
| `rg8uint`                 |                |
| `rg8sint`                 |                |
| `rgba8unorm`              | ✔              |
| `rgba8unorm-srgb`         |                |
| `rgba8snorm`              |                |
| `rgba8uint`               | ✔              |
| `rgba8sint`               | ✔              |
| `bgra8unorm`              |                |
| `bgra8unorm-srgb`         |                |
| **16-bit per component**  |                |
| `r16uint`                 |                |
| `r16sint`                 |                |
| `r16float`                |                |
| `rg16uint`                |                |
| `rg16sint`                |                |
| `rg16float`               |                |
| `rgba16uint`              | ✔              |
| `rgba16sint`              | ✔              |
| `rgba16float`             | ✔              |
| **32-bit per component**  |                |
| `r32uint`                 | ✔              |
| `r32sint`                 | ✔              |
| `r32float`                | ✔              |
| `rg32uint`                |                |
| `rg32sint`                |                |
| `rg32float`               |                |
| `rgba32uint`              | ✔              |
| `rgba32sint`              | ✔              |
| `rgba32float`             | ✔              |
| **mixed component width** |                |
| `rgb10a2uint`             |                |
| `rgb10a2unorm`            |                |
| `rg11b10ufloat`           |                |


# Appendix A: Implementation details


### Vulkan

In Vulkan, a `read_write` texel buffer would map to a storage texel buffer decorated as `Coherent`, and shader accesses would be performed with the `OpImageRead` and `OpImageWrite` instructions.
A texel buffer with a `read-only` access mode could use a uniform texel buffer instead, which would use `OpImageFetch` instead `OpImageRead`.

When the `TEXEL_BUFFER` usage flag is set on buffer creation, both of the Vulkan texel buffer bits would be set:<br/>
`VK_BUFFER_USAGE_UNIFORM_TEXEL_BUFFER_BIT | VK_BUFFER_USAGE_STORAGE_TEXEL_BUFFER_BIT`

The [required image formats](https://registry.khronos.org/vulkan/specs/1.2-extensions/html/vkspec.html#features-required-format-support) for storage texel buffers includes:

```
R8G8B8A8_UNORM
R8G8B8A8_UINT
R8G8B8A8_SINT
R16G16B16A16_UINT
R16G16B16A16_SINT
R16G16B16A16_SFLOAT
R32_UINT
R32_SINT
R32_SFLOAT
R32G32_UINT
R32G32_SINT
R32G32_SFLOAT
R32G32B32A32_UINT
R32G32B32A32_SINT
R32G32B32A32_SFLOAT
```

For the other formats, [gpuinfo.org](https://vulkan.gpuinfo.org/listbufferformats.php) has information on how widespread support is.
For 1- and 2-channel `R{8,16}_{SINT,UINT,SFLOAT}`, support is currently around 80% for storage texel buffers.

**TODO:** We should do this query against WebGPU's baseline requirements, as the percentage for devices we actually support may be higher.

Vulkan has a `maxTexelBufferElements` limit for the maximum size of a texel buffer.
[gpuinfo.org shows that](https://vulkan.gpuinfo.org/displaydevicelimit.php?name=maxTexelBufferElements&platform=all) more than 85% of devices support 128MB texel buffers.


### Metal

Metal has a `texel_buffer` type that provides similar functionality, which was introduced in Metal 2.1.
The [Metal Feature Set Tables](https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf) show the supported formats for each access mode.
Unnormalized integer and floating point formats are supported for all access modes, as is `RGBA8Unorm`.
Using a `read-write` access mode also requires support for the Tier 2 `MTLReadWriteTextureTier`.
A `mem_texture` fence would be needed to make texel buffer writes visible within an invocation.

To get coverage on older Metal versions, it would be possible to polyfill by using a regular device buffer and doing the format conversions inside the shader.
This requires that the storage format is specified inside the shader.

The maximum texel buffer size is 64MB for the Apple2 GPU family, and 256MB for Apple3 and above.


### D3D12

In D3D12, a texel buffer can map to an Unordered Access View (UAV) for a buffer with a `DXGI_FORMAT`, and that UAV can be accessed in the shader with 32-bit result types.
See [Typed unordered access view (UAV) loads](https://docs.microsoft.com/en-us/windows/win32/direct3d12/typed-unordered-access-view-loads).
The `RWBuffer` should be prefixed with `globallycoherent`, and the element type needs to be prefixed with `unorm` or `snorm` if a normalized format is being used.

Format support for typed UAV loads and stores in D3D12 can be checked [here](https://docs.microsoft.com/en-us/windows/win32/direct3ddxgi/hardware-support-for-direct3d-12-0-formats).
The set of required formats includes:

```
R8G8B8A8_UNORM
R8G8B8A8_UINT
R8G8B8A8_SINT
R16G16B16A16_UINT
R16G16B16A16_SINT
R16G16B16A16_FLOAT
R8_UINT
R8_SINT
R16_UINT
R16_SINT
R16_FLOAT
R32_UINT
R32_SINT
R32_SFLOAT
R32G32B32A32_UINT
R32G32B32A32_SINT
R32G32B32A32_FLOAT
```


# Open Questions

1. Should this be an extension, or a core feature?
   - To make it core, implementations would need to polyfill for Metal <2.1. We would also need to drop the formats that are not required everywhere (e.g. `R8_UINT`), or make them optional.
   - Decision at F2F:
       - Make it core.
       - Drop the formats that are not widespread (leaving them for a [future texture format tier extension](https://github.com/gpuweb/gpuweb/issues/3837)).
       - We do not need to support Metal <2.1 (Metal 2.2 is our minimum requirement now).
