# Fragment depth (less, greater, any)

**Roadmap:** This proposal is **under active development, but has not been standardized for inclusion in the WebGPU specification. The proposal is likely to change before it is standardized.** WebGPU implementations **must not** expose this functionality; doing so is a spec violation. Note however, an implementation might provide an option (e.g. command line flag) to enable a draft implementation, for developers who want to test this proposal.

Issue:

- https://github.com/gpuweb/gpuweb/issues/5342

## Motivation

The ability for fragment shaders to explicitly write to the depth buffer via the `@builtin(frag_depth)` attribute is critical for many modern rendering techniques, including custom depth biasing for shadows, precise depth fog, and complex depth-based effects.

In the current WGSL specification, the mere act of writing to `@builtin(frag_depth)` often incurs a significant performance penalty because driver heuristics cannot guarantee that the fragment shader output will adhere to the depth written by the rasterizer's interpolated depth. Consequently, writing to `frag_depth` typically forces the GPU to disable crucial early-Z optimizations for the entire draw call.

The introduction of a new `depth_mode` built-in parameter for the `@builtin(frag_depth)` with modes `less`, `greater`, and `any` directly addresses this performance limitation by letting the developer express their intent to the hardware.

*   The `any` mode maintains the existing, unconditional behavior of `frag_depth`.
*   The `less` and `greater` modes are used when a fragment shader declares it will only write depth values that are guaranteed to be less than (or greater than) the existing depth. The driver can be assured that any fragment whose interpolated depth already fails the declared comparison cannot possibly satisfy the conditional write, allowing it to be rejected early.

## HLSL

*   `SV_Depth`: Depth buffer data. Can be written by pixel shader
*   `SV_DepthGreaterEqual`: In a pixel shader, allows outputting depth, as long as it is greater than or equal to the value determined by the rasterizer. Enables adjusting depth without disabling early Z.
*   `SV_DepthLessEqual`: In a pixel shader, allows outputting depth, as long as it is less than or equal to the value determined by the rasterizer. Enables adjusting depth without disabling early Z.

Source: https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-semantics

## Metal

If a fragment function writes a depth value, the `depth_argument` needs to be specified with one of the following values: `any`, `greater`, `less`.

Source: https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf

## OpenGL

The built-in fragment shader variable `gl_FragDepth` may be redeclared using one of the following layout qualifiers: `depth_any`, `depth_greater`, `depth_less`,  `depth_unchanged`.

Source: https://registry.khronos.org/OpenGL/extensions/EXT/EXT_conservative_depth.txt

## Vulkan

In cases where you know that the fragment shader will move the depth value in only one direction (toward or away from the viewer), you can apply the SPIR-V `DepthGreater` or `DepthLess` execution modes to the fragment shader’s entry point with the `OpExecutionMode` instruction.

When `DepthGreater` is applied, then Vulkan knows that no matter what your shader does, the resulting depth values produced by the fragment shader will only be greater than the values produced by interpolation. Therefore, if the depth test is `VK_COMPARE_OP_GREATER` or `VK_COMPARE_OP_GREATER_OR_EQUAL`, then the fragment shader cannot negate the result of a depth test that’s already passed.

Likewise, when `DepthLess` is applied, then Vulkan knows that the fragment shader will only make the resulting depth value less than it would have been and therefore cannot negate the result of a passing `VK_COMPARE_OP_LESS` or `VK_COMPARE_OP_LESS_OR_EQUAL` test.

Source: https://usermanual.wiki/Document/Vulkan2BProgramming2BGuide2BThe2BOfficial2BGuide2Bto2BLearning2BVulkan.1140066211.pdf

## WGSL

### Language extension

| WGSL language extension | Description |
| --- | --- |
| `fragment_depth` | Adds built-in `depth_mode` parameter support for fragment's depth |

### Built-in `depth_mode` parameter to `frag_depth`

An optional `depth_mode` parameter declated after the built-in `frag_depth` name is allowed and
defaults to `any`.

It can be either `@builtin(frag_depth)`, `@builtin(frag_depth, greater)`,
`@builtin(frag_depth, lesser)`, or `@builtin(frag_depth, any)`.

This applies `depth_mode` on the `frag_depth` built-in output value in a fragment shader.

### Example usage

```wgsl
requires fragment_depth;

@fragment
fn main() -> @builtin(frag_depth, greater) f32 {
  return 1.0f;
}
```

### Built-in Value Mappings

| Built-in | SPIR-V | MSL | HLSL | GLSL |
|----------|--------|-----|------|------|
| frag_depth, any | SpvBuiltInFragDepth | depth(any) | SV_Depth | depth_any |
| frag_depth, greater | SpvBuiltInFragDepth + OpExecutionMode DepthGreater | depth(greater) | SV_DepthGreaterEqual | depth_greater |
| frag_depth, less | SpvBuiltInFragDepth + OpExecutionMode DepthLess | depth(less) | SV_DepthLessEqual | depth_less |

## Open sub-issues

- https://github.com/search?q=parent-issue%3Agpuweb%2Fgpuweb%235342+state%3Aopen+&type=issues

## Resources

- https://github.com/gfx-rs/wgpu/pull/7676
- https://github.com/gpuweb/gpuweb/issues/4891#issuecomment-3341897141
- https://therealmjp.github.io/posts/to-earlyz-or-not-to-earlyz/
