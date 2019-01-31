# Rejected Fatal Error Handling Revisions

Appendix document for [ErrorHandling.md](ErrorHandling.md).

Revisions in this document were rejected by the author (@kainino0x) before publishing.
They are kept for posterity, as examples of previous ideas.

## Revision 3-ish

The `GPUAdapter` and `GPUDevice` are event targets which receive events about adapter and device status.

```webidl
partial interface GPUAdapter : EventTarget {
    readonly attribute boolean isReady;
};

interface GPUAdapterLostEvent : Event {
    readonly attribute DOMString reason;
};

interface GPUAdapterReadyEvent : Event {};
```

```webidl
partial interface GPUDevice : EventTarget {};

interface GPUDeviceLostEvent : Event {
    readonly attribute boolean recoverable;
    readonly attribute DOMString reason;
};
```

If `GPUAdapter`'s `isReady` attribute is false, `createDevice` will fail. 
`isReady` may be set to `false` when a `"gpu-device-lost"` event fires.
It will always be set to `true` when a `"gpu-adapter-ready"` event fires.

 - `GPUAdapter` `"gpu-adapter-lost" -> GPUAdapterLostEvent`:
   Signals that the `GPUAdapter` cannot be used anymore.
   Sets the adapter's status to `"invalid"`.
   Any further `createDevice` calls will return invalid objects.

 - `GPUAdapter` `"gpu-adapter-ready" -> GPUAdapterReadyEvent`:
   Signals when it is okay to create new devices on this adapter.
   It may fire only if:
    - the adapter is still valid,
    - the adapter's `isReady` attribute is `true`, and
    - the adapter's `isReady` attribute was `false`.

 - `GPUDevice` `"gpu-device-lost" -> GPUDeviceLostEvent`:
   Signals that the `GPUDevice` cannot be used anymore.
   Sets the status of the device and its objects to `"invalid"`.
   (The `"gpulogentry"` event will not fire after a device loss, so this makes all further operations on the device effectively no-ops.)
   This may happen if something goes fatally wrong on the device (e.g. unexpected out-of-memory, crash, or native device loss).
   When this event is handled, the adapter's `isReady` attribute may be `false`, which indicates the application cannot make new devices.
   This event **may** cause the adapter's `isReady` attribute to become `false`.


### Rejected

This scheme requires apps to do a spaghettical incantation in order to know what to do, and when.
It involves listening to all of these events, diligently checking flags in the event handlers, and understanding weird races (like an adapter became ready and then was immediately lost, or an adapter became ready and then vends an immediately lost device).
