# Texture component swizzle 🥤

**Roadmap:** This proposal is **under active development, but has not been standardized for inclusion in the WebGPU specification. The proposal is likely to change before it is standardized.** WebGPU implementations **must not** expose this functionality; doing so is a spec violation. Note however, an implementation might provide an option (e.g. command line flag) to enable a draft implementation, for developers who want to test this proposal.

Issue:

- https://github.com/gpuweb/gpuweb/issues/5179


## Motivation

Texture component swizzle lets you to specify how the channels of a texture (red, green, blue, and alpha) are mapped to the color components when accessed by a shader. It is supported everywhere WebGPU runs, except for Mac family 1 GPU devices. Therefore it would be nice to expose it as an optional feature.

## API changes

The GPUFeatureName `"texture-component-swizzle"` controls access to texture component mapping, which is anticipated to be available in Metal, Vulkan, D3D12, and OpenGL ES 3.

```webidl
partial enum GPUFeatureName {
    "texture-component-swizzle",
};
```

The GPUTextureViewDescriptor `swizzle` option lets you rearrange or even replace the data from a texture's channels when creating a GPUTextureView. This is done by assigning a value from the GPUComponentSwizzle enum to each of the `r`, `g`, `b`, and `a` components in your texture view.

```webidl
partial dictionary GPUTextureViewDescriptor {
    GPUTextureComponentSwizzle swizzle;
};

// Structure specifying a custom color component mapping for a texture view.
dictionary GPUTextureComponentSwizzle {
    GPUComponentSwizzle r = "r";
    GPUComponentSwizzle g = "g";
    GPUComponentSwizzle b = "b";
    GPUComponentSwizzle a = "a";
};

// A set of options to choose from when specifying a component swizzle.
enum GPUComponentSwizzle {
    "zero",     // Force its value to 0.
    "one",      // Force its value to 1.
    "r",        // Take its value from the red channel of the texture.
    "g",        // Take its value from the green channel of the texture.
    "b",        // Take its value from the blue channel of the texture.
    "a",        // Take its value from the alpha channel of the texture.
};
```

The `GPUTexture.createView(descriptor)` algorithm is extended with the following validation rules changes:

- If `descriptor.usage` includes the `RENDER_ATTACHMENT` or `STORAGE_BINDING` bit:
  - `descriptor.swizzle.r` must be `"r"`.
  - `descriptor.swizzle.g` must be `"g"`.
  - `descriptor.swizzle.b` must be `"b"`.
  - `descriptor.swizzle.a` must be `"a"`.

## Validation

A validation error happens if the swizzle is not the default and the `"texture-component-swizzle"` feature is not enabled.

If the feature `"core-features-and-limits"` is not enabled on a device, a draw call may not bind two views of the same texture differing in swizzle. Only a single swizzle per texture is supported. This is enforced via validation at draw time.

## Javascript example

Imagine you have a texture with a single red channel (`r8unorm` format). In your shader, you want to use this as a grayscale image where the red, green, and blue components all have the same value from the texture's red channel, and the alpha is fully opaque:

```js
const adapter = await navigator.gpu.requestAdapter();
if (!adapter.features.has("texture-component-swizzle")) {
  throw new Error("Texture component swizzle is not available");
}
// Explicitly request texture component mapping support.
const device = await adapter.requestDevice({
  requiredFeatures: ["texture-component-swizzle"],
});

// ... Assuming myTexture is a GPUTexture with a single red channel.

const textureView = myTexture.createView({
  swizzle: {
    r: 'r',  // Map the view's red component to the texture's red channel
    g: 'r',  // Map the view's green component to the texture's red channel
    b: 'r',  // Map the view's blue component to the texture's red channel
    a: 'one' // Force the view's alpha component to 1.0
  }
});
```

## Open Questions

- Are there new validation rules needed if the view is depth-stencil or multisampled?
- In Compatibility Mode, this could count against the [texture and sampler combination limit](https://github.com/gpuweb/gpuweb/blob/main/proposals/compatibility-mode.md#21-limit-the-number-of-texturesampler-combinations-in-a-stage), or it might not be exposed at all.

## Resources

- [Vkswizzle(3) Vulkan Manual Page](https://registry.khronos.org/vulkan/specs/latest/man/html/VkComponentMapping.html)
- [D3D12_SHADER_RESOURCE_VIEW_DESC structure (d3d12.h)](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_shader_resource_view_desc)
- [MTLTextureSwizzleChannels | Apple Developer Documentation](https://developer.apple.com/documentation/metal/mtltextureswizzlechannels)
- [OpenGL ES 3.1 section 14.2.1](https://registry.khronos.org/OpenGL/specs/es/3.1/es_spec_3.1.pdf#page=331)
