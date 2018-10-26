# Multiple Queues

Multiple queues is important for:

- Explicit submission onto less capable queues, such as pure copy queues.
- Explicit distribution of submissions on machines with multiple queues of the same family.

## QueueFamily

There are multiple families of queues.
Availible families of queues are surfaced via `sequence<QueueFamily> Adapter.queueFamilies`.
Support for `graphics`, `compute`, and `copy` operations are surfaced by the respective attributes on the QueueFamily.
Queue families with `graphics` or `compute` will always have `copy`.
There may be queue families in the future like D3D12's video decode queues, which do not support copy operations.
If there are any families that support graphics, there is at least one family that supports both compute and graphics.
The most capable family is always first in the `Adapter.queueFamilies` list.
(It will either be a graphics+compute, or at least compute)
Exposed adapters must have at least a compute family.
Users can also create `QueueFamily`s.

## Queue Creation

Queues are created at Device creation time, and are exposed via `sequence<Queue> Device.queues`.
Each element in `sequence<QueueFamily> WebGPUDeviceDescriptor.queueRequests` results in a corresponding element in `Device.queues`.
If an user-provided QueueFamily does not match a family in `Adapter.queueFamilies`, a more capable family is used.
If no available family can satisfy an user-provided family, device creation fails.

## Synchronization

Queues can have fences inserted into them, and any queue can wait on that fence to be complete.

Synchronizing access to resources across queues should be done by telling a queue to wait until a fence is complete, followed by submitting command buffers that depend on that fence.
Resource data may have multiple concurrent readers, or exclusively one writer, at a time.
Resources may have multiple concurrent readers and writers, so long as all subranges satisfy many-read/single-write exclusion. [1]
If different commands would violate this exclusion, the implmentation injects synchronization.
If a command is submitted that will never be able to synchronize for exclusion without subsequent user commands, that Submit is refused.

[1]: For MVP, we require reads/write exclusion at whole-resource granularity, instead of allowing subranges.

### How Is Implicit Synchronization Done

Implicit Synchronization is clearly possible via the degenerate approach of strict serialization.
Viability depends on how difficult it is to inject synchronization with minimal overhead, and in particular minimal excess serialization.

Each CommandBuffer knows all reads and writes to its resources, and satisfies reads/write exclusion internally.
(out of scope of multi-queue discussion)
Further, baked CommandBuffers know their required starting memory barrier requirements, as well as their end state.

Each Resource effectively has:

~~~
struct LastAccess {
   CommandBuffer cb;
   AccessBits access;
};
list<LastAccess> last_accesses;
~~~

Each CommandBuffer effectively has:

~~~
struct ResourceAccess {
   Resource res;
   AccessBits src_access;
   AccessBits dst_access;
};
list<ResourceAccess> res_accesses;
~~~

For a `submit(sequence<WebGPUCommandBuffer> buffers)`, implementations inject any required synchronization.
On submit, each CommandBuffer in turn traverses its resources and identifies any outstanding synchronization requirements.
(i.e. a CommandBuffer with a Texture read knows that some other previously-submitted CommandBuffer last wrote to that Texture, and establishes a dependency on this write)
Upon submission, each CommandBuffers tags its resources with the relevant synchronization info for later CommandBuffers to check against.

In Vulkan, synchronization injection takes the form of synthesizing VkSubmitInfos, synchronizing via VkSemaphores and VkPipelineStageFlags, as well as submitting synthesized CommandBuffers containing memory barriers and queue family transfers.
(Queue family transfers may require submitting synthesized CommandBuffers to other queues, as well)

Implementation may warn users about synchronization overhead.

## Further work

Overhead could be reduced by allowing users to provide access/memory barrier hints and queue transfer hints.
Providing bad hints may cause worse performance, which implementations should warn users about.
