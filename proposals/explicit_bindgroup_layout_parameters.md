
# WGSL Explicit Bindgroup Layout Parameters

* Authors: @kainino0x, @kangz, @dneto0, @dj2
* Updated: Oct 8, 2025
* Issue: [#5353](https://github.com/gpuweb/gpuweb/issues/5353)
* Status: **Proposal**

In order to be able to create more pipelines with the `auto` layout in WebGPU, and to provide the
needed information to implement bindless, we propose to add binding layout information for textures
and samplers into WGSL.

The requirements of bindless add extra constraints on how the extra information is provided because
for bindless we need the information in the generic parameter for `getBinding` and `hasBinding`.
(See [Bindless Investigation](https://hackmd.io/@cwfitzgerald/wgpu-bindless#Shader-API-round-2) for
description of get/has binding.)

Motivating Issues:
1. [#4956](https://github.com/gpuweb/gpuweb/issues/4956)
2. [#4957](https://github.com/gpuweb/gpuweb/issues/4957)
3. The type changes are also required for bindless, [#380](https://github.com/gpuweb/gpuweb/issues/380).


# Proposal

Add an optional template parameter to the types of samplers and sampled-textures to specify the
needed layout information.

* Sampler would be extended to permit a `filtering`, `non_filtering,`or `unknown` template parameter
* [Sampled texture types](https://gpuweb.github.io/gpuweb/wgsl/#sampled-texture-type) where the
  [sampled type](https://gpuweb.github.io/gpuweb/wgsl/#sampled-type) is a floating point type would
  be extended to take a `filterable`/`unfilterable`/`unknown` template parameter.

In both cases, if the parameter is not specified, it would be `unknown`, in which case the `"auto"`
layout algorithm will pick a value, as it does today.

The parameters do not apply to non-float sampled texture binding types with integer and depth
types: `texture_*<i32>`, `texture_*<u32>`, and `texture_depth_*`.

## Example

```wgsl
@group(0) @binding(0) var sampler1: sampler<filtering>;
@group(0) @binding(1) var sampler2: sampler<non_filtering>;

@group(0) @binding(2) var tex1: texture_2d<f32, filterable>;
@group(0) @binding(3) var tex2: texture_2d<f32, unfilterable>;

var res = hasBinding<texture_1d<i32, unfilterable>>(arg_0, 1u);
let b = getBinding<sampler<non_filtering>>(bindings, 2)
```

There are several uses of the extra annotation.

1. Information for the WebGPU API on how to configure the pipelines associated with this shader when
   doing an `auto` layout.
2. Validation of the texture/sampler pairs used in texture calls to make sure unfilterable textures
   are not sampled with filtering.
   * Note that `"auto"` layout chooses based on the existing constraints, so it can't
     create conflicts.
3. Runtime checks in the `getBinding`/`hasBinding` calls in bindless, to make sure the API provided
   texture/sampler matches the filtering requirements of the retrieved value. (`unknown` types are
   not allowed here — see below.)

## Validation

Validation of the texture/sampler pairs used in texture calls to make sure unfilterable textures are
not sampled with filtering.  These cases generate shader-creation errors.  The compatibility
matrix is:

|                              | Sampler `filtering` | Sampler `non_filtering` | Sampler `unknown` |
| :--------------------------- | :-----------------: | :---------------------: | :---------------: |
| Texture `float`              | Y                   | Y                       | Y                 |
| Texture `unfilterable_float` | N                   | Y                       | *YA*              |
| Texture `unknown`            | *YA*                | Y                       | Y                 |

Note: YA means “yes because of the auto algorithm”: the automatic defaulting algorithm will ensure
compatibility with actual uses in the shader.

Only one parameter can be provided to a texture/sampler. Providing it twice (e.g.
`sampler<filtering, filtering>` is a `createShaderModule` error). The filtering parameters for
textures must only be used with a floating-point sampled type.

For `getBinding`/`hasBinding`, the extra layout parameter is required. (Relaxing this restriction
would require inferring the parameter; see "Automatic layouts for bindless" below.)

The extra filtering parameter provided in the shader will trigger errors on the API side if they
don't match up with the bind group information. At pipeline creation with an *explicit* layout,
validation includes:

* A `sampler<non_filtering>` with a `type: "filtering"` sampler bind group entry is an error.
  A `texture_*<unfilterable>` with a `sampleType: "float"` texture bind group entry is an error.
* A `sampler<filtering>` with a `type: "non-filtering"` bind group entry is an error.
  A `texture_*<filterable>` with a `sampleType: "unfilterable-float"` texture bind group entry is
  an error. (These aren't strictly necessary, but it seems like it would be a mistake vs being
  intentional. If we make it an error to start, we can loosen if we find folks encountering the
  issue more than expected.)

It's allowed to create an auto-layout pipeline where some bindings have filtering parameters and
others do not. (The validation rules above prevent pre-existing conflicts.) The
[auto-layout algorithm](https://gpuweb.github.io/gpuweb/#default-pipeline-layout) would change to
first obey the filtering parameter, then apply defaults from there.

* For example, currently auto-layout always chooses `"filtering"` for samplers. If there is a
  texture call that combines a `texture_*<unfilterable>` texture with a sampler with no filtering
  parameter, the sampler will be `"non_filtering"`. (`non_filtering` samplers are valid to use with
  any texture, so this default doesn't cascade into additional constraints on other textures.)

## Function Parameters

The new filtering parameters will affect function parameters. The extra filtering information can be
provided when writing a function signature.

```wgsl
fn a(b: sampler<filtering>, c: texture_2d<f32, unfilterable>)
```

This will then require any `sampler`/`texture` passed into this function to match the needed filter
parameters. (Although, see "Conversions between types with different filterability/filteringness"
below).

If no filterable parameters are provided, then they must be traceable back to static (non-bindless)
bindings, and, as today, the `"auto"` layout algorithm or bind group layout validation will take
care of them. That is, the transitive closure of call sites of this function must eventually reach
only non-bindless bindings for those parameters.  (See issue below)

## *Binding depth textures to non-depth bind points*

Later, in order to support [#4957](https://github.com/gpuweb/gpuweb/issues/4957), the texture type
parameter can additionally be `depth`. Validation-wise, this is exactly the same as `unfilterable`,
but in `"auto"` layouts it will produce `sampleType: "depth"` instead of
`sampleType: "unfilterable-float"`.

## Conversions between types with different filterability/filteringness

Developers will want to be able to write code libraries that can act on any kind of
`texture_2d<f32>`, whatever its filterability is (for example if all they do is a `textureLoad`), or
taking any kind of sampler and using it on a filterable f32 texture. To support this (without static
polymorphism), conversions between texture and sampler types are possible, that always go in the
direction of the more constraining type:

* `texture_*d<f32, filterable/unknown>` \-\> `texture_*d<f32, unfilterable>`
* `sampler<non_filtering/unknown>` \-\> `sampler<filtering>`

## Language Extension

A new **language extension** is added, `filtering_parameters`, to signal that this extension
is required.


# Alternate Considerations

* **The filtering information provided as an attribute**
  * This works for the non-bindless use-case but becomes difficult for bindless. We need to be able
    attach the annotation to `getBinding` and `hasBinding` function calls and doing so becomes hard
    to read: `getBinding<@layout_type(filtering) sampler>(bindings, 2)`
  * Also since bindless makes bindings dynamic, the information needs to exist in the texture/sampler
    type itself to be able to do validation, unless we statically trace all texture/sampler usages
    back to their `getBinding` call — see "Automatic layouts for bindless".
* **Determine the annotation automatically from the shader.**
  * Produces spooky-action as changing how the texture/sampler are used would then change what the
    annotations are and hence how the pipelines are created on the API side.
* **A specific type per filtering parameter**
  * A `filterable_sampler` or `texture_filtering_1d<f32>` could be created but will potentially
    create a huge number of new types.
* **Don't make the auto-layout algorithm more complicated — don't solve constraints from thetexture-sampling calls.**
  * If we did this, then using a `texture_*<unfilterable>` with a `sampler` without a layout type
    would be invalid, because samplers always default to `"filtering"`. The user would need to add
    `layout_type(non_filtering)` to the sampler (which, as above, shouldn't have cascading effects).
* **Automatic layouts for bindless**
  * `unknown`-type samplers and textures types are not allowed in `getBinding`/`hasBinding` because
    we would have to infer them at shader-creation time by backsolving from where they're used in
    texture-sampling calls. That may be possible, but it probably isn't a good idea (it's like the
    `"auto"` layout algorithm, but more complicated, and importantly would result in runtime
    failures instead of validation failures when the auto layout turned out not to be what you wanted).
