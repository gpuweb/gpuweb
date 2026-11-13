# Shader Print

* Status: [Draft](README.md#status-draft)
* Created: 2026-11-13
* Issue: [#4704](https://github.com/gpuweb/gpuweb/issues/4704)

## Motivation

Debugging shaders in WebGPU is difficult, particularly in browser environments where attaching
platform-specific GPU debuggers is inconvenient or unavailable.

This proposal introduces a `print` built-in function in WGSL that allows shaders to format and log
scalar and vector expressions directly to the browser developer console or native device logging
callback.

## WGSL Changes

### New Built-In Functions

**Overload**

```wgsl
fn print(str: string)
```

**Description**

Emit the string expression `str` to the implementation-defined print output stream.


### Template String Syntax

This proposal introduces string literals that use JavaScript-style template literal syntax:

- Backticks (`` ` ``) delimit the start and end of the string literal.
- Expressions are embedded inside `${...}` placeholders. Embedded expressions must evaluate to a
  scalar or vector type.
- Newlines and escape characters are permitted inside the template literal.

The `string` type can only be used for expressions that are passed to the `print` built-in function,
or as the type of a `const` declaration.

### Examples

```wgsl
print(`expected ${x * 2}, got ${result}!`);

print(
`here is an example that uses
\t- embedded newlines
\t- escape characters (\$, \`, \\)
`);
```

## Output and Testing

### Output Routing

- **Native:** Output is routed to the device logging callback.
- **Browsers:** Output is routed to the developer console.
- A callback could also be added to the WebGPU API to allow applications to capture output.

### Standardization of Output

Not standardizing the exact output text or delivery mechanism provides some advantages:

- Implementations have freedom over number formatting and can prepend useful diagnostic tags (such
  as the shader stage, pipeline label, entry point, or invocation ID).
- Implementations can treat `print` as a no-op if a particular pipeline or device configuration
  cannot accommodate it (e.g. a pipeline already uses the maximum number of storage buffers, or the
  device does not support vertex-stage atomics). This flexibility is particularly important if `print` is exposed as a language extension rather than a device-gated `enable` extension.

If output is not standardized, CTS coverage will be limited to:

- Validation tests for template string syntax and embedded expression types.
- Ensuring pipelines that use `print` compile and run to completion.
- Verifying the order of evaluation for embedded `${...}` sub-expressions with side effects.

## Implementation and Native API Mapping

### Native API Support

- **Metal (MSL):** Metal 3.2+ provides built-in shader logging via `<metal_logging>` and the
  `os_log` facility (`os_log_default.log_debug(...)`), configured and captured on the host through
  `MTLLogState`.
- **Vulkan (SPIR-V):** Vulkan supports shader debug printing via the `SPV_KHR_non_semantic_info`
  SPIR-V extension and the `NonSemantic.DebugPrintf` extended instruction set, which is processed by
  the Vulkan Validation Layers debug printf feature.
- **D3D12 (HLSL):** HLSL does not yet have a universally supported built-in shader
  `printf` instruction, though an upcoming
  [HLSL `printf` proposal](https://github.com/microsoft/hlsl-specs/pull/932) is in progress.

### Implementation via a Storage Buffer

Implementations can support shader print by writing print payloads to a storage buffer and reading
the buffer back on the host:

1. **Shader instrumentation:** The compiler allocates an internal `read_write` storage buffer bound
   to an available bind group/binding slot. Each `print` call atomically reserves space in this
   buffer and writes a record header (such as a format string ID and invocation metadata) followed
   by the evaluated scalar/vector payload values.
2. **Host readback and formatting:** After command buffer execution, the implementation copies and
   maps the print buffer on the host, reconstructs the formatted strings using the recorded format
   table and payload values, and emits them to the device log or developer console.


## Open Questions

- **Bikeshed name:** `print` vs `log` vs `shaderLog` vs ...

- **Language extension vs. optional `enable` extension:** Should `print` be exposed as a language
  extension (acting as a no-op unless activated by an implementation-specific toggle), or
  as an `enable` extension gated by a WebGPU device feature?

- **Formatting:** How should developers control value formatting (e.g., decimal precision)?
  - New JS-style built-in formatting functions:
    ```wgsl
    print(`result = ${toFixed(x, 2)}`);
    ```
  - Rust/Python-style inline format specifiers:
    ```wgsl
    print(`result = ${x : .2f}`);
    ```
  - Another mechanism?

- **Capturing output:** Should WebGPU expose a callback API to capture shader print output?

- **Output standardization:** Should any aspect of the message format be standardized?

- **Severity flag:** Should `print` support a severity level (e.g., info, warning, error) via an
  optional parameter, distinct built-in functions, or another syntax so that messages can be
  filtered or styled appropriately in the console and device logs?
