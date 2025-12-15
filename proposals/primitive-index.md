# Primitive Index

* Status: [Merged](README.md#status-merged)
* Issue: [#1786](https://github.com/gpuweb/gpuweb/issues/1786)

The WebGPU feature `primitive-index` introduces the ability to use the `primitive_index` builtin in fragment shaders in WGSL.

## Motivation

The `primitive_index` is a unique integer for each primitive (triangle, line, or point) in a single drawn instance. This is useful in a variety of effects, from simple uses like computing flat shading to more complex uses such as advanced material effects or supporting modern virtualized geometry pipelines.

It is a common feature in the underlying native APIs (D3D, Metal, Vulkan, OpenGL), and as a result supporting this builtin increases the number of shaders that can be directly ported to the web.

## Status
This feature has been approved by the working group and added to the WebGPU and WGSL specs.

## Native API Availability
| Platform | Type | Notes |
|----------|------|-------|
| SPIR-V | 32-bit integer | Requires geometry shaders, mesh shaders, or raytracing. Available as the `PrimitiveID` builtin |
| HLSL | u32 | Requires D3D10. Available as the `SV_PrimitiveID` semantic |
| GLSL | i32 | Requires GLSL 1.50 and later, ESSL 3.2. (ESSL 3.1 with GL_EXT_geometry_shader). Available as the `gl_primitiveID` builtin |
| Metal | u32 | Requires Metal 2.2 on MacOS or Metal 2.3 on iOS. Available as `[[primitive_id]]` |

Due to non-universal availability, use of this builtin will be gated behind a WebGPU feature, `primitive-index`. Also, the `enable primitive_index` statement will be required when using this builtin with WGSL.

## Behavior
 * `primitive_index` is restricted to `fragment` shaders.
 * The index of the first primitive is zero, incrementing by one for each subsequent primitive.
 * The `primitive_index` resets to zero between each instance drawn.
 * The `primitive_index` value is uniform across the primitive.
 * Primitive restart has no effect on the value of variables decorated with `primitive_index`.
 * HLSL specifies that if the primitive id overflows (exceeds 2^32 – 1), it wraps to 0.
   * This should not apply to WebGPU since all applicable draw call count arguments are unsigned 32 bit integers, and thus can never exceed that.
 * There is no support for automatically generating a primitive index for adjacent primitives.
 * For an adjacent primitive, the index is only maintained for the internal non-adjacent primitives.

All of the topologies in `GPUPrimitiveTopology` are supported. (Generally, adjacency topologies would
not be supported but WebGPU does not have any adjacency topologies).

| Topology | Primitive |
|----------|-----------|
| point-list | Each vertex is a primitive |
| line-list | Each vertex pair is a primitive |
| line-strip | Each adjacent vertex pair is a primitive |
| triangle-list | Each vertex triplet is a primitive |
| triangle-strip | Each group of 3 adjacent vertices is a primitive |

## WGSL Specification
This extension adds a new `builtin_value_name` entry for `primitive_index`.
An entry is added to the _Built-in input and output values_ table:
 * _Name_: `primitive_index`
 * _Stage_: `fragment`
 * _Direction_: `input`
 * _Type_: `u32`
 * _Extension_: `primitive_index`

## Example usage

Enabling the `primitive-index` feature for a `GPUDevice`:

```js
const adapter = await navigator.gpu.requestAdapter();

const requestedFeatures = [];
if (adapter.features.has('primitive-index')) {
    requestedFeatures.psuh('primitive-index');
} else {
    // Use an alternate code path or communicate error to user.
}

const device = await adapter.requestDevice({ requestedFeatures });
```

Using `primitive_index` builtin in a WGSL shader:

```wgsl
enable primitive_index

@fragment fn fs_main(@builtin(primitive_index) prim_index: u32) -> @location(0) vec4f {
    return vec4f(f32(prim_index));
}
```

## Alternatives considered

The value that the `primitive_index` provides is impossible to emulate in all situations without API support. The most practical route would be to calculate the index from the existing `vertex_index` builtin, but this does not support indexed geometry. Given that indexed geometry is the most common format for large meshes and can reduce memory requirements significantly, this is not a viable restriction.

## References
* [GLSL gl_PrimitiveID](https://registry.khronos.org/OpenGL-Refpages/gl4/html/gl_PrimitiveID.xhtml)
  * [GL_EXT_geometry_shader](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_geometry_shader.txt)
* [ESSL gl_PrimitiveID](https://registry.khronos.org/OpenGL-Refpages/es3/html/gl_PrimitiveID.xhtml)
* [HLSL PrimitiveId](https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-input-assembler-stage-using#primitiveid)
* [HLSL SV_PrimitiveId](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-semantics)
  * [HLSL FunctionalSpec](https://microsoft.github.io/DirectX-Specs/d3d/archive/D3D11_3_FunctionalSpec.htm#:~:text=declaration%20for%20Shaders.-,8.17%20PrimitiveID,-PrimitiveID%20is%20a)
* [Metal p.119](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf)
* [Vulkan PrimitiveId](https://registry.khronos.org/vulkan/specs/latest/man/html/PrimitiveId.html)
