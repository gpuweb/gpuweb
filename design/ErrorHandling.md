# Error Handling

The simplest design for error handling would be to do it synchronously, for example with Javascript exceptions and object creation returning `null`.
However, this would introduce a lot of synchronization points for multi-threaded/multi-process WebGPU implementations, making it too slow to be useful.

There are a number of cases that developers or applications need error handling for:

 - *Debugging*: Getting errors synchronously during development, to break in to the debugger.
 - *Telemetry*: Collecting error logs in deployment, for bug reporting and telemetry.
 - *Recovery*: Recovering from recoverable errors (like out-of-memory on resource creation).
 - *Fallback*: Tearing down the application and falling back, e.g. to WebGL, 2D Canvas, or static content.

Meanwhile, error handling should not make the API clunky to use.

There are several types of WebGPU calls that get their errors handled differently:

 - *Creation*: WebGPU Object creation.
 - *Encoding*: Recording of GPU commands in `WebGPUCommandEncoder`.
 - *Operations*: Other API calls, such as `WebGPUQueue.submit`.

## *Debugging*: Dev Tools

Implementations should provide a way to enable synchronous validation, for example via a debug shim or via the developer tools.
The extra CPU overhead should be acceptable for debugging purposes.

## *Telemetry* \& *Fallback*: Error Logging

`WebGPUDevice` keeps a log of errors that happened on each thread (main thread or Web Worker).
The application "eventually" recieves these errors, asynchronously via a callback.

These errors are all delivered through one stream - not directly associated with the objects or operations that produced them.
They should not be used by applications to recover from expected, recoverable errors.
Instead, the error log may be used for handling unexpected errors in deployment, for bug reporting and telemetry.

```
enum WebGPULogEntryType {
    "device-lost",
    "validation-error",
    "recoverable-out-of-memory",
};

interface WebGPULogEntry {
    readonly attribute WebGPULogEntryType type;
    readonly attribute any object;
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
 - `"device-lost"`: the `WebGPUDevice` cannot be used anymore.
   This may happen if the device is destroyed by the application, reclaimed by the browser, or something goes terribly wrong.
   (An application may request a new device, or choose to fallback to other content.)
 - `"out-of-memory": an allocation failed because too much memory was used by the application (CPU or GPU).
   This includes recoverable out of memory errors that aren't opt-ed in to be handled by the application when the resource was created.

For creation errors, the `object` attribute holds the object handle that was created.
(It will point to an "invalid" object.)
It preserves the JavaScript object wrapper of that handle (including any extra JavaScript properties attached to that wrapper).

The `reason` is human-readable text, provided for debugging/reporting/telemetry.

When an error is reported by the WebGPU implementation, the `onLog` attribute, if set, receives this error (asynchronously).
`onLog` is called once per error log entry.
(If `onLog` is set or changed after some operation which logs an error, that error may or may not be sent to the new `onLog` handler.)

`onLog` may be called with a `"context-lost"`.
If a `"context-lost"` error is logged, no other errors will be subsequently logged.

The WebGPU implementation may choose to not log an error if too many errors, or too many errors of the same kind, have been logged.

## Object Creation

WebGPU objects are opaque handles.
On creation, such a handle is "pending" until the backing object is created by the implementation.
After that, a handle may refer to a successfully created object (called a "valid object"), or an error that occured during creation (called an "invalid object").

When a WebGPU object handle is passed to an operation, the object will resolve (to "valid" or "invalid") before it is actually used by that operation.

### Error propagation of invalid objects

Using any invalid object in a WebGPU operation produces a validation error.
The effect of an error depends on the type of a call:

 - For object creation, the call produces a new invalid object.
 - For `WebGPUCommandEncoder` encoding methods, the `WebGPUCommandEncoder.finishEncoding` method will return an invalid object.
 - For other WebGPU calls, the call becomes a no-op.

In each case, an error is logged to the error log.

## *Recovery*: Recoverable Errors

Recoverable errors are produced only by object creation.
The status of an object can be retrieved asynchronously (see next section).

```
enum WebGPUObjectStatus {
    // The object is valid.
    "valid",
    // The object is invalid due to a non-fatal allocation failure.
    // The application can use this as a signal to scale back resource usage, if possible.
    "out-of-memory",
    // The object is invalid for another, unrecoverable reason.
    "invalid",
};
```

(Note that object creation failures always send an error to the error log, regardless of the object type or the type of failure.)

If an application uses recoverable allocation, the implementation will still generate error log entries:
a `"recoverable-out-of-memory"` error for the object creation, and `"validation-error"`s for any subsequent uses of the invalid object.
The application may need to understand whether such error log entries were part of a recovered allocation (e.g. to avoid sending telemetry for those errors).
To facilitate this filtering, the handle to the invalid object (including "expando" JavaScript properties) is attached to the error log entry (see above).

### Recoverable errors in object creation

A recoverable error is exposed as a `WebGPUObjectStatusQuery`.

```
// (Exact form/type subject to change.)
typedef Promise<WebGPUObjectStatus> WebGPUObjectStatusQuery;

typedef (WebGPUBuffer or WebGPUTexture) StatusableObject;

partial interface WebGPUDevice {
    WebGPUObjectStatusQuery getObjectStatus(StatusableObject object);
};
```

A concrete example: When creating a buffer, the following logic applies:

 - `createBuffer` returns a `WebGPUBuffer` object `buffer` immediately.
 - A `WebGPUObjectStatusQuery` can be obtained by calling `device.getObjectStatus(buffer)`.
   At a later time, that query resolves to a `WebGPUObjectStatus` that is one of:
       - Creation succeeded (`"valid"`).
       - Creation encountered a recoverable error (`"out-of-memory"`).
         (The application can then choose to retry a smaller allocation of a *new* `WebGPUBuffer`.)
       - Creation encountered another type of error out of the control of the application (`"invalid"`).

Regardless of any recovery efforts the application makes, if creation fails,
the resulting object is invalid (and subject to error propagation).

Checking the status of a `WebGPUBuffer` or `WebGPUTexture` is **not** required.
It is only necessary if an application wishes to recover from recoverable errors such as out of memory.
(If it does, it is responsible for avoiding using the invalid object.)

## Open Questions and Considerations

 - WebGPU could guarantee that objects such as `WebGPUQueue` and `WebGPUFence` can never be errors.
   If this is true, then the only synchronous API that needs special casing is buffer mapping, where `mapping` is always `null` for an invalid `WebGPUBuffer`.

 - Should developers be able to self-impose a memory limit (in order to emulate lower-memory devices)?
   Should implementations automatically impose a lower memory limit (to improve portability)?

 - To help developers, `WebGPULogEntry.reason` could contain some sort of "stack trace" and could take advantage of debug name of objects if that's something that's present in WebGPU.
   For example:

   ```
   Failed <myQueue>.submit because commands[0] (<mainColorPass>) is invalid:
   - <mainColorPass> is invalid because in setIndexBuffer, indexBuffer (<mesh3.indexBuffer>) is invalid
   - <mesh3.indexBuffer> is invalid because it got an unsupported usage flag (0x89)
   ```

 - The exact shape of `WebGPUObjectStatusQuery` (currently `Promise<WebGPUObjectStatus>`) may piggy-back on the decision taken for `WebGPUFence`.

## Resolved Questions
   
 - Should there be a mode/flag which causes OOM errors to trigger context loss?
    - Resolved: Not necessary, since an application can manually destroy the context based on entries in the error log.

 - In a world with persistent object "usage" state:
   If an invalid command buffer is submitted, and its transitions becomes no-ops, the usage state won't update.
   Will this cause future command buffer submits to become invalid because of a usage validation error?
    - Tentatively resolved: WebGPU is expected not to require explicit usage transitions.

 - Should an object creation error immediately log an error to the error log?
   Or should it only log if the error propagates to a device-level operation?
    - Tentatively resolved: errors should be logged immediately.
