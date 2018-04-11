# Error Handling

The simplest design for error handling would be to do it synchronously, for example with Javascript exceptions and object creation returning `null`.
However, this would introduce a lot of synchronization points for multi-threaded/multi-process WebGPU implementations, making it infeasible.

There are a number of cases that developers or applications care about:

 - *Debugging*: Getting errors synchronously during development, to break in to the debugger.
 - *Telemetry*: Collecting error logs in deployment, for bug reporting and telemetry.
 - *Recovery*: Recovering from recoverable errors (like out-of-memory on resource creation).

Meanwhile, error handling should not make the API clunky to use.

There are several types of WebGPU calls that get their error handled differently:

 - *Creation*: WebGPU Object creation.
 - *Encoding*: Recording of GPU commands in `WebGPUCommandEncoder`.
 - *Operations*: Other commands, such as `WebGPUQueue.submit`.

## *Telemetry*: Error Logging

The error log is a stream of error objects which are reported to the application asynchronously.
These errors are not directly associated with the objects or operations that produced them.
Instead, they are used for handling unexpected errors in deployment, for bug reporting and telemetry.

```
enum WebGPULogEntryType {
    "device-lost",
    "validation-error",
    "recoverable-out-of-memory",
};

interface WebGPULogEntry {
    WebGPULogEntryType type;
    DOMString? reason;
};

partial interface WebGPUDevice {
    // TODO: This is probably not the best design. It is just a strawman.
    WebGPULogEntry getNextLogEntryFromStream();
};
```

`WebGPUStatusType` makes a distinction between several `WebGPULogEntryType`s:

 - `"validation-error"`: either the application did something wrong, or it chose not to recover from a recoverable error.
 - `"device-lost"`: things went horribly wrong and the `WebGPUDevice` cannot be used anymore. (Applications can choose to try making a new device.)
 - `"recoverable-out-of-memory": an allocation failed in a recoverable way. This is logged regardless of whether the application actually recovers from the condition.

The `reason` is human-readable text, provided for debugging/reporting/telemetry.

## Object Creation

WebGPU objects the application uses are handles that either represent a successfully created object, or an error that occured during creation.
Successfully created objects are called "valid objects" and "invalid objects" otherwise.

### Error propagation of invalid objects

Using any invalid object in a WebGPU call produces a validation error.
The effect of an error depends on the type of a call:

 - For object creation, the call produces an invalid object.
 - For `WebGPUCommandEncoder` method, the `WebGPUCommandEncoder.finishEncoding` method will return an invalid object.
   (This is like any other object creation except that `WebGPUCommandEncoder` a builder object.)
 - For other WebGPU calls, the call is a no-op, and an error is logged to the error log.

Effectively this puts every WebGPU object type in the "Maybe Monad".

## *Recovery*: Recoverable Errors

Recoverable errors are produced only by object creation.
A recoverable error is exposed asynchronously by the object which was created.

`WebGPUStatus` is an enum indicating either that the object is valid, or the type of recoverable error that occurred.

```
enum WebGPUStatus {
    "valid",
    "out-of-memory",
};
```

Non-recoverable errors are not exposed via this mechanism; they are only logged via the Error Logging mechanism.

### Recoverable errors in object creation

A recoverable error is exposed as a `Promise<WebGPUStatus>`.

(The final design may use a different object other than `Promise<WebGPUStatus>`.
That decision isn't at the core of this proposal.)

```
partial interface WebGPUBuffer {
    Promise<WebGPUStatus> attribute status;
};

partial interface WebGPUTexture {
    Promise<WebGPUStatus> attribute status;
};
```

(In the future, the same attribute can be added to any object which is determined to require recoverable errors.)

When creating a buffer, the following logic applies:

 - `createBuffer` returns a `WebGPUBuffer` object `B1` immediately.
 - A `Promise<WebGPUStatus>` can be obtained from the `WebGPUBuffer` object.
   At a later time, that promise either:
    - Rejects, if creation failed due to an unrecoverable error, or
    - Resolves to a `WebGPUStatus`. It resolves if either:
       - Creation succeeded (`"valid"`), or
       - Creation encountered a recoverable error (`"out-of-memory"`).
         The application can then choose to retry a smaller allocation.

Regardless of any recovery efforts the application makes, if creation fails,
`B1` is an invalid object, subject to error propagation.

Checking the `status` of a `WebGPUBuffer` or `WebGPUTexture` is **not** required.
It is only necessary if an application wishes to recover from recoverable errors.
It is up to the application to avoid using the invalid object `B1`.

## Other considerations

 - Implementations should provide a way to enable synchronous validation, for example via the devtools.
   The extra CPU overhead should be acceptable for debugging purposes.

 - WebGPU could guarantee that objects such as `WebGPUQueue` and `WebGPUFence` can never be errors.
   If this is true, then the only synchronous API that needs special casing is buffer mapping, where `mapping` is always `null` for error `WebGPUBuffer`.

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

 - The exact shape of `Promise<WebGPUStatus>` will piggy-back on the decision taken for `WebGPUFence`.
