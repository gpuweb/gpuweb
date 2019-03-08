# Error Handling

The simplest design for error handling would be synchronous, for example with Javascript exceptions.
However, this would introduce a lot of round-trip synchronization points for multi-threaded/multi-process WebGPU implementations, making it too slow to be useful.

There are a number of cases that developers or applications need error handling for:

 - *Debugging*: Getting errors synchronously during development, to break in to the debugger.
 - *Telemetry*: Collecting error logs in deployment, for bug reporting and telemetry.
 - *Recovery*: Recovering from recoverable errors (like out-of-memory on resource creation).
 - *Fatal Errors*: Handling device/adapter loss, either by restoring WebGPU or by fallback to non-WebGPU content.

Meanwhile, error handling should not make the API clunky to use.

There are several types of WebGPU calls that get their errors handled differently:

 - *Creation*: WebGPU Object creation.
 - *Encoding*: Recording of GPU commands in `GPUCommandEncoder`.
 - *Operations*: Other API calls, such as `GPUQueue.submit`.

## *Debugging*: Dev Tools

Implementations should provide a way to enable synchronous validation, for example via a "break on WebGPU error" option in the developer tools.
The extra overhead needs to be low enough that applications can still run while being debugged.

## *Fatal Errors*: Lost/Recovered Events

<!-- calling this revision 6 -->

```webidl
interface GPUDeviceLostInfo {
    readonly attribute DOMString message;
};

partial interface GPUDevice {
    readonly attribute Promise<GPUDeviceLostInfo> lost;
};
```

`GPUAdapter.requestDevice` requests a device from the adapter.
It returns a Promise which resolves when a device is ready.
The Promise may not resolve for a long time - it resolves when the browser is ready for the application to bring up (or restore) its content.
If the adapter is unable to create a device (i.e. because the adapter was lost), the Promise rejects.

The `GPUDevice` may be lost if something goes fatally wrong on the device (e.g. unexpected driver error, crash, or native device loss).
The `GPUDevice` provides a promise, `device.lost`, which resolves when the device is lost.
It will **never** reject and may be pending forever.

Once `lost` resolves, the `GPUDevice` cannot be used anymore.
The device and all objects created from the device have become invalid.
All further operations on the device and its objects are errors.
The `"validationerror"` event will no longer fire. (This makes all further operations no-ops.)

### Example Code

```js
class MyRenderer {
  constructor() {
    this.adapter = null;
    this.device = null;
  }
  async begin() {
    try {
      await this.initWebGPU();
    } catch (e) {
      console.error(e);
      this.initFallback();
    }
  }
  async initWebGPU() {
    await this.ensureDevice();
    // ... Upload resources, etc.
  }
  initFallback() { /* try WebGL, 2D Canvas, or other fallback */ }
  async ensureDevice() {
    // Stop rendering. (If there was already a device, WebGPU calls made before
    // the app notices the device is lost are okay - they are no-ops.)
    this.device = null;

    // Keep current adapter (but make a new one if there isn't a current one.)
    // If we can't get an adapter, ensureDevice rejects and the app falls back.
    await ensureAdapter();

    try {
      await ensureDeviceOnCurrentAdapter();
      // Got a device.
      return;
    } catch (e) {
      console.error("device request failed", e);
      // That failed; try a new adapter entirely.
      this.adapter = null;
      // If we can't get a new adapter, it causes ensureDevice to reject and the app to fall back.
      await ensureAdapter();
      await ensureDeviceOnCurrentAdapter();
    }
  }
  async ensureAdapter() {
    if (!this.adapter) {
      // If no adapter, get one.
      // (If requestAdapter rejects, no matching adapter is available. Exit to fallback.)
      this.adapter = await gpu.requestAdapter({ /* options */ });
    }
  }
  async ensureDeviceOnCurrentAdapter() {
    this.device = await this.adapter.requestDevice({ /* options */ });
    this.device.lost.then((info) => {
      // Device was lost.
      console.error("device lost", info);
      // Try to get a device again.
      this.ensureDevice();
    });
  }
}
```

### Case Studies

*What signals should the app get, and when?*

Two independent applications are running on the same webpage against two devices on the same adapter.
The tab is in the background, and one device is using a lot of resources.
 - The browser chooses to lose the heavier device.
    - `device.lost` resolves, message = recovering device resources
    - (App calls `createDevice` on any adapter, but it doesn't resolve yet.)
 - Later, the browser might choose to lose the smaller device too.
    - `device.lost` resolves, message = recovering device resources
    - (App calls `createDevice` on any adapter, but it doesn't resolve yet.)
 - Later, the tab is brought to the foreground.
    - Both `createDevice` Promises resolve.
      (Unless the adapter was lost, in which case they would have rejected.)

A page begins loading in a tab, but then the tab is backgrounded.
 - On load, the page attempts creation of a device.
    - `createDevice` Promise will resolve.

A device's adapter is physically unplugged from the system (but an integrated GPU is still available).
 - The same adapter, or a new adapter, is plugged back in.
    - A later `requestAdapters` call may return the new adapter. (In the future, it might fire a "gpuadapterschanged" event.)

An app is running on an integrated adapter.
 - A new, discrete adapter is plugged in.
    - A later `requestAdapters` call may return the new adapter. (In the future, it might fire a "gpuadapterschanged" event.)

An app is running on a discrete adapter.
 - The adapter is physically unplugged from the system. An integrated GPU is still available.
    - `device.lost` resolves, `requestDevice` on same adapter rejects, `requestAdapters` gives the new adapter.
 - The same adapter, or a new adapter, is plugged back in.
    - A later `requestAdapters` call may return the new adapter. (In the future, it might fire a "gpuadapterschanged" event.)

The device is lost because of an unexpected error in the implementation.
 - `device.lost` resolves, message = whatever the unexpected thing was.

A TDR-like scenario occurs.
 - The adapter is lost, which loses all devices on the adapter.
   `device.lost` resolves on every device, message = adapter reset. Application must request adapter again.
 - (TODO: alternatively, adapter could be retained, but all devices on it are lost.)

All devices and adapters are lost (except for software?) because GPU access has been disabled by the browser (for this page or globally, e.g. due to unexpected GPU process crashes).
 - `device.lost` resolves on every device, message = whatever

WebGPU access has been disabled for the page.
 - `requestAdapters` rejects (or returns a software adapter).

The device is lost right as it's being returned by requestDevice.
 - `device.lost` resolves.

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
   Should implementations automatically impose a lower memory limit (to improve stability and portability)?

 - To help developers, should `GPUValidationErrorEvent.message` contain some sort of "stack trace" taking advantage of object debug labels?
   For example:

   ```
   <myQueue>.submit failed:
   - commands[0] (<mainColorPass>) was invalid:
   - in setIndexBuffer, indexBuffer (<mesh3.indices>) was invalid:
   - in createBuffer, desc.usage was invalid (0x89)
   ```

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
