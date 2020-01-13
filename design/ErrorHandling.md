# Error Handling

The simplest design for error handling would be synchronous, for example with Javascript exceptions.
However, this would introduce a lot of round-trip synchronization points for multi-threaded/multi-process WebGPU implementations, making it too slow to be useful.

There are a number of cases that developers or applications need error handling for:

 - *Debugging*: Getting errors synchronously during development, to break in to the debugger.
 - *Fatal Errors*: Handling device/adapter loss, either by restoring WebGPU or by fallback to non-WebGPU content.
 - *Fallible Allocation*: Making fallible resource allocations (detecting out-of-memory).
 - *Testing*: Checking success of WebGPU calls, for conformance testing or application unit testing.
 - *Telemetry*: Collecting error logs in deployment, for bug reporting and telemetry.

There is one other use case that is closely related to error handling:

 - *Waiting for Completion*: Waiting for completion of off-queue GPU operations (like object creation).

Meanwhile, error handling should not make the API clunky to use.

## *Debugging*: Dev Tools

Implementations should provide a way to enable synchronous validation, for example via a "break on WebGPU error" option in the developer tools.
The extra overhead needs to be low enough that applications can still run while being debugged.

## *Fatal Errors*: requestAdapters, requestDevice, and device.lost

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
      // (If requestAdapters rejects, no matching adapter is available. Exit to fallback.)
      const adapters = await navigator.gpu.requestAdapters({ /* options */ });
      this.adapter = adapters[0]; // (Or, manually search through the returned adapters.)
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
    - (App calls `requestDevice` on any adapter, but it doesn't resolve yet.)
 - Later, the browser might choose to lose the smaller device too.
    - `device.lost` resolves, message = recovering device resources
    - (App calls `requestDevice` on any adapter, but it doesn't resolve yet.)
 - Later, the tab is brought to the foreground.
    - Both `requestDevice` Promises resolve.
      (Unless the adapter was lost, in which case they would have rejected.)

A page begins loading in a tab, but then the tab is backgrounded.
 - On load, the page attempts creation of a device.
    - `requestDevice` Promise will resolve.

A device's adapter is physically unplugged from the system (but an integrated GPU is still available).
 - The same adapter, or a new adapter, is plugged back in.
    - A later `requestAdapters` call may return the new adapter.
      (In the future, it might fire a "gpuadapterschanged" event.)

An app is running on an integrated adapter.
 - A new, discrete adapter is plugged in.
    - A later `requestAdapters` call may return the new adapter.
      (In the future, it might fire a "gpuadapterschanged" event.)

An app is running on a discrete adapter.
 - The adapter is physically unplugged from the system. An integrated GPU is still available.
    - `device.lost` resolves, `requestDevice` on same adapter rejects, `requestAdapters`
      returns a new list excluding the discrete GPU, and including the integrated GPU.
 - The same adapter, or a new adapter, is plugged back in.
    - A later `requestAdapters` call may return the new adapter.
      (In the future, it might fire a "gpuadapterschanged" event.)

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

## Operation Errors and Internal Nullability

WebGPU objects are opaque handles.
On creation, such a handle is "pending" until the backing object is created by the implementation.
Asynchronously, a handle may refer to a successfully created object (called a "valid object"), or an internally-empty/unsuccessful object (called an "invalid object").
The status of an object is opaque to JavaScript, except that any errors during object creation can be captured (see below).

If a WebGPU object handle A is passed to a WebGPU API call C that requires a valid object, that API call opaquely accepts the object regardless of its status (pending, valid, or invalid).
However, internally and asynchronously, C will not be validated and executed until A's status has resolved.
If A resolves to invalid, C will fail (asynchronously).

Errors in operations or creation will generate an error **into the current scope**.
An error may be captured by a surrounding Error Scope (described below).
If an error is not captured, it may fire the Device's "unhandlederror" event (below).

### Categories of WebGPU Calls

#### Initialization

Creation of the adapter and device.

  - `gpu.requestAdapters`
  - `GPUAdapter.requestDevice`

Handled by "Fatal Errors" above.

#### Object-Returning

WebGPU Object creation and getters.

  - `GPUDevice.createTexture`
  - `GPUDevice.createBuffer`
  - `GPUDevice.createBufferMapped`
  - `GPUTexture.createView`
  - `GPUTexture.createDefaultView`
  - `GPUCommandEncoder.finish`
  - `GPUDevice.getQueue`
  - `GPUSwapChain.getCurrentTexture`

If there is an error, the returned object is invalid, and an error is generated into the current scope.

#### Encoding

Recording of GPU commands in `GPUCommandEncoder`.

  - `GPUCommandEncoder.*`
  - `GPURenderPassEncoder.*`
  - `GPUComputePassEncoder.*`

These commands do not report errors.
Instead, `GPUCommandEncoder.finish` returns an invalid object and generates an error into the current scope.

#### Promise-Returning

  - `GPUDevice.createBufferMappedAsync`
  - `GPUCanvasContext.getSwapChainPreferredFormat`
  - `GPUFence.onCompletion`
  - `GPUBuffer.mapReadAsync`
  - `GPUBuffer.mapWriteAsync`

If there is an error, the returned Promise rejects.

#### Void-Returning

  - `GPUQueue.submit`
  - `GPUQueue.signal`
  - `GPUBuffer.unmap`
  - `GPUBuffer.destroy`
  - `GPUTexture.destroy`

If there is an error, an error is generated into the current scope.

#### Infallible

  - `GPUFence.getCompletedValue`

This call cannot fail.

## Error Scopes

Each device\* maintains a persistent "error scope" stack state.
Initially, the device's error scope stack is empty.
`GPUDevice.pushErrorScope(filter)` creates an error scope and pushes it onto the stack.

`GPUDevice.popErrorScope()` pops an error scope from the stack, and returns a `Promise<GPUError?>`, which resolves once the enclosed operations are complete.
It resolves to null if no errors were captured, and otherwise resolves to the first error that occurred in the scope -
either a `GPUOutOfMemoryError` or a `GPUValidationError` object containing information about the validation failure.

An error scope captures an error if its filter matches the type of the error scope:
`pushErrorScope('out-of-memory')` captures `GPUOutOfMemoryError`s;
`pushErrorScope('validation')` captures `GPUValidationError`s.
`pushErrorScope('none')` never captures errors, but can be used to detect operation completion.
The filter mechanism prevents developers from accidentally silencing validation errors when trying to do fallible allocation or wait for completion.

If an error scope captures an error, the error is not passed down to the enclosing error scope.
Each error scope stores only the **first error** it captures, and returns that error when the scope is popped.
Any further errors it captures are **silently ignored**.

If an error is not captured by an error scope, it is passed out to the enclosing error scope.

If there are no error scopes on the stack, `popErrorScope()` throws OperationError.

If the device is lost, `popErrorScope()` always rejects with OperationError.

\* Error scope state is **per-device, per-execution-context**.
That is, when a `GPUDevice` is posted to a Worker for the first time, the new `GPUDevice` copy's error scope stack is empty.
(If a `GPUDevice` is copied *back* to an execution context it already existed on, it shares its error scope state with all other copies on that execution context.)

```webidl
enum GPUErrorFilter {
    "none",
    "out-of-memory",
    "validation"
};

interface GPUOutOfMemoryError {};

interface GPUValidationError {
    readonly attribute DOMString message;
};

typedef (GPUOutOfMemoryError or GPUValidationError) GPUError;

partial interface GPUDevice {
    void pushErrorScope(GPUErrorFilter filter);
    Promise<GPUError?> popErrorScope();
};
```

### *Fallible Allocation*

An `out-of-memory` error scope can be used to detect allocation failure.

#### Example: tryCreateBuffer

```js
async function tryCreateBuffer(device, desc) {
  device.pushErrorScope('out-of-memory');
  const buffer = device.createBuffer(desc);
  if (await device.popErrorScope() !== null) {
    return null;
  }
  return buffer;
}
```

### *Waiting for Completion*

Since error scope results only return once the enclosed operations are complete, a `none` error scope can be used to detect completion of off-queue operations.
(On-queue operation completion can be detected with `GPUFence`.)

#### Example: createReadyRenderPipeline

```js
async function createReadyRenderPipeline(device, desc) {
  device.pushErrorScope('none');
  const pipeline = device.createRenderPipeline(desc);
  await device.popErrorScope(); // always resolves to null
  return pipeline;
}
```

`createReadyRenderPipeline` is asynchronous.
`requestAnimationFrame`'s callback is not treated as asynchronous - only the first task is guaranteed to occur before the frame is displayed.

```js
class Renderer {
  init() {
    const fastPipeline = createRenderPipeline(...);
    this.pipeline = fastPipeline;
  }

  prepareSlowPipeline() {
    createReadyRenderPipeline(...).then((slowPipeline) => {
      this.pipeline = slowPipeline;
    });
  }

  draw() {
    if (wantSlowPipeline) {
      prepareSlowPipeline();
    }
    // draw object with this.pipeline.
    // It switches to the "slowPipeline" when it becomes available.
  }
}

renderer.init();
const frame = () => {
  requestAnimationFrame(frame);
  renderer.draw();
};
requestAnimationFrame(frame);
```

### *Testing*

Tests need to be able to reliably detect both expected and unexpected errors.

### Example

```js
device.pushErrorScope('out-of-memory');
device.pushErrorScope('validation');

{
  // Do stuff that shouldn't produce errors.
  {
    device.pushErrorScope('validation');
    device.doOperationThatErrors();
    device.popErrorScope().then(error => { assert(error !== null); });
  }
  // More stuff that shouldn't produce errors
}

// Detect unexpected errors.
device.popErrorScope().then(error => { assert(error === null); });
device.popErrorScope().then(error => { assert(error === null); });
```

## *Telemetry*

If an error is not captured by an explicit error scope, it bubbles up to the device and **may** fire its `uncapturederror` event.

This mechanism is like a programmatic way to access the warnings that appear in the developer tools.
Errors reported via the validation error event *should* also appear in the developer tools console as warnings (like in WebGL).
However, some developer tools warnings might not necessarily fire the event, and message strings could be different (e.g. some details omitted for security).

The WebGPU implementation may choose not to fire the `uncapturederror` event for a given error, for example if it has fired too many times, too many times in a row, or with too many errors of the same kind.
This is similar to how console warnings would work, and work today for WebGL.
(In badly-formed applications, this mechanism can prevent the events from having a significant performance impact on the system.)

**Unlike** error scoping, the `uncapturederror` event can only fire on the main thread (Window) event loop.

```webidl
[
    Constructor(DOMString type, GPUUncapturedErrorEventInit gpuUncapturedErrorEventInitDict),
    Exposed=Window
]
interface GPUUncapturedErrorEvent : Event {
    readonly attribute GPUError error;
};

dictionary GPUUncapturedErrorEventInit : EventInit {
    required DOMString message;
};

// TODO: is it possible to expose the EventTarget only on the main thread?
partial interface GPUDevice : EventTarget {
    [Exposed=Window]
    attribute EventHandler onuncapturederror;
};
```

#### Example

```js
const device = await adapter.requestDevice({});
device.addEventListener('uncapturederror', (event) => {
  appendToTelemetryReport(event.message);
});
```

## Open Questions and Considerations

 - Is there a need for synchronous, programmatic capture of errors during development?
   (E.g. an option to throw an exception on error instead of surfacing the error asynchronously.
   Asynchronous error handling APIs are not enough to polyfill this.)
   This would only be needed for printf-style debugging; a "break on WebGPU error" would be used for Dev Tools debugging.

 - How can a synchronous application (e.g. WASM port) handle all of these asynchronous errors?
   A synchronous version of `popErrorState` and other entry points would need to be exposed on Workers.
   (A more general solution for using asynchronous APIs synchronously would also solve this.)

 - Should there be a maximum error scope depth?

 - Or should error scope balance be enforced by changing the API to e.g. `device.withErrorScope('none', () => { device.stuff(); /*...*/ })`?

 - Should the error scope filter be a bitfield?

 - Should the error scope filter have a default value?

 - Should errors beyond the first in an error scope be silently ignored, bubble up to the parent error scope, or be immediately given to the `uncapturederror` event?
    - (Currently, it is silently ignored.)

 - Should there be codes for different error types, to slightly improve testing fidelity? (e.g. `invalid-object`, `invalid-value`, `invalid-state`)

 - Should developers be able to self-impose a memory limit (in order to emulate lower-memory devices)?
   Should implementations automatically impose a lower memory limit (to improve stability and portability)?

 - To help developers, should `GPUUncapturedErrorEvent.message` contain some sort of "stack trace" taking advantage of object debug labels?
   For example:

   ```
   <myQueue>.submit failed:
   - commands[0] (<mainColorPass>) was invalid:
   - in setIndexBuffer, indexBuffer (<mesh3.indices>) was invalid:
   - in createBuffer, desc.usage was invalid (0x89)
   ```

 - How do applications handle the case where they've allocated a lot of optional memory, but want to make another required allocation (which could fail due to OOM)?
   How do they know when to free an optional allocation first?
    - For now, applications wanting to handle this kind of case must always use fallible allocations.
    - (We will likely improve this with a `GPUResourceHeap`, once we figure out what that looks like.)

 - Should attempting to use a buffer or texture in the `"out-of-memory"` state (a) result in immediate device loss, (b) result in device loss when used in a device-level operation (submit, map, etc.), or (c) just produce a validation error?
    - Currently described: none, implicitly (c)

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
    - For non-OOM, tentatively resolved: They can, inside of an error scope. Any subsequent errors can be suppressed. Not sure if it's useful.
    - For OOM, see other questions about OOM.

 - Should there be an API that exposes object status?
    - Resolved: No, but errors during object creation can be detected.

 - Should there be a way to capture out-of-memory errors without capturing validation errors? (And vice versa?)
    - Resolved: Yes, so applications don't accidentally silence validation errors.
