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

A new `swizzle` option is added to the `GPUTextureViewDescriptor` which allows for rearranging or replacing the data from the texture's channels when creating a `GPUTextureView`. The `swizzle` value is a string of length four, with each character mapping to the view's red, green, blue, and alpha components, respectively. Each character can be either:
- `"r"`: Take its value from the red channel of the texture.
- `"g"`: Take its value from the green channel of the texture.
- `"b"`: Take its value from the blue channel of the texture.
- `"a"`: Take its value from the alpha channel of the texture.
- `"0"`: Force its value to 0.
- `"1"`: Force its value to 1.

```webidl
partial dictionary GPUTextureViewDescriptor {
    DOMString swizzle = "rgba";
};
```

If the `"texture-component-swizzle"` feature is enabled, reading or sampling the depth or stencil aspect of a texture behaves as if the texture contains the values (V, 0, 0, 1) where V is the actual depth or stencil value. Otherwise, the values are (V, X, X, X) where X is an implementation-defined unspecified value.
To reduce compatibility issues in practice, implementations *should* provide (V, 0, 0, 1) wherever possible, even if this feature is not enabled.

## Validation

The `GPUTexture.createView(descriptor)` algorithm is extended with the following changes:

- `descriptor.swizzle` must be a four-character string that only includes `"r"`, `"g"`, `"b"`, `"a"`, `"0"`, or `"1"`, otherwise a `TypeError` is raised.

- If `descriptor.swizzle` is not `"rgba"`, the `"texture-component-swizzle"` feature must be enabled.

The `renderable texture view` definition requirements are extended with the following change:

- `descriptor.swizzle` must be `"rgba"`.

The `GPUDevice.createBindGroup()` algorithm is extended with the following change:

- `storageTextureView.[[descriptor]].swizzle` must be `"rgba"`.

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

// Map the view's red, green, blue components to the texture's red channel
// and force the view's alpha component to 1.0.
const textureView = myTexture.createView({ swizzle: "rrr1" });
```

## Resources

- [Vkswizzle(3) Vulkan Manual Page](https://registry.khronos.org/vulkan/specs/latest/man/html/VkComponentMapping.html)
- [D3D12_SHADER_RESOURCE_VIEW_DESC structure (d3d12.h)](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/ns-d3d12-d3d12_shader_resource_view_desc)
- [MTLTextureSwizzleChannels | Apple Developer Documentation](https://developer.apple.com/documentation/metal/mtltextureswizzlechannels)
- [OpenGL ES 3.1 section 14.2.1](https://registry.khronos.org/OpenGL/specs/es/3.1/es_spec_3.1.pdf#page=331)
