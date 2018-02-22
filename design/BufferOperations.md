# Buffer operations

This describes operations that are done on `WebGPUBuffer` objects directly and are not buffered inside a `WebGPUCommandBuffer`.
The two primitives we need to support are the CPU writing data inside the buffer for use by the GPU (upload) and the CPU reading data produced by the GPU (readback).

Design constraints are:

 - For the portability of the API, prevent data races between the CPU and the GPU.
 - For performance, minimize the number of times the data is copied around.
 - To make the API non-blocking, only allow asynchronous readbacks.
 - For performance on multi-process implementations, make an asynchronous upload path.

## Buffer mapping

### map[Write|Read] and unmap

The way to have the minimal number of copies for upload and readback is to provide a buffer mapping mechanism.
This mechanism has to be asynchronous to ensure the GPU is done using the buffer before the application can look into the ArrayBuffer.
Otherwise on implementation where the ArrayBuffer is directly a pointer to the buffer memory, data races between the CPU and the GPU could occur.

We want the status of a map operation to act as both a promise, and something that's pollable as there are advantages to both.
`WebGPUMappedMemory` is an object that is `then`-able, meaning that it acts like a Javascript `Promise` but is pollable at the same time.

The mapping operations for `WebGPUBuffer` are:

```
partial interface WebGPUBuffer {
    WebGPUMappedMemory mapWrite(u32 offset, u32 size);
    WebGPUMappedMemory mapRead(u32 offset, u32 size);
};
```

These operations return new `WebGPUMappedMemory` objects representing the current range of the buffer for writing or mapping.
The results are initialized in the "pending" state and transition at Javascript task boundary to the "available" state when the implementation can determine the GPU is done using the buffer.
Calling `mapRead` or `mapWrite` puts the buffer in the mapped state.
No operations are allowed in a buffer in that state except additional calls to `mapRead` or `mapWrite` and calls to `unmap`.
In particular a mapped buffer cannot be used in a `WebGPUCommandBuffer` given to `WebGPUQueue.submit`.
The following must be true or a validation error occurs for `mapWrite` (resp. `mapRead`):

 - The buffer must have been created with the `WebGPUBufferUsage.MAP_WRITE` (resp. `WebGPUBufferUsage.MAP_READ`) usage.
 - `offset + size` must not overflow and be at most the size of the buffer
 - Depending on the design of memory barriers, the buffer must be, or allowed to be in the `WebGPUBufferUsage.MAP_WRITE` (resp. `WebGPUBufferUsage.MAP_READ`) usage.

Then a mapped buffer can be unmapped with:

```
partial interface WebGPUBuffer {
    void unmap();
};
```

This operation invalidates all the `WebGPUMappedMemory` created from the buffer and puts the buffer in the unmapped state.
The buffer must be in the mapped state otherwise a validation error occurs when `unmap` is called.

### WebGPUMappedMemory

`WebGPUMappedMemory` is an object representing a mapped region of a buffer that's both pollable and promise-like.

It can be in one of three states: pending, available and invalidated.

The pollable interface is:

```
partial interface WebGPUMappedMemory {
    bool isPending();
    ArrayBuffer getPointer();
};
```

`isPending` return true if the object is in the pending state, false otherwise.
`getPointer` returns an ArrayBuffer representing the buffer data if the object is in the available state, null otherwise.

`WebGPUMappedMemory` is also `then`-able, meaning that it acts like a Javascript `Promise`:

```
partial interface WebGPUMappedMemory {
    Promise then(WebGPUMappedMemorySuccessCallback success,
                 optional WebGPUMappedMemoryErrorCallback error);
};
```

This acts like a `Promise<ArrayBuffer>.then` that is resolved on the Javascript task boundary in which the implementation detects the GPU is done with the buffer.
On that boundary:

 - The `WebGPUMappedMemory` goes in the available state.
 - If the `WebGPUMappedMemory` was created via `WebGPUBuffer.mapWrite`, its content is cleared to 0.
 - `success` is called with the content of the memory as an argument.

If `success` hasn't been called when the WebGPUMappedMemory gets invalidated (meaning the object is still in the pending state), `error` is called instead. When `WebGPUMappedMemory` goes from the available state to the invalidated state, the `ArrayBuffer` for its content gets neutered. The return value of `then` acts like the return value of `Promise.then`.

The `ArrayBuffer` of a `WebGPUMappedMemory` created from a `mapWrite` is where the application should write the data and its content is made available to the buffer when the `WebGPUMappedMemory` is invalidated (i.e. `WebGPUBuffer.unmap` is called).

## Immediate data upload

Buffer mapping is the path with the least number of copies but it is often useful to upload data to a buffer *right now*, if only for debugging.
A `WebGPUBuffer` operation is provided that takes an ArrayBuffer and copies its content at an offset in the buffer.

```
partial interface WebGPUBuffer {
    void setSubData(ArrayBuffer data, u32 offset);
}
```

This operation acts as if it was done after all previous "device-level" commands and before all subsequent "device-level" commands.
"Device level" commands are all commands not buffered in a `WebGPUCommandBuffer`, and include `WebGPUQueue.submit`.
The content of `data` is only read during the call and can be modified by the application afterwards.
The following must be true or a validation error occurs:

 - The buffer must have been created with the `WebGPUBufferUsage.TRANSFER_DST` usage flag.
 - `offset + data.length` must not overflow and be at most the size of the buffer.
 - Depending on the design of memory barriers, the buffer must be, or allowed to be in the `WebGPUBufferUsage.TRANSFER_DST` usage.
   - In particular the buffer must not be currently mapped.

## Unused designs

### Persistently mapped buffer

Persistently mapped buffer are when the result of mapping the buffer can be kept by the application while the buffer is in use by the GPU.
We didn't find a way to have persistently mapped buffers and at the same time keep things data race free between the CPU and GPU.
Being data race free would be possible if ArrayBuffer could be unneutered but this is not the case.

### Promise<ArrayBuffer> readback();

This didn't have a pollable interface and forced an extra buffer-to-buffer copy to occur if the GPU execution could be resumed immediately.

### NXT's MapReadAsync(callback);

Not a pollable interface.

## Issues

### GC discoverability

It isn't clear yet what happens when a buffer gets garbage collected while it is mapped.
The simple answer is that the `WebGPUMappedMemory` objects get invalidated but that would allow the application to discover when the GC runs.

### GC pressure

The `WebGPUMappedMemory` design makes each mapped region create two garbage collected objects. This could lead to some GC pressure.

### Side effects between mapped memory regions

What happens when `WebGPUMappedMemory` object's region in the buffer overlap?
Are write from one visible from the other?
If they are, maybe `WebGPUMappedMemory.getPointer` should return an `ArrayBufferView` instead.

### Interactions with workers

Can a buffer be mapped in multiple different workers?
If that's the case, the pointer should be represented with a `SharedArrayBufer`.
