# Error Handling

The simplest design for error handling would be to do it synchronously, for example with Javascript exceptions and object creation returning `null`.
However, this would introduce a lot of synchronization points for multi-threaded/multi-process WebGPU implementations, making it too slow to be useful.

There are a number of cases that developers or applications need error handling for:

 - *Debugging*: Getting errors synchronously during development, to break in to the debugger.
 - *Fallible Allocation*: Making fallible resource allocations (detecting out-of-memory).
 - *Testing*: Checking success of WebGPU calls, for conformance testing or application unit testing.
 - *Telemetry*: Collecting error logs in deployment, for bug reporting and telemetry.
 - *Fallback*: Tearing down the application and falling back, e.g. to WebGL, 2D Canvas, or static content.

Meanwhile, error handling should not make the API clunky to use.

## *Debugging*: Dev Tools

Implementations should provide a way to enable synchronous validation, for example via a "break on WebGPU error" option in the developer tools.
The extra overhead needs to be low enough that applications can still run while being debugged.

## *Telemetry*: Validation Error Logging

Logging of validation errors (which includes errors caused by using objects that are invalid for any reason).

This mechanism is like a programmatic way to access the warnings that appear in the developer tools.
Errors reported via the validation error event *should* also appear in the developer tools console as warnings (like in WebGL).
However, some developer tools warnings might not necessarily fire the event, and message could be different (e.g. some details omitted for security).

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

## Object and Operation Status

### Internal Nullability

WebGPU objects are opaque handles.
On creation, such a handle is "pending" until the backing object is created by the implementation.
After that, a handle may refer to a successfully created object (called a "valid object"), or an error that occured during creation (called an "invalid object").

When a WebGPU object handle is passed to a WebGPU API call, the object must resolve (to "valid" or "invalid") before the implementation can perform validation on that call.

### Categories of WebGPU Calls

Each category of WebGPU call has its errors handled in a different way.

#### Initialization

Creation of the adapter and device.

  - `gpu.requestAdapter`
  - `GPUAdapter.requestDevice`

Handled by "Fatal Errors" above.

#### Object-Returning

WebGPU Object creation and getters.

  - `GPUDevice.create*`
  - `GPUTexture.create*View`
  - `GPUCommandEncoder.finish`
  - `GPUDevice.getQueue`
  - `GPUSwapChain.getCurrentTexture`

If there is an error, the returned object is invalid.

See "Object Status" below.

#### Object-Promise-Returning*

Async WebGPU Object creation.

  - `GPUDevice.createReady*`
  - `GPUDevice.createBufferMappedAsync`

If there is an error, either the returned object is invalid, or the Promise rejects.

See "Object Status" below.

#### Encoding

Recording of GPU commands in `GPUCommandEncoder`.

  - `GPU*Encoder.*`

These commands do not report errors.
Instead, any error is reported by `GPUCommandEncoder.finish`.

#### Other-Promise-Returning

  - `GPUDevice.getSwapChainPreferredFormat`
  - `GPUFence.onCompletion`
  - `GPUBuffer.mapReadAsync`
  - `GPUBuffer.mapWriteAsync`

If there is an error, the returned Promise rejects.

#### Void-Returning

  - `GPUQueue.submit`
  - `GPUQueue.signal`
  - `GPUBuffer.setSubData`
  - `GPUBuffer.unmap`
  - `GPUBuffer.destroy`
  - `GPUTexture.destroy`
  - `GPUFence.getCompletedValue`

See "Operation Status" below.

## Object Status

As described above, objects may be internally "valid" or "invalid".
For testing, it is necessary to be able to inspect this status.
Through this mechanism, allocation failure ("out-of-memory") can also be expressed.

Object status can be queried with `getStatus`.
`getStatus` returns a Promise which resolves to a `GPUObjectStatus` object that reports the status of the object.
`GPUObjectStatus` includes a `type`, which describes the general category of error, as well as a `message` (an implementation-defined human-readable message string about the error).

`getStatus` rejects if the device is lost.

```webidl
enum GPUErrorType {
    "invalid-object", // `this` or an object argument was invalid.
    "invalid-value",  // A non-object argument was wrong (out of range, or invalid enum).
    "invalid-state",  // `this` or an object argument was in a wrong state (e.g. mapped).
    // TODO: more?
    "out-of-memory"   // An allocation failed nonfatally.
};

interface GPUObjectStatus {
    readonly attribute boolean valid;

    // These are only set if valid == false.
    readonly attribute GPUErrorType? type;
    readonly attribute DOMString? message;
};

typedef (GPUBindGroup
      or GPUBindGroupLayout
      or GPUBuffer
      or GPUCommandBuffer
      or GPUCommandEncoder
      or GPUComputePipeline
      or GPUFence
      or GPUPipelineLayout
      or GPUProgrammablePassEncoder
      or GPUQueue
      or GPURenderPipeline
      or GPUSampler
      or GPUShaderModule
      or GPUSwapChain
      or GPUTexture
      or GPUTextureView) GPUStatusableObject;

partial interface GPUDevice {
    Promise<GPUObjectStatus> getObjectStatus(GPUStatusableObject object);
};
```

#### Alternatives

- Instead of `device.getStatus(obj)`, have `obj.getStatus()`. Con: Pollutes objects with rarely-used methods. Pro: Maybe slightly more clear to users.

- The Promise could reject if the object is invalid. Con: Promises can only reject to DOMExceptions, meaning we have to express error categories via established DOMException error codes. (Also not sure if DOMException allows custom `message`s.)

### Operation Status

For the "Void-Returning" operations, errors are reported via `getLastOperationStatus()`.

  - `GPUQueue.submit`
  - `GPUQueue.signal`
  - `GPUBuffer.setSubData`
  - `GPUBuffer.unmap`
  - `GPUBuffer.destroy`
  - `GPUTexture.destroy`
  - `GPUFence.getCompletedValue` (never fails)

`device.getLastOperationStatus()` always resolves to the status of the most recent void-returning operation.
If called multiple times in a row, it returns the same result (but not the same object).

`getLastOperationStatus` returns a Promise that resolves to a `GPUOperationStatus` object describing the status of the last operation on this object.
`GPUOperationStatus` includes a `type`, which describes the general category of error, as well as a `message` (an implementation-defined human-readable message string about the error).

`getStatus` rejects if the device is lost.

```webidl
interface GPUOperationStatus {
    readonly attribute boolean succeeded;

    // These are only set if succeeded == false.
    readonly attribute GPUErrorType? type;
    readonly attribute DOMString? message;
};

partial interface GPUDevice {
    Promise<GPUOperationStatus> getLastOperationStatus();
};
```

#### Alternatives

  - `{GPUQueue,GPUBuffer,GPUTexture}.getLastOperationStatus`: the same but per-object.
    Cons: pollutes objects with rarely used methods; requires each object to keep data for its last operation status.
    Pro: associated with the object that had the error.

  - `getOperationStatuses`: returns a sequence of statuses for past operations.
    Con: sequence will grow unboundedly unless there is some arbitrary limit.

  - Change void-returning operations to return Promise<void>.
    Con: creates too much garbage.

## *Testing*

When testing object-returning methods, `getStatus`'s returned status is used.

```js
const buffer = device.createBuffer({size: -1});
const status = await buffer.getStatus();
expect(!status.valid);
expect(status.type === 'invalid-value');

await loseDevice(device); // (implemented somehow)
buffer.getStatus().then(testFailed, testPassed); // should reject
```

When testing void-returning methods, `getLastOperationStatus`'s returned status is used.

```js
buffer.unmap()
const status = await device.getLastOperationStatus();
expect(!status.succeeded);
expect(status.type === 'invalid-state');

await loseDevice(device); // (implemented somehow)
device.getLastOperationStatus().then(testFailed, testPassed); // should reject
```

When testing promise-returning methods, the promise's resolve/reject state is used.

```js
buffer.mapWriteAsync().then(testFailed, testPassed); // should reject
```

## *Fallible Allocation*

On failure to allocate, `buffer.getStatus` or `texture.getStatus` returns a status with type `"out-of-memory"`.
The application can detect this and use it as a signal to reallocate.

`"out-of-memory"` objects are special invalid objects.
If an `"out-of-memory"` object is used (mapped, used as an argument, etc.), it signals that the application has not handled the out-of-memory case for this allocation.
As a result, any such use results in device loss, so the application can fall back instead of breaking unpredictably.

```js
let buffer = device.createBuffer(desc); // If this fails, try again.
const status = await buffer.getStatus();
if (status.type === 'out-of-memory') {
  freeSomeMemory();
  buffer = device.createBuffer(desc); // If this fails, return an out-of-memory
                                      // object which results in device loss and fallback.
}
```

## Open Questions and Considerations

 - Should developers be able to self-impose a memory limit (in order to emulate lower-memory devices)?
   Should implementations automatically impose a lower memory limit (to improve stability and portability)?

 - To help developers, `GPUValidationErrorEvent.message` could contain some sort of "stack trace" and could take advantage of object debug labels.
   For example:

   ```
   Failed <myQueue>.submit because commands[0] (<mainColorPass>) is invalid:
   - <mainColorPass> is invalid because in setIndexBuffer, indexBuffer (<mesh3.indexBuffer>) is invalid
   - <mesh3.indexBuffer> is invalid because it got an unsupported usage flag (0x89)
   ```

 - How do applications handle the case where they've allocated a lot of optional memory, but want to make another required allocation (which could fail due to OOM)?
   How do they know when to free an optional allocation first?
    - For now, applications wanting to handle this kind of case must always use fallible allocations.
    - (We will likely improve this with a `GPUResourceHeap`, once we figure out what that looks like.)

 - Should attempting to use a buffer or texture in the `"out-of-memory"` state (a) result in immediate device loss, (b) result in device loss when used in a device-level operation (submit, map, etc.), or (c) just produce a validation error?
    - Currently described: (a)

## Resolved Questions

 - In a world with persistent object "usage" state:
   If an invalid command buffer is submitted, and its transitions becomes no-ops, the usage state won't update.
   Will this cause future command buffer submits to become invalid because of a usage validation error?
    - Tentatively resolved: WebGPU is expected not to require explicit usage transitions.

 - Should an object creation error immediately log an error to the error log?
   Or should it only log if the error propagates to a device-level operation?
    - Tentatively resolved: errors should be logged immediately.

 - Should applications be able to intentionally create graphs of potentially-invalid objects, and recover from this late?
   E.g. create a large buffer, create a bind group from that, create a command buffer from that, then choose whether to submit based on whether the buffer was successfully allocated.
    - For non-OOM, tentatively resolved: They can, but it is not useful, and they will incur a lot of validation log events by doing so.
    - For OOM, see other question about OOM.

 - Should there be an API to query object status?
    - Resolved: Yes. It is needed for testing.
