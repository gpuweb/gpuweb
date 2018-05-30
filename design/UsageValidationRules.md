## Definition of "resources being used"

Resources in WebGPU can be used in different ways that are declared at resource creation time and interact with various validation rules.

Buffers have the following usages (and commands inducing that usage):
 - `VERTEX` for the `buffers` in calls to `WebGPUCommandEncoder.setVertexBuffers`
 - `INDEX` for `buffer` in calls to `WebGPUCommandEncoder.setIndexBuffer`
 - `INDIRECT` for `indirectBuffer` in calls to `WebGPUCommandEncode.{draw|drawIndexed|dispatch}Indirect`
 - `UBO` and `STORAGE` for buffers referenced by bindgroups passed to `setBindGroup`, with the usage corresponding to the binding's type.
 - `TRANSFER_SRC` for buffers used as the copy source of various commands.
 - `TRANSFER_DST` for buffers used as the copy destination of various commands.
 - (Maybe `STORAGE_TEXEL` and `UNIFORM_TEXEL`?)

Textures have the following usages:
 - `OUTPUT_ATTACHMENT` for the subresources referenced by `WebGPURenderPassDescriptor`
 - `SAMPLED` and `STORAGE` for subresources corresponding to the image views referenced by bindgroups passed to `setBindGroup`, with the usage corresponding to the binding's type.
 - `TRANSFER_SRC` for textures used as the copy source of various commands.
 - `TRANSFER_DST` for textures used as the copy destination of various commands.

Read only usages are `VERTEX`, `INDEX`, `INDIRECT`, `UBO`, `TRANSFER_SRC` and `SAMPLED`.

## Render passes

In render passes the only writable resources are textures used as `OUTPUT_ATTACHMENT` and resources used as `STORAGE`.

To avoid data hazards the simplest validation rules would be to check for every subresource that it is used as either:
 - `OUTPUT_ATTACHMENT`
 - A combination of read-only usages
 - `STORAGE`

## Compute passes

They are similar to render passes, every subresource (alternatively every resource) must be used as either:
 - A combination of read-only usages
 - `STORAGE`

## Other operations

Assuming we don't have "copy passes" and that other operations are top-level, then a command buffers looks like a sequence of:
 - Compute passes
 - Render passes
 - Copies and stuff

There are no particular constraints on the usage of the operations (apart from resources having been created with the proper usage flags).

## Discussion

There are cases where the resource usage tracking could get expensive for example if subresources of a texture with an odd index use `STORAGE` while even ones use `SAMPLED`.
That said such a case is unlikely to happen in real-world applications.

The cost of the state tracking necessary to add memory barriers inside compute passes and at command buffer top-level seems manageable (though difficult to describe in the 30 minutes I have before the meeting).

There is no read-only storage that could be used in combination with other read-only usages because some APIs don't support it.
For example D3D12 assumes UAV is always writeable and disallows transitioning to a combination of UAV and a read-only usage.

## Open questions

### More constrained texture usage validation

Each layer and mip-level of textures can have an independent usage which means implementations might need to track usage per mip-level per layer of a resource.
If this is deemed too costly, we could only have two sub-resources tracked in textures: the part as `OUTPUT_ATTACHMENT` and the rest.
This would mean for example that a texture couldn't be used as both  `STORAGE` and a read-only usage inside a render pass.
The state tracking required in implementation would become significantly simpler at the cost of flexibility for the applications.
When using the more constrained version of usage validation for textures, the cost of validation is O(commands).
