# Buffer Mapping

For each Buffer with MAP_READ or MAP_WRITE usage, an IPC implemention maintains a parallel
shared-memory buffer for use with immediate (non-round-trip) mapping.

## WebGLBuffer.map

`ArrayBuffer? WebGLBuffer.map(WebGPUMapFlags flags);`

Requires that for each queue to which a modification to the buffer has been submitted,
a subsequent WebGPU fence has been confirmed by the client to be 'complete'.
For a Buffer with the MAP_READ usage, the implementation will, upon completion of the
final pending fence, map the underlying buffer, copy from the underlying buffer into the
shared-memory buffer, and unmap. This means the shared-memory buffer is ready to be
mapped.
