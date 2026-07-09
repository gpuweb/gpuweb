# WGSL Enums

* Status: [Draft](README.md#status-draft)
* Created: 2026-07-08
* Issue: [#4856](https://github.com/gpuweb/gpuweb/issues/4856)

## Motivation

There is currently no enum support in WGSL. While not strictly necessary, there are potential future
uses for things like `ray_query` where we want to be able to pass in a bitmask of flags to the query.
They are also just useful as a grouping mechanism for specific values.

## Language support

The enums are, essentially, sugaring over the underlying type values, so they will be supported in
all backend languages as specific values.

### HLSL

Supported as of HLSL 2021, supports both the C style where the values become global identifiers and
the c++ `enum class` style where the values are not globals

### MSL

Supports both C style as global values and C++ `enum class` with scoped values.

### GLSL

No enums in GLSL.

### SPIR-V

No enums in SPIR-V.

## WGSL

### Language Extension

| Name    | Description |
| ------- | ----------- |
| `enums` | Adds the ability to declare `enum`'s and have `enum`s be a valid type identifier |

### Example Usage

```wgsl
requires enums;

enum MyEnum : u32 {
  a = 0,
  b = (1 * 3) - (1 + 1),
}

enum bitmask MyBitmask : u32 {
  none = 0x00,

  a = 0x01,
  b = 0x02,
  c = 0x04,

  d = 0x07,  // Combination of a, b, c
}

fn f(v: MyEnum) {
  if (v == MyEnum.a) {
    // do something
  }

  switch(v) {
    case MyEnum.a: {}
    case MyEnum.b: {}
  }
}

@override kThing: u32 = 1;
@group(0) @binding(0) var<storage> my_val: u32;
fn b() {
  let a = MyBitmask(my_val);  // Convert from underlying type
  my_val = u32(MyBitmask.d);  // Convert to underlying type

  let b = MyEnum(kThing);  // Convert from override
}
```

## Description

There would be two ways to declare an enum either, `enum` or `enum bitmask`. The available features
and restrictions are slightly different between the two.

The underlying type for an enum is required. For `enum` it *must* be `i32` or `u32`. For
`enum bitmask` it *must* be `u32`. Each enum value *must* have a value associated with it, the
compiler does not attempt to generate values based on incrementing from the last used value.

Enums can be explicitly cast to/from their underlying type.

An `enum` can be used for comparison operators, as `switch` case entries, stored into structs and
stored into variables.

An `enum bitmask` has the same availability as an `enum` with the added capability that it can be
used in bitwise `&`, `|` and `^` operations.

Declaring an `enum` makes the name associated with the enum available as a typename, similar to a
`struct`. An `enum` has the following properties:

* Concrete
* Storable

* **Q:** The enums are not hostshareable. The issue being, how do we validate that the values from
         the host are within the enum range. This would require checking at each access to the
         struct member which could be costly.

An `enum` is *not* `host-sharable` due to needing to validate the values coming from the host. The
cast from the underlying type is required.

### `enum`

An enum is strictly a list of names to values. The names can be accessed by using the full name
`MyEnum.a`, `MyEnum.b`. Each name in the enum must be unique in that enum. The values do not need to
be contiguous, and they do not need to start from zero. If the enum has a signed type the values
may be negative.

### `enum bitmask`

The `enum bitmask` extends the `enum` to be usable as a bitmask, so the `|`, `&` and `^` operators
are available.  The bitwise operators require both the right-hand side and left-hand side of the
operator to be the same enum type. (i.e. you cannot `&` an enum value against the underlying
integer type).

### Comparison operators

The enum values can be used in `==` and `!=` operations. The left-hand side and right-hand side of
the operation must both be of the enum type. (i.e. you can't do `MyBitmask.a == 0x01`).

An `enum`, but not `enum bitmask`, would also support the comparison operators `<`, `>`, `<=`, and
`>=` comparing against the values in the entries. The `enum bitmask` does not provide these extra
operators as the values do not provide the same meanings.

## Access

Accessing an enum entry is done with the `.` operator. The enum name is required, the values are
only accessible when fully named (e.g `MyBitmask.a` is value, just `a` would be invalid as the name
is not in scope).

* **Q:** The `.` could be a `::` to match C++ and Rust. The `.` seems like it would be what we'd want
         for namespaces, so using that in the proposal, can be discussed.

## Conversions

There are no implicit conversions for `enum` values. They can be converted to their underlying type
through an explicit cast (e.g `u32(MyEnum.a)`). The  conversion rank rules are then applied to the
resulting value.

When doing a conversion into an enum (e.g. `let a = MyEnum(1u)`) there is validation that the value
is a valid enum entry. For an `enum` we verify that the provided underlying value is a value in the
`enum`. When the  `bitmask` modifier is applied, we verify that all of the bits in the underlying
value are bits in the values of the enum.

* If we know the underlying value at shader creation, it is a shader creation error if these rules
  are violated
* For `override` conversion values it will be a pipeline creation error if the rules are violated
* Otherwise, it's a dynamic error if the rules are violated. For a dynamic error, an *indeterminate*
  value from the enum will be returned by the cast, it can be any value.
  * For a regular `enum` this means we'll have to do a `value == MyEnum.a || value == MyEnum.b` check
  * If the `enum` range is dense the check can be `min(maxValue, max(minValue, value))`
  * For a `enum bitmask` we need to do a `value & All_Bits_From_MyEnum == value`

When converting into an enum, the conversion rules for the underlying type would apply to the value
passed into the constructor.

```wgsl
enum MyEnum : u32 {
  Val1 = 1,
}

fn foo() {
  let a = MyEnum(1i);      // expected to fail -- no implicit conversion from i32 to u32
  let b = MyEnum(u32(1i)); // expected to pass -- explicit cast to u32
  let c = MyEnum(1);       // expected to pass -- AbstractInt -> u32
}
```

* **Q:** Is the requirement for the explicit conversion here just extra noise? Should there be some
         kind of implicit conversion permitted in the constructors?

## Zero Initialization

When an enum is used in a zero-initialized `var`, (e.g. one in `workgroup` or used without an
initializer in `function` or `private`) then the enum is *required* to have a value of `0` in the
enum. (This is in order to allow us to continue using things like Vulkan zero initialization which
zeros all bits).

## Validation

* An `enum` must contain at least one entry.
* The underlying type must be an `i32` or `u32`
* Each entry in an `enum`  must have a value.
* Each name in an `enum` must be unique in that enum
* Each value in an `enum`  must be the same type as the underlying type (note, this means that
  automatic feasible conversions will occur)
* Each `expression` used as a value must be a `const-expression`
* Each value in an `enum bitmask` must be either:
  * A power of 2 value in the `enum`
  * Or, a combination of bits in the other values, no new bits may be introduced
  * Or a zero value. (e.g. SPIR-V Relaxed atomic mask)

## Switch statements

The enum values can be used in switch case statements.

For an `enum` if the switch lists every entry in the enum then the `default` statement is not
allowed. The `enum` values are directly compared to the case statements.

* **Q:** Should the `default` be disallowed in this case, or just optional?

```wgsl
let v = MyEnum.b;
switch (v) {
  case MyEnum.a, MyEnum.b: {}
  // default not allowed
}

switch (v) {
  case MyEnum.a: {}
  default: {}
}
```

For an `enum bitmask` the `default` statement is required. The case values are directly compared to
the switch condition, and must match all bits.

```wgsl
let k = MyBitmask.a | MyBitmask.b;
switch (k) {
  case MyBitmask.none, MyBitmask.a: {}
  case MyBitmask.b: {}
  case MyBitmask.c: {}
}

switch (k) {
  case MyBitmask.none: {}
  case MyBitmask.d: {}  // would this match or not?
}

```

A switch is not required to list all entries in the enum, a `default` will cover any missing entries.

## Grammar

```ebnf
enum_decl
  : attribute 'enum' ident ':' type_specifier '{' enum_entries '}'
  | attribute 'enum' 'bitmask' ident ':' type_specifier '{' enum_entries '}'

enum_entries:
  enum_entry (',' enum_entry)* ','?

enum_entry:
  ident '=' expression  // Must be const_expression

global_decl:
  ...
  | enum_decl

component_or_swizzle_specifier:
  ...
  | '.' enum_entry_name   // Could just be `member_ident` if we changed that one?
```

## Desugaring

An `enum`  is a sugaring over the value for each entry. Once the validation rules are applied the
enum can be converted to the underlying type and treated as that type when emitted to
backend compilers.

# Alternatives

* Do nothing, do not provide enums
  * This is, essentially, what we have now. The area this falls apart is if we want to add builtin
    methods which take bitmask values. (See
    [https://github.com/gfx-rs/wgpu/blob/trunk/docs/api-specs/ray\_tracing.md\#ray-queries](https://github.com/gfx-rs/wgpu/blob/trunk/docs/api-specs/ray_tracing.md#ray-queries)
    and the Flags for `RayDesc::flags`).
  * This has the downside that we can't validate the values being passed into the call. It can be
    any `u32` value, not just a combination of the required flags.
  * Would also mean we'd have to provide global names for the constants to be accessed which requires
    C like naming of `RayQueryForceOpaque` instead of the, slightly, nicer `RayQuery.ForceOpaque`
