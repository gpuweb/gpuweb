# FP16 usages support

**Roadmap:** This draft extension is **on the standards track**, but is a work in progress. User agents must not implement/expose these features until they are merged into the main specs.

**GPUFeatureName:** `"fp16-in-shader-and-buffer"`

## WebGPU Spec Changes

- Add `"fp16-in-shader-and-buffer"` in `enum GPUFeatureName`.
- Modify the 4th paragraph of constants in [10.1.2. GPUProgrammableStage](https://www.w3.org/TR/webgpu/#GPUProgrammableStage) section:
  > Values are specified as `GPUPipelineConstantValue`, which is a `double` which is converted to the WGSL data type of the corresponding pipeline-overridable constant (`bool`, `i32`, `u32`, or `f32`) via [an IDL value](https://webidl.spec.whatwg.org/#dfn-convert-ecmascript-to-idl-value) ([boolean](https://webidl.spec.whatwg.org/#idl-boolean), [long](https://webidl.spec.whatwg.org/#idl-long), [unsigned long](https://webidl.spec.whatwg.org/#idl-unsigned-long), or [float](https://webidl.spec.whatwg.org/#idl-float)). If the "fp16-in-shader-and-buffer" feature is enabled, a  pipeline-overridable constant may be of WGSL data type `f16`. The specified `GPUPipelineConstantValue` for a pipeline-overridable constant of `f16` is convert to [float](https://webidl.spec.whatwg.org/#idl-float) via [an IDL value](https://webidl.spec.whatwg.org/#dfn-convert-ecmascript-to-idl-value), then convert to WGSL type `f16` via IEEE-754 binary32 to IEEE-754 binary16 conversion.
- Add a `"fp16-in-shader-and-buffer"` section in ["Feature Index"](https://www.w3.org/TR/webgpu/#feature-index) chapter with the following functionality defination.
    > Using "`enable f16;`" directive in WGSL code is allowed if and only if the `"fp16-in-shader-and-buffer"` feature is enabled; otherwise using it must result in a compilation error when creating shader module.

## WGSL Spec Changes

### [4. Types](https://www.w3.org/TR/WGSL/#types)

<!--
Change the example to include the new-added f16 type.
-->

- Modify the third paragragh as below:
	> For example, the mathematical number 1 corresponds to four distinct values in WGSL:
	> - the 32-bit signed integer value 1,
	> - the 32-bit unsigned integer value 1u,
	> - the 32-bit floating point value 1.0, and
	> - the 16-bit floating point value 1.0.

### [4.1. Type Checking](https://www.w3.org/TR/WGSL/#type-checking-section)

<!--
Change the example to include the new-added f16 types.
-->

- Modify the 8th paragragh as below:
	> Each distinct type parameterization for a type rule is called an overload. For example, unary negation (an expression of the form -e) has twelve overloads, because its type rules are parameterized by a type T that can be any of:
	> - i32
	> - vec2\<i32\>
	> - vec3\<i32\>
	> - vec4\<i32\>
	> - f32
	> - vec2\<f32\>
	> - vec3\<f32\>
	> - vec4\<f32\>
	> - f16
	> - vec2\<f16\>
	> - vec3\<f16\>
	> - vec4\<f16\>

### [4.2. Plain Types](https://www.w3.org/TR/WGSL/#floating-point-types)

<!--
Define the f16 type along with other existing types, allow f16 matrix, and point out that using f16 with unsupported devices will result in a WGSL error.
-->

- Add a paragraph at the end of section [4.2.3. Floating Point Type](https://www.w3.org/TR/WGSL/#floating-point-types):
    > The **_f16_** type is the set of 16-bit floating point values of the IEEE-754 binary16 (half precision) format. 
        Using **_f16_** type is allowed if and only if the program has an "enable f16;" directive, otherwise there is a shader-creation error. The support for "enable f16;" directive is optional. See § 12.5 Floating Point Evaluation for details.
- Modify the section [4.2.4. Scalar Types](https://www.w3.org/TR/WGSL/#scalar-types):
	> The **_scalar_** types are bool, i32, u32, f16, and f32.

	> The **_numeric scalar_** types are i32, u32, f16, and f32.
	
	> The **_integer scalar_** types are i32 and u32.
- Modify the table in section [4.2.6 Matrix Types](https://www.w3.org/TR/WGSL/#matrix-types):
	> | Type | Description |
	> | - | - |
	> | mat*N*x*M*\<*T*\> | Matrix of *N* columns and *M* rows of type *T*, where *N* and *M* are both in {2, 3, 4}, and *T* must be f32 or f16. Equivalently, it can be viewed as *N* column vectors of type vec*M*\<*T*\>. |

### [4.3. Memory](https://www.w3.org/TR/WGSL/#memory)

<!--
Define the memory layout of f16 types, make using them in uniform/storage buffer well defined.
-->

- Add "`, T is i32, u32, or f32`" after the "`vec2<T>`", "`vec3<T>`" and "`vec4<T>`" in the *Alignment and size for host-shareable types* table in the section [4.3.7.1. Alignment and Size](https://www.w3.org/TR/WGSL/#alignment-and-size), and merge the following table into it:
    > | Host-shareable type *T* | AlignOf(*T*) | SizeOf(*T*) |
    > | - | - | - |
    > | f16 | 2 | 2 |
    > | vec2\<f16\> | 4 | 4 |
    > | vec3\<f16\> | 8 | 6 |
    > | vec4\<f16\> | 8 | 8 |
    > | mat2x2\<f16\> | 4 | 8 |
    > | mat2x3\<f16\> | 8 | 16 |
    > | mat2x4\<f16\> | 8 | 16 |
    > | mat3x2\<f16\> | 4 | 12 |
    > | mat3x3\<f16\> | 8 | 24 |
    > | mat3x4\<f16\> | 8 | 24 |
    > | mat4x2\<f16\> | 4 | 16 |
    > | mat4x3\<f16\> | 8 | 32 |
    > | mat4x4\<f16\> | 8 | 32 |
- Add the following f16 internal layout after the f32 layout in the section [4.3.7.4. Internal Layout of Values](https://www.w3.org/TR/WGSL/#internal-value-layout):
    > A value V of type f16 is represented in IEEE-754 binary16 format. It has one sign bit, 5 exponent bits, and 10 fraction bits. When V is placed at byte offset k of host-shared buffer, then:
    > * Byte k contains bits 0 through 7 of the fraction.
	> * Bits 0 through 1 of Byte k+1 contains bits 8 through 9 of the fraction.
	> * Bits 2 through 6 of byte k+1 contains bits 0 through 4 of the exponent.
	> * Bit 7 of byte k+1 contains the sign bit.
- Modify the *Alignment requirements of a host-shareable type for storage and uniform storage classes* table as below in the section [4.3.7.5. Storage Class Layout Constraints](https://www.w3.org/TR/WGSL/#storage-class-layout-constraints)
	> | Host-shareable type *S* | RequiredAlignOf(*S*, storage) | RequiredAlignOf(*S*, uniform) |
	> | - | - | - |
	> | i32, u32, f32, or f16 | AlignOf(*S*) | AlignOf(*S*) |
	> | atomic\<*T*\> | AlignOf(*S*) | AlignOf(*S*) |
	> | vec*N*\<*T*\> | AlignOf(*S*) | AlignOf(*S*) |
	> | mat*N*x*M*\<*T*\>, *T* is f16 or f32 | AlignOf(*S*) | AlignOf(*S*) |
	> | array\<*T*, *N*\> | AlignOf(*S*) | round(16, AlignOf(*S*)) |
	> | array\<*T*\> | AlignOf(*S*) | round(16, AlignOf(*S*)) |
	> | struct *S* | AlignOf(*S*) | round(16, AlignOf(*S*)) |

### [4.7. Type Declaration Grammar](https://www.w3.org/TR/WGSL/#type-declarations)

<!--
Add float16 type in the grammar.
-->

- Add the float16 item into the list, as shown below:
	> **_type_decl_** :
	>   | ident
	>   | bool
	>   | float32
	>   | float16
	>   | int32
	>   (...afterward omitted)

### [6.3. Type Constructor Expressions](https://www.w3.org/TR/WGSL/#type-constructor-expr)

<!--
Define the constructor of f16 tpyes by adding the scalar constructor and modifying the matrix constructors.
-->

- Merge the following table into the *Scalar constructor type rules* table in section [6.3. Type Constructor Expressions](https://www.w3.org/TR/WGSL/#type-constructor-expr):
	> | Precondition | Conclusion | Notes |
	> | - | - | - |
	> | *e*: f16 | f16(e) : f16 | Identity. |
- Modify the *Matrix constructor type rules* table in section [6.3. Type Constructor Expressions](https://www.w3.org/TR/WGSL/#type-constructor-expr) by:
    - In the "Precondition" column, replace all "*f32*" with "*T*", and add "*T* is *f32* or *f16*" at the end of each cell in this column
    - In the "Conclusion" column, replace all "*f32*" with "*T*"

### [6.4. Zero Value Expressions](https://www.w3.org/TR/WGSL/#zero-value-expr)

<!--
Add zero value expressions for f16 scalar, vector (inherited), and matrix along with other types.
-->

- Modify the second paragraph as below:
	> The zero values are as follows:
	> * `bool()` is `false`
	> * `i32()` is 0
	> * `u32()` is 0
	> * `f32()` is 0.0
	> * `f16()` is 0.0
	> * The zero value for an *N*-element vector of type *T* is the *N*-element vector of the zero value for *T*.
	> * The zero value for an *N*-column *M*-row matrix of `f32` or `f16` is the matrix of those dimensions filled with 0.0 entries.
	> * The zero value for a constructible N-element array with element type E is an array of N elements of the zero value for E.
	> * The zero value for a constructible structure type S is the structure value S with zero-valued members.
- Merge the following table into the *Scalar zero value type rules* table:
	> | Precondition | Conclusion | Notes |
	> | - | - | - |
	> |  | `f16()`: f16 | 0.0<br />Zero value |
- Modify the *Matrix zero type rules* table by:
    - In the "Precondition" column, add "*T* is f32 or f16" in each cell
    - In the "Conclusion" column, replace all "f32" with "*T*"

### [6.5. Conversion Expressions](https://www.w3.org/TR/WGSL/#conversion-expr)

<!--
Add conversion expressions between f16 types and others. The conversions between f16 and other non-float types follow the same behaviors as f32, and conversions between f16 and f32 scalar, vector and matrix follow the natural floating point value conversion behaviors.
-->

- Merge the following table into the *Scalar conversion type rules* table:
	> | Precondition | Conclusion | Notes |
	> | - | - | - |
	> | *e*: f16 | bool(*e*): bool | Coercion to boolean.<br />The result is false if *e* is 0.0 or -0.0, and true otherwise. In particular NaN and infinity values map to true. | 
	> | *e*: f16 | i32(*e*): i32 | Value conversion, rounding toward zero. | 
	> | *e*: f16 | u32(*e*): u32 | Value conversion, rounding toward zero. | 
	> | *e*: f16 | f32(*e*): f32 | Lossless value conversion.  | 
	> | *e*: bool | f16(*e*): f16 | Conversion of a boolean value to floating point<br/>The result is 1.0 if *e* is true and 0.0 otherwise. | 
	> | *e*: i32 | f16(*e*): f16 | Value conversion, including invalid cases. | 
	> | *e*: u32 | f16(*e*): f16 | Value conversion, including invalid cases. | 
	> | *e*: f32 | f16(*e*): f16 | Lossy value conversion. | 
- Merge the following table into the *Vector conversion type rules* table:
	> | Precondition | Conclusion | Notes |
	> | - | - | - |
	> | *e*: vec*N*\<f16\> | vec*N*\<bool\>(*e*): vec*N*\<bool\> | Component-wise coercion to boolean.<br />The result is false if *e* is 0.0 or -0.0, and true otherwise. In particular NaN and infinity values map to true. |
	> | *e*: vec*N*\<f16\> | vec*N*\<i32\>(*e*): vec*N*\<i32\> | Component-wise value conversion, rounding toward zero. |
	> | *e*: vec*N*\<f16\> | vec*N*\<u32\>(*e*): vec*N*\<u32\> | Component-wise value conversion, rounding toward zero. |
	> | *e*: vec*N*\<f16\> | vec*N*\<f32\>(*e*): vec*N*\<f32\> | Component-wise lossless value conversion. |
	> | *e*: vec*N*\<bool\> | vec*N*\<f16\>(*e*): vec*N*\<f16\> | Component-wise conversion of a boolean value to floating point<br />The result is 1.0 if *e* is true and 0.0 otherwise. |
	> | *e*: vec*N*\<i32\> | vec*N*\<f16\>(*e*): vec*N*\<f16\> | Component-wise value conversion, including invalid cases. |
	> | *e*: vec*N*\<u32\> | vec*N*\<f16\>(*e*): vec*N*\<f16\> | Component-wise value conversion, including invalid cases. |
	> | *e*: vec*N*\<f32\> | vec*N*\<f16\>(*e*): vec*N*\<f16\> | Component-wise lossy value conversion. |
- Add the following table named *Matrix conversion type rules* at the end of this section:
	> | Precondition | Conclusion | Notes |
	> | - | - | - |
	> | *e*: mat*N*x*M*\<f16\> | mat*N*x*M*\<f32\>(*e*): mat*N*x*M*\<f32\> | Component-wise lossless value conversion. |
	> | e: mat*N*x*M*\<f32\> | mat*N*x*M*\<f16\>(*e*): mat*N*x*M*\<f16\> | Component-wise lossy value conversion. |

### [6.6. Reinterpretation of Representation Expressions](https://www.w3.org/TR/WGSL/#bitcast-expr)

<!--
Only allow the identical bitcast for f16 scalar, and disallow bitcast between f16 scalar and other scalar types.
Allow bitcast for f16 vector and other types that have a same bits number.
-->

- Modify the *Bitcast type rules* table in this section to disable bitcast between f16 and other types:
	> | Precondition | Conclusion | Notes |
	> | - | - | - |
	> | *e*: *T*<br/>*T* is a numeric scalar or numeric vector type | bitcast\<*T*\>(*e*): *T* | Identity transform. Component-wise when *T* is a vector.<br/>The result is *e*. |
	> | *e*: *T1*<br/>*T1* is i32, u32, or f32<br/>*T2* is not *T1* and is i32, u32, or f32 | bitcast\<*T2*\>(*e*): *T2* | Reinterpretation of bits as *T2*.<br/>The result is the reinterpretation of the bits in *e* as a *T2* value. |
	> | *e*: vec*N*\<*T1*\><br/>*T1* is i32, u32, or f32<br/>*T2* is not *T1* and is i32, u32, or f32 | bitcast\<vec*N*\<*T2*\>\>(*e*): vec*N*\<*T2*\> | Component-wise reinterpretation of bits as T2.<br/>The result is the reinterpretation of the bits in *e* as a vec*N*\<*T2*\> value. |
- Merge the following table into the *Bitcast type rules* table in this section:
    > | Precondition | Conclusion | Notes |
	> | - | - | - |
	> | *e*: vec2&lt;f16&gt;<br/>*T* is i32, u32, or f32 | bitcast&lt;*T*&gt;(*e*): *T* | Reinterpretation of bits as *T*.<br/>The result is the reinterpretation of the 32 bits in *e* as a *T* value, following the internal layout rules. |
	> | *e*: *T*<br/>*T* is i32, u32, or f32 | bitcast&lt;vec2&lt;f16&gt;&gt;(*e*): vec2&lt;f16&gt; | Reinterpretation of bits as vec2&lt;f16&gt;.<br/>The result is the reinterpretation of the 32 bits in *e* as a vec2&lt;f16&gt; value, following the internal layout rules. |
	> | *e*: vec4&lt;f16&gt;<br/>*T* is i32, u32, or f32 | bitcast&lt;vec2&lt;*T*&gt;&gt;(*e*): vec2&lt;*T*&gt; | Reinterpretation of bits as vec2&lt;*T*&gt;.<br/>The result is the reinterpretation of the 64 bits in *e* as a vec2&lt;*T*&gt; value, following the internal layout rules. |
	> | *e*: vec2&lt;*T*&gt;<br/>*T* is i32, u32, or f32 | bitcast&lt;vec4&lt;f16&gt;&gt;(*e*): vec4&lt;f16&gt; | Reinterpretation of bits as vec4&lt;f16&gt;.<br/>The result is the reinterpretation of the 64 bits in *e* as a vec4&lt;f16&gt; value, following the internal layout rules. |

### [6.9. Arithmetic Expressions](https://www.w3.org/TR/WGSL/#arithmetic-expr)

<!--
Allow using f16 types for all arithmetic expressions.
-->

- Modify the *Unary arithmetic expressions* table:
    - In "Precondition" column, replace "*T* is i32, f32, vec*N*\<i32\> or vec*N*\<f32\>" with "*T* is i32, f32, f16, vec*N*\<i32\>, vec*N*\<f32\> or vec*N*\<f16\>"
- Modify the *Binary arithmetic expressions* table:
    - In "Precondition" column, replace all "*T* is i32, u32, f32, vec*N*\<i32\>, vec*N*\<u32\>, or vec*N*\<f32\>" with "*T* is i32, u32, f32, f16, vec*N*\<i32\>, vec*N*\<u32\>, vec*N*\<f32\>, or vec*N*\<f16\>"
- Modify the *Binary arithmetic expressions with mixed scalar and vector operands* table:
    - In "Precondition" column, replace the "*S* is one of f32, i32, u32" with "*S* is one of i32, u32, f32, f16"
- Modify the *Matrix arithmetic* table:
    - In "Precondition" column, replace all "f32" with "*T*", and add "*T* is f32 or f16" at the end of each cell in this column
    - In "Conclusions" column, replace all "f32" with "*T*"

### [6.10. Comparison Expressions](https://www.w3.org/TR/WGSL/#comparison-expr)

<!--
Allow using f16 types for all comparison expressions.
-->

- Modify the *Comparisons* table:
    - In "Precondition" column, replace all "*TF* is f32 or vec*N*\<f32\>" with "*TF* is f32, f16, vec*N*\<f32\> or vec*N*\<f16\>"

### [10.1. Enable Directive](https://www.w3.org/TR/WGSL/#enable-directive-section)

<!--
List the directive required by this (and others, in the future) extension.
-->

- Add a table named "Extension identifier" at the end of this section as below:
    > | Identifier | WebGPU extension name | Description |
    > | - | - | - |
    > | `f16` | `"fp16-in-shader-and-buffer"` | Keyword `f16` is valid if and only if this extension is enabled. |

### [12.5.1. Floating Point Accuracy](https://www.w3.org/TR/WGSL/#floating-point-accuracy)

<!--
Update the floating point accuracy requirement for f16, following the [Vulkan Spec](https://www.khronos.org/registry/vulkan/specs/1.2-khr-extensions/html/chap42.html#spirvenv-precision-operation).
m-->

- Modify the *Accuracy of expressions* table: 
    - In the first (head) row, split the "Accuracy" cell into two columns, respectively "Accuracy for f32" and "Accuracy for f16"
    - In the 5th row ("`x / y`"), split the cell in second column into two two cloumns, respectively "2.5 ULP for `|y|` in the range \[2^-126, 2^126\]" and "2.5 ULP for `|y|` in the range \[2^-14, 2^14\]"
- Modify the *Accuracy of built-in functions* table: 
    - In the first (head) row, split the "Accuracy" cell into two columns, respectively "Accuracy for f32" and "Accuracy for f16"
    - In both 5th and 6th rows ("`atan(x)`" and "`atan2(y,x)`"), split the cells in second columns into two cloumns, respectively "4096 ULP" and "5 ULP"
    - In both 9th and 37th rows ("`cos(x)`" and "`sin(x)`"), split the cells in second columns into two cloumns, respectively "Absolute error ≤ 2^-11 inside the range of \[-π, π\]" and "Absolute error ≤ 2^-7 inside the range of \[-π, π\]"
    - In both 14th and 15th rows ("`exp(x)`" and "`exp2(x)`"), split the cells in second columns into two cloumns, respectively "3 + 2 * |x| ULP" and "1 + 2 * |x| ULP"

### [12.5.2. Floating point conversion](https://www.w3.org/TR/WGSL/#floating-point-conversion)

<!--
Add f16 along with f32 as a valid WGSL type.
-->

- Modify the first paragraph as follow, and remove the note of binary16:
	> In this section, a floating point type may be any of:
	> * The f32 and f16 type in WGSL.
	> * A hypothetical type corresponding to a binary format defined by the IEEE-754 floating point standard.

### [14. Keyword Summary](https://www.w3.org/TR/WGSL/#keyword-summary)

<!--
Make `f16` a valid keyword.
-->

- Add following item into ["14.1.1. Type-defining Keywords"](https://www.w3.org/TR/WGSL/#type-defining-keywords), before "float32" (alphabet order).
    > **_float16_** : 
    > ` | 'f16'` 
- Remove "f16" from reserved words list in ["14.2. Reserved Words".](https://www.w3.org/TR/WGSL/#reserved-words)

### [16.3. Float built-in functions](https://www.w3.org/TR/WGSL/#float-builtin-functions)

<!--
Allow using f16 in all float built-in functions except for `quantizeToF16`, and define new built-in structure for the result of `frexp` and `modf` with f16 types.
-->

- Modify the table in this section by:
    - In every row except 11th ("`cross`"), 16th ("`faceForward`"), 20th ("`frexp`" with f32), 21th ("`frexp`" with vec*N*\<f32\>), 30th ("`mix(e1: T ,e2: T ,e3: f32 ) -> T`"), 31th ("`modf`" for f32), 32th ("`modf`" for vec*N*\<f32\>), 33th ("`normalize`"), 35th ("`quantizeToF16`"), 37th ("`reflect`"), 38th ("`refract`"), replace "T is f32 or vec*N*\<f32\>" with "T is f32, f16, vec*N*\<f32\>, or vec*N*\<f16\>" in the cell of "Parameterization" column.
    - In rows of 11th ("`cross`") and 33th ("`normalize`"), replace "T is f32" with "T is f32 or f16" in the cells of "Parameterization" column.
    - In rows of 16th ("`faceForward`"), 37th ("`reflect`"), and 38th ("`refract`"), replace "T is vec*N*\<f32\>" with "T is vec*N*\<f32\> or vec*N*\<f16\>" in the cell of "Parameterization" column.
    - In the 30th row ("`mix(e1: T ,e2: T ,e3: f32 ) -> T`"), modify the "Parameterization" cell into "*T1* is f32 or f16\<br/\>*T2* is vec*N*\<*T1*\>", modify the "Overload" cell into "`mix(e1: T2 ,e2: T2 ,e3: T1 ) -> T2`", replace "Same as mix(e1,e2,T(e3))" in the "Description" cell by "Same as mix(e1,e2,T2(e3))".
- Merge the following table into the table in this section:
    > <table>
    <thead>
    <tr><th>Parameterization</th><th>Overload</th><th>Description</th></tr>
    </thead>
    <tr>
    <td> T is f16 </td>
    <td> frexp(e:T) -> __frexp_result_f16 </td>
    <td> 
    
    Splits *e* into a significand and exponent of the form significand * 2^exponent. Returns the __frexp_result_f16 built-in structure, defined as if as follows:
    
    ```rust
    struct __frexp_result_f16 {
      sig : f16; // significand part
      exp : i32; // exponent part
    }
    ```
    The magnitude of the significand is in the range of [0.5, 1.0) or 0.
    </td>
    </tr>
    <tr>
    <td> T is vecN&lt;f16&gt; </td>
    <td> frexp(e:T) -> __frexp_result_vecN_f16 </td>
    <td> 
    
    Splits the component of *e* into a significand and exponent of the form significand * 2^exponent. Returns the __frexp_result_vecN_f16 built-in structure, defined as if as follows:
    
    ```rust
    struct __frexp_result_vecN_f16 {
      sig : vecN<f16>; // significand part
      exp : vecN<i32>; // exponent part
    }
    ```
    The magnitude of each component of the significand is in the range of [0.5, 1.0) or 0.
    </td>
    </tr>
    <tr>
    <td> T is f16 </td>
    <td> modf(e:T) -> __modf_result_f16 </td>
    <td> 
    
    Splits *e* into fractional and whole number parts. Returns the __modf_result_f16 built-in structure, defined as if as follows:
    
    ```rust
    struct __modf_result_f16 {
      fract : f16; // fractional part
      whole : f16; // whole part
    }
    ```
    </td>
    </tr>
    <tr>
    <td> T is vecN&lt;f16&gt; </td>
    <td> modf(e:T) -> __modf_result_vecN_f16 </td>
    <td> 
    
    Splits the component of *e* into fractional and whole number parts. Returns the __modf_result_vecN_f16 built-in structure, defined as if as follows:
    
    ```rust
    struct __modf_result_vecN_f16 {
      fract : vecN<f16>; // fractional part
      whole : vecN<f16>; // whole part
    }
    ```
    The magnitude of each component of the significand is in the range of [0.5, 1.0) or 0.
    
    </td></table>
    

### [16.5. Matrix built-in functions](https://www.w3.org/TR/WGSL/#matrix-builtin-functions)

<!--
Allow using f16 matrix in matrix built-in functions.
-->

- Modify the table in this section by:
    - In "Parameterization" column, replace all "T is f32" with "T is f32 or f16".

### [16.6. Vector built-in functions](https://www.w3.org/TR/WGSL/#vector-builtin-functions)

<!--
Allow using f16 vector in vector built-in functions.
-->

- Modify the table in this section by:
    - In "Parameterization" column, replace the "T is f32" with "T is f32 or f16" in the second row.

### [16.10. Data packing built-in functions](https://www.w3.org/TR/WGSL/#pack-builtin-functions)

<!--
Allow using f16 along with f32 in all data packing built-in functions.
-->

- Replace the table in this section by the following table:
    > | Parameterization | Overload | Description |
    > | - | - | - |
    > | T is f32 or f16 | `pack4x8snorm(e: vec4<T>) -> u32` | Converts four normalized floating point values to 8-bit signed integers, and then combines them into one u32 value.<br />Component e[i] of the input is converted to an 8-bit twos complement integer value ⌊ 0.5 + 127 × min(1, max(-1, e[i])) ⌋ which is then placed in bits 8 × i through 8 × i + 7 of the result. |
    > | T is f32 or f16 | `pack4x8unorm(e: vec4<T>) -> u32` | Converts four normalized floating point values to 8-bit unsigned integers, and then combines them into one u32 value.<br/>Component e[i] of the input is converted to an 8-bit unsigned integer value ⌊ 0.5 + 255 × min(1, max(0, e[i])) ⌋ which is then placed in bits 8 × i through 8 × i + 7 of the result. |
    > | T is f32 or f16 | `pack2x16snorm(e: vec2<T>) -> u32` | 	Converts two normalized floating point values to 16-bit signed integers, and then combines them into one u32 value.<br/>Component e[i] of the input is converted to a 16-bit twos complement integer value ⌊ 0.5 + 32767 × min(1, max(-1, e[i])) ⌋ which is then placed in bits 16 × i through 16 × i + 15 of the result. |
    > | T is f32 or f16 | `pack2x16unorm(e: vec2<T>) -> u32` | Converts two normalized floating point values to 16-bit unsigned integers, and then combines them into one u32 value.<br/>Component e[i] of the input is converted to a 16-bit unsigned integer value ⌊ 0.5 + 65535 × min(1, max(0, e[i])) ⌋ which is then placed in bits 16 × i through 16 × i + 15 of the result. |
    > |  | `pack2x16float(e: vec2<f32>) -> u32` | Converts two floating point values to half-precision floating point numbers, and then combines them into one u32 value.<br/>Component e[i] of the input is converted to a IEEE-754 binary16 value, which is then placed in bits 16 × i through 16 × i + 15 of the result. See § 12.5.2 Floating point conversion. |
    > |  | `pack2x16float(e: vec2<f16>) -> u32` | Combines two f16 floating point numbers into one u32 value. Component e[i] of the input is placed in bits 16 × i through 16 × i + 15 of the result. |


## References

- <https://github.com/gpuweb/gpuweb/issues/2512>
