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

Apps can establish whether a buffer has completed its transition to
MAP_READ/MAP_WRITE by using `.then()`.

## WebGPUBuffer.mapping and unmap()

Once the app has established that the transition to MAP_READ/MAP_WRITE is
complete, `mapping` is changed from `null` to an `ArrayBuffer` backed by the
mapped data.

When done with the mapping, the app relinquishes control of the mapped bytes
with `WebGPUBuffer.unmap()`, which neuters the ArrayBuffer, and nulls `mapping`.
