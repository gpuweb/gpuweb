# Subgroup Matrix

* Status: [Draft](README.md#status-draft)
* Created: 2025-10-02
* Issue: [#4195](https://github.com/gpuweb/gpuweb/issues/4195)

Note: This proposal is largely copied from the design of the
[Chromium experimental
feature](https://dawn.googlesource.com/dawn/+/refs/heads/main/docs/dawn/features/subgroup_matrix.md).
Also see the
[slides](https://docs.google.com/presentation/d/1wiy3-ar58ah1W9Qc5trd0gG7fwCo93IJ9YCtQoR6W6c/edit?usp=sharing)
presented at the 2025-09 WebGPU F2F.

## Background

Subgroup matrices are an abstract matrix data type. Computations on subgroup matrices utilize the SIMD nature of the GPU and are distributed among multiple invocations. Subgroup matrices are a critical primitive for ML workloads: Large matrix-multiply operations can be decomposed into many matrix multiplies over small sub-blocks of the larger matrices.  (Note that 1x1 convolutions are mathematically the same as matrix multiply.)



*   Backgrounder: https://docs.nvidia.com/deeplearning/performance/dl-performance-matrix-multiplication/index.html

Many GPUs now support this feature, with various parameterizations of block sizes, component data types, and result types.  In the following, a typical block matrix multiply operation is:


    Accum = A * B

or

	Accum = A * B + Accum


    where  Accum is M-row, N-column,


    A is M-row K-column,


    B is K-row, N-column.


## Target API support


### SPIR-V/Vulkan

Originally introduced as an Nvidia vendor extension ([SPV_NV_cooperative_matrix](https://github.khronos.org/SPIRV-Registry/extensions/NV/SPV_NV_cooperative_matrix.html) and [VK_NV_cooperative_matrix](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#VK_NV_cooperative_matrix)). NVIDIA presented an overview of the feature and its benefits, in a 2019 blog post and a [2022 presentation](https://www.khronos.org/assets/uploads/developers/presentations/Cooperative_Matrix_May22.pdf), and [optimization guide](https://docs.nvidia.com/deeplearning/performance/dl-performance-matrix-multiplication/index.html). The functionality has since been standardized as [SPV_KHR_cooperative_matrix](https://github.khronos.org/SPIRV-Registry/extensions/KHR/SPV_KHR_cooperative_matrix.html) and [VK_KHR_cooperative_matrix](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#VK_KHR_cooperative_matrix).

The Vulkan extension has two feature bits:

*   cooperativeMatrix: basic feature support
*   cooperativeMatrixRobustBufferAccess: robust buffer support for cooperative matrix load and store (usual caveats).

There is a supported stages property in <code>[VkPhysicalDeviceCooperativeMatrixPropertiesKHR](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#VkPhysicalDeviceCooperativeMatrixPropertiesKHR)</code>, but I’ve only ever seen compute supported.

OpTypeCooperativeMatrixKHR represents the abstract type. It parameterized as follows:

*   Component type: Matrix element type (must be a numerical scalar) (Float16/32/64, S/UInt8/16/32/64 currently)
*   Scope: the scope of operations on the type (Device, QueueFamily, Workgroup, or Subgroup)
*   Rows: Number of rows
*   Columns: Number of columns
*   Use: an enum specifying which kind of matrix this is used as:
    *   MatrixAKHR: LHS of a multiply (M rows x K columns)
    *   MatrixBKHR: RHS of a multiply (K rows x N columns)
    *   MatrixAccumulatorKHR: result of multiply-accumulate (M rows x N columns)

SPIR-V can represent a wide variety of cooperative matrices, but actual devices only support a subset of parameterizations. These are queried from the API by calling [vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR). It returns a linked list of [valid enumerations](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#VkCooperativeMatrixPropertiesKHR). Preferred variants are listed earlier in the chain. At least one entry in the list must have power of two values for all of MSize, KSize, and NSize. The enumerations indicate whether they support saturating accumulation. Because the type is abstract it can only be stored in the Function and Private storage classes. Special load and store instructions are used to translate to/from backing memory.

The fundamental operation is OpCooperativeMatrixMulAddKHR. It performs a multiply-accumulate operation. It requires consistent values of scope, M, N, and K for all types. The component types may differ, the operations occur using the result type. Signedness of results and operands is indicated using the Cooperative Matrix Operands (as is saturating accumulation). The result is undefined if saturating accumulation is used, but intermediate results overflow (same as integer dot product).

OpCooperativeMatrixLoadKHR and OpCooperativeMatrixStoreKHR share the following operands:

*   Pointer: a logical pointer into an array (stride is ignored) (limited to Workgroup, StorageBuffer, and PhysicalStorageBuffer storage classes in Vulkan)
*   Memory Layout: an enum for row- or column-majorness
*   Stride: an optional operand indicating the stride between elements (aligned to min(16, align(col/row))).  The stride counts the number of elements in the pointee type; it is not a byte count.  For example, if the pointee type of the Pointer argument is 2xf16 then a stride of 8 translates to a byte stride of 8x (2x2) bytes.

These operations convert to/from the abstract matrix type and memory. The operands **must** be uniform values for the scope.

Additional operations:

*   OpCooperativeMatrixLengthKHR: Number of accessible components from an invocation for a given cooperative matrix type.
*   Conversions: All standard conversions are allowed (FToU, UToF, FToS, SToF, U, S, F, bitcast).
*   Arithmetic: Negate, add, sub, mul, div using the opcode for the appropriate component type. Additionally, OpMatrixTimesScalar is also supported.
*   Constants: OpCompositeConstruct and OpConstantComposite can provide a single fill value for a cooperative matrix.

All operations involving a cooperative matrix **must** only be executed in uniform control flow for scope of the operation.

Cooperative matrices **require** the Vulkan memory model in SPIR-V.

OpTypeCooperativeMatrixKHR can only be instantiated by a variable in the Function or Private storage classes.


### HLSL/Direct3D

Microsoft originally proposed a feature, WaveMatrices, for
[SM6.8](https://microsoft.github.io/DirectX-Specs/d3d/HLSL_SM_6_8_WaveMatrix.html)
as experimental.
This experimental feature was later withdrawn.

Microsoft is now targeting a new feature, linalg::Matrix, for SM6.10.
See https://github.com/microsoft/hlsl-specs/pull/556.
The API side will likely look similar to the WaveMatrix feature, but it is not
included in the proposal yet.

The HLSL feature relies on SFINAE to provide a templated type for matrices.
The type is templated with the following parameters:
* ComponentType: Type of the matrix elements
* M: Number of rows
* N: Number of columns
* Use: Use of the matrix: A, B, or Accumulator
* Scope: The scope of the matrix: thread, wave, or threadgroup

The level of functionality provided is a bit wider than that of SPV_KHR_cooperative_matrix.
Additional functionality includes:
* More type support: 16- and 64-bit integers, unorm and snorm formats.
* Scope: Also supports workgroup scope matrices.
* Conversions: A <-> B, A/B <-> Accumulator
* Coordinates: Can access matrix coordinates when iterating over each thread's values.

### MSL/Metal

Apple calls them simdgroup matrices and support has existed since MSL 2.3.
Not all Metal devices support it (Apple7+ in the [feature set](https://developer.apple.com/metal/Metal-Feature-Set-Tables.pdf)).
Intel-based Macs and many iPads are excluded.
The supported devices include iPhone 12+, some newer iPads, and the M1 and later macs.  Apple7 is A14 Bionic, released in 2020.

MSL support a small number of matrix variants:

*   simdgroup_float8x8
*   simdgroup_half8x8
*   simdgroup_bfloat8x8 (MSL 3.1)

The simdgroup_float8x8 and simdgroup_half8x8 types are equivalent to a SPIR-V 8x8 cooperative matrix with Subgroup scope and corresponding component type. Unlike SPIR-V and HLSL, MSL does not specialize the matrices based on the use.

MSL also has more limited supported operations on simdgroup matrices. For load/store/creation:

*   simdgroup_matrix<_T_, _M_, _N_>: Create diagonal matrix with single value.
*   make_filled_simdgroup_matrix<_T_, _M_, _N_>: Create single value filled matrix.
*   simdgroup_load/store: specify stride, layout (via transpose), and an offset (via origin)

Similar to SPIR-V the device or threadgroup pointer points to a matrix component type.

MSL supports multiply and multiply-accumulate (non-saturating) arithmetic operations.

All functions **must** be called from simdgroup uniform control flow. **Presumably** load and store parameter values **must** be simdgroup uniform though I can’t see this called out in the spec.

MSL allows interfaces to be declared as simdgroup_matrix, but no operators exist for them to make them usable. Effectively, this limits them to function storage.


### SYCL

SYCL is a single-source CPU/GPU compute language, and may reflect support among GPU hardware, at least as exposed through OpenCL.

SYCL has a corresponding proposal, using the terminology “joint matrix”. See https://github.com/intel/llvm/blob/sycl/sycl/doc/extensions/experimental/sycl_ext_oneapi_matrix/sycl_ext_oneapi_matrix.asciidoc


## Proposal


### WGSL


#### Enable Extension

Add a new enable extension, `subgroup_matrix`.
Enables the declaration of subgroup_matrix types, related built-in functions,
and limited use of some scalar types (u8 and i8).
Implicitly depends on subgroups.
WGSL does not require any subgroups enable, but the API does.


#### Types

Add new types:

*   subgroup_matrix_left<_T_, _K_, _M_>: M rows x K columns matrix of T components.
*   subgroup_matrix_right<_T_, _N_, _K_>: K rows x N columns matrix of T components
*   subgroup_matrix_result<_T_, _N_, _M_>: M rows x N columns matrix of T components
*   M, N, and K are const-expressions of positive integer values
    *   Similar to arrays, two subgroup matrices are the same if:
        *   They are the same base type
        *   They have the same component type
        *   The have matching row counts
        *   The have matching column counts
*   T is the component type and must be one of the entries in the table
    *   The scalar shader type is the associated type usable in the shader code for scalar operations and data representation in memory
    *   Can be expanded in the future to support more types (e.g. bfloat16) via new enables.
    *   The u8 and i8 cases are predeclared types that are not otherwise usable in WGSL. For layout calculations, they are of size 1 byte and have an alignment requirement of 1 byte.

| Type | Extra Enable | Element Stride (bytes) | Shader Scalar Type | Min Value | Max Value |
| ---- | ------------ | ---------------------- | ------------------ | --------- | --------- |
| f32  |              | 4                      | f32                |           |           |
| f16  | f16          | 2                      | f16                |           |           |
| u32  |              | 4                      | u32                |           |           |
| i32  |              | 4                      | i32                |           |           |
| u8   |              | 1                      | u32                | 0         | 255       |
| i8   |              | 1                      | i32                | -128      | 127       |

These types are not considered “composite” in the WGSL taxonomy, because they
are not decomposable.
You can’t reference a sub-vector or a single component.
The numeric dimensions must be const-expressions.
These types cannot be part of any interface; they can only be instantiated
in the Function address space.
They are plain types (similar to atomics) so that they can be included in
composite types.
An important use case is to make arrays of these matrices.

It is a pipeline-creation error if any matrix type is not included in a
supported `GPUSubgroupMatrixConfig`, `config`,  on the device:

*   For `subgroup_matrix_left`:
    *   `M` equals `config.M`
    *   `K` equals `config.K`
    *   `T` matches `config.componentType`
*   For `subgroup_matrix_right`:
    *   `K` equals `config.K`
    *   `N` equals `config.N`
    *   `T` matches `config.componentType`
*   For `subgroup_matrix_result`:
    *   `M` equals `config.M`
    *   `N` equals `config.N`
    *   `T` matches `config.resultType`

Why use a “left” and “right” matrix type, instead of a single matrix type like Metal has?

*   D3D and Vulkan both need them.
*   There is no free transpose operation.
    If you had a free transpose, then you can take advantage of:
    A\* B = transpose(transpose(B)\*transpose(A)).
    I haven’t seen a transpose operation in APIs or hardware specs.


#### Variables

A variable containing a subgroup matrix can only be instantiated in Function
address space.
(This limitation comes from SPIR-V and Metal).
These variables are meant to be used as very temporary scratch space.

#### Loading and storing

Builtin functions are used to load and store subgroup matrix values from
variables in workgroup and storage address spaces.
The builtins do two things:

*   Map matrix row and column indices to external memory locations.
    This mapping has two parameters: majorness (row-major, or column-major),
    and an integer Stride.
    Let Base be the byte address of the start of the external matrix, i.e.
    where the [0,0]’th element of the matrix is stored.
    Then
    *   For row-major:
        *   Matrix entry [r,c] maps to the sizeof(T) bytes located at Base + Stride\*r\*sizeof(T) + sizeof(T)\*c
        *   Stride >= number of matrix columns.
    *   For column-major:
        *   Matrix entry [r,c] maps to the sizeof(T) bytes located at Base + Stride\*c\*sizeof(T) + sizeof(T)\*r
        *   Stride >= number of matrix rows.
*   Reinterpret data values between the shader scalar type and the external
    component type T, when those types differ.

For a subgroup_matrix_left/right/result&lt;T, Cols, Rows>, loads and stores are
out-of-bounds if the length of the array of the pointer argument is less than
Offset + Stride \* Rows\* Cols.


#### Attributes

Add an additional error condition to `workgroup_size`.
It is a pipeline-creation error if the x dimension is not a multiple of
`GPUAdapterInfo.subgroupMaxSize` and the shader statically accesses any
subgroup matrix.

Note: this is where the requirement on the subgroups feature stems from in
practice.

*Issue:* A developer is concerned this is too restrictive, and does not allow
for configurations that achieve peak performance. They suggest constraining
the workgroup size x dimension to be a multiple of the device _minimum_ subgroup size.
* Reply: It would be nicer to say the x dimension is a multiple of the selected
workgroup size, but there is no way to portably constrain it that way.
Metal can query the subgroup size of a pipeline, but Vulkan and D3D cannot.
Vulkan and D3D can specify a subgroup size, but Metal cannot.

See https://github.com/gpuweb/gpuweb/pull/5335#discussion_r2408982867

#### Expressions

Supported expressions:

*   Parenthesization
*   Identifier expressions
*   Indirection
*   Address-of
*   Function call expression
*   Type expressions

Explicitly not supported:

*   Decomposition expressions

Possible future expansion:

*   Arithmetic expressions


#### Built-in Values

Pragmatically speaking, this feature depends on the `subgroup_id` feature.

#### Built-in Functions

Calls to these functions:

*   Must only be used in a compute shader stage.
*   Trigger a `subgroup_matrix_uniformity` diagnostic if uniformity analysis
    cannot prove the call is in subgroup uniform control flow.


##### Value constructors

**Overloads**:
```rust
@must_use fn T(value : S) -> T
@must_use fn T() -> T
```

**Preconditions**:<br>
T is a subgroup matrix type whose shader scalar type is S.

**Description**:<br>
Create a subgroup matrix filled with value.

When no value is provided, use S().

Triggers a `subgroup_matrix_uniformity` diagnostic if
uniformity analysis cannot prove value is a subgroup uniform value.

##### Load/store functions

See Loading and Storing above.

**Overload**:
```rust
@must_use fn
subgroupMatrixLoad<T>(p : ptr<AS, SA, AM>,
                      offset : u32,
                      col_major : bool,
                      stride : u32) -> T
```

**Preconditions**:<br>
T is a subgroup matrix type with shader scalar type S.<br>
SA is an array with type S.<br>
AS is storage or workgroup.<br>
AM is read or read_write.

**Description**:<br>
Load a subgroup matrix from p, offset elements from the start of the array.

col_major must be a const-expression.

Triggers a `subgroup_matrix_uniformity` diagnostic if
uniformity analysis cannot prove p, offset, or stride are subgroup uniform
values.

stride counts elements of the component type of T.
Behavior is undefined if stride is less than:

* The number of rows of T if col_major is true
* The number of columns of T is col_major is false


**Overload**:<br>
```rust
fn subgroupMatrixStore(p : ptr<AS, SA, AM>,
                       offset : u32,
                       value : T,
                       col_major : bool,
                       stride : u32)
```

**Preconditions**:<br>
T is a subgroup matrix type whose scalar shader type is S.<br>
SA is an array with element type S.<br>
AS is storage or workgroup.<br>
AM is write or read_write.

**Description**:<br>
Store the subgroup matrix value into p, offset elements from the start of the array.

col_major must be a const-expression.

Triggers a `subgroup_matrix_uniformity` diagnostic if
uniformity analysis cannot prove p, offset, value, or stride are subgroup
uniform values.

stride counts elements of the component type of T.
Behavior is undefined if stride is less than:

* The number of rows of T if col_major is true
* The number of columns of T is col_major is false

##### Matrix arithmetic functions

The operands of a subgroup matrix arithmetic function comprise a **supported
subgroup matrix configuration** if the device has a `GPUSubgroupMatrixConfig`,
`config`, such that all operand types match as below:

*   For `L`:
    *   `M` equals `config.M`
    *   `K` equals `config.K`
    *   `T` matches `config.componentType`
*   For `R`:
    *   `K` equals `config.K`
    *   `N` equals `config.N`
    *   `T` matches `config.componentType`
*   For `RT`:
    *   `M` equals `config.M`
    *   `N` equals `config.N`
    *   `TR` matches `config.resultType`

**Overload**:
```rust
@must_use fn
subgroupMatrixMultiply<RT>(left : L, right : R) -> RT
```

**Preconditions**:<br>
L is a subgroup_matrix_left<T, M, K>.<br>
R is a subgroup_matrix_right<T, K, N>.<br>
RT is a subgroup_matrix_result<TR, M, N>.

**Description**:<br>
Matrix multiply.

It is a pipeline-creation error if L, R, and RT do not comprise a supported
subgroup matrix configuration.

Triggers a `subgroup_matrix_uniformity` diagnostic if
uniformity analysis cannot prove left or right are subgroup uniform values.

**Overload**:
```rust
@must_use fn
subgroupMatrixMultiplyAccumulate<RT>(left : L,
                                     right : R,
                                     acc : RT) -> RT
```

**Preconditions**:<br>
L is a subgroup_matrix_left<T, M, K>.<br>
R is a subgroup_matrix_right<T, K, N>.<br>
RT is a subgroup_matrix_result<TR, M, N>.

**Description**:<br>
Matrix multiply add (left * right + acc).

It is a pipeline-creation error if L, R, and RT do not comprise a supported
subgroup matrix configuration.

Triggers a `subgroup_matrix_uniformity` diagnostic if
uniformity analysis cannot prove left or right are subgroup uniform values.

##### Scalar arithmetic functions

These functions are useful for operations such as applying biases to a model.

**Overload**:
```rust
@must_use fn
subgroupMatrixScalarAdd(matrix : M, value : S) -> M
```

**Preconditions**:<br>
M is a subgroup matrix type with scalar shader type S.

**Description**:<br>
Scalar addition.

value is clamped to a valid range for the component type of M and then added to
each element of matrix.

Triggers a `subgroup_matrix_uniformity` diagnostic if
uniformity analysis cannot prove matrix or value are subgroup uniform values.

**Overload**:
```rust
@must_use fn
subgroupMatrixScalarSubtract(matrix : M, value : S) -> M
```

**Preconditions**:<br>
M is a subgroup matrix type with scalar shader type S.

**Description**:<br>
Scalar subtraction.

value is clamped to a valid range for the component type of M and then added to
each element of matrix.

Triggers a `subgroup_matrix_uniformity` diagnostic if
uniformity analysis cannot prove matrix or value are subgroup uniform values.

**Overload**:
```rust
@must_use fn
subgroupMatrixScalarMultiply(matrix : M, value : S) -> M
```

**Preconditions**:<br>
M is a subgroup matrix type with scalar shader type S.

**Description**:<br>
Scalar multiplication.

value is clamped to a valid range for the component type of M and then added to
each element of matrix.

Triggers a `subgroup_matrix_uniformity` diagnostic if
uniformity analysis cannot prove matrix or value are subgroup uniform values.


**REMOVED** (in an attempt to be safely forward compatible if Metal adds integral components, but no other operators)

**Overload**:
```rust
@must_use fn
subgroupMatrixScalarDivide(matrix : M, value : S) -> M
```

**Preconditions**:<br>
~~M is a subgroup matrix type with scalar shader type S.~~

**Description**:<br>
~~Scalar division.~~

~~value is clamped to a valid range for the component type of M and then added to
each element of matrix.~~

~~Triggers a `subgroup_matrix_uniformity` diagnostic if
uniformity analysis cannot prove matrix or value are subgroup uniform values.~~

#### Uniformity

Subgroup matrices are an abstraction of data spread among the invocations in a
subgroup.
As such the built-in functions must only be called from subgroup uniform
control flow.
Additionally, most of the parameter values must also be subgroup uniform
values.

WGSL does not currently represent subgroup uniformity and empirical testing
shows that implementations do not provide reliable reconvergence.
Vulkan backends that implement VK_KHR_shader_subgroup_uniform_control_flow or,
even better, VK_shader_maximal_reconvergence would be able to make enabling the
analysis at other scopes reasonable, but that is not portable.

For this extension we should add a diagnostic, `subgroup_matrix_uniformity`,
that defaults to `error`.
This diagnostic would be triggered based on workgroup uniformity violations (if
the control is not `off`) for all subgroup matrix built-in functions.
This allows applications some control.
It is likely that most use cases would satisfy workgroup uniformity.

**TODO**: Should we add subgroup uniformity analysis?
If so, how strict should it be as it is mainly a linting help.


#### Floating-point Accuracy

`subgroupMatrixLoad` and `subgroupMatrixStore` should be bit preserving.
ULPs are undefined for other operations.


### API

New GPUFeatureName `subgroup-matrix`

*   Requires `subgroups` (for maxSubgroupSize)
*   Vulkan:
    *   <code>[vkPhysicalDeviceCooperativeMatrixFeaturesKHR](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#VkPhysicalDeviceCooperativeMatrixFeaturesKHR)::cooperativeMatrix</code> is <code>VK_TRUE</code>
    *   <code>[vkPhysicalDeviceCooperativeMatrixPropertiesKHR](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#VkPhysicalDeviceCooperativeMatrixPropertiesKHR)::cooperativeMatrixSupportedStages</code> includes <code>VK_SHADER_STAGE_COMPUTE_BIT</code>
    *   The [supported configurations](?tab=t.0#bookmark=id.x7vevmm1vqtf) list is non-empty
    *   <code>[vkPhysicalDeviceVulkanMemoryModelFeatures](https://registry.khronos.org/vulkan/specs/latest/html/vkspec.html#VkPhysicalDeviceVulkanMemoryModelFeatures)::vulkanMemoryModel</code> is <code>VK_TRUE</code>
    *   <code>[subgroupSizeControl](https://registry.khronos.org/vulkan/specs/latest/html/vkspec.html#features-subgroupSizeControl)</code>feature must be enabled
    *   [computeFullSubgroups](https://registry.khronos.org/vulkan/specs/latest/html/vkspec.html#features-computeFullSubgroups) feature must be enabled
    *   Vulkan pipelines will need to be compiled with <code>VK_PIPELINE_SHADER_STAGE_CREATE_ALLOW_VARYING_SUBGROUP_SIZE_BIT</code> and <code>VK_PIPELINE_SHADER_STAGE_CREATE_REQUIRE_FULL_SUBGROUPS_BIT</code>, or the SPIR-V module must be version 1.6 or later
*   Metal:
    *   Family is Apple 7+
*   D3D: **TODO**

New immutable array, <code>subgroupMatrixConfigs</code>, added to <code>GPUAdapterInfo</code>.


```json
partial interface GPUAdapterInfo {
  [SameObject] readonly attribute FrozenArray<GPUSubgroupMatrixConfig> subgroupMatrixConfigs;
};

enum GPUSubgroupMatrixComponentType {
  "f32",
  "f16",
  "u32",
  "i32",
  "u8",
  "i8",
};

interface GPUSubgroupMatrixConfig {
  readonly attribute GPUSubgroupMatrixComponentType componentType;
  readonly attribute GPUSubgroupMatrixComponentType resultComponentType;
  readonly attribute unsigned long M;
  readonly attribute unsigned long N;
  readonly attribute unsigned long K;
};
```



#### Validation

No specific API validation is necessary; however, it is likely easier to
implement the pipeline-creation error checks in Dawn by adding the subgroup
matrix configurations to the shader reflection information.

WGSL pipeline-creation checks (repeated for ease of reference):

*   All subgroup matrix types are part of a `GPUSubgroupMatrixConfig`
*   All subgroup matrix operands in `subgroupMatrixMultiply` and
    `subgroupMatrixMultipleAccumulate` are part of a single
    `GPUSubgroupMatrixConfig`
*   The x-dimension of `workgroup_size` is a multiple of
    `GPUSupportedLimits::maxSubgroupSize`


### Mapping


#### Types

| Type | SPIR-V<sup>1,2</sup> | MSL<sup>3</sup> | HLSL<sup>4</sup> |
| ---- | -------------------- | --------------- | ---- |
| subgroup_matrix_left<T, K, M> | OpTypeCooperativeMatrixKHR<br>MatrixAKHR use<br>M rows<br>K cols<br>T component type | simdgroup_matrix<T, 8, 8> | Matrix<T, M, K, A, Wave>
| subgroup_matrix_right<T, N, K> | OpTypeCooperativeMatrixKHR<br>MatrixBKHR use<br>K rows<br>N cols<br>T component type | simdgroup_matrix<T, 8, 8> | Matrix<T, K, N, B, Wave>
| subgroup_matrix_result<T, N, M> | OpTypeCooperativeMatrixKHR<br>MatrixAccumulatorKHR use<br>M rows<br>N cols<br>T component type | simdgroup_matrix<T, 8, 8> | Matrix<T, M, N, Accumulator, Wave>

1. All OpTypeCooperativeMatrixKHR use subgroup scope.
2. Component type enum maps directly to SPIR-V type (e.g. i8 to OpTypeInt 8 1).
3. MSL types use the usual mappings (e.g. f32 to float).
4. Most types use the usual mappings.
    Only 8-bit integers differ as they map to packed types.


#### Functions

| Function | SPIR-V | MSL | HLSL |
| -------- | ------ | ---- | ---- |
| Value constructors | OpCompositeConstruct with appropriate value<br>const-expressions could use constant instructions | make_filled_simdgroup_matrix | Splat with appropriate value |
| subgroupMatrixLoad | OpCooperativeMatrixLoadKHR<br>Pointer operand is a direct translation of the WGSL pointer | simdgroup_matrix_load<br>The WGSL pointer needs translated into the origin operand in MSL | Matrix::Load<br>Pointer operand is traced to variable.<br>Offset maybe combination of pointer offset and function call parameter.
| subgroupMatrixStore | OpCooperativeMatrixStoreKHR<br>Pointer operand is a direct translation of the WGSL pointer | simdgroup_matrix_store<br>The WGSL pointer needs translated into the origin operand in MSL | Matrix::Store<br>The WGSL pointer needs translated into the origin operand in MSL | Matrix::Load<br>Pointer operand is traced to variable.<br>Offset maybe combination of pointer offset and function call parameter.
| subgroupMatrixMultiply | OpCooperativeMatrixMulAddKHR<br>C is a zero value matrix matching the result type | simdgroup_multiply | Multiply
| subgroupMatrixMultiplyAccumulate | OpCooperativeMatrixMulAddKHR | simdgroup_multiply_accumulate | MultiplyAccumulate |
| subgroupMatrixScalarAdd | OpI/FAdd with composite constructed value | simdgroup_multiply_accumulate with diagonal matrix for b and filled matrix scalar value for c | operator+=
| subgroupMatrixScalarSubtract | OpI/FSub with composite constructed value | simdgroup_multiply_accumulate with diagonal matrix for b and filled inverted matrix scalar value for c | operator-=
| subgroupMatrixScalarMultiply | OpI/FMul with composite constructed value | simdgroup_multiply with diagonal matrix scalar value for b<sup>1</sup> | operator*=
| ~~subgroupMatrixScalarDivide~~ | ~~OpI/S/FDiv with composite constructed scalar or OpMatrixTimesScalar (for float components with reciprocal scalar value)~~ | ~~simdgroup_multiply with diagonal matrix reciprocal scalar value for b~~ | ~~operator/=~~


#### Properties


##### Vulkan

Filter the list returned from [vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR](https://registry.khronos.org/vulkan/specs/1.3-extensions/html/vkspec.html#vkGetPhysicalDeviceCooperativeMatrixPropertiesKHR) such that:

*   A type and B type match
*   C type and result type match
*   A, B, C, and result types are one of (-> API enum):
    *   VK_COMPONENT_TYPE_FLOAT32_KHR -> f32
    *   VK_COMPONENT_TYPE_FLOAT16_KHR -> f16
    *   VK_COMPONENT_TYPE_SINT32_KHR -> i32
    *   VK_COMPONENT_TYPE_UINT32_KHR -> u32
    *   VK_COMPONENT_TYPE_SINT8_KHR -> i8
    *   VK_COMPONENT_TYPE_UINT8_KHR -> u8
*   saturatingAccumulation is false
*   Scope is `VK_SCOPE_SUBGROUP_KHR`

`VK_COMPONENT_TYPE_FLOAT16` will need to be filtered out of the device properties if the `shader-f16` feature is not requested.

##### D3D12

**TODO**: The feature is still under development.

##### Metal

Hardcode the following configurations if the feature is supported:

| componentType | resultComponentType | M | N | K |
| ------------- | ------------------- | ---- | ---- | ---- |
| f32 | f32 | 8 | 8 | 8 |
| f16 | f16 | 8 | 8 | 8 |

1. Filter out f16 from the device properties if `shader-f16` is not requested on the device.

**TODO**: Should we consider using performance primitives if the device supports Metal 4?

## Future Expansion

It is likely that more component types can be supported in the future.
Metal and SPIR-V can already support bfloat16 for example.

We could consider exposing saturating accumulation.

Other possible future features:
* Workgroup scoped matrices
* Conversions
* Per-element operations
* Tensor addressing
* Reductions

