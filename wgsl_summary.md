# WGSL Specification Summary

## Introduction
WebGPU Shading Language (WGSL) is the shading language for the WebGPU API. It is used to write shaders (programs running on the GPU) for render and compute pipelines.

### Key Concepts
*   **Pipelines:** WGSL is used in Render Pipelines (via draw commands) and Compute Pipelines (via dispatch commands).
*   **Shader:** A portion of a WGSL program that executes a specific shader stage (vertex, fragment, compute). It includes an entry point function, all called functions, accessed variables/constants, and associated types.
*   **Organization:** A WGSL program consists of directives, functions, statements, literals, constants, variables, expressions, types, and attributes.
*   **Imperative & Statically Typed:** Behavior is specified as a sequence of statements. Every expression has a fixed type determined at compile time.
*   **Execution Model:** Work is partitioned into **invocations**.
    *   **Invocations:** Execute the entry point independently.
    *   **Workgroups:** Groups of invocations in compute shaders that can share memory.
    *   **Shared Resources:** All invocations in a stage share API-bound resources (textures, buffers).
    *   **Memory Spaces:** Variables exist in different address spaces (`private`, `function`, `workgroup`, `storage`, `uniform`).
*   **Concurrency:** Invocations execute concurrently/parallelly. Authors must handle **uniformity** and avoid **data races**.

## WGSL Module
A WGSL program is a **shader module**. It is a single unit of source code.
*   **Creation:** Modules are created from UTF-8 text.
*   **Validation:** Modules must be valid according to the WGSL grammar and static analysis rules.
*   **Interface:** Modules communicate with the API via **bindings** (group/binding attributes) and **built-in variables** (e.g., `@builtin(position)`).

## Textual Structure
*   **Character Set:** UTF-8.
*   **Comments:** `//` for single-line, `/* ... */` for multi-line (can be nested).
*   **Identifiers:** Must start with a letter or underscore, followed by letters, digits, or underscores. Some are reserved (keywords).
*   **Keywords:** `fn`, `var`, `let`, `const`, `struct`, `if`, `else`, `switch`, `loop`, `for`, `while`, `break`, `continue`, `return`, etc.
*   **Literals:**
    *   **Integer:** `123`, `0x123`, `123u`.
    *   **Floating-point:** `123.45`, `1.23e4`, `0x1.2p3`, `1.2f`, `1.2h`.
    *   **Boolean:** `true`, `false`.

## Directives
Directives provide module-level controls.
*   **Enable:** `enable extension_name;` - Enables an optional language feature (e.g., `f16`).
*   **Diagnostic:** `diagnostic(severity, path);` - Controls diagnostic message severity (e.g., `off`, `info`, `warning`, `error`).

## Declaration and Scope
*   **Global Scope:** Declarations outside any function (types, constants, variables, functions).
*   **Function Scope:** Declarations inside a function.
*   **Shadowing:** Inner scopes can shadow outer scopes, except for certain cases (like shadowing a type with a variable in the same scope).
*   **Lifetime:**
    * **Module-scope variables:** Live for the duration of the shader stage execution.
    * **Function-scope variables:** Live for the duration of the function call.

    ## Types

    WGSL is statically typed. Every expression has a type.

    ### Scalar Types
    *   **`bool`**: Boolean values `true` and `false`.
    *   **`i32`**: 32-bit signed integer.
    *   **`u32`**: 32-bit unsigned integer.
    *   **`f32`**: 32-bit floating point (IEEE 754).
    *   **`f16`**: 16-bit floating point (binary16). Requires `enable f16;`.
    *   **Abstract Types**: `AbstractInt` and `AbstractFloat` are used for high-precision compile-time calculations. They are automatically converted to concrete types when needed.

    ### Composite Types
    *   **Vectors**: `vecN<T>` where `N` is 2, 3, or 4.
    *   Shorthands: `vec2f`, `vec3i`, `vec4u`, `vec2h`, etc.
    *   **Matrices**: `matCxR<T>` where `C` (columns) and `R` (rows) are 2, 3, or 4. `T` must be a floating-point type.
    *   Shorthands: `mat2x2f`, `mat4x3h`, etc.
    *   **Arrays**: `array<T, N>` (fixed-size) or `array<T>` (runtime-sized).
    *   Runtime-sized arrays can only be the last member of a structure in the `storage` address space.
    *   **Structures**: User-defined types using `struct Name { member : Type, }`.

    ### Resource and Special Types
    *   **Atomics**: `atomic<T>` where `T` is `i32` or `u32`. Used for atomic operations.
    *   **Pointers**: `ptr<address_space, type, access_mode>`. Pointers are used to reference memory.
    *   **Textures**: Various types like `texture_2d<T>`, `texture_cube<T>`, `texture_storage_2d<format, access>`, `texture_depth_2d`, etc.
    *   **Samplers**: `sampler` (filtering) and `sampler_comparison` (depth comparison).

    ## Address Spaces and Access Modes

    Variables exist in **address spaces** which determine where they are stored and their visibility.

    | Address Space | Description | Default Access |
    | :--- | :--- | :--- |
    | `function` | Local to a function. | `read_write` |
    | `private` | Local to an invocation, module-scope. | `read_write` |
    | `workgroup` | Shared among invocations in a workgroup. | `read_write` |
    | `uniform` | Read-only, API-bound buffer. | `read` |
    | `storage` | Read-write or read-only, API-bound buffer. | `read` |
    | `handle` | For textures and samplers. | `read` |

    **Access Modes:** `read`, `write`, `read_write`.

    ## Variable and Value Declarations

    ### `var`
    Declares a named memory location (variable).
    *   `var<address_space, access_mode> name : type = initializer;`
    *   In `function` scope, address space is optional (defaults to `function`).
    *   In `private` and `workgroup` scopes, they are module-scope.

    ### `let`
    Declares a named, immutable value (constant within its scope).
    *   `let name : type = initializer;`
    *   Only allowed in function scope.

    ### `const`
    Declares a compile-time constant.
    *   `const name : type = initializer;`
    *   Value must be a `const-expression`.

    ### `override`
    Declares a pipeline-overridable constant.
    * `override name : type = initializer;`
    *   Value can be overridden during pipeline creation in the API.

    ## Expressions

    WGSL expressions are categorized by the time they are evaluated:
    *   **`const-expression`**: Evaluated at shader creation time.
    *   **`override-expression`**: Evaluated at pipeline creation time.
    *   **`runtime-expression`**: Evaluated during shader execution.

    ### Common Expressions
    *   **Literals**: `123`, `1.5f`, `true`, etc.
    *   **Identifiers**: Variable or constant names.
    *   **Function Calls**: `foo(x, y)`.
    *   **Member Access**: `struct.member` or `vector.x`, `vector.xy`.
    *   **Swizzling**: Vectors support components like `.x`, `.y`, `.z`, `.w`, `.r`, `.g`, `.b`, `.a`, and combinations (e.g., `.rgba`, `.xyz`).
    *   **Index Access**: `array[index]` or `vector[index]`.

    ### Operators
    *   **Unary**: `-` (negation), `!` (logical NOT), `~` (bitwise NOT), `*` (dereference), `&` (address-of).
    *   **Arithmetic**: `+`, `-`, `*`, `/`, `%` (modulo).
    *   **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`.
    *   **Logical**: `&&` (short-circuiting AND), `||` (short-circuiting OR).
    *   **Bitwise**: `&`, `|`, `^` (XOR), `<<` (left shift), `>>` (right shift).

    ## Statements

    Statements are the units of execution within a function.
    *   **Compound**: `{ ... }` blocks.
    *   **Assignments**: `x = y;`, `x += y;`, `x -= y;`, etc. (No `x++` or `x--`).
    *   **Control Flow**:
    *   `if (cond) { ... } else { ... }`
    *   `switch (expr) { case V: { ... } default: { ... } }`
    *   `loop { ... }`: Infinite loop with optional `continuing { ... }` block.
    *   `while (cond) { ... }`
    *   `for (init; cond; update) { ... }`
    *   **Break/Continue**: `break;`, `continue;`, `break if (cond);`.
    *   **Return**: `return;` or `return expr;`.
    *   **Discard**: `discard;` (only in fragment shaders, stops execution and discards the fragment).
    *   **Assertions**: `const_assert(expr);` (evaluated at shader creation time).

    ## Functions

    Functions are defined at the module scope.
    *   `fn name(param1 : type1, param2 : type2) -> return_type { ... }`
    *   Parameters are immutable.
    *   Recursion is **not** allowed.

    ## Attributes

    Attributes provide metadata and control for declarations.
    *   **Entry Points**: `@vertex`, `@fragment`, `@compute`.
    *   **Interface**:
    *   `@location(N)`: Assigns a user-defined location for I/O.
    *   `@builtin(name)`: Maps to a system-defined value (e.g., `position`, `vertex_index`).
    *   `@group(G)`, `@binding(B)`: Resource binding indices.
    *   **Compute**: `@workgroup_size(x, y, z)`.
    *   **Interpolation**: `@interpolate(type, sampling)`.
    *   **Others**: `@id(N)`, `@must_use`, `@invariant`, `@diagnostic(...)`, `@align(A)`, `@size(S)`.

    ## Entry Points

    A WGSL module must contain at least one entry point to be used in a pipeline.
    *   **Vertex**: `@vertex` - processes vertices.
    *   **Fragment**: `@fragment` - processes pixels/fragments.
    *   **Compute**: `@compute` - perform general-purpose computation.
    * Entry points can take parameters and return values, which must be decorated with `@location` or `@builtin` attributes.

    ## Memory and Execution

    ### Memory Layout
    *   **Alignment and Size**: Types have specific alignment and size requirements.
    *   **Layout Attributes**: `@align(A)` and `@size(S)` can be used in structures to control the layout.
    *   **Buffer Binding**: Buffers in `uniform` and `storage` address spaces must follow layout rules (e.g., specific padding).

    ### Execution Model
    *   **Control Flow**: Standard structured control flow.
    *   **Barriers**: `workgroupBarrier()` and `storageBarrier()` synchronize access within a workgroup.
    *   **Invocations**: Compute shaders use workgroups; vertex/fragment shaders use invocations per primitive/pixel.
    *   **Uniformity**: Certain operations (like derivative functions and texture sampling) require uniformity in control flow.

    ## Built-in Functions

    WGSL provides a rich set of built-in functions. They are categorized as follows:

    ### Math and Logic
    *   **Logic**: `all()`, `any()`, `select()`.
    *   **Arithmetic**: `abs()`, `clamp()`, `max()`, `min()`, `modf()`, `sign()`, `saturate()`.
    *   **Exponential**: `exp()`, `exp2()`, `log()`, `log2()`, `pow()`, `sqrt()`, `inverseSqrt()`.
    *   **Trigonometric**: `cos()`, `sin()`, `tan()`, `acos()`, `asin()`, `atan()`, `atan2()`.
    *   **Common**: `ceil()`, `floor()`, `round()`, `trunc()`, `fract()`.

    ### Vector and Matrix
    *   **Vector**: `cross()`, `dot()`, `distance()`, `length()`, `normalize()`, `reflect()`, `refract()`.
    *   **Matrix**: `determinant()`, `transpose()`.

    ### Texture and Sampler
    *   **Sampling**: `textureSample()`, `textureSampleLevel()`, `textureSampleBias()`, `textureSampleGrad()`, `textureSampleCompare()`.
    *   **Load/Store**: `textureLoad()`, `textureStore()`.
    *   **Inquiry**: `textureDimensions()`, `textureNumLayers()`, `textureNumLevels()`.

    ### Atomic
    *   **Operations**: `atomicAdd()`, `atomicSub()`, `atomicMax()`, `atomicMin()`, `atomicAnd()`, `atomicOr()`, `atomicXor()`, `atomicExchange()`, `atomicCompareExchangeWeak()`, `atomicLoad()`, `atomicStore()`.

    ### Miscellaneous
    *   **Synchronization**: `workgroupBarrier()`, `storageBarrier()`.
    *   **Derivatives**: `dpdx()`, `dpdy()`, `fwidth()` (fragment shaders only).
    *   **Packing/Unpacking**: `pack4x8snorm()`, `unpack2x16float()`, etc.
    *   **Data Manipulation**: `bitcast<T>(v)`.



