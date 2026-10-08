# WGSL Bindless Filterability Validation

* Status: [Draft](README.md#status-draft)
* Created: 2026-03-25
* Issue: [#5353](https://github.com/gpuweb/gpuweb/issues/5353)
* Authors: @kainino0x, @jrprice, @dneto0, @dj2

With the current WebGPU API, the shader compiler reports back to the API the
combinations of texture/sampler pairs which are used in the shader. The API then
either creates an `auto` bindgroup layout matching those constraints or
validates the given constraints.

From a shader perspective, the major constraint we need to validate is that an
`unfilterable` texture is not used with a `filtering` sampler. This is
considered Undefined Behaviour by may backends and must be guarded against.

> [!NOTE]
> This proposal does not address using filterability information for enhanced
> auto layout groups. A future proposal to add that may be coming, but we
> believe it can be layered on top of this proposal to just provide more context
> used in this analysis.

Motivating Issues:
1. Validation is required for bindless, [#380](https://github.com/gpuweb/gpuweb/issues/380).

# Proposal
This proposal does not add any new type information in WGSL, from a shader
perspective it does not have any visible effect. What it does is augment how
`getResource` works in order to delay the decision on which texture or sampler
to use until the actual usage combination.

At the point where a texture/sampler is combined, with one of the items coming
from a `getResource` call we inject extra logic to validate that the values exist
in the binding table and can be combined together.

In the case where the incorrect types are provided (or a filtering/filterability)
mismatch we have a `dynamic error` which means we can return what we want. In general
this is either by using a default texture/sampler, or in some cases Tint just returns a
`vec4f(0)` as the result.

This injects a check at each pair usage (any non-paired texture usage can just
use the value and doesn't need to check). These checks may be combined in the
future if we want to make the compiler smarter. When either the texture or
sampler is from the resource table we will need to check for all types as the
integer textures can not be combined with a filtering sampler.

## Data from API

### Runtime information
The API needs to provide information on the ResourceTable entries. There are two pieces of necessary
information:

* Array length of the ResourceTable
* For each element in the ResourceTable the "type" of the underlying resource.

Tint stores this in struct which is accessed through a `tint_resource_table_metadata` global. The
struct is defined as:

```wgsl
struct tint_resource_table_metadata_struct {
    array_length: u32,
    bindings: array<u32>,
}
```

The `bindings` are numbers we use to match-up the types.

For reference when looking at the example output below, in Tint the correspondence is:

```wgsl
    kTexture1d_f32_filterable = 1,
    kTexture1d_f32_unfilterable = 2,
    kTexture1d_f32_unknown_filterable = 3,
    kTexture1d_i32 = 4,
    kTexture1d_u32 = 5,
    kTexture2d_f32_filterable = 6,
    kTexture2d_f32_unfilterable = 7,
    kTexture2d_f32_unknown_filterable = 8,
    kTexture2d_i32 = 9,
    kTexture2d_u32 = 10,
    kTexture2dArray_f32_filterable = 11,
    kTexture2dArray_f32_unfilterable = 12,
    kTexture2dArray_f32_unknown_filterable = 13,
    kTexture2dArray_i32 = 14,
    kTexture2dArray_u32 = 15,
    kTexture3d_f32_filterable = 16,
    kTexture3d_f32_unfilterable = 17,
    kTexture3d_f32_unknown_filterable = 18,
    kTexture3d_i32 = 19,
    kTexture3d_u32 = 20,
    kTextureCube_f32_filterable = 21,
    kTextureCube_f32_unfilterable = 22,
    kTextureCube_f32_unknown_filterable = 23,
    kTextureCube_i32 = 24,
    kTextureCube_u32 = 25,
    kTextureCubeArray_f32_filterable = 26,
    kTextureCubeArray_f32_unfilterable = 27,
    kTextureCubeArray_f32_unknown_filterable = 28,
    kTextureCubeArray_i32 = 29,
    kTextureCubeArray_u32 = 30,

    kTextureMultisampled2d_f32 = 31,
    kTextureMultisampled2d_i32 = 32,
    kTextureMultisampled2d_u32 = 33,

    kTextureDepth2d = 34,
    kTextureDepth2dArray = 35,
    kTextureDepthCube = 36,
    kTextureDepthCubeArray = 37,
    kTextureDepthMultisampled2d = 38,

    kSampler = 39,
    kSampler_filtering = 40,
    kSampler_non_filtering = 41,
    kSampler_comparison = 42,
```

Note, for the HLSL examples below, Tint uses a `ByteAddressBuffer` for the metadata which means we
decompose everything into byte accesses. The access to get the array length will `Load(0u)`. Access
to get binding information will access at `4 + (index * 4)`, with the first `4` being the byte size
of the array length `u32` and then skip over to our index in the binding array at 4 bytes per `u32`.

### Compile time information

For any _Bound_ resource the API needs to provide the shader compiler with the specific attributes
for the bound item. If it's a texture, is it `filterable` or `unfilterable`, if it's a sampler, is
it `filtering` or `non-filtering`.

For each _ResourceTable_ type, the API needs to provide information on where the default item of
that type exists in the metadata table. (In the Dawn case, we provide an offset from the end of the
bound values, so we access at length + offset).


## HasResource

The `HasResource` call turns into a check that the requested index is within range of the binding
array and that the value stored in the binding array matches the type we're storing into.

```wgsl
const kHouseTexture = 4u;

@fragment fn fs() {
    let t = hasResource<texture_2d<i32>>(kHouseTexture);
}
```

```hlsl
Texture2D<int4> tint_resource_table_array[] : register(t28, space4);
ByteAddressBuffer tint_resource_table_metadata : register(t29, space5);

void fs() {
  bool v = false;
  // Validate the metadata table holds at least 4 items
  if ((4u < tint_resource_table_metadata.Load(0u))) {
    // Check that the metadata binding information for the 4th slot is a texture2d_<i32>
    v = (tint_resource_table_metadata.Load(20u) == 9u);
  } else {
    // Binding array is too small, so we do not have this binding at this slot
    v = false;
  }

  // Store the result back into the `t` variable
  bool t = v;
}

```

## GetResource

There are five fundamental cases that need to be handled when using `getResource`. Those cases
revolve around a resource being either _Bound_ (i.e. uses a `var` with a `group,binding`)  or the
resource comes from the ResourceTable.


### Case 1: Bound Texture, Bound Sampler
This is what we have now, nothing changes in this case, we access the texture and sampler directly.


### Case 2: Bound texture, ResourceTable Sampler
In this case the texture is bound to a `var` so we cannot do any substitution on the texture, the
sampler is retrieved from the resource table, so we can swap the sampler for a default if needed.


```wgsl
@group(0) @binding(0) var t : texture_2d<f32>;

@fragment
fn fs() -> @location(0) vec4f {
  let s = getResource<sampler>(0);
  return textureSample(t, s, vec2f(0));
}
```

#### Texture is set `filterable` by the API

```hlsl
struct fs_outputs {
  float4 tint_symbol : SV_Target0;
};


// The bound texture
Texture2D<float4> t : register(t0);

// ResourceTable arrays
Texture2D<float4> tint_resource_table_array[] : register(t28, space4);
Texture2D tint_resource_table_array_1[] : register(t28, space6);
SamplerState tint_resource_table_array_2[] : register(s28, space7);

// ResourceTable Metatdata
ByteAddressBuffer tint_resource_table_metadata : register(t29, space5);

float4 fs_inner() {
  bool has_resource = false;
  if ((0u < tint_resource_table_metadata.Load(0u))) {
    has_resource = any((uint2((tint_resource_table_metadata.Load(4u)).xx) == uint2(40u, 41u)));
  } else {
    has_resource = false;
  }

  uint item_idx = 0u;
  if (has_resource) {
    // Resource exists so the table index is the provided index of `0`
    item_idx = 0u;
  } else {
    // Resource doesn't exist, so we need to get the default resource, `4` is the provided offset
    // into the defaults table, and the metadata provides the table length.
    item_idx = (4u + tint_resource_table_metadata.Load(0u));
  }

  // No check necessary as a `filterable` texutre can be used with both
  // `filtering` and `non-filtering` samplers.

  // Index into the resource table for samplers at the selected index and return the result.
  return t.Sample(tint_resource_table_array_2[item_idx], (0.0f).xx);
}

fs_outputs fs() {
  fs_outputs v_3 = {fs_inner()};
  return v_3;
}

```

#### Texture is set `unfilterable` by the API
```hlsl
struct fs_outputs {
  float4 tint_symbol : SV_Target0;
};

// The bound texture
Texture2D<float4> t : register(t0);

// The resource table arrays
Texture2D<float4> tint_resource_table_array[] : register(t28, space4);
Texture2D tint_resource_table_array_1[] : register(t28, space6);
SamplerState tint_resource_table_array_2[] : register(s28, space7);

// ResourceTable metadata
ByteAddressBuffer tint_resource_table_metadata : register(t29, space5);
float4 fs_inner() {
  bool has_resource = false;
  if ((2u < tint_resource_table_metadata.Load(0u))) {
    has_resource = any((uint2((tint_resource_table_metadata.Load(12u)).xx) == uint2(40u, 41u)));
  } else {
    has_resource = false;
  }

  // Retrieve the kind of the sampler from the metadata
  uint sampler_kind = 0u;
  if (has_resource) {
    sampler_kind = tint_resource_table_metadata.Load(12u);
  } else {
    // Default to `non-filtering` sampler so it works with any texture
    sampler_kind = 41u;
  }

  // Get resource table index for the sampler
  uint item_idx = 0u;
  if (has_resource) {
    item_idx = 2u;
  } else {
    item_idx = (4u + tint_resource_table_metadata.Load(0u));
  }

  // Check that the sampler is usable with a `unfilterable` texturetype
  bool texture_sampler_match = false;
  // `40u` is Filtering Sampler
  if ((sampler_kind == 40u)) {
    texture_sampler_match = false;
  } else {
    texture_sampler_match = true;
  }

  float4 v_4 = (0.0f).xxxx;
  if (texture_sampler_match) {
    // Texture and sampler can be used together, retrieve the sampler and do the sample call
    v_4 = t.Sample(tint_resource_table_array_2[item_idx], (0.0f).xx);
  } else {
    // Just return a texture value of vec4(0) on mis-match
    v_4 = (0.0f).xxxx;
  }
  return v_4;
}

fs_outputs fs() {
  fs_outputs v_5 = {fs_inner()};
  return v_5;
}
```



### Case 3: ResourceTable Texture, No Sampler

```wgsl
const kHouseTexture = 2u;

@fragment fn fs() {
    let texture_load = textureLoad(getResource<texture_1d<f32>>(kHouseTexture), 0, 0);
}
```

```hlsl
// Reesource array
Texture1D<float4> tint_resource_table_array[] : register(t28, space4);

// Resource Table metadata
ByteAddressBuffer tint_resource_table_metadata : register(t29, space5);
void fs() {
  bool has_resource = false;
  if ((2u < tint_resource_table_metadata.Load(0u))) {
    has_resource = any((uint2((tint_resource_table_metadata.Load(12u)).xx) == uint2(1u, 2u)));
  } else {
    has_resource = false;
  }

  uint item_idx = 0u;
  if (has_resource) {
    // Use the requested resource index
    item_idx = 2u;
  } else {
    // Get the default texture
    item_idx = (0u + tint_resource_table_metadata.Load(0u));
  }

  float4 texture_load = tint_resource_table_array[item_idx].Load((int(0)).xx);
}

```


### Case 4: ResourceTable Texture, Bound Sampler

```wgsl
@group(0) @binding(0) var s : sampler;

@fragment
fn fs() -> @location(0) vec4f {
  let t = getResource<texture_2d<f32>>(0);
  return textureSample(t, s, vec2f(0));
}
```

#### Sampler bound as `filtering`
```hlsl
struct fs_outputs {
  float4 tint_symbol : SV_Target0;
};


// Bound sampler
SamplerState s : register(s0);

// Resource arrays
Texture2D<float4> tint_resource_table_array[] : register(t28, space4);
Texture2D tint_resource_table_array_1[] : register(t28, space6);
SamplerState tint_resource_table_array_2[] : register(s28, space7);

// ResourceTable Metadata
ByteAddressBuffer tint_resource_table_metadata : register(t29, space5);

float4 fs_inner() {
  bool has_resource = false;
  if ((0u < tint_resource_table_metadata.Load(0u))) {
    has_resource = any((uint3((tint_resource_table_metadata.Load(4u)).xxx) == uint3(6u, 7u, 34u)));
  } else {
    has_resource = false;
  }

  uint texture_kind = 0u;
  if (has_resource) {
    texture_kind = tint_resource_table_metadata.Load(4u);
  } else {
    // Default to a filterable texture2d_f32
    texture_kind = 6u;
  }

  uint item_idx = 0u;
  if (has_resource) {
    item_idx = 0u;
  } else {
    item_idx = (0u + tint_resource_table_metadata.Load(0u));
  }

  float4 v_3 = (0.0f).xxxx;
  // Verify we have a `filterable` texture2d_f32 texture to use with the `filtering` sampler
  if ((texture_kind == 6u)) {
    v_3 = tint_resource_table_array[item_idx].Sample(s, (0.0f).xx);
  } else {
    v_3 = (0.0f).xxxx;
  }
  return v_3;
}

fs_outputs fs() {
  fs_outputs v_4 = {fs_inner()};
  return v_4;
}
```

#### Sampler bound as `non-filtering`
```hlsl
struct fs_outputs {
  float4 tint_symbol : SV_Target0;
};

// Bound sampler
SamplerState s : register(s0);

// Resource arrays
Texture2D<float4> tint_resource_table_array[] : register(t28, space4);
Texture2D tint_resource_table_array_1[] : register(t28, space6);
SamplerState tint_resource_table_array_2[] : register(s28, space7);

// ResourceTable Metadata
ByteAddressBuffer tint_resource_table_metadata : register(t29, space5);

float4 fs_inner() {
  bool has_resource = false;
  if ((0u < tint_resource_table_metadata.Load(0u))) {
    has_resource = any((uint3((tint_resource_table_metadata.Load(4u)).xxx) == uint3(6u, 7u, 34u)));
  } else {
    has_resource = false;
  }

  uint item_idx = 0u;
  if (has_resource) {
    item_idx = 0u;
  } else {
    item_idx = (0u + tint_resource_table_metadata.Load(0u));
  }

  // No check necessary as a `non-filtering` sampler can be used with both
  // `filterable` and `unfilterable` textures.

  return tint_resource_table_array[item_idx].Sample(s, (0.0f).xx);
}

fs_outputs fs() {
  fs_outputs v_3 = {fs_inner()};
  return v_3;
}
```


### Case 5: ResourceTable Texture, ResourceTable Sampler

```wgsl
@fragment fn fs() -> @location(0) vec4f {
    let t = getResource<texture_2d<f32>>(0);
    let s = getResource<sampler>(1);
    return textureSample(t, s, vec2f(0));
}
```

```hlsl
struct fs_outputs {
  float4 tint_symbol : SV_Target0;
};

// Resource arrays
Texture2D<float4> tint_resource_table_array[] : register(t28, space4);
Texture2D tint_resource_table_array_1[] : register(t28, space6);
SamplerState tint_resource_table_array_2[] : register(s28, space7);

// ResourceTable metadata
ByteAddressBuffer tint_resource_table_metadata : register(t29, space5);

float4 fs_inner() {
  bool has_texture_resource = false;
  if ((0u < tint_resource_table_metadata.Load(0u))) {
    has_texture_resource = any((uint3((tint_resource_table_metadata.Load(4u)).xxx) == uint3(6u, 7u, 34u)));
  } else {
    has_texture_resource = false;
  }

  uint texture_kind = 0u;
  if (has_texture_resource) {
    texture_kind = tint_resource_table_metadata.Load(4u);
  } else {
    texture_kind = 6u;
  }

  uint texture_idx = 0u;
  if (has_texture_resource) {
    texture_idx = 0u;
  } else {
    texture_idx = (0u + tint_resource_table_metadata.Load(0u));
  }

  bool has_sampler_resource = false;
  if ((1u < tint_resource_table_metadata.Load(0u))) {
    has_sampler_resource = any((uint2((tint_resource_table_metadata.Load(8u)).xx) == uint2(40u, 41u)));
  } else {
    has_sampler_resource = false;
  }

  uint sampler_kind = 0u;
  if (has_sampler_resource) {
    sampler_kind = tint_resource_table_metadata.Load(8u);
  } else {
    sampler_kind = 41u;
  }

  uint sampler_idx = 0u;
  if (has_sampler_resource) {
    sampler_idx = 1u;
  } else {
    sampler_idx = (4u + tint_resource_table_metadata.Load(0u));
  }

  bool compatible = false;
  if ((sampler_kind == 40u)) {
    // A `filtering` sampler requires a `filterable` texture
    compatible = (texture_kind == 6u);
  } else {
    // A `non-filtering` sampler works with any texture
    compatible = true;
  }

  float4 v_7 = (0.0f).xxxx;
  if (compatible) {
    v_7 = tint_resource_table_array[texture_idxm_idx].Sample(tint_resource_table_array_2[sampler_idx], (0.0f).xx);
  } else {
    // Non-compatible just return the `vec4f(0)`
    v_7 = (0.0f).xxxx;
  }
  return v_7;
}

fs_outputs fs() {
  fs_outputs v_8 = {fs_inner()};
  return v_8;
}
```

## Language Extension

No new language extension is added. This proposal is an augment to how the
bindless `getResource` call works.


# Alternate Considerations

## **Do nothing**
The combination of a `unfilterable` texture with a `filtering` sampler is
undefined behaviour on my backend platforms. In order to satisfy the security
constraints of the web, we cannot allow that combination to be used. So, we
_must_ validate the call sites.

## **The filtering information provided explicitly**
A lot of consideration was put into the idea of placing the filterability
information into the texture/sampler type information (see [Explicit Bindgroup
Layout Parameters](explicit_bindgroup_layout_parameters.md). There were a few
key downsides with this approach:
 1. Requires extra author information which no other API requires. This makes
    the feature unique to WGSL and, thus, harder to use.
 2. Trying to synthesize this information when converting from SPIR-V, while
    able to catch may cases, can not catch all cases so leaving some shaders
    untranslatable to WGSL.
 3. Discussing this internally, the conversions and interactions with the API
    side cause a lot of confusion. There is a very real concern that trying to
    explain how the filterability attached to a type works when converting
    through the `auto` state, and how these relate to the API side concepts
    would be very difficult.

