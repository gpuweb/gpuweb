# Timeline fences

Having fences store a number internally and wait / signal numbers is what we call numerical fences.
This is the design that D3D12 chose for `ID3D12Fence`.
D3D12 allows waiting on a fence before it is signaled, but Vulkan disallows doing this on `VkSemaphore` because some OSes lack kernel primitive to wait-before-signal.
This means that WebGPU will have to validate that any wait on a fence will be unblocked by a prior signal operation that has been enqueued.
To simplify the validation of signal-before-wait, we can force signaled number to be strictly increasing.

Thus each fence has two pieces of internal state:
 - The signaled value, the latest value passed to a signal to the fence, which is also the greatest thanks to the monotonicity
 - The completed value, the value corresponding to the latest signal operation that has been executed.

The fences will require additional restrictions and operations if WebGPU has multiple queues.
These changes will be tagged with [multi-queue]

# Creating fences

To mirror native APIs, fences are created directly on the `WebGPUDevice`.

```webidl
dictionary WebGPUFenceDescriptor {
    u64 initialValue = 0;

    // [multi-queue]
    WebGPUQueue signalQueue = null;
};

partial interface WebGPUFence {};

partial interface WebGPUDevice {
    WebGPUFence createFence(WebGPUFenceDescriptor descriptor);
};
```

The fence is created with both internal values set to `initialValue` and [multi-queue] is restricted to be signaled on `signalQueue`.
If `signalQueue` is set to `null`, it will act as if it was set to the "default queue" (pending multi-queue definition of what that is).

# Signaling

Signaling a fence is done like via this method:

```webidl
partial interface WebGPUQueue {
    void signal(WebGPUFence fence, u64 signalValue);
};
```

A Javascript exception is generated if:
 - `value` is smaller or equal to the signaled value of the fence.
 - [multi-queue] the fence must be signaled on the queue passed as the `signalQueue` of its descriptor.
   This restriction is to make sure the signal operations are well-ordered, which would be more complicated if you could signal on multiple queues.

After the call the signal value is updated to `signalValue`.

## Observing fences on the CPU

Observing the state of a fence on the CPU can be done by the following synchronous and non-blocking call:

```webidl
partial interface WebGPUFence {
    u64 getCompletedValue();
};
```

Alternatively it is possible to wait for a given value to be completed:

```webidl
partial interface WebGPUFence {
    Promise<void> onCompletion(u64 value);
};
```

This call generates a Javascript exception if `value` is greater than the fence's signaled value (to make sure the promise completes in finite time).
There is no way to synchronously wait on a fence in this proposal (it is better handled via the requestMainLoop proposal).
The promise is completed as soon as the fence's completed value is higher than `value`.
The promise can be rejected for example if the device is lost.

## Waiting on fences on the GPU [multi-queue]

If there are multiple queues, it would be possible to wait on a fence on a different queue:

```webidl
partial interface WebGPUQueue {
    void wait(WebGPUFence fence, u64 value);
};
```

This call generates a Javascript exception if `value` is greater than the fence's signaled value.
It makes further execution on the queue wait until the value is passed on the fence.

## Questions

 - Should we call fences "timelines" and have them created on queues like so `queue.createTimeline()`?
 - How do we wait synchronously on fences?
   Maybe it could be similar to `Atomics.wait`?
