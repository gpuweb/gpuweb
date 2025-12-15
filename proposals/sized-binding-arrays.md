# Sized Binding Arrays

* Status: [Draft](README.md#status-draft)
* Issue: [#822](https://github.com/gpuweb/gpuweb/issues/822)

## Motivation

A common developer request is to add dynamic indexing of bindings to WGSL.
This is a functionality present in WebGL that WebGPU doesn't expose and makes it harder to port some applications from WebGL to WebGPU.
The addition of arrays of bindings would let shaders perform more dynamic use of resources for additional flexibility.
Note that this is *not* the addition of "bindless" which would allow dynamically indexing an unbounded amount of resources.
Bindless requires hardware support that's missing in many devices that WebGPU supports.
Fixed-sized binding arrays are more limited, but enjoy ubiquitous hardware support.
However this proposal is a stepping stone towards bindless as the `bindingArraySize`, `binding_array` and other concept can be extended for bindless in the future.

Hardware may have constraints around what kind of indexing is allowed in binding arrays: const-expression, uniform, or non-uniform indexing.
The choice done for indexing uniformity influences what level of emulation will need to happen in implementations.

Likewise some APIs (Vulkan in particular) have independent features for uniform (and non-uniform) indexing for each type of binding.
WebGPU needs to choose what resources can be dynamically indexed, and what level of emulation they will do in implementations on devices that don't support all the kinds of dynamic indexing.

## API changes

On the API side, `GPUBindGroupLayoutEntry` gains a new `bindingArraySize` property that gives the number of elements of the array for this entry.
The elements for the entry are the ones with binding number between (inclusively) `entry.binding` and `entry.binding + entry.bindingArraySize - 1`.
Arrays of size 1 and single bindings are equivalent between shader and bind group layout matching, such that all current WebGPU code is as if it had the `bindingArraySize` value of 1.
For that reason, `bindingArraySize` is defaulted to 1.

```webidl
partial dictionary GPUBindGroupLayoutEntry {
    GPUSize32 bindingArraySize = 1;
};
```

Changes to validation are done:

 - An `bindingArraySize` value of 0 is invalid and produces an error `GPUBindGroupLayout`.
 - When counting limits, the counts towards limits are multiplied by the `bindingArraySize`.
 - Checks that bindings numbers in a `GPUBindGroupLayout` don't conflict is updated to take into account the ranges for the `bindingArraySize`.
 - Checks that `GPUBindGroup` creation specifies all require bindings is updated to take into account the ranges for the `bindingArraySize`.
 - (Optionally) Checks that bindings with `bindingArraySize > 1` are in the allow-list of bindings for fixed-size arrays.

Pipeline layout defaulting is also updated to reflect and set an `bindingArraySize` in the `GPUBindGroupLayouts` it creates.

## WGSL

A new `sized-binding-arrays` language feature is added.
It can be used for feature detection of both the API-side support and the WGSL-side support.

A new `binding_array<T, N>` type is added that can only be used as a binding and not created directly in shaders.

 - `N` is the size of the array and must be a compile-time constant value or (optionally) an override constant.
   It is validated to less than or equal to the `bindingArraySize` of the respective `GPUBindGroupLayoutEntry`.
 - `T` is the type of the binding this array is used for, which is validated against the rest of the contents of the `GPUBindGroupLayoutEntry`.

(TODO for WGSL, can `binding_array` be passed around in function parameters?)

New array access expressions are added for `binding_array`:

 - `e: binding_array<T, N> and i: i32 or u32` -> `e[i]: T`. The result is the value of the `i`th element of the array value `e`.
    If `i` is outside of the range `[0, N-1]`:

    - It is a shader-creation error if `i` is a const-expression.
    - It is a pipeline-creation error if `i` is an override-expression.
    - Otherwise, any element in the array may be returned.

 - Similar rules for getting a reference to an array element from a memory view to a binding array.

Optionally validation rules for the uniformity, or const-expression-ness of indices into the access expressions are added.

## Extra considerations

WebGPU has composite binding objects with `GPUExternalTexture` that takes multiple slots for limits, and may be represented by multiple bindings in implementations.
The proposal is to allow `binding_array` for `GPUExternalTexture` as well since it can be translated into per-binding types arrays in shaders.

Texel buffers are a potential future addition to WebGPU and should be considered when deciding which binding types can be arrayed.

## Choices for options outlined above.

To be confirmed:

 - Metal and D3D12 allow non-uniform indexing of bindings.
 - OpenGL ES allows non-uniform indexing of at least textures.
 - Vulkan has feature for each individual binding type to allow uniform and non-uniform indexing.
 - Vulkan uniform indexing of everything but texel buffers is ubiquitous (loses only some LLVMPipe reports in the vulkan gpuinfo query)
 - Vulkan uniform indexing of texel buffers is added in Vulkan 1.2, but very prevalent there (apart from some Intel devices?)
 - Vulkan non-uniform indexing of all kinds of bindings is very prevalent but not ubiquitous.

Note that both HLSL and SPIR-V require annotations for non-uniform accesses (or non-uniform are UB).
WGSL compilers could use the uniformity analysis to deduce when annotations need to be added or can be removed.

Given that a reasonable workaround exists to support uniform and non-uniform indexing on devices that don't support it, and that the workaround has been used with great success in WebGL, the proposal is to allow non-uniform indexing of all kinds of bindings.
The workaround looks like the following:

```wgsl
// Replaces
var e = myBindingArray[i];

// With
var e = indexMyBindingArray(i);

fn indexMyBindingArray(i) -> T {
  switch (i) {
    case 0 { return myBindingArray[0]; }
    case 1 { return myBindingArray[1]; }
    // ...
    case N-1 { return myBindingArray[N-1]; }
  }
  return myBindingArray[0];
}
```

This also lets us support all kinds of bindings in fixed-size arrays.

On D3D12 for buffers (and GL?) it may require inlining a switch with the memory access hoisted into it (ugly but workable).

To be confirmed: do all the members of `GPUBindGroupLayoutEntry` need to match for the same array?
It seems that mostly yes except maybe `hasDynamicOffset` and `sampleType`.
TBD
