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
from a `getResource` call we'd inject something similar to:

```wgsl
let tex = getResource<texture_2d<f32>>(0);
let samp = getResource<sampler>(1);


var n = samp.value;
if (samp.is_filtering && tex.is_unfilterable_float) {
  if (tex.default_value) {
    m = tex.default_value;
  } else {
    n = samp.default_value;
  }
} else {
  m = tex.value;
}

let c = textureSample(m, n, vec2(0));

```

So, we check for the bad case of filtering sampler and unfilterable texture and
trigger a "dynamic error" in WGSL and swap in the filterable texture default
(or the sampler if needed).

This injects a check at each pair usage (any non-paired texture usage can just
use the value and doesn't need to check). These checks may be combined in the
future if we want to make the compiler smarter. When either the texture or
sampler is from the resource table we will need to check for all types as the
integer textures can not be combined with a filtering sampler.

## `getResource`

We need to add some smarts into `getResource` to set up the passed around data
correctly.

Assume that the API has setup the metadata:
 1. tex_2d_f32_filterable
 2. sampler_filtering
 3. tex_2d_f32_unfilterable

It would then provide default values appended to the end:

 1. tex_2d_f32  (this is setup as filterable)
 2. sampler     (this is setup as non_filtering)

### sampler

```wgsl
let s = getResource<sampler>(1)
```
In this case, the resource at `1` does not match sampler type so we'd track
`{kNonFiltering, defaults[2], defaults[2]}` the non_filtering default sampler.


```wgsl
let s = getResource<sampler>(2)
```
In this case, the resource at `2` matches sampler type so we'd track
`{kFiltering, resource[2], defaults[2]}`.

### texture
```wgsl
let t = getResource<texture_2d<f32>>(2)
```

In this case, the resource at `2` does not match texture type so we'd track
`{kFilterable, defaults[1], defaults[1]}` the filterable default texture.


```wgsl
let t = getResource<texture_2d<f32>(3)
```
In this case the resource at `3` matches the texture type so we'd track
`{kUnfilterable, resource[3], default[1]}`. We'd have both the table value and
the filterable default value. This will let us swap them at the call sites if
we need to pair with a filtering sampler.


```wgsl
let t = getResource<texture_2d<f32>(1)
```
In this case the resource at `1` matches the texture so we'd return
`{kFilterable, resource[1], resource[1]}` the value itself is already filterable,
so can be used in all combinations, so we can just set the same value into both
fields.


## Combining bind-less and bind-ful
It is possible to pass bind-ful information and combine it with resources
obtained from the bind-less resource table. This will require extra information
provided from the API side at pipeline-creation time in order to add the needed
validation.

(Any bind-ful combined with bind-ful will have been validated by the API side
independently so we don't need to do any checks).

```wgsl
@group(0) @binding(0) var s: sampler;

fn main() {
  let t = getResource<texture_2d<f32>>(0);
}
```
In this case, the API would pass in data saying the binding at `[0, 0]` is
sampler_filterable (or whatever the bind group is set-up to be).

If the texture `t` is unfilterable then we'd swap in the filterable default
texture instead at the combining call.


```wgsl
@group(0) @binding(1) var t: texture_2d<f32>;

fn main() {
  let s = getResource<sampler>(0);
}
```
Similar to above, the API would pass in `[0, 1]` is texture_unfilterable (or the
appropriate value from the bind group).

If the sampler `s` is filtering then we'd swap in the non_filtering default
sampler instead at the combining call. In this case the texture information would
be a marker value in the default case so we know to swap the samplers.


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

