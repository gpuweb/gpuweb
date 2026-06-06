# WGSL Expanded Specification Summary

## 1. Introduction
WebGPU Shading Language (WGSL) is the primary shading language for the WebGPU API. It allows developers to write programs that run on the GPU, handling tasks from graphics rendering (vertex and fragment shaders) to general-purpose computation (compute shaders).

### Relationship with WebGPU
WGSL is designed to map efficiently to modern GPU hardware while maintaining portability across different operating systems and GPU APIs (Vulkan, Metal, D3D12).
*   **Pipelines:** Shaders are used within `GPURenderPipeline` and `GPUComputePipeline`.
*   **Stages:** WGSL supports three entry point stages: `@vertex`, `@fragment`, and `@compute`.
*   **Resources:** WGSL connects to WebGPU buffers and textures via bind groups (`@group` and `@binding`).

## 2. WGSL Module
A WGSL program is called a **shader module**. It is a standalone unit of code.
*   **Validation:** A module must be valid UTF-8. It undergoes several validation phases:
    1.  **Parsing:** Ensuring the code matches the WGSL grammar.
    2.  **Static Analysis:** Checking type safety, scope rules, and control flow.
    3.  **Pipeline Creation:** Some checks are deferred until a pipeline is created (e.g., resource compatibility).
*   **Interface:** The interface between the module and the API is defined by global variables with binding attributes and built-in variables.

## 3. Textual Structure
WGSL source code is UTF-8 encoded text.

### Parsing and Tokenization
1.  **Comment Removal:** Comments are replaced by a single space during initial parsing.
2.  **Template Discovery:** A special pass identifies template lists (`<...>`) to disambiguate them from comparison operators.
3.  **Tokenization:** The text is broken into tokens: literals, keywords, reserved words, and identifiers.

### Blankspace and Line Breaks
Blankspace includes space, horizontal tab, line feed, vertical tab, form feed, carriage return, and several Unicode whitespace characters. Line breaks are used for diagnostic reporting (line numbers).

### Comments
*   **Line Comments:** Start with `//` and extend to the end of the line.
*   **Block Comments:** Start with `/*` and end with `*/`. They **can be nested**.
    ```wgsl
    /* This is a block comment.
       /* This is a nested block comment. */
       The outer comment continues here.
    */
    ```

### Identifiers
Identifiers name variables, functions, and types.
*   **Rules:** Must start with a letter or underscore. Can contain letters, digits, and underscores.
*   **Unicode:** WGSL supports Unicode identifiers (e.g., `Δέλτα`).
*   **Restrictions:** Cannot be a keyword or reserved word. Cannot be a single underscore `_` or start with two underscores `__` (except for certain internal names).

### Keywords and Reserved Words
**Keywords** (active in the language):
`array`, `atomic`, `bool`, `break`, `case`, `const`, `const_assert`, `continue`, `continuing`, `default`, `diagnostic`, `discard`, `else`, `enable`, `f16`, `f32`, `fallthrough`, `false`, `fn`, `for`, `i32`, `if`, `let`, `loop`, `mat2x2`, `mat2x3`, `mat2x4`, `mat3x2`, `mat3x3`, `mat3x4`, `mat4x2`, `mat4x3`, `mat4x4`, `override`, `ptr`, `requires`, `return`, `sampler`, `sampler_comparison`, `struct`, `switch`, `texture_1d`, `texture_2d`, `texture_2d_array`, `texture_3d`, `texture_cube`, `texture_cube_array`, `texture_multisampled_2d`, `texture_storage_1d`, `texture_storage_2d`, `texture_storage_2d_array`, `texture_storage_3d`, `true`, `type`, `u32`, `var`, `vec2`, `vec3`, `vec4`, `while`.

**Reserved Words** (cannot be used as identifiers):
`asm`, `bf16`, `do`, `enum`, `f64`, `handle`, `i8`, `i16`, `i64`, `mat`, `premerge`, `regardless`, `u8`, `u16`, `u64`, `unless`, `using`, `vec`, `void`.

### Literals
*   **Boolean:** `true`, `false`.
*   **Integer:** 
    *   Decimal: `123`, `0`.
    *   Hexadecimal: `0x123`, `0Xabc`.
    *   Suffixes: `i` for `i32`, `u` for `u32`. No suffix means `AbstractInt`.
*   **Floating-point:**
    *   Decimal: `12.34`, `1e-3`, `0.f`, `1.5h`.
    *   Hexadecimal: `0x1.fp-4`, `0xap+2f`.
    *   Suffixes: `f` for `f32`, `h` for `f16`. No suffix means `AbstractFloat`.

## 4. Directives
Directives must appear at the very top of the module.

### Enable Directive
Enables optional language features that depend on hardware support.
```wgsl
enable f16;
enable subgroups;
```
If the implementation or the device doesn't support the extension, a shader-creation error occurs.

### Requires Directive
Documents that the shader requires specific language extensions.
```wgsl
requires readonly_and_readwrite_storage_textures;
```
This is used for portability signaling.

### Diagnostic Directive
Controls the severity of diagnostic messages globally.
```wgsl
diagnostic(off, derivative_uniformity);
```
Severities: `error`, `warning`, `info`, `off`.

## 5. Declaration and Scope
### Scopes
1.  **Module Scope:** Declarations outside any function. Includes functions, structures, and module-scope variables (`var<private>`, `var<workgroup>`, etc.).
2.  **Function Scope:** Declarations inside a function. Includes parameters and `let`/`var` declarations.
3.  **Statement Scope:** Declarations inside a block (`{ ... }`), like in an `if` or `loop`.

### Shadowing
An identifier in an inner scope can **shadow** an identifier with the same name in an outer scope.
```wgsl
var<private> x : i32 = 1;

fn foo() {
    let x = 2; // Shadows global x
    {
        let x = 3; // Shadows inner x
    }
}
```
Exceptions: You cannot shadow a type name with a variable name in the same scope.

### Lifetime
*   **Module-scope variables:** Exist for the entire duration of the shader execution.
*   **Function-scope variables:** Exist only while the function is executing.
*   **Invocations:** Each invocation has its own copy of `private` and `function` variables. `workgroup` variables are shared across all invocations in a single workgroup.

## 6. Types
WGSL is a statically typed language. Every expression has a fixed type determined at shader creation time.

### Scalar Types
*   **`bool`**: Represents boolean values `true` and `false`.
*   **`i32`**: A 32-bit signed integer (two's complement). Range: [-2^31, 2^31 - 1].
*   **`u32`**: A 32-bit unsigned integer. Range: [0, 2^32 - 1].
*   **`f32`**: A 32-bit floating-point type (IEEE 754 binary32).
*   **`f16`**: A 16-bit floating-point type (binary16). Requires `enable f16;`.
*   **`AbstractInt`**: An arbitrary-precision signed integer used for compile-time constants.
*   **`AbstractFloat`**: An arbitrary-precision floating-point type used for compile-time constants.

### Vector Types
Vectors are ordered collections of 2, 3, or 4 scalar components of the same type.
*   **Syntax:** `vecN<T>` where `N` is 2, 3, or 4, and `T` is a scalar type.
*   **Shorthands:**
    *   `vec2f`, `vec3f`, `vec4f` (for `f32`)
    *   `vec2i`, `vec3i`, `vec4i` (for `i32`)
    *   `vec2u`, `vec3u`, `vec4u` (for `u32`)
    *   `vec2h`, `vec3h`, `vec4h` (for `f16`)
    *   `vec2b`, `vec3b`, `vec4b` (for `bool`)
*   **Alignment/Size:**
    *   `vec2`: Align 8, Size 8
    *   `vec3`: Align 16, Size 12
    *   `vec4`: Align 16, Size 16

### Matrix Types
Matrices are collections of floating-point scalars arranged in columns and rows. WGSL uses **column-major** layout.
*   **Syntax:** `matCxR<T>` where `C` is columns (2, 3, 4), `R` is rows (2, 3, 4), and `T` is `f32` or `f16`.
*   **Shorthands:** `mat4x4f`, `mat3x2h`, etc.
*   **Alignment:** Same as the alignment of its column vector (e.g., `mat4x2f` has alignment of `vec2f`, which is 8).

### Array Types
*   **Fixed-size:** `array<T, N>` where `N` is a constant expression.
*   **Runtime-sized:** `array<T>`. Only allowed as the last member of a structure in the `storage` address space.
*   **Element Type:** `T` must be a "fixed-footprint" type (cannot be another runtime-sized array).

### Structure Types
User-defined types with named members.
*   **Declaration:**
    ```wgsl
    struct MyStruct {
        @align(16) position : vec3f,
        @size(16) color : vec4f,
        flags : u32,
    }
    ```
*   **Layout Rules:**
    *   `@align(N)`: Forces the member to start at an offset that is a multiple of `N`.
    *   `@size(S)`: Forces the member to occupy at least `S` bytes.

### Atomic Types
Provide atomic operations (e.g., `atomicAdd`).
*   **Syntax:** `atomic<T>` where `T` is `i32` or `u32`.
*   **Restriction:** Atomics can only reside in the `storage` or `workgroup` address spaces.

### Resource Types
#### Texture Types
*   **Sampled:** `texture_1d<T>`, `texture_2d<T>`, `texture_2d_array<T>`, `texture_3d<T>`, `texture_cube<T>`, `texture_cube_array<T>`. `T` is `f32`, `i32`, or `u32`.
*   **Multisampled:** `texture_multisampled_2d<T>`.
*   **External:** `texture_external`. Used for video frames.
*   **Depth:** `texture_depth_2d`, `texture_depth_2d_array`, `texture_depth_cube`, `texture_depth_cube_array`, `texture_depth_multisampled_2d`.
*   **Storage:** `texture_storage_2d<format, access>`. Format must be a supported texel format (e.g., `rgba8unorm`).

#### Sampler Types
*   **`sampler`**: For standard texture sampling.
*   **`sampler_comparison`**: For depth comparison sampling.

### Pointer and Reference Types
*   **Pointer:** `ptr<address_space, T, access_mode>`. Pointers are handles to memory.
*   **Reference:** An internal concept representing a memory location. References are automatically dereferenced in most contexts.

## 7. Address Spaces and Access Modes
### Address Spaces
| Address Space | Storage Location | Scope | Access | Shared? |
| :--- | :--- | :--- | :--- | :--- |
| `function` | Stack | Function | `read_write` | No |
| `private` | Invoc.-private | Module | `read_write` | No |
| `workgroup` | Workgroup local | Module | `read_write` | Yes (in workgroup) |
| `uniform` | GPU Buffer | Module | `read` | Yes |
| `storage` | GPU Buffer | Module | `read`, `read_write` | Yes |
| `handle` | Opaque (Texture) | Module | `read` | Yes |

### Access Modes
*   **`read`**: Only read operations allowed.
*   **`write`**: Only write operations allowed (storage textures).
*   **`read_write`**: Both read and write allowed.

## 8. Variable and Value Declarations
### `var`
Declares a named memory location.
*   **Syntax:** `var<address_space, access_mode> name : type = initializer;`
*   **Usage:**
    ```wgsl
    @group(0) @binding(0) var<uniform> config : Config;
    var<private> counter : u32 = 0u;
    fn main() {
        var local_x : f32 = 1.0;
    }
    ```

### `let`
Declares a named, immutable value. The value is computed at **runtime**.
*   **Syntax:** `let name : type = expression;`
*   **Restriction:** Only allowed in function scope.

### `const`
Declares a **compile-time** constant.
*   **Syntax:** `const name : type = expression;`
*   **Restriction:** The expression must be a `const-expression`.

### `override`
Declares a **pipeline-creation-time** constant.
*   **Syntax:** `@id(123) override name : type = expression;`
*   **Usage:** Can be overridden by the WebGPU API during pipeline creation.

## 9. Expressions and Operators
WGSL expressions are classified by their evaluation time:
*   **`const-expression`**: Evaluated during shader creation (e.g., `1 + 2`).
*   **`override-expression`**: Evaluated during pipeline creation.
*   **`runtime-expression`**: Evaluated during shader execution.

### Operator Precedence (Highest to Lowest)
1.  **Unary:** `!`, `~`, `-`, `*`, `&`
2.  **Multiplicative:** `*`, `/`, `%`
3.  **Additive:** `+`, `-`
4.  **Shift:** `<<`, `>>`
5.  **Relational:** `<`, `>`, `<=`, `>=`, `==`, `!=`
6.  **Binary AND:** `&`
7.  **Binary XOR:** `^`
8.  **Binary OR:** `|`
9.  **Logical AND:** `&&`
10. **Logical OR:** `||`

### Detailed Operators
*   **Arithmetic:** `+`, `-`, `*`, `/`, `%`. Division by zero is undefined behavior at runtime but a shader-creation error for `const-expressions`.
*   **Bitwise:** `&` (AND), `|` (OR), `^` (XOR), `~` (NOT), `<<` (Left Shift), `>>` (Right Shift).
*   **Logical:** `&&` (Short-circuiting AND), `||` (Short-circuiting OR), `!` (NOT).
*   **Comparison:** `==`, `!=`, `<`, `>`, `<=`, `>=`. Produce `bool` or `vecN<bool>`.

### Vector Access (Swizzling)
*   Components can be accessed using `.x`, `.y`, `.z`, `.w` or `.r`, `.g`, `.b`, `.a`.
*   **Swizzling:** `vec.xyz`, `vec.xxxx`, `vec.bgra`.
*   **Index Access:** `vec[i]` where `i` is a `u32` or `i32`.

## 10. Statements
### Control Flow
*   **Compound Statement:** A block of code `{ ... }`.
*   **Assignment:** `variable = expression;` or compound assignments like `+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `>>=`, `<<=`.
*   **If Statement:**
    ```wgsl
    if (condition) {
        // ...
    } else if (other_condition) {
        // ...
    } else {
        // ...
    }
    ```
*   **Switch Statement:**
    ```wgsl
    switch (value) {
        case 0, 1: { // Multiple selectors
            // ...
        }
        case 2: {
            // ...
            fallthrough; // Optional fallthrough to next case
        }
        default: {
            // ...
        }
    }
    ```
*   **Loop Statement:** The most basic loop.
    ```wgsl
    loop {
        if (condition) { break; }
        // ...
        continuing {
            // Code here runs after each iteration, before the next.
            // Often used for incrementing counters.
            break if (exit_condition);
        }
    }
    ```
*   **While Statement:** `while (condition) { ... }`
*   **For Statement:** `for (var i = 0; i < 10; i++) { ... }`

### Other Statements
*   **`break`**: Exit the current loop or switch.
*   **`continue`**: Skip to the `continuing` block or the next iteration.
*   **`return`**: Exit the current function, optionally with a value.
*   **`discard`**: (Fragment shader only) Stops execution and prevents the fragment from being written to the framebuffer.
*   **`const_assert`**: A compile-time assertion.
    ```wgsl
    const_assert(WIDTH > 0);
    ```

## 11. Functions
Functions are the primary unit of modularity.
*   **Syntax:**
    ```wgsl
    fn name(param1 : T1, param2 : T2) -> ReturnType {
        // Body
        return result;
    }
    ```
*   **Parameters:** Are immutable `let` values. To modify a value, it must be passed as a pointer (`ptr<... , T>`).
*   **Recursion:** **Strictly forbidden** in WGSL.
*   **Entry Points:** Functions decorated with `@vertex`, `@fragment`, or `@compute`.

## 12. Attributes
Attributes are used to provide metadata to the compiler.

### General Attributes
*   **`@id(N)`**: Specifies the numerical ID for an `override` constant.
*   **`@must_use`**: Applied to a function; results in a warning if the return value is ignored.
*   **`@diagnostic`**: Controls diagnostic message severity for a specific scope.

### Interface Attributes
*   **`@location(N)`**: Specifies the input/output location for vertex and fragment stages.
*   **`@builtin(name)`**: Maps a parameter or return value to a system-defined value.
*   **`@group(G)`, `@binding(B)`**: Specifies the bind group and binding index for resources.

### Stage-Specific Attributes
*   **`@vertex`**, **`@fragment`**, **`@compute`**: Mark a function as an entry point.
*   **`@workgroup_size(x, y, z)`**: Required for `@compute` entry points.
*   **`@interpolate(type, sampling)`**: Controls how values are interpolated between vertex and fragment stages.
    *   Types: `perspective` (default), `linear`, `flat`.
    *   Sampling: `center`, `centroid`, `sample`.
*   **`@invariant`**: Used with `@builtin(position)` to ensure identical results for the same input.

## 13. System-Defined Built-in Variables
*   **`vertex_index`**: Index of the current vertex (u32).
*   **`instance_index`**: Index of the current instance (u32).
*   **`position`**: Vertex output / fragment input position (vec4f).
*   **`front_facing`**: Whether the fragment is front-facing (bool).
*   **`frag_depth`**: Fragment output depth (f32).
*   **`sample_index`**: Multi-sample index (u32).
*   **`sample_mask`**: Sample coverage mask (u32).
*   **`local_invocation_id`**: In-workgroup ID (vec3u).
*   **`global_invocation_id`**: Global ID across all workgroups (vec3u).
*   **`workgroup_id`**: ID of the current workgroup (vec3u).
*   **num_workgroups**: Total number of workgroups dispatched (vec3u).

## 14. Built-in Functions
WGSL provides a comprehensive standard library of built-in functions.

### Logical Built-ins
*   **`all(v: vecN<bool>) -> bool`**: Returns true if all components are true.
*   **`any(v: vecN<bool>) -> bool`**: Returns true if any component is true.
*   **`select(f: T, t: T, cond: bool) -> T`**: Returns `f` if `cond` is false, `t` if true.
*   **`select(f: vecN<T>, t: vecN<T>, cond: vecN<bool>) -> vecN<T>`**: Component-wise selection.

### Arithmetic Built-ins
*   **`abs(e: T) -> T`**: Absolute value.
*   **`clamp(e: T, low: T, high: T) -> T`**: Constrains `e` to range `[low, high]`.
*   **`max(e1: T, e2: T) -> T`**: Maximum of two values.
*   **`min(e1: T, e2: T) -> T`**: Minimum of two values.
*   **`saturate(e: T) -> T`**: `clamp(e, 0.0, 1.0)`.
*   **`sign(e: T) -> T`**: Returns 1.0, 0.0, or -1.0.
*   **`step(edge: T, x: T) -> T`**: Returns 0.0 if `x < edge`, else 1.0.
*   **`smoothstep(low: T, high: T, x: T) -> T`**: Smooth interpolation between 0 and 1.

### Trigonometric and Exponential
*   **`cos(e: T)`, `sin(e: T)`, `tan(e: T)`**: Trigonometric functions (radians).
*   **`acos(e: T)`, `asin(e: T)`, `atan(e: T)`, `atan2(y: T, x: T)`**: Inverse trig.
*   **`exp(e: T)`, `exp2(e: T)`**: Natural and base-2 exponential.
*   **`log(e: T)`, `log2(e: T)`**: Natural and base-2 logarithm.
*   **`pow(base: T, exp: T) -> T`**: `base` raised to `exp`.
*   **`sqrt(e: T)`, `inverseSqrt(e: T)`**: Square root and its reciprocal.

### Vector and Matrix Built-ins
*   **`cross(e1: vec3<T>, e2: vec3<T>) -> vec3<T>`**: Cross product.
*   **`dot(e1: vecN<T>, e2: vecN<T>) -> T`**: Dot product.
*   **`distance(e1: vecN<T>, e2: vecN<T>) -> T`**: Euclidean distance.
*   **`length(e: vecN<T>) -> T`**: Vector length.
*   **`normalize(e: vecN<T>) -> vecN<T>`**: Vector with length 1.0.
*   **`reflect(i: vecN<T>, n: vecN<T>) -> vecN<T>`**: Reflection vector.
*   **`refract(i: vecN<T>, n: vecN<T>, eta: T) -> vecN<T>`**: Refraction vector.
*   **`determinant(e: matNxN<T>) -> T`**: Matrix determinant.
*   **`transpose(e: matCxR<T>) -> matRxC<T>`**: Matrix transpose.

### Common Floating Point
*   **`ceil(e: T)`, `floor(e: T)`, `round(e: T)`, `trunc(e: T)`**: Rounding functions.
*   **`fract(e: T) -> T`**: Fractional part (`e - floor(e)`).
*   **`modf(e: T) -> __modf_result<T>`**: Returns fractional and integral parts as a struct.
*   **`frexp(e: T) -> __frexp_result<T>`**: Decomposes into significand and exponent.

### Texture Built-ins
*   **`textureDimensions(t: T) -> vecN<u32>`**: Returns dimensions of a texture.
*   **`textureNumLayers(t: T) -> u32`**: Returns layer count.
*   **`textureNumLevels(t: T) -> u32`**: Returns mip level count.
*   **`textureSample(t: texture_2d<f32>, s: sampler, coords: vec2f) -> vec4f`**: Standard sampling.
*   **`textureSampleLevel(t, s, coords, level)`**: Sample at specific mip level.
*   **`textureSampleBias(t, s, coords, bias)`**: Sample with mip bias.
*   **`textureSampleCompare(t: texture_depth_2d, s: sampler_comparison, coords, depth_ref)`**: Comparison sampling.
*   **`textureLoad(t: texture_2d<T>, coords: vec2i, level: i32) -> vec4<T>`**: Direct texel fetch.
*   **`textureStore(t: texture_storage_2d<F, write>, coords: vec2i, value: vec4<T>)`**: Write to storage texture.

### Atomic Built-ins
Operate on `atomic<i32>` or `atomic<u32>`.
*   **`atomicLoad(p: ptr<AS, atomic<T>>) -> T`**
*   **`atomicStore(p: ptr<AS, atomic<T>>, v: T)`**
*   **`atomicAdd(p, v)`, `atomicSub(p, v)`, `atomicMax(p, v)`, `atomicMin(p, v)`**
*   **`atomicAnd(p, v)`, `atomicOr(p, v)`, `atomicXor(p, v)`**
*   **`atomicExchange(p, v) -> T`**
*   **`atomicCompareExchangeWeak(p, cmp, v) -> __atomic_compare_exchange_result<T>`**

### Synchronization and Barriers
*   **`storageBarrier()`**: Synchronizes access to `storage` memory within a workgroup.
*   **`workgroupBarrier()`**: Synchronizes execution and `workgroup` memory within a workgroup.
*   **`textureBarrier()`**: (Language extension) Synchronizes `storage` texture access.

### Derivatives (Fragment Only)
*   **`dpdx(e: T)`, `dpdy(e: T)`**: Partial derivative with respect to screen space X or Y.
*   **`fwidth(e: T)`**: Sum of absolute derivatives (`abs(dpdx(e)) + abs(dpdy(e))`).

### Data Manipulation
*   **`bitcast<T>(v: S) -> T`**: Reinterprets the bits of `v` as type `T`.
*   **`pack4x8snorm(v: vec4f) -> u32`**: Packs 4 floats into a u32.
*   **`unpack4x8snorm(v: u32) -> vec4f`**: Unpacks u32 into 4 floats.

## 15. Appendix: Conversion Ranks
When matching function overloads, WGSL uses a conversion rank system to find the best match.

| Source | Destination | Rank |
| :--- | :--- | :--- |
| `T` | `T` | 0 (Identity) |
| `AbstractFloat` | `f32` | 1 |
| `AbstractFloat` | `f16` | 2 |
| `AbstractInt` | `i32` | 3 |
| `AbstractInt` | `u32` | 4 |
| `AbstractInt` | `AbstractFloat` | 5 |
| `AbstractInt` | `f32` | 6 |
| `AbstractInt` | `f16` | 7 |

Higher ranks are "less preferred" than lower ranks. A rank of infinity (not in table) means no conversion is possible.

