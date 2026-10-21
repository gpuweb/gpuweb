# Acceleration Structure

* Status: [Draft](README.md#status-draft)
* Created: 2026-10-13
* Issue: [#11053](https://github.com/gpuweb/gpuweb/issues/11053)

# Description

In order to support either the `rayQuery` operations or future ray tracing shaders, there is a need
to create `AccelerationStructure` objects for use by the subsequent shaders.

This proposal provides the basis for creating, updating and providing acceleration structure objects
to fragment and compute shaders.

There are two types of acceleration structures, *top-level acceleration structures* (TLAS) and
*bottom-level acceleration structures* (BLAS). The top-level acceleration structure is constructed
out of instances of the bottom-level acceleration structures. The bottom-level acceleration structure
is created out of triangles or axis-aligned bounding boxes. (In the case of Metal it can also be
created with curves, but that is not supported on either Vulkan or DX12, so will not be considered
in this proposal).

Each entry in the top-level acceleration structure has an associated transformation matrix, so a
single bottom-level acceleration element can be instanced multiple times into the top-level
structure and placed with different scaling, rotation and translation based on the transform matrix.

The amount of memory required by the GPU to create an acceleration structure may not be exactly known
at creation time, requiring the user to over-allocate the storage necessary for the structure, as
such, a created acceleration structure may not be stored in the optimal amount of memory. In order to
fix this issue, as long as the structure was created with the ability, an acceleration structure can
be **compacted** into another acceleration structure providing tighter bounds on the amount of
memory required.

The building of an acceleration structure is expensive. In order to allow the acceleration structure
to be updated a **refit** operation is provided. This refit cannot add new geometry but it can alter
the existing geometry in the acceleration structure.

# Platform Support

## Vulkan

* Requires:
  * [`VK_KHR_acceleration_structure`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_acceleration_structure.html)
  * [`VK_KHR_deferred_host_operations`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_deferred_host_operations.html)
  * [`SPV_KHR_ray_query`](https://github.khronos.org/SPIRV-Registry/extensions/KHR/SPV_KHR_ray_query.html)  `(to provide OpTypeAccelerationStructureKHR)`
  * Vulkan 1.2 or
  * Vulkan Version 1.1 with VK\_EXT\_descriptor\_indexing and VK\_KHR\_buffer\_device\_address

### Object

The created object is a
[`VkAccelerationStructureKHR`](https://docs.vulkan.org/refpages/latest/refpages/source/VkAccelerationStructureKHR.html).

### Creation/Destruction

[`vkCreateAccelerationStructureKHR`](https://docs.vulkan.org/refpages/latest/refpages/source/vkCreateAccelerationStructureKHR.html) and
[`vkDestroyAccelerationStructureKHR`](https://docs.vulkan.org/refpages/latest/refpages/source/vkDestroyAccelerationStructureKHR.html)
to create and destroy. There is also a
[`vkCreateAccelerationStructure2KHR`](https://docs.vulkan.org/refpages/latest/refpages/source/vkCreateAccelerationStructure2KHR.html)
which is provided by the [`VK_KHR_device_address_commands`](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_device_address_commands.html) extension.

### Building

Acceleration structure is created with
[vkCmdBuildAccelerationStructuresKHR](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdBuildAccelerationStructuresKHR.html)

* set mode to `VK_BUILD_ACCELERATION_STRUCTURE_MODE_BUILD_KHR`
* `srcAccelerationStructure` is `VK_NULL_HANDLE`
* `dstAccelerationStructure` is the structure to build
* `flag` set to match the usage flags provided
  * `VK_BUILD_ACCELERATION_STRUCTURE_ALLOW_COMPACTION_BIT_KHR`
  * `VK_BUILD_ACCELERATION_STRUCTURE_ALLOW_UPDATE_BIT_KHR`

### Compaction

Acceleration structures are compacted with
[`vkCmdCopyAccelerationStructureKHR`](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdCopyAccelerationStructureKHR.html)

* set mode to `VK_COPY_ACCELERATION_STRUCTURE_MODE_COMPACT_KHR`
* `src` is the uncompacted structure
* `dst` is the new structure to write into

The
[`vkCmdWriteAccelerationStructuresPropertiesKHR`](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdWriteAccelerationStructuresPropertiesKHR.html)
is used to get the needed size to create the `dst` structure. This is done using a query pool which
needs to be submitted and then the value retrieved from the pool results.

### Refit

A refit is done with
[vkCmdBuildAccelerationStructuresKHR](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdBuildAccelerationStructuresKHR.html).

* set mode to `VK_BUILD_ACCELERATION_STRUCTURE_MODE_UPDATE_KHR`
* `srcAccelerationStructure` and `dstAccelerationStructure` should point to the same
  acceleration structure

## DX12

* Requires:
  * DXR Tier 1.1 / SM 6.5
  * Check `D3D12_RAYTRACING_TIER_1_1` on device interface

### Object

Pointer to a `ID3D12Resource` with `D3D12_RESOURCE_STATE_RAYTRACING_ACCELERATION_STRUCTURE`

### Creation/Destruction

I *think* this is just a GPUBuffer that is created/destroyed of the correct sizes.

### Building

Acceleration structure is built with [BuildRaytracingAccelerationStructure](https://github.com/microsoft/DirectX-Specs/blob/master/d3d/Raytracing.md#buildraytracingaccelerationstructure)

* `SourceAccelerationStructureData` set to `0`

### Compaction

Compaction with [`CopyRaytracingAccelerationStructure`](https://github.com/microsoft/DirectX-Specs/blob/master/d3d/Raytracing.md#copyraytracingaccelerationstructure)

* Uses `D3D12_RAYTRACING_ACCELERATION_STRUCTURE_COPY_MODE_COMPACT`

### Refit

Use
[BuildRaytracingAccelerationStructure](https://github.com/microsoft/DirectX-Specs/blob/master/d3d/Raytracing.md#buildraytracingaccelerationstructure)
with an `|`'d in flag of `D3D12_RAYTRACING_ACCELERATION_STRUCTURE_BUILD_FLAG_PERFORM_UPDATE`

## Metal

* Requires:
  * Metal 2.3
  * `MTLDevice.supportsRaytracing`

### Object

The acceleration structure is a
[`MTLAccelerationStructure`](https://developer.apple.com/documentation/metal/mtlaccelerationstructure?language=objc).

### Creation/Destruction

[`newAccelerationStructureWithDescriptor:`](https://developer.apple.com/documentation/metal/mtldevice/makeaccelerationstructure\(descriptor:\)?language=objc) or
[newAccelerationStructureWithSize:](https://developer.apple.com/documentation/metal/mtldevice/makeaccelerationstructure\(size:\)?language=objc)

### Building

[`buildAccelerationStructure:descriptor:scratchBuffer:scratchBufferOffset:`](https://developer.apple.com/documentation/metal/mtlaccelerationstructurecommandencoder/build\(accelerationstructure:descriptor:scratchbuffer:scratchbufferoffset:\)?language=objc)

### Compaction

[`copyAndCompactAccelerationStructure:toAccelerationStructure:`](https://developer.apple.com/documentation/metal/mtlaccelerationstructurecommandencoder/copyandcompact\(sourceaccelerationstructure:destinationaccelerationstructure:\)?language=objc)
the size of the compacted buffer is retrieved with [writeCompactedAccelerationStructureSize:toBuffer:offset:sizeDataType:](https://developer.apple.com/documentation/metal/mtlaccelerationstructurecommandencoder/writecompactedsize\(accelerationstructure:buffer:offset:sizedatatype:\)?language=objc)

### Refit

[`refitAccelerationStructure:descriptor:destination:scratchBuffer:scratchBufferOffset:`](https://developer.apple.com/documentation/metal/mtlaccelerationstructurecommandencoder/refit\(sourceaccelerationstructure:descriptor:destinationaccelerationstructure:scratchbuffer:scratchbufferoffset:\)?language=objc)

## OpenGL

The acceleration structures are not supported in OpenGL. This feature would not be available
in compat mode.

# WebGPU Implementation

## Feature Name

The feature is gated behind the `acceleration-structure` name. This will allow it to be used by both
ray query and full ray tracing.

## Object

The acceleration structure is held in an opaque `GPUAccelerationStructure` object.

## Creation/Destruction

```proto
[Exposed=(Window, Worker), SecureContext]
partial interface GPUDevice {
  GPUAccelerationStructure createAccelerationStructure(
      GPUAccelerationStructureDescriptor descriptor);

  GPUAccelerationStructure createAndBuildAccelerationStructure(
      GPUAccelerationStructureDescriptor descriptor,
      GPUAccelerationStructureBuildDescriptor descriptor);
};
```

There is a `createAccelerationStructure` method exposed on the `GPUDevice` to create both the
top and bottom level acceleration structures. The create method takes a
`GPUAccelerationStructureDescriptor` to describe what is being created.

A convenience `createAndBuildAccelerationStructure` method is provided to do both the creation
and building in a single call.

```proto
enum GPUAccelerationStructureType {
  "bottom-level",
  "top-level"
};

dictionary GPUAccelerationStructureDescriptor : GPUObjectDescriptorBase {
  required GPUAccelerationStructureType type;
  GPUAccelerationStructureUsageFlags usage;

  sequence<GPUAccelerationStructureGeometrySizingDescriptor> geometries;
  unsigned long maxInstanceCount = 0;
};
```

The `type` is one of:

* "bottom-level" – create a bottom level acceleration structure
* "top-level" – create a top level acceleration structure

The `usage` flags available are:

* ALLOW\_REFIT – setup the acceleration structure to allow updates
  * There is a cost to using this option, on D3D: `This option may result in increased memory
    consumption, build times, and lower raytracing performance.`
  * RADV uses a more compressed BVH without this option:
    [https\://gitlab.freedesktop.org/mesa/mesa/-/blob/main/src/amd/vulkan/radv\_acceleration\_structure.c\#L306](https://gitlab.freedesktop.org/mesa/mesa/-/blob/main/src/amd/vulkan/radv_acceleration_structure.c#L306)
  * Intel ANV writes side data to allow making the update
    [https\://gitlab.freedesktop.org/mesa/mesa/-/blob/main/src/intel/vulkan/genX\_acceleration\_structure.c\#L347](https://gitlab.freedesktop.org/mesa/mesa/-/blob/main/src/intel/vulkan/genX_acceleration_structure.c#L347)
* ALLOW\_COMPACTION – setup the acceleration structure to allow compaction
  * There is a cost to using this option, on D3D: This option may result in increased memory
    consumption and build times.

Q: Should we include the `ALLOW_REFIT` and `ALLOW_COMPACTION` flags or should we just always enable
them for WebGPU? Would the cost for enabling refit be too high if it potentially lowers performance?

The `BOTTOM_LEVEL` and `TOP_LEVEL` flags are mutually exclusive, if one is applied the other
**must not** be applied.

If the usage includes `BOTTOM_LEVEL` then the `geometries` list **must** contain at least one
`GPUAccelerationStructureGeometrySizingDescriptor`. The `maxInstanceCount` value **must** be `0`.
The sizing descriptors must be greater than or equal to the number of vertices/indices which will be
inserted during the build operation.

```proto
dictionary GPUAccelerationStructureTriangleSizingDescriptor {
  required unsigned long maxVertexCount;
  required GPUVertexFormat vertexFormat;

  unsigned long maxIndexCount = 0;
  GPUIndexFormat indexFormat = undefined;
};

dictionary GPUAccelerationStructureAABBSizingDescriptor {
  required unsigned long maxAABBCount;
};

dictionary GPUAccelerationStructureGeometrySizingDescriptor {
  required GPUAccelerationStructureGeometryType type;

  GPUAccelerationStructureTriangleSizingDescriptor triangles;
  GPUAccelerationStructureAABBSizingDescriptor aabbs;
};
```

**Q:** What validation is needed for the contents of the vertex/index buffer. If the index buffer
references outside the vertex buffer, is that handled in hardware, or do we need to validate all of
the index buffer entries beforehand?

- Do we need to copy the index buffer and zero out any vertex buffer reference which is out of range?

**Q:** Should this be a single structure like the following with the restriction that exactly one of `maxVertexCount` and `maxAABBCount` can be set?

```proto
dictionary GPUAccelerationStructureTriangleSizingDescriptor {
};

dictionary GPUAccelerationStructureAABBSizingDescriptor {
};

dictionary GPUAccelerationStructureGeometrySizingDescriptor {
  unsigned long maxVertexCount = 0;
  GPUVertexFormat vertexFormat = undefined;

  unsigned long maxIndexCount = 0;
  GPUIndexFormat indexFormat = undefined;

  unsigned long maxAABBCount = 0;
};
```

The sizing descriptor will be used to calculate the maximum needed buffer size to hold the
acceleration structure. This will usually be larger than is strictly necessary and then a compaction
operation will be performed to set the acceleration structure to the optimal size. The sizing is
calculated by the underlying platform.

* Vulkan – [vkGetAccelerationStructureBuildSizesKHR](https://docs.vulkan.org/refpages/latest/refpages/source/vkGetAccelerationStructureBuildSizesKHR.html)
  This will require creating a `VkAccelerationStructureGeometryKHR` structure, which requires the vertex and index formats.
* DX12 – [`GetRaytracingAccelerationStructurePrebuildInfo`](https://github.com/microsoft/DirectX-Specs/blob/master/d3d/Raytracing.md#getraytracingaccelerationstructureprebuildinfo)
* Metal – [`accelerationStructureSizesWithDescriptor:`](https://developer.apple.com/documentation/metal/mtldevice/accelerationstructuresizes\(descriptor:\)?language=objc)

If the usage includes `TOP_LEVEL` then the `maxInstanceCount` list **must** be greater than `0`. The
`geometries` list **must** be empty. The `maxInstanceCount` **must** be greater than, or equal to the
number of instances which will be inserted during the build operation.

There are two types of `GPUAccelerationStructureGeometryDescriptor`. All of the descriptors in the
`geometries` list **must** have the same `GPUAccelerationStructureGeometryType`. There are two types
of geometries which can be created: `triangles` and `aabbs`.

## Building

```proto
[Exposed=(Window,Worker), SecureContext]
partial interface GPUCommandEncoder {
  undefined buildAccelerationStructure(
      GPUAccelerationStructure destination,
      GPUAccelerationStructureBuildDescriptor descriptor);
};

```

In order to populate the acceleration structure a *build* operation must be performed. This will
build the underlying bottom or top level acceleration structure.

```proto
dictionary GPUAccelerationStructureBuildDescriptor : GPUObjectDescriptorBase {
  sequence<GPUAccelerationStructureGeometryDescriptor> geometries;
  sequence<GPUAccelerationStructureInstanceDescriptor> instances;
};
```

If this is a bottom-level acceleration structure then the `geometries` list must contain at least one
descriptor and the `instances` list must be empty.

If this is a top-level acceleration structure then the `instances` list must contain at least one
descriptor and the `geometries` list must be empty.

```proto
dictionary GPUAccelerationStructureTriangleGeometryDescriptor {
  required GPUBuffer vertexBuffer;
  required GPUVertexFormat vertexFormat;
  required GPUSize64 vertexStride;

  GPUBuffer indexBuffer;
  GPUIndexFormat indexFormat;

  GPUSize64 vertexOffset = 0;
  GPUSize64 indexOffset = 0;

  unsigned long vertexCount;
  unsigned long indexCount;
};

dictionary GPUAccelerationStructureAABBGeometryDescriptor {
  required GPUBuffer buffer;

  GPUSize64 offset = 0;
  GPUSize64 stride = 24;

  unsigned long count;
};

dictionary GPUAccelerationStructureGeometryDescriptor {
  required GPUAccelerationStructureGeometryType type;

  boolean isOpaque = true;

  GPUAccelerationStructureTriangleGeometryDescriptor triangles;
  GPUAccelerationStructureAABBGeometryDescriptor aabbs;
};
```

The geometries consist of triangles or axis-aligned bounding boxes. For a bottom-level acceleration
structure **all** of the descriptors must be the same type, either all `triangles` or all `aabbs`.

```proto
dictionary GPUAccelerationStructureInstanceDescriptor {
  required GPUAccelerationStructure source;

  required sequence<sequence<float>> transform;
  unsigned long mask = 0xff;
  unsigned long id = 0;
  boolean forceOpaque = false;
  boolean forceNonOpaque = false;
};

```

The `source` of an instance descriptor is the bottom-level acceleration structure this instance
refers to. It **must** be a bottom-level acceleration structure.

The `transform` is a 3x4 row-major transformation matrix to apply to the instance.

The `mask` is a user controlled mask. It will be used to compare against a mask set in the shader
call to allow turning off geometry programmatically. The two masks are combined with a bitwise `and`
operation. If the result is non-zero then the intersection proceeds, otherwise the object is culled.

The `id` is a user-set ID which will be provided in the ray query results.

The forceOpaque and forceNonOpaque are flags to force the geometry to be opaque or non-opaque. Note,
these aren't used directly in this proposal but tie into the `rayQuery` proposal where they can be
set here but overridden in `rayQuery` if desired.

## Compaction

```proto
[Exposed=(Window, Worker), SecureContext]
interface GPUAccelerationStructure {
  Promise<GPUAccelerationStructure> compactAccelerationStructure(
    GPUAccelerationStructure source);
};

```

The sizes used in the initial creation and building of the acceleration structure may have been
larger than the size actually required by the structure. The sizes can be consolidated into a more
compact structure which uses less memory if the original acceleration structure was created with the
`ALLOW_COMPACTION` flag.

The `source` acceleration structure must have been fully created before it can be compacted, so a
barrier is necessary.

## Refit

```proto
[Exposed=(Window,Worker), SecureContext]
partial interface GPUCommandEncoder {
  undefined refitAccelerationStructure(
    GPUAccelerationStructure destination,
    GPUAccelerationStructureRefitDescriptor descriptor);
};
```

The creation of a full acceleration structure is expensive. In the case where some geometry has moved
around, or vertices have changed, but the number of vertices and instances remains the same, then a
`refit` operation can be performed.  In order to refit, the `destination` must have been created with
the `ALLOW_REFIT` flag.

```proto
dictionary GPUAccelerationStructureRefitDescriptor {
  sequence<GPUBuffer> vertexBuffers;
  sequence<GPUBuffer> instanceBuffers;
};
```

All of the vertex information from the original `build` command is re-used during the refit, this
does mean they need to be stored and revalidated. (They could be added here, if it's preferable, but
they **must** match the original operation so they'd be needed for validation regardless.)

The `vertexBuffers` and `instanceBuffers` must be the same number as was originally provided in the
build call. The new vertex and instance transform data will be updated into the acceleration structure.

The `vertexBuffer` holds the updated vertex information used in a bottom-level acceleration structure
and the list must contain at least one buffer. The `instanceBuffers` **must** be empty.

The `instanceBuffers` hold the updated 3x4 row-major transformation matrices for the instances in
the top-level acceleration structure. There must be at least one of them when refitting a top-level
acceleration structure. The `vertexBuffers` **must** be empty.

A refit of a top-level acceleration structure does **not** alter the tree geometry, it just updates
the transformation matrices. This means that as the structure is refitted then bounding boxes can
stretch and overlap. After a number of refits the whole structure should be rebuilt to maintain
efficiency.

# Bindings

A top-level acceleration structure can be placed in a bind group. A bottom-level acceleration
structure **may not** be placed in a bind group.

# WGSL

The acceleration structure will be exposed to WGSL as a new *handle* type. The new handle is guarded
by an enable of `acceleration_structures`.

```wgsl
enable acceleration_structures;

@group(0) @binding(0) var accel : acceleration_structure;
```

The `acceleration_structure` is an opaque object and acts similar to a `texture` handle.

It can be passed to functions.

It can be placed in a `let` if the `texture_and_sampler_let` feature is enabled.

This proposal does not define any functions which can use the structure, they will come in
other WGSL proposals.

# WebIDL

```proto
enum GPUFeatureName {
  "acceleration-structure"
};

enum GPUAccelerationStructureGeometryType {
  "triangles",
  "aabbs"
};

typedef [EnforceRange] unsigned long GPUAccelerationStructureUsageFlags;
[Exposed=(Window, Worker), SecureContext]
namespace GPUAccelerationStructureUsage {
  const GPUFlagsConstant BOTTOM_LEVEL     = 0x01;
  const GPUFlagsConstant TOP_LEVEL        = 0x02;

  const GPUFlagsConstant ALLOW_REFIT      = 0x04;
  const GPUFlagsConstant ALLOW_COMPACTION = 0x08;
};

dictionary GPUAccelerationStructureRefitDescriptor {
  sequence<GPUBuffer> vertexBuffers;
  sequence<GPUBuffer> instanceBuffers;
};

[Exposed=(Window, Worker), SecureContext]
interface GPUAccelerationStructure {
  readonly attribute GPUAccelerationStructureUsageFlags flags;
  readonly attribute unsigned long long sizeInBytes;

  undefined destroy();


  Promise<GPUAccelerationStructure> compactAccelerationStructure(
    GPUAccelerationStructure source);
};
GPUAccelerationStructure includes GPUObjectBase;

dictionary GPUAccelerationStructureTriangleGeometryDescriptor {
  required GPUBuffer vertexBuffer;
  required GPUVertexFormat vertexFormat;
  required GPUSize64 vertexStride;

  GPUBuffer indexBuffer;
  GPUIndexFormat indexFormat;

  GPUSize64 vertexOffset = 0;
  GPUSize64 indexOffset = 0;

  unsigned long vertexCount;
  unsigned long indexCount;
};

dictionary GPUAccelerationStructureAABBGeometryDescriptor {
  required GPUBuffer buffer;

  GPUSize64 offset = 0;
  GPUSize64 stride = 24;

  unsigned long count;
};

dictionary GPUAccelerationStructureGeometryDescriptor {
  required GPUAccelerationStructureGeometryType type;

  boolean isOpaque = true;

  GPUAccelerationStructureTriangleGeometryDescriptor triangles;
  GPUAccelerationStructureAABBGeometryDescriptor aabbs;
};

dictionary GPUAccelerationStructureInstanceDescriptor {
  required GPUAccelerationStructure source;

  required sequence<sequence<float>> transform;
  unsigned long mask = 0xff;
  unsigned long id = 0;
  boolean forceOpaque = false;
  boolean forceNonOpaque = false;
};

dictionary GPUAccelerationStructureBuildDescriptor : GPUObjectDescriptorBase {
  sequence<GPUAccelerationStructureGeometryDescriptor> geometries;
  sequence<GPUAccelerationStructureInstanceDescriptor> instances;
};

dictionary GPUAccelerationStructureTriangleSizingDescriptor {
  required unsigned long maxVertexCount;
  required GPUVertexFormat vertexFormat;

  unsigned long maxIndexCount = 0;
  GPUIndexFormat indexFormat;

  boolean hasIndexBuffer = false;
};

dictionary GPUAccelerationStructureAABBSizingDescriptor {
  required unsigned long maxAABBCount;
};

dictionary GPUAccelerationStructureGeometrySizingDescriptor {
  required GPUAccelerationStructureGeometryType type;

  GPUAccelerationStructureTriangleSizingDescriptor triangles;
  GPUAccelerationStructureAABBSizingDescriptor aabbs;
};

enum GPUAccelerationStructureType {
  "bottom-level",
  "top-level"
};

dictionary GPUAccelerationStructureDescriptor : GPUObjectDescriptorBase {
  required GPUAccelerationStructureType type;
  GPUAccelerationStructureUsageFlags usage;

  sequence<GPUAccelerationStructureGeometrySizingDescriptor> geometries;
  unsigned long maxInstanceCount = 0;

  GPUAccelerationStructure compactionSource;
};

[Exposed=(Window, Worker), SecureContext]
partial interface GPUDevice {
  GPUAccelerationStructure createAccelerationStructure(
      GPUAccelerationStructureDescriptor descriptor);

  GPUAccelerationStructure createAndBuildAccelerationStructure(
      GPUAccelerationStructureDescriptor descriptor,
      GPUAccelerationStructureBuildDescriptor buildDescriptor);
};

[Exposed=(Window,Worker), SecureContext]
partial interface GPUCommandEncoder {
  undefined buildAccelerationStructure(
      GPUAccelerationStructure destination,
      GPUAccelerationStructureBuildDescriptor descriptor);

  undefined refitAccelerationStructure(
    GPUAccelerationStructure destination,
    GPUAccelerationStructureRefitDescriptor descriptor);
};
```

# References

* [https\://docs.vulkan.org/refpages/latest/refpages/source/VK\_KHR\_acceleration\_structure.html](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_acceleration_structure.html)
* [https\://github.com/microsoft/DirectX-Specs/blob/master/d3d/Raytracing.md](https://github.com/microsoft/DirectX-Specs/blob/master/d3d/Raytracing.md)
* [https\://developer.apple.com/documentation/metal/ray-tracing-with-acceleration-structures?language=objc](https://developer.apple.com/documentation/metal/ray-tracing-with-acceleration-structures?language=objc)
* [https\://github.com/maierfelix/dawn-ray-tracing/blob/master/RT\_SPEC.md](https://github.com/maierfelix/dawn-ray-tracing/blob/master/RT_SPEC.md)
* [https\://github.com/gfx-rs/wgpu/blob/trunk/docs/api-specs/ray\_tracing.md](https://github.com/gfx-rs/wgpu/blob/trunk/docs/api-specs/ray_tracing.md)

