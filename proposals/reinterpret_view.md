# Reinterpret/View

* Status: [Draft](README.md#status-draft)
* Created: 2026-01-21
* Issue: [#5338](https://github.com/gpuweb/gpuweb/issues/5338)

# Overview

This proposal covers an alternative to
[bufferView](https://github.com/gpuweb/gpuweb/blob/main/proposals/buffer-view.md)
based on discussion in the [2026-01-13
meeting](https://docs.google.com/document/d/1lXoX9sYDTpjpFMC2ilxHHzYp7Bv1F05_i2_qIjihx_w/edit?usp=sharing).
The proposal covers two flavors: reinterpret and view.
Feel free to bikeshed about names.

Both flavors represent a departure from the bufferView proposal by allowing
pointer reinterpretation on more pointers and dropping the new type altogether.

# Reinterpret

```rust
@must_use fn reinterpret<T'>(p : ptr<AS, T, AM>) -> ptr<AS, T', AM>
@must_use fn reinterpret<AM'>(p : ptr<AS, T, AM>) -> ptr<AS, T, AM'>
@must_use fn reinterpret<T', AM'>(p : ptr<AS, T, AM>) -> ptr<AS, T', AM'>
```

`AS` is the address space and could be any address space (except handle).

TODO: Should `immediate` be allowed? It complicates the calculation of used slots.

TODO: Decide allowed address spaces.

`AM` is the access mode and must be valid for the address space.<br>
`AM'` must be read or write and can only be provided if `AM` is read_write.

Note: This would be the first use of write only access modes and the spec would need updating accordingly. This allows authors to more easily satisfy the [alias analysis](https://gpuweb.github.io/gpuweb/wgsl/#aliasing) rule that prevents a function from having multiple writable views to the same root variable.
* We would have to relax this rule from [6.3 Reference and Pointer Types](https://gpuweb.github.io/gpuweb/wgsl/#ref-ptr-types)
    * If a pointer type appears in the program source, it must also be valid to declare a variable, somewhere in the program, with the pointer type’s address space, store type, and access mode.

TODO: Decide if stricter access modes are desirable.

`T` and `T'`must be valid for `AS`. Additionally they cannot contain any atomic type.
`T'` is the reinterpreted type. Restrictions on `T'`:
* Align(T') <= Align(T)
* SizeOf(T') <= SizeOf(store type of RootIdentifier(p)) + AccumulatedOffset(p)
    * RootIdentifier is a function that returns the root identifier of p. Its value type is used in the size calculation.
    * AccumulatedOffset is a function that returns accumulated byte offset from the root identifier to the input pointer through various access expressions.
    * It would be a shader-creation error if the accumulated constant offset violated the above relation and a pipeline-creation error if the accumulated override offset violated it.
       * Note: this is intended to check mixed constant and non-constant offsets
Implementations would handle the robustness at runtime otherwise.

The function reinterprets the store type of p. Optional bonus feature: It also allows restricting the access mode.

Examples

```rust
struct S {
 a : vec4u,
 b : array<u32>,
}

@group(0) @binding(0) var<storage> v1 : array<u32, 128>;
@group(0) @binding(1) var<storage> v2 : S;

fn foo() {
  // Allowed. Root is v1 which is 128 elements (512 bytes)
  // output value type is 64 elements (256 bytes), offset is 64 elements (256 bytes)
  let p1 = reinterpret<array<u32, 64>>(&v1[64]);

  // Disallowed. Output value type is too large 256 elements (1024 bytes)
  // vs 128 elements (512 bytes)
  let p2 = reinterpret<array<u32, 256>(&v1);

  // Allowed. This might raise eyebrows, but align of S is 16.
  let p3 = reinterpret<array<vec4u>>(&v2);

  // Note that implementations need to be careful here.
  // If v2.b does not have a length divisible by 4 some easy translations
  // might produce incorrect results.
  let len = arrayLength(p3);

  // Diallowed due to alignment restrictions.
  let p4 = reinterpret<vec4u>(&v1[0]);
```

# View

Many restrictions are the same as `reinterpret`. The primary difference being the offset is explicit in the `view` call instead of being part of the pointer type itself.

```rust
@must_use fn view<T'>(p : ptr<AS, T, AM>, offset : I) -> ptr<AS, T', AM>
@must_use fn view<AM'>(p : ptr<AS, T, AM>, offset : I) -> ptr<AS, T, AM'>
@must_use fn view<T', AM'>(p : ptr<AS, T, AM>, offset : I) -> ptr<AS, T', AM'>
```

`AS` is the address space and could be any address space (except handle).

TODO: Should immediate be allowed? It complicates the calculation of used slots.

TODO: Decide allowed address spaces.

`AM` is the access mode and must be valid for the address space.<br>
`AM'` must be read or write and can only be provided if AM is read_write.

Note: This would be the first use of write only access modes and the spec would need updated accordingly

TODO: Decide if stricter access modes are desirable.

`T` and `T'` must be valid for `AS`. Additionally they cannot contain any atomic type.
T' is the view type. Restrictions on T':
* Align(T') <= Align(T)
* SizeOf(T') <= SizeOf(T)
* An invalid memory view is returned if SizeOf(T') + offset > SizeOf(T)
    * Standard early evaluation variants

`I` must be `i32` or `u32`.  Optional: Add overloads that drop `I`, defaulting to `0`.

The function reinterprets the store type of p as T'. The returned pointer is offset from p by offset bytes. Additionally, allows restricting the access mode.

Examples:

```rust
struct S {
 a : vec4u,
 b : array<u32>,
}

@group(0) @binding(0) var<storage> v1 : array<u32, 128>;
@group(0) @binding(1) var<storage> v2 : S;

fn foo() {
  // Allowed. Root is v1 which is 128 elements (512 bytes)
  // output value type is 64 elements (256 bytes), offset is 64 elements (256 bytes)
  let p1 = view<array<u32, 64>>(&v1, 64);

  // Disallowed. Data type of input is u32 and smaller than the return
  // data type.
  let p2 = view<array<u32, 64>(&v1[64], 0);

  // Allowed. This might raise eyebrows, but align of S is 16.
  let p3 = view<array<vec4u>>(&v2, 0);

  // Disallowed due to alignment restrictions.
  let p4 = view<array<vec4u>>(&v2.b, 0);

  // Diallowed due to alignment restrictions.
  let p4 = view<vec4u>(&v1[0], 0);
}

fn helper(ptr<storage,array<u32,64>> pv) -> u32 {
   return pv[0];
}
fn caller() {
   let u = helper(view<array<u32,64>>(v, 4 * 64)); // u = v[64]
}
```

# Padding

WGSL says that an implementation won’t modify padding bytes. Does that apply to view and reinterpret? Consider the following:

```rust
struct S {
  a : u32,
  b : vec4u,
}

var<workgroup> v1 : array<vec3u, 4>;
var<workgroup> v2 : S;

fn foo() {
  let p1 = reinterpret<array<vec4u, 4>(&v1);
  // This writes padding in vec3u.
  p1[0][3] = 1u;

  let p2 = reinterpret<array<vec4u, 2>(&v2);
  // This writes padding between members a and b.
  p2[0][1] = 2u;
```

If padding cannot be touched, the output types must be further restricted. In practice, the alignment and no-padding constraints combine to push shader authors to declare variables as arrays of elements which have the largest supported element size and alignment that can be tightly packed.  At that point what are we gaining over and above using an opaque base type as in the BufferView proposal?

Alternatively we could add a carve out for allowing padding byte to be modified in the case of a reinterpreted, or viewed, piece of memory. This does mean implementations would need to be careful about loading/storing of any data structure with padding bytes.

# Discussion

Reinterpret is closest to C++ `reinterpret_cast`. The ergonomics are very similar. Strict typing requirements are loosened via the use of the root identifier. The pointer argument is treated as a starting address, and the size check is against the type at the root identifier (pointer parameter or variable).  No mixing of bytes and elements in user code (though mentally this must be done). It allows “convenient” use cases more naturally than `view`.

`View` has stricter size requirements than `reinterpret`. It is “purer” from a type checking point-of-view. The mixing of bytes and elements could be confusing, but users are mostly pushed away from passing pointers based on index expressions anyways. View is easier to analyze since it doesn’t require tracing to a root identifier.

Size, alignment, and padding restrictions mean neither Reinterpret nor View provide exactly the fluency and familiarity of C/C++ style pointer casts.

`BufferView` tries to look different by using a different type. It does not raise the padding question since all reinterpretations occur on the base opaque type. Bytes fit more naturally with the opaque type too. Both `reinterpret` and `view` allow multiple reinterpretations, but require more restrictions as a result. The relaxed address space restrictions and access mode mutation could also be applied to `bufferView`. A major consideration is whether only allowing reinterpretations on the root opaque type is a better tradeoff than the size restrictions that allow reinterpretation more liberally.

A practical implication of the alignment restrictions for both `reinterpret` and `view` is that it pushes users toward just an array of vec4u in some form. So there is no real base type information to be had anyways, so why not just an opaque type (i.e. buffer)? The only advantage would be multiple reinterpretations and I’m unsure of the real value of addition.

All three proposals should be able to provide equivalent functionality. Only one of the three variants should be accepted as a language feature.

