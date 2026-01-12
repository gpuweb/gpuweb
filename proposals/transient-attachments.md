# Transient Attachments

* Status: [Draft](README.md#status-draft)
* Created: 2025-11-19
* Issue: [#5396](https://github.com/gpuweb/gpuweb/issues/5396)

## Motivation

When a texture is declared transient (or "memoryless"), the GPU knows that the contents of that texture are only needed temporarily—specifically, only within the current render pass. Moreover, since the texture contents are discarded after the render pass, the driver may not even need to allocate space for that texture in the main VRAM at all.

Even without hardware support for transient attachments, the hint can be used to reuse the allocation of transient textures between passes, which reduces peak memory usage.

## API changes

A new `TRANSIENT_ATTACHMENT` is added to `GPUTextureUsage` to let developers create attachments that allow render pass operations to stay in tile memory, avoiding VRAM traffic and potentially avoiding VRAM allocation for the textures.

```webidl
partial namespace GPUTextureUsage {
    const GPUFlagsConstant TRANSIENT_ATTACHMENT = 0x20;
};
```

## Validation

The `GPUCanvasContext/configure(configuration)` algorithm is extended with the following change:

- If `configuration.usage` includes the `TRANSIENT_ATTACHMENT` bit, throw a TypeError.

The `validating GPUTextureDescriptor(this, descriptor)` algorithm is extended with the following change:

- If `descriptor.usage` includes the `TRANSIENT_ATTACHMENT` bit:
  - `descriptor.usage` must contain only and exactly `TRANSIENT_ATTACHMENT` and `RENDER_ATTACHMENT` bits.
  - `descriptor.dimension` must be `"2d"`.
  - `descriptor.mipLevelCount` must be 1.
  - `descriptor.size.depthOrArrayLayers` must be 1.

The `GPURenderPassColorAttachment Valid Usage` algorithm is extended with the following change:

- If `renderViewDescriptor.usage` includes the `TRANSIENT_ATTACHMENT` bit:
  - `this.loadOp` must be `"clear"`.
  - `this.storeOp` must be `"discard".`

The `GPURenderPassDepthStencilAttachment Valid Usage` algorithm is extended with the following change:

- If `this.view.[[descriptor]].usage` includes the `TRANSIENT_ATTACHMENT` bit:
  - If format has a depth aspect:
    - `this.depthLoadOp` must be `"clear"`.
    - `this.depthStoreOp` must be `"discard".`
  - If format has a stencil aspect:
    - `this.stencilLoadOp ` must be `"clear"`.
    - `this.stencilStoreOp ` must be `"discard".`

## Javascript example

```js
const adapter = await navigator.gpu.requestAdapter();
const device = await adapter.requestDevice();

if ('TRANSIENT_ATTACHMENT' in GPUTextureUsage) {

  const transientTexture = device.createTexture({
    size: [42, 42],
    // The TRANSIENT_ATTACHMENT flag indicates the texture content is temporary,
    // potentially keeping it in fast on-chip memory.
    usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TRANSIENT_ATTACHMENT,
    format: 'rgba8unorm',
  });

  // I can now use this texture to serve as transient attachments, e.g.
  // as color attachments in a render pipeline.
}
```

## Resources

- [VkMemoryPropertyFlagBits(3) Manual Page](https://registry.khronos.org/VulkanSC/specs/1.0-extensions/man/html/VkMemoryPropertyFlagBits.html)
- [MTLStorageModeMemoryless | Apple Developer Documentation](https://developer.apple.com/documentation/metal/mtlstoragemode/memoryless?language=objc)

## Open sub-issues

- https://github.com/search?q=parent-issue%3Agpuweb%2Fgpuweb%235179+state%3Aopen+&type=issues

