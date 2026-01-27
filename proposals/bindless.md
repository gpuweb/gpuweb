# Bindless

* Status: [Draft](README.md#status-draft)
* Created: 2025-10-13
* Issue: [#380](https://github.com/gpuweb/gpuweb/issues/380) and child issues.

Previous discussions happened on:

 - [Bindless investigation and proposal (HackMD)](https://hackmd.io/PCwnjLyVSqmLfTRSqH0viA) (which the motivation and investigation part of this document is taken from).
 - [Bindless for WebGPU: wgpu edition (HackMD)](https://hackmd.io/@cwfitzgerald/wgpu-bindless) with additional design ideas and implementation constraints.
 - [WebGPU Bindless 2025 F2F (Google Slides)](https://docs.google.com/presentation/d/1mOUQUQIOjND14orEvJ5Uv04_2i8Dcis3pO1ZlnPTFyg/edit?usp=sharing) which is the proposal used for the first version of this document.

Other useful resources:

 - [Presentation of wgpu-rs bindless support in 2023](https://docs.google.com/document/d/1bbwoAu7NZ5GAWAE12xUNZi08fRuSRDfYLzHxV6yFDF8/edit?tab=t.0#heading=h.9sruw02gevmf)
 - [A series of posts from Traverse Research on bindless](https://blog.traverseresearch.nl/bindless-rendering-setup-afeb678d77fc)
 - ["Descriptors are hard" presentation from Faith Ekstrand](https://indico.freedesktop.org/event/10/contributions/402/attachments/243/327/2025-09-29%20-%20XDC%202025%20-%20Descriptors%20are%20Hard.pdf)

## Motivation

In the current (non-bindless) WebGPU binding model, shaders have access to a small set of resources that are in the `GPUBindGroups` currently bound at the time `draw*` or `dispatch*` is called.
The CPU-side code of the application has to know the what are all resources a shader might need and bind it at command-recording time.
The amount of resources bound while executing a shader also has to stay under limits that can be fairly low.

This model was chosen for the first version of WebGPU as WebGPU without extension needs to run on a variety of hardware, including hardware that has a fixed number of "registers" configured to access resources.
In this "bindful" model, `setBindGroup` sets the internal state of the registers, and shader assembly uses a register number to name a resource.
Over the last decades, GPU architectures have shifted to a "bindless" model where resources are instead named in shaders assembly by a GPU memory pointer, or an index into a table somewhere in memory.
This let shaders index a vastly increased amount of resources and allowed many new kinds of GPU algorithms.

In more recent rendering engines many algorithms execute on the GPU that need global information about the scene or the objects contained in it.
They need access to each texture potentially used by an object in case they need to process that object.
This blows way past the resource limits in the bindful model.
Examples of algorithms that do this are:

 - Visibility buffers, which do a first rasterization pass with just object and triangle IDs in a render target, then have a compute shader / large quad that handles the texturing of all objects at once.
 - Ray-tracing where rays can be launched in any direction and need to get the texture of the intersected object.
 - Rendering 2D contents with many embedded images.
 - And a lot, lot more.

In some cases texture atlasing can be used as a (painful) workaround, but it can become extremely messy, inefficient (with lots of the atlas unused), or inflexible.
Exposing the bindless capabilities of the hardware would enhance the programming model of WebGPU and unlock many exciting new applications and capabilities.

## Investigation

### Bindless concepts

**Residency**: Residency management where the driver makes sure all used resources are swapped-in to GPU memory can no longer be done totally automatically; it needs information from the application.
When the GPU runs out of memory to keep all allocations of all resources in GPU memory at the same time, the driver can swap them in and out of system (CPU) memory to keep the necessary working set available in GPU memory when shaders execute.
In the bindful model, the driver has close to perfect information of which resources will be used and does that automatically.
In bindless, applications can use any resource at any time so applications must manage residency by telling the driver which resources must be kept resident when.
The WebGPU implementation must still be resilient to misbehaving pages that try to oversubscribe resources.

**Indexing of descriptors - uninitialized entries**: In all APIs bindless is be done by indexing descriptors (Metal can a bit more flexible) in arrays of descriptors that have been allocated by the application.
Applications allocate conservatively-sized arrays and elements might not be initialized, or contain stale data (esp past the currently used index range).
Sparse arrays are supported in target APIs, as long as the uninitialized entries are not used.

**Indexing of descriptors - index uniformity**: Some hardware can only index inside the descriptor arrays uniformly, though a scalarization loops allows emulating non-uniform indexing.

**Descriptor homogeneity**: Hardware descriptors may have different sizes depending on the resource type.
For example a buffer could be a 64bit virtual address, while a sampled texture could be a 64 byte data payload.
This makes allocation of the descriptor arrays and their indexing in the shader depend on the type of descriptor, so descriptor types may not always be mixed in the same descriptor array.

**Samplers**: Samplers stayed "bindful" a lot longer than other types of resources because they are pure fixed-function object that don't have contents.
In all APIs bindless for samplers has additional constraints and limits.

### D3D12 / HLSL

Overall D3D12 was designed with bindless at the forefront with the descriptor tables, although support depends on the hardware tier.
CBV UAV SRV descriptor heaps are heterogeneous on the API side but HLSL only gained support with `ResourceHeaps` in Shader Model 6.6.

#### D3D12

D3D12's binding model is centered around the [root signature](https://learn.microsoft.com/en-us/windows/win32/direct3d12/root-signatures-overview) and [descriptor heaps](https://learn.microsoft.com/en-us/windows/win32/direct3d12/creating-descriptor-heaps)

Resource in D3D12 are bound in the root signature (equivalent of the `GPUPipelineLayout`) that can contain root constants (immediate data), root descriptors (a single binding) or a root descriptor table (an array of bindings).
The root descriptor table [is defined with `set*RootDescriptorTable`](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/nf-d3d12-id3d12graphicscommandlist-setgraphicsrootdescriptortable) as the `D3D12_GPU_DESCRIPTOR_HANDLE` (GPU memory pointer) to the first element of the array.
This handle must be inside one of the two currently bound descriptor heaps (the one for sampler, or the one for everything else).

Descriptors heaps are either CPU heaps used for staging, or GPU heaps that are actually used by the hardware and usable in root signature.
D3D12 supports [copies between heaps](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/nf-d3d12-id3d12device-copydescriptors) to move from staging to shader-visible heaps.
Shader-visible heaps and root descriptor tables have limits that depend on the [resource binding tier](https://learn.microsoft.com/en-us/windows/win32/direct3d12/hardware-support).
Tier 2 is bindless for textures, Tier 3 bindless for everything. Both tiers have a limit of 2048 max descriptors in sampler heaps but [recent D3D12 features](https://microsoft.github.io/DirectX-Specs/d3d/VulkanOn12.html#sampler-descriptor-heap-size-increase) add a queryable maximum of at least 4000.

D3D12 delegates [residency management](https://learn.microsoft.com/en-us/windows/win32/direct3d12/residency) to the application that tags individual memory heaps (allocations from which resources are sub-allocated) resident and evicts them.

CBV_UAV_SRV descriptor heaps in D3D12 are heterogeneous with a device-wide [increment](https://learn.microsoft.com/en-us/windows/win32/api/d3d12/nf-d3d12-id3d12device-getdescriptorhandleincrementsize) between descriptors when copying between heaps or indexing them.

It is not allowed to change a descriptor in a heap while it might be in use by commands as that could be a data-race.

#### HLSL

On the HLSL side, using bindless is done by declaring unsized arrays of textures, and specifying it is unbounded in the root signature (if one is provided in the HLSL):

```
// Declaration
Texture2D<float4> textures[] : register(t0)

// Root signature
DescriptorTable( CBV(b1), UAV(u0, numDescriptors = 4), SRV(t0, numDescriptors=unbounded) )
```

Non-uniform indexing must be done with an extra `NonUniformResourceIndex` keyword:

```
tex1[NonUniformResourceIndex(myMaterialID)].Sample(samp[NonUniformResourceIndex(samplerID)], texCoords);
```

The restriction here is that a single type is given for the array so it is not possible to chose dynamically inside the shader what the type of the binding will be.
It has to be statically known to be UAV, SRV or CBV, and even then it must be a single type for each of there (a float, uint, or int texture).
Overlapping of the root descriptor range in the same root descriptor table is allowed which could be used to have different types in HLSL.

Shader Model 6.6 lifts this restriction with the [dynamic resources](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_DynamicResources.html) feature. The `ResourceDescriptorHeap` HLSL object can be used to cast any index to any resource type:

```
<resource variable> = ResourceDescriptorHeap[uint index];
<sampler variable> = SamplerDescriptorHeap[uint index];
```

### Metal / MSL

Metal [argument buffer tier 2](https://developer.apple.com/documentation/metal/buffers/improving_cpu_performance_by_using_argument_buffers?language=objc) supports dynamically indexing resources in arbitrarily-sized argument buffers.
[After specific-OS releases](https://developer.apple.com/documentation/metal/buffers/improving_cpu_performance_by_using_argument_buffers?language=objc) it seems that the argument buffer layout is transparent and could be used for heterogeneous descriptor but there is no indication how.

#### Metal

Argument buffers are `MTLBuffers` that contain resources usable by the shader.
Their layout is opaque (maybe until macOS 13.0 for Tier2 devices?) and they have to be filled by using an `MTLArgumentEncoder` which is similar to a `GPUBindGroupLayout` either reflected from an `MTLLibrary` or created directly with `MTLArgumentDescriptor`.
It is called out explicitly that argument buffers cannot contain unions, so that can't be used for heterogeneous descriptors.
The argument buffers are bound with the `set*Buffer` method like any other buffer.
With argument buffer tier 2 it is also possible to directly write `buffer.gpuAddress` somewhere in `argumentBuffer.contents`.

When using argument buffers, the application must handle residency explicitly by calling `useResource`, `useHeap` (when suballocating resources), or `useResidencySet`.

Samplers used with argument buffers must have supportsArgumentBuffer set to true, and MTLDevices have a query for the maximum number of unique such samplers that are supported.

#### MSL

Here is an example from the Metal documentation.
The argument to the entrypoint is a reference to a structure containing resources itself.
The layout of this struct must correspond to the `MTLArgumentEncoder`:

```
struct ArgumentBufferExample{
    texture2d<float, access::write> a;
    depth2d<float> b;
    sampler c;
    texture2d<float> d;
    device float4* e;
    texture2d<float> f;
    int g;
};


kernel void example(constant ArgumentBufferExample & argumentBuffer [[buffer(0)]])
{
```

Metal Shading Language Specification 3.2 section 2.14.1 "The Need for a Uniform Type" shows that Metal will scalarize non-uniform indexing in arrays of resources, but at a cost.

It's not immediately clear how heterogeneous bindless would be expressed in MSL.

#### Metal 4

[Metal 4](https://developer.apple.com/documentation/metal/understanding-the-metal-4-core-api) overhauls the Metal API with many reworked concepts for command encoding, barriers and resource bindings.
It adds a [`MTL4ArgumentTable`](https://developer.apple.com/documentation/metal/mtl4argumenttable) object that's used in [`setArgumentTable`](https://developer.apple.com/documentation/metal/mtl4rendercommandencoder/setargumenttable(_:stages:)?language=objc) to set the resources that subsequent shader invocations will use.
Argument tables are created with a max count of textures/buffers/samplers and with entries updated individually on the CPU.
The Metal documentation notes that "Metal takes a snapshot of the resources in the argument table when you encode a draw, dispatch, or execute command." which is a copy-on-write semantic.

The single (really per-stage) current argument table is the only way to pass resources to a shader in Metal 4 and shaders use "indexed" entrypoint arguments to references resources in the current argument table.
Because of this it seems that argument table cannot be used to implement bindless because their entries cannot be indexed dynamically but more importantly because the copy-on-write would be too expensive if it happened each time a bindful resource is changed, or an immediate updated.
Instead bindless will still need to use argument buffers that are stored inside the argument table.

### Vulkan / SPIR-V

Vulkan promoted [`VK_EXT_descriptor_indexing`](https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VK_EXT_descriptor_indexing.html) ([documentation](https://docs.vulkan.org/samples/latest/samples/extensions/descriptor_indexing/README.html)) to core in Vulkan 1.2, it is how bindless is exposed in that API.
Further extensions enable additional niceness, like [`VK_EXT_mutable_descriptor_type`](https://registry.khronos.org/vulkan/specs/1.3-extensions/man/html/VK_EXT_mutable_descriptor_type.html).

#### Vulkan

Applications start by querying [`VkPhysicalDeviceVulkan12Features`](https://registry.khronos.org/vulkan/specs/1.3-khr-extensions/html/vkspec.html#VkPhysicalDeviceDescriptorIndexingFeatures).`dynamicIndexing` then can get more information from [`VkPhysicalDeviceDescriptorIndexingFeatures`](https://registry.khronos.org/vulkan/specs/1.3-khr-extensions/html/vkspec.html#VkPhysicalDeviceDescriptorIndexingFeatures) like whether updating descriptors sets in use is possible, if sparse descriptor sets are possible, and if SPIR-V can use the `RuntimeDescriptorArray` capability.

When creating a `VkDescriptorSet` new flags can be passed to the last binding to specify the set my be sparse, may be updated after being bound / while in use, and maybe have a variable length array as the last element.
When allocating a descriptor set for this layout, [`VkDescriptorSetVariableDescriptorCountAllocateInfo`](https://registry.khronos.org/vulkan/specs/1.3-khr-extensions/html/vkspec.html#VkDescriptorSetLayoutCreateFlagBits) is passed to specify how big this variable size array at the end will be.

Descriptor sets can only be modified on the device timeline and descriptors cannot be modified while they might be in use as that would be a race.
`VK_EXT_descriptor_buffer` is another related extension which could allow pipelining the updates to descriptors with other queue operations.

By default in Vulkan, all resources are resident at all time and the application must manage residency by itself.
Some Vulkan extensions like [`VK_EXT_memory_budget`](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_EXT_memory_budget.html) and [`VK_EXT_pageable_device_local_memory`](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_EXT_pageable_device_local_memory.html) allow getting a memory budget and asking the driver to manage residency but are far from available on all systems.

#### SPIR-V

The bindings instead of being pointers to `OpTypeImage` or `OpTypeArray<OpTypeImage, N>` can be `OpTypeRuntimeArray<OpTypeImage>` which allows for unbounded indexing.

When using mutable descriptor types for heterogeneous descriptors, [multiple bindings can be aliased on the same set/binding location](https://github.com/microsoft/DirectXShaderCompiler/blob/main/docs/SPIR-V.rst#resourcedescriptorheaps-samplerdescriptorheaps), one for each type of descriptor accessed in the shader.

### Constraints from WebGPU implementations

In the target APIs, a call to `setBindGroup/setResourceTable` results in a underlying API command that bakes a GPU pointer (or index in heap) in the native command buffer.
The APIs don't support patching these GPU pointers / indices before submitting commands to the GPU.
This means that **`GPUBindGroups/GPUResourceTables` set in an encoder cannot have their underlying API object replaced before submit.**

Other constraints from (some) underlying APIs are that bindings can only be updated on the device timeline, and that updates must not race with potential uses of these bindings by the GPU.
This means that **Bindings cannot be overwritten before `onSubmittedWorkDone` since the last time they were visible on the queue timeline**.

#### Vulkan with `VK_EXT_descriptor_heap`

The [`VK_EXT_descriptor_heap`](https://docs.vulkan.org/features/latest/features/proposals/VK_EXT_descriptor_heap.html) extension is a rework of bindless support in Vulkan to address many of the problems with the previous approaches and looks to be the recommended path for bindless on drivers that support the extension.
It is conceptually similar to D3D12's descriptor management but gives more control to applications.
Concretely it completely replaces the `VkDescriptorSet` state on command buffers with a combination of two descriptor heaps (one for resources, one for samplers) set on the command encoder, and at least 256 bytes of "push data" accessible immediately by shaders (that are used instead of "push constants").

Descriptor heaps are allocated from buffers with the `VK_BUFFER_USAGE_DESCRIPTOR_HEAP_BIT_EXT` and filled with descriptor data.
During the recording of commands, the current resource and sampler heaps are set using their `VkBuffer` device address with the [`vkCmdBind[Sampler|Resource]HeapEXT`](https://docs.vulkan.org/features/latest/features/proposals/VK_EXT_descriptor_heap.html#_descriptor_heaps) functions.
The driver exposes the size and alignment constraints of various kinds of descriptors (see [`VkPhysicalDeviceDescriptorHeapPropertiesEXT`](https://docs.vulkan.org/features/latest/features/proposals/VK_EXT_descriptor_heap.html#_device_properties)).
Using this information, the application gets the bit representation of descriptors using [`vkWrite[Sampler|Resource]DescriptorsEXT`](https://docs.vulkan.org/features/latest/features/proposals/VK_EXT_descriptor_heap.html#_getting_descriptors) that writes them in CPU memory.
The application then puts the descriptors in the descriptor heap memory as it chooses.
Similarly to D3D12, the required limit on sampler descriptor heaps is very small at 4000 while at least 2^20 resources are supported.

The extension has [a lot more API surface](https://docs.vulkan.org/features/latest/features/proposals/VK_EXT_descriptor_heap.html#_vkdescriptorsetlayout_mapping) to allow transitioning from a `VkDescriptorSet` model to `VK_EXT_descriptor_heap` iteratively.
New options are added to pipeline compilation that does a SPIR-V transform from using bind points directly populated by `VkDescriptorSet` to sourcing offset into the current descriptor heap from push data. (and many other kinds of indirection to emulate push descriptors, dynamic buffer offsets, etc).
There is also complexity around support for border colors, secondary command buffers, etc (but this doesn't affect WebGPU).

Note that since the descriptor heaps are just ranges of `VkBuffers`, it is possible to do GPU-GPU copies of descriptors.

#### SPIR-V with `SPV_EXT_descriptor_heap`

[`SPV_EXT_descriptor_heap`](https://github.khronos.org/SPIRV-Registry/extensions/EXT/SPV_EXT_descriptor_heap.html) is necessary for shaders used with `VK_EXT_descriptor_heap`.
It adds two new builtins, `SamplerHeapEXT` and `ResourceHeapEXT` that are declared as "untyped pointer in `UniformConstant`" address space.
From these pointers the shaders computes explicit offsets in the resource heaps and "casts" them to the correct descriptor type.

The size of resources can be retrieved using `OpConstantSizeOfEXT` which also makes the extension add a number of `[Offset|ArrayStride]IdEXT` as alternatives to `Offset/ArrayStride` that can use the result of a constant computation.
There is no discussion in that extension of how shaders use "push data" but it's most likely reusing the existing SPIR-V support for push constants.

## Proposal

### WebGPU API

A new `GPUResourceTable` concept is added to WebGPU that represents a variable-size, sparse and (totally or partially) heterogenous set of bindings.
The resource table can be set in the `GPUCommandEncoder` state and used in shaders to retrieve the resource of a given type at a given index in the currently set `GPUResourceTable`.
Bindings in the `GPUResourceTable` can be updated over time as new resources become needed, or previous resources get no longer in use.
To efficiently implement the validation, memory barrier and other similar kind of tracking needed for `GPUResourceTable`, the mutable resources contained in them must be "pinned" to a certain usage which prevents other kinds of accesses to them.

#### Adapter capabilities and device creation

Two new optional features are added:

 - `"sampling-resource-table"` that exposes a new `GPUResourceTable` that's a sparse array of resources accessible from shaders. It may only contain samplers and sampled textures.
 - `"heterogeneous-resource-table"` that depends on it, that additionally allows any kind of resource but uniform buffers in resource tables.

There are two separate extensions because while the heterogeneous resource tables is what we want to expose in the future, requiring support for it would prevent exposing resources tables on a lot of devices that support the sampling version only.

```webidl
partial enum GPUFeatureName {
    "sampling-resource-table",
    "heterogeneous-resource-table",
};
```

Resource tables are sized by the developer with a value passed in `createResourceTable` so a new limit is needed to expose the underlying API limitations on the size of the bindless things.
D3D12 has fixed limits per "resource binding tier" (with 500 000 being the base one) while Vulkan has limits per binding type that would be better to have as a single minimum limit (at least 500 000 in practice).
The new `maxResourceTableSize` limit is added, of class "maximum" and minimum of 50'000 when either optional feature is available.

```webidl
partial dictionary GPUSupportedLimits {
    readonly attribute unsigned long maxResourceTableSize;
};
```

#### Resource tables creation

The `GPUResourceTable` creation only takes the size of the resource table as an argument.
Because the `GPUResourceTable` is an object containing data, it gets a `.destroy()` method as well as a reflection of its creation parameters.

```webidl
dictionary GPUResourceTableDescriptor : GPUObjectDescriptorBase {
    required GPUSize32 size;
};
partial interface GPUResourceTable {
    void destroy();

    readonly unsigned long size;
};
partial interface GPUDevice {
    GPUResourceTable createResourceTable(GPUResourceTableDescriptor descriptor);
};
```

The steps for `GPUDevice.createResourceTable(desc)` are:

 - if `desc.size > this.limits.maxResourceTableSize` throw a `RangeError` and return.

    - Note: this is done to avoid the need to create giant content-timeline arrays if `size` is huge but fails validation on the device timeline.

 - Let `t` be a new WebGPU object (this, GPUResourceTable, desc).
 - let `t.size` be `desc.size`.
 - On the device timeline:

    - If any of the following is not satisfied, invalidate `t`:

        - `"sampling-resource-table"` is enabled (explicitly or implicitly with `"heterogeneous-resource-table"`).

    - Create the device allocation for `t`. If it fails without side-effects, generate an out-of-memory error, invalidate `t` and return.

 - Return `t`.

The steps for `GPUResourceTable.destroy()` are:

 - On the device timeline, set `this.[[destroyed]]` to `true` (it is a state initially set to `false`). Note that implementations no longer need `this.[[availableAfterSubmit]]` for tracking and can free it.

Additional validation rule for `queue.submit()`:

 - All `GPUResourceTable` referenced in the commands must have `[[destroyed]]` at `false`.

#### Encoder state and pipeline compatibility

The `GPUResourceTable` that shaders will access is set on the `GPUBindingCommandsMixin` using `setResourceTable`.
There is a single resource table set on encoders at a time, and the resource table can be unset by passing `null` to `setResourceTable`.

```webidl
partial interface GPUBindingCommandsMixin {
    void setResourceTable(GPUResourceTable? table);
}
```

Steps for `GPUBindingCommandsMixin.setResourceTable(table)` are all on the device timeline:

 - Validate the encoder state of `this`, if it returns false, return.
 - If any of the following requirements are unmet, invalidate `this` and return.

    - `"sampling-resource-table"` is enabled (explicitly or implicitly with `"heterogeneous-resource-table"`).
    - `table` is either `null` or valid to use with `this`.

 - Set `this.[[resource_table]]` to `table` (it is a state initially set to `null`).
 - If `table` is not `null`, append it to `this.[[resource_tables_used]]`.

Since the shaders can use new encoder state, there needs to be new information passed in the pipelines and validated in `draw/dispatch`.
The use of a `GPUResourceTable` is the same in compute and render pipelines so a new compatibility state is added in `GPUPipelineLayoutDescriptor` with changes to algorithms dealing with `GPUPipelineLayout`:

```webidl
partial dictionary GPUPipelineLayoutDescriptor {
    bool usesResourceTable = false;
};
```

Changes to algorithms are:

 - In `createPipelineLayout` a validation error is generated (and an error object) if `usesResourceTable` is `true` but `"sampling-resource-table"` is not enabled (explicitly or implicitly with `"heterogeneous-resource-table"`).
 - In validating `GPUProgrammableStage(stage, descriptor, layout, device)` a validation error is generated if the shader uses the WGSL resource table builtins but `layout.[[desc]].usesResourceTable` is `false`, or if the types used to access the resource tables are not supported with the extensions enabled (for example storage textures when only `"sampling-resource-table"` is enabled).
 - In creating the defaulting pipeline layout, if the shader uses the WGSL resource table builtins, set `desc.usesResourceTable` to `true`.
 - In the validation for `dispatch*` and `draw*` add a check that if `pipeline.[[desc]].layout.[[desc]].usesResourceTable` is `true`, then the encoder's `[[resource_table]]` is not null.
 - In `queue.submit`, validate that none of the tables in the various encoder's `[[resource_tables_used]]` are destroyed.
 - Similar to `GPUBindGroups`, reset `[[resource_table]]` after a call to `executeBundles`.

#### Pinning of buffer and texture usages

Experience from wgpu-rs' prototyping of bindless is that the overhead of validating the state of resources and generating memory barriers for the resource tables is unacceptable.
There is the need to make the resources in the resource tables be "free" for validation and memory barrier generation, instead of walking them for each usage synchronization scope.
This proposal introduces "resource pinning" to a specific kind of usage.
When a resource is unpinned it can be used with any usages specified at creation, but when pinned only the single pinned usage is allowed.
This proposal contains WGSL-side validation for the accesses which is augmented to also check that resources are pinned in addition to being present and of the correct type.
This way unpinned resources are not accessible via resource tables, ensuring that correct validation and barriers are done when resources are pinned.

```webidl
partial interface GPUTexture {
    void pin(GPUTextureUsage usage);
    void unpin();
};
```

TODO: [#5375](https://github.com/gpuweb/gpuweb/issues/5375) Add the similar interface for `GPUBuffer`.

TODO: [#5376](https://github.com/gpuweb/gpuweb/issues/5376) Should usages be used when they don't differentiate between read-only storage access and writeable storage access?

TODO: [#5378](https://github.com/gpuweb/gpuweb/issues/5378) Pinning and unpinning add additional state to resources that makes WebGPU code less composable, are there better alternatives?

TODO: [#5381](https://github.com/gpuweb/gpuweb/issues/5381) Add a mechanism to allow unpinning locally for some sets of commands (like rendering to one of the textures in the resource table).

Validation for `GPUTexture.pin(usage)`:

 - `"sampling-resource-table"` must be enabled on the device (explicitly or implicitly with `"heterogeneous-resource-table"`).
 - `this` must not have been destroyed.
 - `usage` must be a single shader usage.

Validation for `GPUTexture.unpin()`:

 - `"sampling-resource-table"` must be enabled on the device (explicitly or implicitly with `"heterogeneous-resource-table"`).

Note that the calls to `pin` and `unpin` don't need to be balanced.
Pinning replaces the currently pinned usage, if any.

Every check for `GPUTexture.[[destroyed]]` for use with `usage` of the texture by the GPU has an additional check that the pinned usage, if any, matches `usage`.
In implementations this can be done with almost no additional overhead to the current validation of `[[destroyed]]` by replacing sets of used resources into maps of resources to usages, and by combining the `usage` and `[[destroyed]]` checks in a single bitmask check.

#### Updates of bindings in resource tables

The set of resources that the application needs to access will evolve over time.
For example in a rendering engine that supports streaming of assets, when new content is loaded (models, map chunks, etc) it will need to be added to the resource table, and some now unused content removed.
Resource tables can use a lot of memory so this proposal adds a way to update the content of existing resource tables over time.
Other proposals were made that involved copy-on-write semantics, but not selected for this proposal because:

 - Resource tables can contain megabytes of data, so copying them is expensive and would increase peak memory usage.
 - Due to the implementation constraints listed above, updates wouldn't happen in the resource tables already referenced in command encoders (even encoders that are still open for recording).
 - Transparently optimizing the copy-on-write is not possible because the application can always detect if a resource has been made available, which would cause subtle races and non-portability (an application might rely on the copy happening, but on faster hardware the optimization would reuse a now unused binding faster).

The D3D12 and Vulkan 1.2 require that resource tables are modified by the CPU, without racing with the GPU trying to use the modified binding.
This is somewhat similar to the design constraint for buffer mapping, where ownership is transferred back and forth between the CPU and GPU, but for resource tables we should try to have a simpler looking API.

```webidl
partial interface GPUResourceTable {
    void update(GPUIndex32 slot, GPUBindingResource resource);
    GPUIndex32 insertBinding(GPUBindingResource resource);
    void removeBinding(GPUIndex32 slot);
};
```

Two ways to update the resource tables are exposed to allow both implicit and explicit allocation of resources in the resource table.
`insertBinding` is simpler to use because it defers to the browser's tracking of which slots may be in use and returns to the user the `slot` it placed the `resource` on (or an exception on failure).
On the other hand `update` gives the application control of where it places binding, which may be useful to allocate contiguous ranges, for hardcoded slots, or when porting code manually allocating in D3D12/Metal/Vulkan already.

`GPUQueue` is augmented to have monotonic numbers that can be used to refer to `GPUQueue.submit()` calls and the ones that have been completed for use in the validation of `GPUResourceTable.update/insertBinding/removeBinding`:

 - An additional state is added to `GPUQueue`:

   - A `Number` called `[[lastSubmitIndex]]` with initial value of `0`.
   - A `Number` called `[[completedSubmitIndex]]` with initial value of `0`.

 - In the steps of `GPUQueue.submit`, add do:

   - Increment `this.[[lastSubmitIndex]]`.
   - Let `submitIndex` = `this.[[lastSubmitIndex]]`.
   - `this.onSubmittedWorkDone().then(() => {this.[[completedSubmitIndex]] = submitIndex})`.

This is necessary for resource tables to track when is the last time that a slot may have been used on the GPU.
It is valid to overwrite a slot only when it can no longer be used on the GPU and both `GPUResourceTable.update` and `GPUResourceTable.insertBinding` use that in their internal logic.
The user can make a slot no longer possible to use on the GPU using `removeBinding` but because some GPU work might still be in-flight, the slot will only become available later, when current GPU work is completed.

Additional internal state is added to `GPUResourceTable`:

 - An `Array<Number>` called `[[availableAfterSubmit]]` of size `this.size` initially filled with `0` values.

Steps for `GPUResourceTable.update(slot, resource)`:

 - If any of the following is not satisfied, throw an `OperationError`:

    - `this.destroy()` has never been called. (Note: this is a content timeline check, but `[[destroyed]]` is a device-timeline boolean)
    - `slot` must be `< this.size`.
    - `this.[[availableAfterSubmit]][slot] <= this.[[device]].queue.[[completedSubmitIndex]]`

 - Set `this.[[availableAfterSubmit]][slot]` to `Infinity`.
 - On the device timeline:

   - If any of the following is not satisfied, generate a validation error and return.

      - `this` is valid and `destroy()` hasn't been called on it.
      - If `resource` is not possible to set in the `GPUResourceTable` (TODO [#5374](https://github.com/gpuweb/gpuweb/issues/5374), determine the compatibility rules, depending on sampling vs. heterogeneous).

   - Set the entry at `slot` in the table to `resource`.

Steps for `GPUResourceTable.insertBinding(resource)`:

 - Let `slot` be `this.[[availableAfterSubmit]].findIndex((e) => e <= this.[[device]].queue.[[completedSubmitIndex]])`. TODO: [#5466](https://github.com/gpuweb/gpuweb/issues/5466) returning the minimum requires O(log N) operation, returning the freed slots in the order they are freed can be O(1), decide which one to do.
 - If `slot` is `undefined`, throw an `OperationError`.
 - Call `this.update(slot, resource)`.
 - Return `slot`.

Steps for `GPUResourceTable.removeBinding(slot)`:

 - If any of the following is not satisfied, throw an `OperationError`:

    - `this.destroy()` has never been called. (Note: this is a content timeline check, but `[[destroyed]]` is a device-timeline boolean)
    - `slot` must be `< this.size`

 - Set `this.[[availableAfterSubmit]][slot]` to `this.[[device]].queue.[[lastSubmitIndex]]`.

 - On the device timeline:

   - If `this` isn't valid, generate a validation error and return.
   - Remove the entry at `slot`.

### WGSL
To provide access to the data in the `GPUResourceTable` the concept of a resource table is added to
WGSL. The resource table is an implicit concept, there is no type, address space or name for the
table, it's implicitly available if a `GPUResourceTable` has been bound.

In order to access the resource table two new methods are added, `getResource` and `hasResource`.

#### New enable extension
The bindless feature will not be available on all devices so must be guarded by an `enable` when
used in WGSL.

The enable name is `resource_table`.

#### New methods
In order to access the resource table two new methods, `getResource` and `hasResource` are defined.

##### `hasResource`
Used to determine if a given `index` in the resource table contains the given `T` type of texture.

```
@must_use fn hasResource<T>(index: I) -> bool
```

* `I` is an `i32` or `u32`
* `T` is a format-less storage texture (e.g. `texture_storage_2d<f32>`), sampled texture, multisampled
  texture, depth texture, or sampler.

NOTE: Eventually the `T` will also contain storage `buffer view` objects and texel buffers.

`hasResource` returns true if the item at `index` of the resource table is of type `T`.

##### `getResource`
Retrieves a texture of type `T` from the `index` in the resource table. If the texture is out of
bounds, or the binding is not a type `T` a default texture of type `T` is returned. (i.e. this
method will  _always_ return a texture of the correct type, it just may not be the one at the given
`index`).

```
@must_use fn getResource<T>(index: I) -> T
```

* `I` is an `i32` or `u32`
* `T` is a format-less storage texture (e.g. `texture_storage_2d<f32>`), sampled texture, multisampled
  texture, depth texture, or sampler.

NOTE: Eventually the `T` will also contain storage `buffer view` objects and texel buffers.

`getResource` returns the value in the resource table at `index` of type `T`.

If `index` is outside the bounds of the resource table then a default value of type `T` will be
returned. If the item at `index` is not of type `T` then a default value of type `T` is returned.
Essentially, a value is always returned, it may be a synthesized default value.

###### Default Resources
When a given index is either out of bounds, or the requested `T` type does not match what is bound
a default resource is returned. These resources are defined as:

TODO: [#5471](https://github.com/gpuweb/gpuweb/issues/5471) Define the default resources
<table>
<tr><th>Type<th>Defaults
<tr>
    <td>format-less storage texture
    <td>
<tr>
    <td>sampled texture
    <td>
<tr>
    <td>multisampled texture
    <td>
<tr>
    <td>depth texture
    <td>
<tr>
    <td>sampler
    <td>
</table>

#### Type Compatibility Rules
The `T` types used in the `getResource` and `hasResource` methods allow some flexibility in their
types based on the filtering settings.

TODO: [#5470](https://github.com/gpuweb/gpuweb/issues/5470) define the compatibility rules when they are known.


#### Example usage

```
enable resource_table;

const kCatTexture = 0u;
const kHouseTexture = 1u;

@fragment fn fs() {
    let cat = textureLoad(getResource<texture_2d<f32>>(kCatTexture));

    if (hasResource<texture_2d<f32>>(kHouseTexture)) {
        let house = textureLoad(getResource<texture_2d<f32>>(kHouseTexture));
    }
}
```

### Alternatives considered

#### Bindless GPUBindGroups

A previous version of the proposal added a "dynamic binding array" concept to `GPUBindGroup`, declared in the `GPUBindGroupLayoutDescriptor` with a starting binding and resource kind.
The `GPUBindGroupDescriptor` had a creation argument that would decide of the size of the binding array and `GPUBindGroup` gained all the `destroy/update/insertBinding/removeBinding` methods that are on `GPUResourceTable`.
In the shader the binding array could be accessed with `@group(N) @binding(M) var resources : resource_binding`.

Discussion in [#5372](https://github.com/gpuweb/gpuweb/issues/5372) and offline determined that the `GPUResourceTable` approach was preferable because:

 - It removes the confusing indices between the "slots" that are used in the shader and the "binding" numbers at the API level, which are offset by `GPUBindGroupDescriptor.dynamicArray.start`.
 - It avoids putting two complex but orthogonal aspects of WebGPU in the same object (`GPUBindGroup`).
 - Developers really like the `GPUResourceTable` equivalent in HLSL SM 6.6 ["Dynamic Resources"](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_6_DynamicResources.html).
 - It is much more efficiently implementable on the Vulkan descriptor heap extension (that's the better way that heterogeneous is exposed in Vulkan).
 - It more clearly guides developers towards having only one bindless thing in shaders, supporting multiple per shader would involve implementation acrobatics.
