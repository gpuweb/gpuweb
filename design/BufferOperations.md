# Buffer operations

This explainer describes the operations that are available on the `GPUBuffer` object directly.
They are `setSubData` which is an immediate data upload operation, and `mapWriteAsync`, `mapReadAsync` and `unmap` which are memory mapping operations.

## Prelimineries: buffered / unbuffered commands

Assuming there is a single queue, there are two types of commands in WebGPU:

 - "Buffered commands": any commands on a `GPUCommandBuffer`, `GPUComputePassEncoder` or `GPURenderPassEncoder`.
 - "Unbuffered commands": all other commands.

Assuming there is a single queue, there is a total order on the unbuffered commands: they all execute atomically in the order they were called.
`GPUQueue.submit` is special because it atomically executes all the commands stored in its `commands` argument.

## `GPUBuffer.setSubData`

```webidl
partial interface GPUBuffer {
    void setSubData(u32 offset, ArrayBuffer data);
}
```

Calling `setSubData` on a `buffer` causes its content in the range `[offset, offset + data.length)` to be updated with the content of `data`.
The update to the content of `buffer` happens atomically after all previous unbuffered operations and before all subsequent unbuffered operations.

The following must be true or a validation error occurs on the call to `setSubData`:

 - `buffer` must have been created with the `TRANSFER_DST` usage flag.
 - `offset + data.length` must be less or equal to the size of `buffer`.
 - `buffer` must be in the unmapped state (which also means it hasn't been destroyed with `GPUBuffer.destroy`)
 - `data.length` and `offset` aren't aligned (TODO investigate alignment constraints)

## Buffer mapping

### `MAP_READ` and `MAP_WRITE`

The `MAP_READ` and `MAP_WRITE` buffer creation usage flags need to be specified to create a buffer mappable for reading (resp. for writing).
An additional validation constraint is that the `MAP_READ` and `MAP_WRITE` may not be used in combination.

```webidl
partial interface GPUBufferUsage {
    const u32 MAP_READ = 1;
    const u32 MAP_WRITE = 2;
}
```

**TODO**: should `MAP_WRITE` be allowed only with read-only usages?
It would allow clearing the buffer only on creation and not on every map.

### The `GPUBuffer` state machine

Buffers have an internal state machine that has three states:

 - **Unmapped**: where the buffer can be used in queue submits or `setSubData`
 - **Mapped**: after a map operation and the subsequent `unmap` where the buffer cannot be used in queue submits or `setSubData`
 - **Destroyed**: after a call to `GPUBuffer.destroy` where it is a validation error to do anything with the buffer.

In the following a buffer's state is a shorthand for the buffer's state machine.
Buffers created with `GPUDevice.createBuffer` start in the unmapped state.
Buffers created with `GPUDevice.createBufferMapped` or `GPUDevice.createBufferMappedAsync` start in the mapped state.

State transitions are the following:

 - Unmapped to destroyed: with `GPUBuffer.destroy`
 - Mapped to destroyed: with `GPUBuffer.destroy`
 - Unmapped to mapped: with any successful `mapReadAsync` or `mapWriteAsync` call.
 - Mapped to unmapped: with any successful `unmap` call.

### Buffer mapping operations

The mapping operations for buffer mapping are:

```webidl
partial interface GPUBuffer {
    Promise<ArrayBuffer> mapReadAsync();
    Promise<ArrayBuffer> mapWriteAsync();
};
```

These calls return a promise of a "mapping" that is an `ArrayBuffer` that represents the content of the buffer for reading (for `mapReadAsync`) or writing (for `mapWriteAsync`).
The promise will settle before signals for the completion of follow-up unbuffered commands.
Upon success the buffer is put in the mapped state.

The following must be true or the call fails and will return a promise that will reject:

 - `buffer` must have been created with the `MAP_READ` usage flag for `mapReadAsync` and the `MAP_WRITE` flag for `mapWriteAsync`
 - `buffer` must be in the unmapped state.

A buffer can be unmapped with:

```webidl
partial interface GPUBuffer {
    void unmap();
};
```

Upon success the buffer is put in the unmapped state, its mapping detached or a pending mapping promise rejected.

The following must be true or the unmapping call on `buffer` fails:

 - `buffer` must have been created with the `MAP_READ` or the `MAP_WRITE` usage flags.
 - `buffer` must not be in the destroyed state (this means it is ok to call `unmap` on an unmapped buffer).

Calling `GPUBuffer.destroy` on a buffer with the `MAP_READ` or `MAP_WRITE` usage flags contains an implicit call to `GPUBuffer.unmap`.
Note that the mapping isn't detached when the `GPUBuffer` is garbage-collected, so this means that mappings keep a reference to their buffer.

What happens with the content of mappings depends of which function was used to create it:
 - Mappings created with `mapReadAsync` represents the content of the buffer after all previous unbuffered operations before the call to `mapReadAsync` completed.
   Nothing happens when the mapping is detached.
 - Mappings created with `mapWriteAsync` are filled with zeros.
   When they are detached, it is as if `buffer.setSubData(0, mapping)` was called.

### Creating an already mapped buffer

A buffer can be created already mapped:

```webidl
partial interface GPUDevice {
    (GPUBuffer, ArrayBuffer) createBufferMapped(GPUBufferDescriptor descriptor);
    Promise<(GPUBuffer, ArrayBuffer)> createBufferMappedAsync(GPUBufferDescriptor descriptor);
};
```

`GPUDevice.createBufferMapped` returns a buffer in the mapped state along with an write mapping representing the whole range of the buffer.
`GPUDevice.createBufferMappedAsync` returns the same values as a promise and provides more opportunities for optimization in implementations of the API.

The mapping starts filled with zeros.

## Examples

Using `GPUBuffer.setSubData` would look like this:

```js
// device is a GPUDevice
const myUBO = device.createBuffer({
    "size":4 * 16,
    "usage": GPUBufferUsage.TRANSFER_DST | GPUBufferUsage.UNIFORM
});

const uboData = Float32Array(some4x4Matrix);

myUBO.setSubData(0, uboData.buffer);
// myUBO now contains data representing some44Matrix
```

Using `GPUBuffer.mapReadAsync` would look like this:

```js
const readPixelsBuffer = device.createBuffer({
    "size": 4,
    "usage": GPUBufferUsage.MAP_READ | GPUBufferUsage.TRANSFER_DST,
});

// Commands copying a pixel from a texture into readPixelsBuffer are submitted

readPixelsBuffer.mapReadAsync().then((data) => {
    checkPixelValue(data);

    // Unmap if we want to reuse the buffer
    readPixelsBuffer.unmap();
});
```

Using `GPUBuffer.mapWriteAsync` would look like this:

```js
// model is some 3D framework resource.
const size = model.computeVertexBufferSize();

const stagingVertexBuffer = device.createBuffer({
    "size": size,
    "usage": GPUBufferUsage.MAP_WRITE | GPUBufferUsage.TRANSFER_SRC,
});

stagingVertexBuffer.mapWriteAsync().then((stagingData) => {
    model.decompressVerticesIn(stagingData);

    stagingvertexBuffer.unmap();

    // Enqueue copy from the staging buffer to the real vertex buffer.
});
```
