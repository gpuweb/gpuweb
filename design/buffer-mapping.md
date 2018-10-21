# THIS DOCUMENT IS OUT OF DATE BECAUSE TRANSITIONS AREN'T IN WEBGPU

# Buffer Mapping

For each Buffer with MAP_READ or MAP_WRITE usage, an IPC implemention maintains
a parallel shared-memory buffer for use with immediate (non-round-trip) mapping.
However, this mapping is only accessible at well-defined times.

## Transition to MAP_READ or MAP_WRITE

When an app wants to map a buffer for read or write, it submits a command buffer
containing a transition of the buffer's usage to MAP_READ or MAP_WRITE, and
inserts a fence into the queue. (either immediately, or coalescing later)

## WebGPUFence

Fences are one-shot, where the CPU waits for the GPU/server/API to 'signal'
a fence as passed. They are created with WebGPUQueue.insertFence().

WebGPUFences start in the unsignaled state and transition once from unsignaled to signaled.
This transition can be detected with `WebGPUFence.promise.then()`.
Alternatively `WebGPUFence.wait()` can be used, it waits (potentially no time) for the fence to be in the signaled state and return true.
If the WebGPUFence is still unsignaled after the specified timeout, `WebGPUFence.wait()` returns 0, implementation might not wait for the whole specified timeout.
On the UI thread, the `milliseconds` argument is always clamped to 0, and the status of the fence can only change at micro-task boundary.
WebGPUFences are not shareable.

Apps can establish whether a buffer has completed its transition to
MAP_READ/MAP_WRITE by waiting for a WebGPU fence to be signaled.

## WebGPUBuffer.mapping and unmap()

Once the app has established that the transition to MAP_READ/MAP_WRITE is
complete, `mapping` is changed from `null` to an `ArrayBuffer` backed by the
mapped data.

When done with the mapping, the app relinquishes control of the mapped bytes
with `WebGPUBuffer.unmap()`, which neuters the ArrayBuffer, and nulls `mapping`.
