# Error Handling

The simplest design for error handling would be to do it synchronously, for example with Javascript exceptions and object creation returning `null`.
However this would introduce a lot of synchronization point for multi-threaded WebGPU implementations (or multi-process in the case of Chromium).

There are a number of cases that applications care about:

 - Getting errors synchronously during development, to breakin to the debugger
 - Getting notified that some error occured in deployed applications for telemetry
 - Being able to handle out-of-memory errors on resource creation
 - Ideally not have error handling make the API clunky to use

There are several types of WebGPU calls that get their error handled differently:

 - WebGPU Object creation.
 - Recording of GPU commands in `WebGPUCommandEncoder`.
 - Other commands such as `WebGPUQueue.submit`

## Status objects

The error status of WebGPU is provided to the application through a `WebGPUStatus` object, that contains both the `type` of the error (or success) as well as a text `reason` for debugging and telemetry.
The asynchronous error handling is done via WebGPU returning `Promise<WebGPUStatus>`.
(Alternatively the API could return a `WebGPUStatus` that's promisable / pollable / callbackable).

```
enum WebGPUStatusType {
    "success",
    "validation-error",
    "context-lost",
    "out-of-memory",
};

interface WebGPUStatus {
    WebGPUStatusType type;
    DOMString? reason;
};
```

`WebGPUStatusType` makes a distinction between several error causes (in addition to success):

 - Validation errors because the application did something wrong.
 - Out of memory cases that are recoverable.
 - Context loss where things went horribly wrong and the `WebGPUDevice` cannot be used anymore.

## Error handling in object creation

WebGPU objects the application uses are handles that either represent a successfully created object, or an error that occured during creation.
Successfully created objects are called "valid objects" and "invalid objects" otherwise.
It is possible to get a `WebGPUStatus` for an object that contains whether it is an error or a success.
This is done through `WebGPUObjectBase` from which most WebGPU objects inherit.

```
interface WebGPUObjectBase {
    Promise<WebGPUStatus> attribute status;
};
```

## Error handling in other operations

When a call other than object creation triggers an error, an error is recorded on the `WebGPUDevice`.
The current error status for this worker can be queried with `WebGPUDevice.getCurrentStatus`.
`getCurrentStatus` works like `glGetError` in that it returns the first error that happened after the last `getCurrentStatus` or success if none.
Unlike `glGetError` it is asynchronous, and stores one error status per Worker (so that middleware can do its own tracking without interference from other workers, for example).

```
partial interface WebGPUDevice {
    Promise<WebGPUStatus> getCurrentStatus();
};
```

## Error propagation of invalid objects

There is a general validation rule that using any invalid object in a WebGPU call is a validation error.
The effect of an error depends on the type of a call:

 - For object creation, the call produces an invalid object
 - For `WebGPUCommandEncoder` method, the `WebGPUCommandEncoder.finishEncoding` method will return an invalid object.
   This is like other object creation except that `WebGPUCommandEncoder` is a builder pattern
 - For other WebGPU calls, the call is a noop, and an error is recorded for this worker on the `WebGPUDevice`

Effectively this puts WebGPU in the "Maybe Monad".

## Other considerations

Implementation will provide a way to enable synchronous validation, for example via the devtools.
The extra CPU overhead should be ok with development purpose.

WebGPU could guarantee that objects such as `WebGPUQueue` and `WebGPUFence` can never be errors.
If this is true, then the only synchronous API that needs special casing is buffer mapping, where `mapping` is always `null` for error `WebGPUBuffer`.

Should WebGPU propagate all creation errors to the `WebGPUDevice` (unless the application explicitly chooses against it, for example for OOM)?
This would help application centralize telemetry in a single place.

To help developers, `WebGPUStatus.reason` could contain some sort of "stack trace" and could take advantage of debug name of objects if that's something that's present in WebGPU.
For example:

```
Failed <myQueue>.submit because commands[0] (<mainColorPass>) is invalid:
- <mainColorPass> is invalid because in setIndexBuffer, indexBuffer (<mesh3.indexBuffer>) is invalid
- <mesh3.indexBuffer> is invalid because it got an unsupported usage flag (0x89)
```

Also the exact shape of `WebGPUStatus` and how it is returned will piggy-back on the decision taken for `WebGPUFence`.
