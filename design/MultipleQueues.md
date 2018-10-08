# Multiple Queues

Queues are created at Device creation time, and are exposed via `sequence<Queue> Device.queues`.
There are multiple types of queues, denoted by the `.type` bitfield on the Queue object.
Queues can support `graphics` operations, `compute` operations, both, or neither.
"Neither" Queues can only execute copy commands.
If there are any queues that support graphics, there is at least one queue that supports
both compute and graphics.
The most capable queue is always first in the `Device.queues` list.
(It will either be a graphics+compute queue, or compute queue)
Devices must be able to support at least a compute queue, or device creation will fail.

## Synchronization

Queues can have fences inserted into them, and any queue can wait on that fence to be complete.
Synchronizing usage of resources across queues should be done by telling a queue to wait until
a fence is complete, followed by submitting command buffers that depend on that fence.
