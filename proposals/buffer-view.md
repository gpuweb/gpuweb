# Buffer View

* Status: [Draft](README.md#status-draft)
* Created: 2025-10-20
* Issue: [#5338](https://github.com/gpuweb/gpuweb/issues/5338)

# Overview

This proposal intends to add a new opaque host-shareable type to WGSL and two
new built-in functions to interact with the type.
The purpose of the type is to provide a limited form of type-punning support in
WGSL.
That is, to support reinterpreting data in a buffer as various different types.

This can also serve as a solution to a similar sort of request for workgroup
memory: [#5136](https://github.com/gpuweb/gpuweb/issues/5156).

New functionality will be added under the language extension: `buffer_view`.

# Buffer Type

Add a new opaque host-shareable type to WGSL: `buffer<N>`.
This type can be the type of a variable in the storage, uniform, or workgroup
address spaces.
No other value declarations of the type are allowed (though it may appear in a
pointer type).
The type is **not** constructible and so it cannot be used in assignments.

The template parameter specifies the size of the buffer in bytes.
It is optional for storage buffer, but required for uniform buffers and
workgroup variables.
If included it must be an override-expression, but for storage buffer and
uniform buffers, it must further be a const-expression.
When omitted, the size is unspecified, but can be accessed via the
`bufferLength` built-in function.

**TODO**: Minimum size requirement for N?

**TODO**: Do we want any new type categories?
Right now we can’t have pointers to buffer in a classic buffer, but if we ever
allow them would we also want buffer pointers?

The only way to interact with the `buffer` type is via new built-in functions.

# Function Parameters

Since buffers cannot be acted on directly, they cannot be passed as function
parameters; however they can be supported as pointer parameters.
Passing a buffer pointer as a function parameter requires
`unrestricted_pointer_parameters` since the support address spaces are
otherwise disallowed.

When allowed, standard type matching would require N to match.
That is a bit awkward from an author’s point of view.
We should consider allowing the following relaxations:
* A sized buffer can be passed to any unsized buffer (e.g. `ptr<uniform,
  buffer<32>>` can be passed to a parameter of type `ptr<uniform, buffer>`).
* A larger buffer can be passed to a smaller buffer (e.g. `ptr<storage,
  buffer<128>, read_write>` can be passed to `ptr<storage, buffer<32>,
  read_write>`).

These relaxations could also be extended to let-declarations, but that seems
not particularly necessary right now.

**TODO**: Decide on relaxations.
If we don’t want any we’ll need two overloads per built-in function.

# bufferView

```rust
@must_use
fn bufferView<T>(p : ptr<AS, buffer, AM>, offset : u32) -> ptr<AS, T, AM>

@must_use
fn bufferView<T>(p : ptr<AS, buffer<N>, AM>, offset : u32) -> ptr<AS, T, AM>
```

`AS` must be storage, uniform, or workgroup.
`AM` must be read or read_write (normal address space restrictions apply).
`T` must be a host-shareable type (other than buffer or any type containing an
atomic type) and satisfy the address space layout constraints.

Note: `T` cannot be nor contain an atomic type because you cannot cast from a
non-atomic type to an atomic type in MSL.

This function converts a buffer pointer into a useful pointer at the given
offset.
The result pointer can then be used to access the underlying buffer memory in
the same way as any normal pointer is used.
It is effectively a pointer reinterpret cast.

The requirement on `T` would mean that implementations would have to check more
places than just variables for satisfied address space layout constraints.
Since `T` cannot be a buffer type, this function cannot be chained into
multiple calls.
The input and output type restrictions restrict the breadth of type-punning
allowed in the language.
Effectively we would always be casting from an unmodified root identifier
(modulo let unpacking) and only casting once before a memory access.

An invalid memory reference is returned if `SizeOf(T) + offset >
bufferLength(p)`.
This eliminates some possible in bounds behaviour, but is easier for
implementations.

If `offset % RequiredAlignOf(T, AS) != 0`, then:
* It is a shader-creation error if `offset` is a const-expression
* It is a pipeline-creation error if `offset` is an override-expression
* The implementation shall use an equivalent value to: `offset &
  ~(RequiredAlignOf(T) - 1)`

Note: this will interact with `uniform_buffer_standard_layout`.

Implementations would need track offsets for any subsequent calls to
`arrayLength` to adjust the result by the offset.

# bufferLength

```rust
@must_use fn bufferLength(p : ptr<AS, buffer, AM>) -> u32

@must_use fn bufferLength(p : ptr<AS, buffer<N>, AM>) -> u32
```

`AS` must be storage, uniform, or workgroup.
`AM` must be read or read_write (normal address space restrictions apply).

Returns the byte size of the buffer.
If `N` is specified, return `N`.

**TODO**: Should we replace this and `arrayLength` with a single `length` function?

# API

The main interaction with the API is for bindings and the minBindingSize.
Propose the following (in descending priority):
* Use the size (`N`) if provided (required for uniform)
* Search forwards (across function calls) from each unsized buffer to find all
  the calls to `bufferView`.
  For each call, define Offset as the offset parameter if it is a
  const-expression and 0 otherwise.
  Let the minBindingSize be the maximum of `SizeOf(T) + Offset` among all the
  calls.
* Use a value of 4 bytes

The goal would be to be able to statically elide as many bounds checks as
possible.

**TODO**: Decide on minimum binding size.

**TODO**: Note that bindless may add additional complications since you cannot
know the static slot.

# Backends

## Vulkan

The cleanest implementation would utilize untyped pointers.
The buffer type could be codegen’d as a runtime array of u32s and then the
result type for the `bufferView` call would be used as the base type of the
first access chain.
Unfortunately, untyped pointers are not widely supported yet.

Available right now would be to codegen the variable as a runtime array of
either u32 or u16 (depending on the smallest access size).
Read-only buffers could always use u32, but read/write buffers should prefer
the smallest type.
Memory accesses would composed or decomposed similar to other transforms (e.g.
`uniform_buffer_standard_layout`).

## D3D

This fits pretty naturally with ByteAddressBuffers (except now uniform buffers
might use ByteAddressBuffer more often).
The D3D backend would have to accumulate the offset parameter into subsequent
memory operations accessing the ByteAddressBuffers to ensure the correct offset
is provided.

## Metal

MSL supports pointer casting so the buffer type could be codegen’d as a `char*`
and then casted where the bufferView call is made.
`char*` is used to make this TBAA safe.
Additionally pointer casts should conservatively be tagged as `mayalias`.
Implementations could opportunistically optimize this away.

## GLSL

Very similar to the Vulkan backend, but base buffer would be an array of u32 in
GLSL.


