# Error Handling

The simplest design for error handling would be to do it synchronously, for example with Javascript exceptions and object creation returning `null`.
However, this would introduce a lot of synchronization points for multi-threaded/multi-process WebGPU implementations, making too slow to be useful.

There are a number of cases that developers or applications need error handling for:

 - *Debugging*: Getting errors synchronously during development, to break in to the debugger.
 - *Telemetry*: Collecting error logs in deployment, for bug reporting and telemetry.
 - *Recovery*: Recovering from recoverable errors (like out-of-memory on resource creation).
 - *Fallback*: Tearing down the application and falling back, e.g. to WebGL, 2D Canvas, or static content.

Meanwhile, error handling should not make the API clunky to use.

There are several types of WebGPU calls that get their error handled differently:

 - *Creation*: WebGPU Object creation.
 - *Encoding*: Recording of GPU commands in `WebGPUCommandEncoder`.
 - *Operations*: Other commands, such as `WebGPUQueue.submit`.

## *Telemetry*: Error Logging

`WebGPUDevice` keeps a log of errors that happened on each WebWorker which the application can query asynchronously.
These errors are not directly associated with the objects or operations that produced them.
They should not be used by applications to recover from expected errors.
Instead, they are used for handling unexpected errors in deployment, for bug reporting and telemetry.

```
enum WebGPULogEntryType {
    "device-lost",
    "validation-error",
    "recoverable-out-of-memory",
};

interface WebGPULogEntry {
    readonly attribute WebGPULogEntryType type;
    readonly attribute DOMString? reason;
};

callback WebGPULogCallback = void (WebGPULogEntry error);

partial interface WebGPUDevice {
    attribute WebGPULogCallback onLog;
};
```

`WebGPUObjectStatusType` makes a distinction between several error types:

 - `"validation-error"`: validation of some WebGPU call failed - including if an argument was an "invalid object".
   (Either the application did something wrong, or it chose not to recover from a recoverable error.)
 - `"device-lost"`: things went horribly wrong, and the `WebGPUDevice` cannot be used anymore.
   (An application may request a new device.)
 - `"out-of-memory": an allocation failed because too much memory was used by the application (CPU or GPU).
   This includes recoverable out of memory errors that aren't opt-ed in to be handled by the application when the resource was created.

The `reason` is human-readable text, provided for debugging/reporting/telemetry.

When an error is reported by the WebGPU implementation, the `onLog` attribute, if set, receives this error (asynchronously).
`onLog` is called once per error log entry.

`onLog` may be called with a `"context-lost"`.
If a `"context-lost"` error is logged, no other errors will be subsequently logged.

The WebGPU implementation may choose to not log an error if too many errors, or too many errors of the same kind, have been logged.

## Object Creation

WebGPU objects are handles that either represent a successfully created object, or an error that occured during creation.
Successfully created objects are called "valid objects"; unsuccessfully created objects are called "invalid objects".

### Error propagation of invalid objects

Using any invalid object in a WebGPU call produces a validation error.
The effect of an error depends on the type of a call:

 - For object creation, the call produces an invalid object.
 - For `WebGPUCommandEncoder` methods, the `WebGPUCommandEncoder.finishEncoding` method will return an invalid object.
   (This is like any other object creation: a `WebGPUCommandBuffer` is created from a `WebGPUCommandEncoder` builder object.)
 - For other WebGPU calls, the call is a no-op.

In each case, an error is logged to the error log.

## *Recovery*: Recoverable Errors

Recoverable errors are produced only by object creation.
A recoverable error is exposed asynchronously by the handle which was synchronously created.

`WebGPUObjectStatus` is an enum indicating either that the object is valid, invalid because of an out of memory, or for another reason.
Application can use the `"out-of-memory"` status as a signal to scale back resource usage if it is possible.

```
enum WebGPUObjectStatus {
    "valid",
    "out-of-memory",
    "invalid",
};
```

Errors on object creation are added to the `WebGPUDevice` error log, unless they are `"out-of-memory"` and opt-ed in to be handled by the application.
An application opts into handling the recoverable errors itself by specifying `logRecoverableError = false` in the `WebGPUBufferDescriptor` and `WebGPUTextureDescriptor`.

### Recoverable errors in object creation

A recoverable error is exposed as a `Promise<WebGPUObjectStatus>`.

(The final design may use a different object other than `Promise<WebGPUObjectStatus>`.
This part isn't at the core of this proposal.)

```
partial interface WebGPUBuffer {
    readonly attribute Promise<WebGPUObjectStatus> status;
};

partial interface WebGPUTexture {
    readonly attribute Promise<WebGPUObjectStatus> status;
};
```

(In the future, the same attribute can be added to any object which is determined to require recoverable errors.)

When creating a buffer, the following logic applies:

 - `createBuffer` returns a `WebGPUBuffer` object immediately.
 - A `Promise<WebGPUObjectStatus>` can be obtained from the `WebGPUBuffer` object.
   At a later time, that promise resolves to a `WebGPUObjectStatus` that is one of:
       - Creation succeeded (`"valid"`).
       - Creation encountered a recoverable error (`"out-of-memory"`).
         (The application can then choose to retry a smaller allocation.)
       - Creation encountered another type of error out of the control of the application (`"invalid"`).

Regardless of any recovery efforts the application makes, if creation fails,
`B1` is an invalid object, subject to error propagation.

Checking the `status` of a `WebGPUBuffer` or `WebGPUTexture` is **not** required.
It is only necessary if an application wishes to recover from recoverable errors such as out of memory.
It is up to the application to avoid using the invalid object.

## Other considerations

 - Implementations should provide a way to enable synchronous validation, for example via the devtools.
   The extra CPU overhead should be acceptable for debugging purposes.

 - WebGPU could guarantee that objects such as `WebGPUQueue` and `WebGPUFence` can never be errors.
   If this is true, then the only synchronous API that needs special casing is buffer mapping, where `mapping` is always `null` for an invalid `WebGPUBuffer`.
   
 - Should there be a mode which causes OOM errors to trigger context loss?
   Probably not necessary, since an application could manually kill the context if it sees errors in the error log.

 - Should an object creation error immediately log an error to the error log?
   Or should it only log if the error propagates to a device-level operation?

 - To help developers, `WebGPULogEntry.reason` could contain some sort of "stack trace" and could take advantage of debug name of objects if that's something that's present in WebGPU.
   For example:

   ```
   Failed <myQueue>.submit because commands[0] (<mainColorPass>) is invalid:
   - <mainColorPass> is invalid because in setIndexBuffer, indexBuffer (<mesh3.indexBuffer>) is invalid
   - <mesh3.indexBuffer> is invalid because it got an unsupported usage flag (0x89)
   ```

 - In a world with persistent object "usage" state:
   If an invalid command buffer is submitted, and its transitions becomes no-ops, the usage state won't update.
   Will this cause future command buffer submits to become invalid because of a usage validation error?

 - The exact shape of `Promise<WebGPUObjectStatus>` will piggy-back on the decision taken for `WebGPUFence`.
