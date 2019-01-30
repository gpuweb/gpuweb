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
 - *Encoding*: Recording of GPU commands in `GPUCommandEncoder`.
 - *Operations*: Other API calls, such as `GPUQueue.submit`.

## *Debugging*: Dev Tools

Implementations should provide a way to enable synchronous validation, for example via a debug shim or via the developer tools.
The extra overhead needs to be low enough that applications can still run while being debugged.

## *Telemetry*: Validation Error Logging

Logging of validation errors (which includes errors caused by using objects that are invalid for any reason).

```webidl
[
    Constructor(DOMString type, GPUValidationErrorEventInit gpuValidationErrorEventInitDict),
    Exposed=Window
]
interface GPUValidationErrorEvent : Event {
    readonly attribute DOMString message;
};

dictionary GPUValidationErrorEventInit : EventInit {
    required DOMString message;
};

partial interface GPUDevice : EventTarget {
    attribute EventHandler onvalidationerror;
};
```

`WebGPUDevice` `"validationerror"` -> `GPUValidationErrorEvent`:
Fires when a non-fatal error occurs in the API, i.e. a validation error (including if an "invalid" object is used).

When there is a validation error in the API (including operations on "invalid" WebGPU objects), an error is logged.
When a validation error is discovered by the WebGPU implementation, it may fire a `"validationerror"` event on the `GPUDevice`.
These events should not be used by applications to recover from expected, recoverable errors.
Instead, the error log may be used for handling unexpected errors in deployment, for bug reporting and telemetry.

`"validationerror"` events are all delivered through the device.
They are not directly associated with the objects or operations that produced them.

The `"validationerror"` event always fires on the main thread (Window) event loop.

For creation errors, the `object` attribute holds the object handle that was created.
(It will always point to an "invalid" object.)
It preserves the JavaScript object wrapper of that handle (including any extra JavaScript properties attached to that wrapper).

The `message` is a human-readable string, provided for debugging/reporting/telemetry.

The WebGPU implementation may choose not to fire the `"validationerror"` event for a given log entry if there have been too many errors, too many errors in a row, or too many errors of the same kind.
(In badly-formed applications, this mechanism can prevent the `"validationerror"` events from having a significant performance impact on the system.)

No `"validationerror"` events will be fired after the device is lost.
(Though a there may be one "just before" the device is lost, if the error would be useful for telemetry.)

### Example

```js
const adapter = await gpu.requestAdapter({ /* options */ });
const device = await adapter.requestDevice({ /* options */ });
device.addEventListener('validationerror', (event) => {
    appendToTelemetryReport(event.message);
});
```

## Object Creation

WebGPU objects are opaque handles.
On creation, such a handle is "pending" until the backing object is created by the implementation.
After that, a handle may refer to a successfully created object (called a "valid object"), or an error that occured during creation (called an "invalid object").

When a WebGPU object handle is passed to an operation, the object will resolve (to "valid" or "invalid") before it is actually used by that operation.

### Error propagation of invalid objects

Using any invalid object in a WebGPU operation produces a validation error.
The effect of an error depends on the type of a call:

 - For object creation, the call produces a new invalid object.
 - For `GPUCommandEncoder` encoding methods, the `GPUCommandEncoder.finishEncoding` method will return an invalid object.
 - For other WebGPU calls, the call becomes a no-op.

In each case, an error is logged to the error log.

## *Recovery*: Recoverable Errors

Recoverable errors are produced only by object creation.
The status of an object can be retrieved asynchronously (see next section).

```
enum GPUObjectStatus {
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

A recoverable error is exposed as a `GPUObjectStatusQuery`.

```
// (Exact form/type subject to change.)
typedef Promise<GPUObjectStatus> GPUObjectStatusQuery;

typedef (GPUBuffer or GPUTexture) StatusableObject;

partial interface GPUDevice {
    GPUObjectStatusQuery getObjectStatus(StatusableObject object);
};
```

A concrete example: When creating a buffer, the following logic applies:

 - `createBuffer` returns a `GPUBuffer` object `buffer` immediately.
 - A `GPUObjectStatusQuery` can be obtained by calling `device.getObjectStatus(buffer)`.
   At a later time, that query resolves to a `GPUObjectStatus` that is one of:
    - Creation succeeded (`"valid"`).
    - Creation encountered a recoverable error (`"out-of-memory"`).
      (The application can then choose to retry a smaller allocation of a *new* `GPUBuffer`.)
    - Creation encountered another type of error out of the control of the application (`"invalid"`).

Regardless of any recovery efforts the application makes, if creation fails,
the resulting object is invalid (and subject to error propagation).

Checking the status of a `GPUBuffer` or `GPUTexture` is **not** required.
It is only necessary if an application wishes to recover from recoverable errors such as out of memory.
(If it does, it is responsible for avoiding using the invalid object.)

## Open Questions and Considerations

 - WebGPU could guarantee that objects such as `GPUQueue` and `GPUFence` can never be errors.
   If this is true, then the only synchronous API that needs special casing is buffer mapping, where `mapping` is always `null` for an invalid `GPUBuffer`.

 - Should developers be able to self-impose a memory limit (in order to emulate lower-memory devices)?
   Should implementations automatically impose a lower memory limit (to improve portability)?

 - To help developers, `GPUValidationErrorEvent.message` could contain some sort of "stack trace" and could take advantage of debug name of objects if that's something that's present in WebGPU.
   For example:

   ```
   Failed <myQueue>.submit because commands[0] (<mainColorPass>) is invalid:
   - <mainColorPass> is invalid because in setIndexBuffer, indexBuffer (<mesh3.indexBuffer>) is invalid
   - <mesh3.indexBuffer> is invalid because it got an unsupported usage flag (0x89)
   ```

 - The exact shape of `GPUObjectStatusQuery` (currently `Promise<GPUObjectStatus>`) may piggy-back on the decision taken for `GPUFence`.

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
