# Command Submission

Command buffers carry sequences of user commands on the CPU side.
They can be recorded independently of the work done on GPU, or each other.
They go through the following stages:

creation -> "recording" -> "ready" -> "executing" -> done

Command buffers are created from and submitted to a command queue.
Creation and submission do not have to follow the same order.
The queue is also used to signal fences, allowing the user to know when the command buffers are done.

## Detailed Model

Users issue rendering and compute commands (such as resource bindings, draw calls, etc) via command buffers.
The concept of `WebGPUCommandBuffer` matches the native graphics APIs.
Those command buffers go through the following stages in their life cycle.
It starts with creating a new `WebGPUCommandBuffer` from a `WebGPUCommandQueue` instance.
From this point, the command buffer is considered to be in "recording" state.

Commands can be encoded independent of anything done on `WebGPUDevice` or the underlying GPU.
The recording is CPU-only operation, and multiple command buffers can be recorded independently on web workers.
(TODO: disallow recording multiple command buffers on the same thread/web worker?).
Recording usually consists of a number of passes, be it render or compute, with occasional copy operations inserted between them.

Since a programmable pass defines the resource binding scope, synchronization rules, fixes the resource usage, and exposes a number of specific operations, we encapsulate the encoder of a pass into a separate object, such as `WebGPURenderPassEncoder` and `WebGPUComputePassEncoder`.
The pass encoder object can be obtained from a command buffer by calling `beginRenderPass` or `beginComputePass` correspondingly.
The command buffer is expected to be in "recording" state, or otherwise a synchronous error is triggered.
No operations may be done on the `WebGPUCommandBuffer` if there is an open pass being encoded to it.
Calling any methods on the command buffer with an open pass, or submitting it to the command queue, triggers a synchronous error.
A pass encoding consists of state setting code and draw/dispatch calls, which are all methods on the corresponding encoder object.
In order to close a pass, the user calls `WebGPUProgrammablePassEncoder::endPass`, which returns the owner `WebGPUCommandBuffer` object.
Passes cannot straddle command buffers, and a command buffer may contain multiple passes.

In order to finish recording a command buffer, the user calls `WebGPUCommandBuffer::finish` method, which transitions it from "recording" to the "ready" state.
It is valid to transfer this object between web workers.
When "ready", a command buffer can only be submitted for execution via `WebGPUCommandQueue::submit`, and no recording operations are available.
This method gets a sequence of command buffers and submits them (in the given order) to the GPU driver.
There are a few hidden (from the user point of view) stages here before the command buffer actually reaches the GPU.

Once submitted, the command buffer switches to "executing" state, which means the command buffer will execute (both on the CPU and GPU) in finite time.
If the WebGPU implementation fails to submit the command buffer due to a problem with recorded content (e.g. exceeding the limit for the instance count in a draw call), it is turned into an internally null object, and the asynchronous error is reported.
The feature to re-use command buffers for multiple submissions is still being discussed, and until this is clear, we consider the `WebGPUCommandBuffer` to be moved into submission.
Any operations on a command buffer in the "executing" state, other than dropping it (which is what the user is expected to do), would trigger a synchronous error.

If the submission is successful, then at some point in time the GPU will be done processing it.
The WebGPU implementation takes the responsibility to detect this moment and gracefully recycle/destroy this command buffer, when it's safe to do so.
