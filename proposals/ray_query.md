# Ray Query

* Status: [Draft](README.md#status-draft)
* Created: 2026-10-13
* Issue: [#11055](https://github.com/gpuweb/gpuweb/issues/11055)

## Description

The `ray_query` extension provides the ability to do intersection queries against an acceleration
structure inside a `fragment` or `compute` shader. This allows doing things like calculating shadows
for objects within the shader. It does not provide the full functionality of ray tracing shaders,
    but is a lighter companion feature.

```wgsl
@group(0) @binding(0) var accel : acceleration_structure;

@fragment
fn main() {
  let origin = vec3f(0, 0, 0);
  let direction = vec3f(1, 1, 1);
  let t_min = 0.0001;
  let t_max = 1000;
  let cull_mask = 0xff;
  let ray = RayDesc(origin, direction, t_min, t_max, mask);

  var rq = rayQueryInitialize(accel,
                              RayQueryFlags::force_opaque | RayQueryFlags::cull_front_face,
                              ray);
  while (rayQueryProceed(rq)) {
     if (rayQueryGetCandidateType(rq) == RayQueryIntersectionType::triangle) {
rayQueryCommitCandidate(rq);
    }
  }

  let ty = rayQueryGetCommittedType(rq);
  if (ty != RayQueryIntersectionType::none) {
    let id = rayQueryGetCommittedInstanceId(rq);
    ...
  }
}
```

# Platform Comparison

## SPIR-V

* Requires: [`SPV_KHR_ray_query`](https://github.khronos.org/SPIRV-Registry/extensions/KHR/SPV_KHR_ray_query.html)
* Ext Requires: SPIR-V 1.0
* [https\://vulkan.gpuinfo.org/displayextensiondetail.php?extension=VK\_KHR\_ray\_query](https://vulkan.gpuinfo.org/displayextensiondetail.php?extension=VK_KHR_ray_query)

### Enabling

```
OpCapability RayQueryKHR
OpCapability RayTraversalPrimitiveCullingKHR
```

### Ray Flags

| Purpose | Flag |
| ----- | ----- |
| No Modifications | NoneKHR |
| First Hit Optimization | TerminateOnFirstHitKHR |
| Skip Candidate Eval | OpaqueKHR |
| Force Candidate Eval | NoOpaqueKHR |
| Skip Pipeline Hits | SkipClosestHitShaderKHR |
| Skip Complex Geometry | SkipAABBsKHR  (Requires RayTraversalPrimitiveCullingKHR) |
| Skip Standard Triangles | SkipTrianglesKHR   (Requires RayTraversalPrimitiveCullingKHR) |
| Cull Front Faces | CullFrontFacingTrianglesKHR |
| Cull Back Faces | CullBackFacingTrianglesKHR |
| Cull Opaque Geometry | CullOpaqueKHR |
| Cull Non-Opaque Geometry | CullNoOpaqueKHR |

### Ray Iteration

| Name | Opcode |
| :---- | :---- |
| Initialize | `OpRayQueryInitializeKHR` query acceleration structure RayFlags  \-- 32-bit integer Cull Mask  \-- 32-bit integer Ray origin  \-- vec3f Ray TMin \-- f32 Ray Direction  \-- vec3f Ray TMax \-- f32 |
| Terminate | `OpRayQueryTerminateKHR` |
| Generate Intersection (for an AABB intersection) | `OpRayQueryGenerateIntersectionKHR` Hit T  \-- f32 |
| Confirm intersection (for a triangle intersection) | `OpRayQueryConfirmIntersectionKHR` |
| Proceed | `OpRayQueryProceedKHR` Returns bool (true if traversal is incomplete, false if complete) |

### Ray Info

| Name | Opcode |
| :---- | :---- |
| TMin | `OpRayQueryGetRayTMinKHR`  \-\> f32 |
| Ray Flags | `OpRayQueryGetRayFlagsKHR` \-\> 32-bit integer |
| Ray Direction | `OpRayQueryGetWorldRayDirectionKHR`  \-\> vec3f |
| Ray Origin | `OpRayQueryGetWorldRayOriginKHR`  \-\> vec3f |

### Intersection Info

The `IntersectionId` used in these queries is either `RayQueryCandidateIntersectionKHR` for the
current candidate intersection or `RayQueryCommittedIntersectionKHR` for the closest recorded hit so far.

| Name | Opcode |
| :---- | :---- |
| Type | `OpRayQueryGetIntersectionTypeKHR`  \-\> (Triangle or AABB) |
| T | `OpRayQueryGetIntersectionTKHR` \-\> f32 |
| Instance custom Index | `OpRayQueryGetIntersectionInstanceCustomIndexKHR`  \-\> 32-bit integer |
| Instance ID | `OpRayQueryGetIntersectionInstanceIdKHR`  \-\> 32-bit integer |
| Geometry Index | `OpRayQueryGetIntersectionGeometryIndexKHR`  \-\> 32-bit integer |
| Primitive Index | `OpRayQueryGetIntersectionPrimitiveIndexKHR`  \-\> 32-bit integer |
| Barycentrics | `OpRayQueryGetIntersectionBarycentricsKHR`  \-\> vec2f |
| Front Face | `OpRayQueryGetIntersectionFrontFaceKHR`  \-\> boolean |
| Object Ray Direction | `OpRayQueryGetIntersectionObjectRayDirectionKHR`  \-\> vec3f |
| Object Ray Origin | `OpRayQueryGetIntersectionObjectRayOriginKHR`  \-\> vec3f |
| Object to World matrix | `OpRayQueryGetIntersectionObjectToWorldKHR`  \-\> mat4x3 |
| World to Object matrix | `OpRayQueryGetIntersectionWorldToObjectKHR`  \-\> mat4x3 |

### Candidate Info

| Name | Opcode |
| :---- | :---- |
| AABB Opaque | `OpRayQueryGetIntersectionCandidateAABBOpaqueKHR`  \-\> boolean |

## Metal

* Requires:
  * 2.4 for intersection\_query

### Enable

```c
#include <metal_raytracing>
using namespace metal::raytracing
```

### Ray Flags

Assume an `intersection_params p` has been declared.

| Purpose | Name |
| ----- | ----- |
| No Modifications | Empty `intersection_params` |
| First Hit Optimization | `p.accept_any_intersection(true)` |
| Skip Candidate Eval | `p.force_opacity(forced_opacity::opaque)` |
| Force Candidate Eval | `p.force_opacity(forced_opacity::non_opaque)` |
| Skip Pipeline Hits | N/A |
| Skip Complex Geometry | `p.set_geometry_cull_mode(geometry_cull_mode::bounding_box)` |
| Skip Standard Triangles | Either leave `<triangle_data>` off the `intersection_query` declaration or `p.set_geometry_cull_mode(geometry_cull_mode::triangle)` |
| Cull Front Faces | `p.set_opaque_triangle_cull_mode(triangle_cull_mode::front)`  `p.set_non_opaque_triangle_cull_mode(triangle_cull_mode::front)` |
| Cull Back Faces | `p.set_opaque_triangle_cull_mode(triangle_cull_mode::back)` `p.set_non_opaque_triangle_cull_mode(triangle_cull_mode::back)` |
| Cull Opaque Geometry | N/A |
| Cull Non-Opaque Geometry | N/A |

The *Skip Complex Geometry* and *Skip Standard Triangles* are a bit more complicated in Metal then
Vulkan. In Vulkan it's just a bitmask, so you can apply both of them at the same time. To do the
equivalent in Metal it's tricker.

The `set_geometry_cull_mode` method takes a single `enum class` value, not a bitmask, so you can
set *either* `triangle` or `bounding_box`. The `<triangle_data>` trick needs to be handled at
*compile* time as it's a template argument to `intersection_query`.

So, if we know at compile time we can mix dropping `<triangle_data>` with a cull mode of
`bounding_box` but if we accept the ray flags through a storage buffer, or some other runtime value
then we can't do that. The only way to do it is manually. The downside is you don't gain the benefit
which is to skip the complex geometry intersection checks.

Manually we'd need to inject something like:

```c
intersection_query<instancing, triangle_data> q(ray, accel, params);

while (q.next()) {
    if (flags & RayFlagsSkipTrianglesKHR) {
        if (q.get_candidate_intersection_type() == intersection_type::triangle) {
            continue;
        }
    }
    if (flags & RayFlagsSkipAABBsKHR) {
        if (q.get_candidate_intersection_type() == intersection_type::bounding_box) {
            continue;
        }
    }

    // Process intersections...
}
```

### Ray Iteration

| Name |  |
| :---- | :---- |
| Initialize | `intersection_query<T>(ray, acceleration_structure, intersection_params)` `T` is a list of template params which can include: `instancing` (access instance\_id and user\_instance\_id) and it's an instance acceleration structure `triangle_data` (can read barycentrics, front\_face)  The `intersection_params` is configured with the calls in the Ray Flags section above. `ray(float3 origin, float3 direction, float min_dist, float_max_dist, uint mask, uint user_data)` The `mask` is the same as the `OpRayQueryInitializeKHR::cull_mask` The `intersection_query` can also be created without providing any params (using the default constructor) in which case it needs to be reset before being used: `q.reset(ray, acceleration_structure, intersection_params)` |
| Terminate | `q.abort()` |
| Generate Intersection | `q.commit_bounding_box_intersection(f32 distance)` |
| Confirm intersection | `q.commit_triangle_intersection()` |
| Proceed | `q.next()` True if a candidate was found |

The `interesection_query` has the restrictions:

* cannot be used as a member of a structure/union
* cannot be returned from a function
* cannot be assigned to

These restrictions prevent the `intersection query` object from being copied

### Ray Info

| Name |  |
| :---- | :---- |
| TMin | `q.get_ray_min_distance()` \-\> f32 |
| Ray Flags | `q.get_intersection_params()`  \-\> intersection\_params |
| Ray Direction | `q.get_world_space_ray_direction()` \-\> vec3f |
| Ray Origin | `q.get_world_space_ray_origin()` \-\> vec3f |

### Intersection Info

| Name |  |
| :---- | :---- |
| Type | `q.get_candidate_intersection_type()` `q.get_committed_intersection_type()` \-\> (none, triangle, bounding\_box, curve) |
| T | `q.get_candidate_triangle_distance()` \-\> f32 Only for triangle intersection `q.get_committed_distance()` \-\> f32 |
| Instance custom Index | `q.get_candidate_instance_id()` `q.get_committed_instance_id()` \-\> u32 |
| Instance ID | `q.get_candidate_user_instance_id()` `q.get_committed_user_instance_id()` \-\> u32 |
| Geometry Index | `q.get_candidate_geometry_id()` `q.get_committed_geometry_id()` \-\> u32 |
| Primitive Index | `q.get_candidate_primitive_id()` `q.get_committed_primitive_id()` \>- u32 |
| Barycentrics | `q.get_candidate_triangle_barycentric_coord()` `q.get_committed_triangle_barycentric_coord()` \-\> vec2f Must be a triangle intersection |
| Front Face | `q.is_candidate_triangle_front_facing()` `q.is_committed_triangle_front_facing()` \-\> bool Must be a triangle intersection |
| Object Ray Direction | `q.get_candidate_ray_direction()` `q.get_committed_ray_direction()` \-- vec3f |
| Object Ray Origin | `q.get_candidate_ray_origin()` `q.get_committed_ray_origin()` \-- vec3f |
| Object to World matrix | `q.get_candidate_object_to_world_transform()` `q.get_committed_object_to_world_transform()`  \-\> mat4x3 |
| World to Object matrix | `q.get_candidate_world_to_object_transform()` `q.get_committed_world_to_object_transform()` \-\> mat4x3 |

### Candidate Info

| Info |  |
| :---- | :---- |
| AABB Opaque | `q.is_candidate_non_opaque_bounding_box()` \-\> boolean Must be a bounding box intersection |

## HLSL

* Require: DXR Tier 1.1 / SM 6.5

### Ray Flags

| Purpose | Name |
| ----- | ----- |
| No Modifications | RAY\_FLAG\_NONE |
| First Hit Optimization | RAY\_FLAG\_ACCEPT\_FIRST\_HIT\_AND\_END\_SEARCH |
| Skip Candidate Eval | RAY\_FLAG\_FORCE\_OPAQUE |
| Force Candidate Eval | RAY\_FLAG\_FORCE\_NON\_OPAQUE |
| Skip Pipeline Hits | RAY\_FLAG\_SKIP\_CLOSEST\_HIT\_SHADER |
| Skip Complex Geometry | RAY\_FLAG\_SKIP\_PROCEDURAL\_PRIMITIVES |
| Skip Standard Triangles | RAY\_FLAG\_SKIP\_TRIANGLES |
| Cull Front Faces | RAY\_FLAG\_CULL\_FRONT\_FACING\_TRIANGLES |
| Cull Back Faces | RAY\_FLAG\_CULL\_BACK\_FACING\_TRIANGLES |
| Cull Opaque Geometry | RAY\_FLAG\_CULL\_OPAQUE |
| Cull Non-Opaque Geometry | RAY\_FLAG\_CULL\_NON\_OPAQUE |

### Ray Iteration

| Name |  |
| :---- | :---- |
| Initialize | `RayQuery<RayFlags>` With SM6.9+ another template param for `RayQuery_Flags` was added but they aren't relevant for this document `q.TraceRayInline(acceleration_structure, ray_flags, instance_inclusion_mask, RayDesc)`  `ray_flags` is `|`'d with the template `RayFlags` `instance_inclusion_mask` is the same as the `OpRayQueryInitializeKHR::cull_mask` `RayDesc` float3 origin float t\_min float3 direction float t\_max |
| Terminate | `q.Abort()` |
| Generate Intersection | `q.CommitProceduralPrimitiveHit(float t)` |
| Confirm intersection | `q.CommitNonOpaqueTriangleHit()` |
| Proceed | `q.Proceed()` |

### Ray Info

| Name |  |
| :---- | :---- |
| TMin | `q.RayTMin()` \-\> f32 |
| Ray Flags | `q.RayFlags()` \-\> u32 |
| Ray Direction | `q.WorldRayDirection()` \-\> vec3f |
| Ray Origin | `q.WorldRayOrigin()` \-\> vec3f |

### Intersection Info

| Name |  |
| :---- | :---- |
| Type | `q.CandidateType() q.CommittedStatus()` \-\> (triangle, primitive) |
| T | `q.CandidateTriangleRayT()` \-\> f32 For a triangle candidate only `q.CommittedRayT()` \-\> f32 |
| Instance custom Index | `q.CandidateInstanceIndex()` `q.CommittedInstanceIndex()` \-\> u32 |
| Instance ID | `q.CandidateInstanceID()` `q.CommittedInstanceID()` \-\> u32 |
| Geometry Index | `q.CandidateGeometryIndex()` `q.CommittedGeometryIndex()` \-\> u32 |
| Primitive Index | `q.CandidatePrimitiveIndex()` `q.CommittedPrimitiveIndex()` \-\> u32 |
| Barycentrics | `q.CandidateTriangleBarycentrics()` `q.CommittedTriangleBarycentrics()` \-\> vec2f Triangle candidate only |
| Front Face | `q.CandidateTriangleFrontFace()` `q.CommittedTriangleFrontFace()` \-\> bool Triangle candidate only |
| Object Ray Direction | `q.CandidateObjectRayDirection()` `q.CommittedObjectRayDirection()` \-\> vec3f |
| Object Ray Origin | `q.CandidateObjectRayOrigin()` `q.CommittedObjectRayOrigin()` \-\> vec3f |
| Object to World matrix | `q.CandidateWorldToObject3x4()` `q.CommittedWorldToObject3x4()` \-\> mat4x3 |
| World to Object matrix | `q.CandidateObjectToWorld3x4()` `q.CommittedObjectToWorld3x4()` \-\> mat4x3 |

### Candidate Info

| Info |  |
| :---- | :---- |
| AABB Opaque | `q.CandidateProceduralPrimitiveNonOpaque()` \-\> boolean Must be a primitive intersection |

# WGSL

New feature `ray_query`.

New handle type `ray_query`. May only be created in a `var` in `function` scope. Maybe passed as a
pointer to functions. It may *not* be returned from a function.

```wgsl
enum bitmask RayQueryFlags : u32 {
   none = 0x00u
   accept_first_hit = 0x01u,
   force_opaque = 0x02u,
   force_non_opaque = 0x04u,
   skip_triangles = 0x8u,
   skip_aabb = 0x10u,
   cull_front_face = 0x20u,
   cull_back_face = 0x40u,
}

enum RayQueryIntersectionType : u32 {
  none = 0u,
  triangle = 1u,
  aabb = 2u,
}
```

* **Q**: Do we allow `skip_triangles | skip_aabb` and if so, how do we handle Metal? Is the ray
flags a `const` or `override value`, or do we do runtime work? We'd always have to do the work for
dynamic flags.

```wgsl
struct RayDesc {
  origin: vec3f,
  direction: vec3f,
  t_min: f32,
  t_max: f32,
  mask: u32,
}
```

### Ray Iteration

```wgsl
fn rayQueryInitialize(tlas: acceleration_structure,
                      flags: RayQueryFlags,
                      ray: RayDesc) -> ray_query;
fn rayQueryProceed(q: ray_query) -> bool
fn rayQueryTerminate(q: ray_query)

fn rayQueryCommitCandidate(q: ray_query)  // For a triangle
fn rayQueryCommitCandidate(q: ray_query, T: f32)  // For an AABB
```

* **Q**: For validation other than `rayQueryInitialize`, the `rayQueryProceed` call *has* to be made
before every other function can be called. So, we need to validate that it's called (and probably in
control flow that is actually executed. Not sure how to phrase that

### Ray Info

This could be done with free functions, or a single call to return the `RayDesc` struct. (Using free
functions matches nicely to how textures are handled.)

&nbsp;

```wgsl
fn rayQueryRayTMin(q: ray_query) -> f32
fn rayQueryRayTMax(q: ray_query) -> f32
fn rayQueryRayOrigin(q: ray_query) -> vec3f
fn rayQueryRayDirection(q: ray_query) -> vec3f
```

**Or**

```wgsl
fn rayQueryRayInfo(q: ray_query) -> RayDesc  // Same data, but mask == 0
```

* **Q**: Is it worth it to have the `mask` in here? We could possibly figure it out by tracking
what ray was used to initialize the ray query and then just inject the value

### Intersection Info

These could be done as

1. free functions, duplicating for committed/candidate
2. free functions take a committed/candidate flag
3. combined struct return duplicating for committed/candidate
4. combined struct return taking a committed/candidate flag
5. templated on the data being requested

#### 1 Individual calls

```wgsl
fn rayQueryGetCandidateType(q: ray_query) -> RayQueryIntersectionType
fn rayQueryGetCommittedType(q: ray_query) -> RayQueryIntersectionType

fn rayQueryGetCandidateTriangleT(q: ray_query) -> f32
fn rayQueryGetCommittedT(q: ray_query) -> f32

fn rayQueryGetCandidateInstanceIndex(q: ray_query) -> u32
fn rayQueryGetCommittedInstanceIndex(q: ray_query) -> u32

fn rayQueryGetCandidateInstanceId(q: ray_query) -> u32
fn rayQueryGetCommittedInstanceId(q: ray_query) -> u32

fn rayQueryGetCandidateGeometryIndex(q: ray_query) -> u32
fn rayQueryGetCommittedGeometryIndex(q: ray_query) -> u32

fn rayQueryGetCandidatePrimitiveIndex(q: ray_query) -> u32
fn rayQueryGetCommittedPrimitiveIndex(q: ray_query) -> u32

fn rayQueryGetCandidateTriangleBarycentrics(q: ray_query) -> vec2f
fn rayQueryGetCommittedTriangleBarycentrics(q: ray_query) -> vec2f

fn rayQueryGetCandidateTriangleFrontFace(q: ray_query) -> bool
fn rayQueryGetCommittedTriangleFrontFace(q: ray_query) -> bool

fn rayQueryGetCandidateAABBNonOpaque(q: ray_query) -> bool

fn rayQueryGetCandidateObjectRayDirection(q: ray_query) -> vec3f
fn rayQueryGetCommittedObjectRayDirection(q: ray_query) -> vec3f

fn rayQueryGetCandidateObjectRayOrigin(q: ray_query) -> vec3f
fn rayQueryGetCommittedObjectRayOrigin(q: ray_query) -> vec3f

fn rayQueryGetCandidateWorldToObject(q: ray_query) -> mat4x3
fn rayQueryGetCommittedWorldToObject(q: ray_query) -> mat4x3

fn rayQueryGetCandidateObjectToWorld(q: ray_query) -> mat4x3
fn rayQueryGetCommittedObjectToWorld(q: ray_query) -> mat4x3
```

#### 2 Query type per call

```wgsl
enum RayQueryType: u32 {
  Candidate : 0,
  Committed : 1,
}

fn rayQueryGetType(q: ray_query, t: RayQueryType) -> RayQueryIntersectionType
fn rayQueryGetT(q: ray_query, t: RayQueryType) -> f32  // if candidate, ony triangle
fn rayQueryGetInstanceIndex(q: ray_query, t: RayQueryType) -> u32
fn rayQueryGetInstanceId(q: ray_query, t: RayQueryType) -> u32
fn rayQueryGetGeometryIndex(q: ray_query, t: RayQueryType) -> u32
fn rayQueryGetPrimitiveIndex(q: ray_query, t: RayQueryType) -> u32
fn rayQueryGetTriangleBarycentrics(q: ray_query, t: RayQueryType) -> vec2f
fn rayQueryGetTriangleFrontFace(q: ray_query, t: RayQueryType) -> bool
fn rayQueryGetAABBNonOpaque(q: ray_query, t: RayQueryType) -> bool
fn rayQueryGetObjectRayDirection(q: ray_query, t: RayQueryType) -> vec3f
fn rayQueryGetObjectRayOrigin(q: ray_query, t: RayQueryType) -> vec3f
fn rayQueryGetWorldToObject(q: ray_query, t: RayQueryType) -> mat4x3
fn rayQueryGetObjectToWorld(q: ray_query, t: RayQueryType) -> mat4x3
```

#### 3 Struct return

```wgsl
struct RayResult {
  type: RayQueryIntersectionType,
  t: f32,                        // if candidate query only set for triangle
  instance_index: u32,
  instance_id: u32,
  geometry_index: u32,
  primitive_index: u32,
  triangle_barycentrics: vec3f, // only set if type is triangle
  triangle_front_face: bool,    // only set if type is triangle
  aabb_non_opaque: bool,        // only set if type is aabb
  ray_origin: vec3f,
  ray_direction: vec3f,
  world_to_object: mat4x3,
  object_to_world: mat4x3,
}

fn rayQueryGetCandidateIntersectionInfo(q: ray_query) -> RayResult
fn rayQueryGetComittedIntersectionInfo(q: ray_query) -> RayResult
```

#### 4 Struct return with query type

```wgsl
fn rayQueryGetIntersectionInfo(q: ray_query, t: RayQueryType) -> RayResult
```

#### 5 Templated on data being requested

```wgsl
enum RayQueryType: u32 {
  Candidate : 0,
  Committed : 1,
}

enum RayQueryRequest : u32 {
  Type,
  T,
  InstanceIndex,
  InstanceId,
  GeometryIndex,
  PrimitiveIndex,
  TriangleBarycentrics,
  TriangleFrontFace,
  AABBNonOpaque
  ObjectRayDirection,
  ObjectRayOrigin,
  WorldToObject,
  ObjectToWorld
}

fn rayQuery<RayQueryRequest, RayQueryType>(q: ray_query) -> RayQueryIntersectionType

```

# Undefined Behaviour

There is a lot of UB which needs to be handled in the `rayQuery` implementation. From what I've
seen the following are all a factor (there maybe others)

* `proceed` must be called before either `committed` or `candidate` values can be retrieved
* `committed` must not be used while `proceeded` returns `true`
* `candidate` must not be used after `proceeded` returns `false`

There may also be some UB in what data can be queried in the `candidate` and `committed` requests.

## References

* [https\://microsoft.github.io/DirectX-Specs/d3d/Raytracing.html\#rayquery](https://microsoft.github.io/DirectX-Specs/d3d/Raytracing.html#rayquery)
* [https\://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf](https://developer.apple.com/metal/Metal-Shading-Language-Specification.pdf)
* [https\://github.khronos.org/SPIRV-Registry/extensions/KHR/SPV\_KHR\_ray\_query.html](https://github.khronos.org/SPIRV-Registry/extensions/KHR/SPV_KHR_ray_query.html)

