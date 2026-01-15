# WebGPU Compatibility Mode Explainer

## Proponents

- [GPU for the Web Community Group](https://www.w3.org/community/gpu/)

## Participate
- https://github.com/gpuweb/gpuweb/issues
- https://github.com/gpuweb/gpuweb/discussions

## Proposal

- [WebGPU Compatibility Mode](https://github.com/gpuweb/gpuweb/blob/main/proposals/compatibility-mode.md)

## User-Facing Problem

WebGPU does not run on older devices that lack support for modern graphics APIs, such as Vulkan, Metal, and Direct3D12. This reduces the reach of WebGPU by over half a billion potential users.

## Proposed Approach

[WebGPU Compatibility Mode](https://github.com/gpuweb/gpuweb/blob/main/proposals/compatibility-mode.md) is an opt-in, lightly restricted subset of [WebGPU](https://www.w3.org/TR/webgpu/) capable of running older graphics APIs such as OpenGL and Direct3D11. The goal is to expand the reach of WebGPU applications to older devices that do not have the modern, explicit graphics APIs that core WebGPU requires. This requires Compatibility Mode to prohibit the use of some WebGPU features that the older APIs do not support.

In order to permit a Web developer to opt in to the Compatibility Mode subset, WebGPU uses the `featureLevel` member in `GPURequestAdapterOptions`. This attribute supports the strings `"core"` and `"compatibility"`. To use it, developers set:

```
options.featureLevel = "compatibility"
```

And call `navigator.gpu.requestAdapter(options)`.

Other than support for the `featureLevel` attribute, the main web-facing changes required for a user agent to support Compatibility Mode are validation of the mode’s restrictions. If a web developer attempts to use a feature not supported by Compatibility Mode, a validation error will be generated (as is done currently for other invalid WebGPU content).

Some user agents, such as Safari, may choose not to implement Compatibility Mode, since their target devices all support a modern graphics API. For this reason, UAs are allowed to ignore a request for `"compatibility"` by returning a `"core"` adapter. WebGPU Compatibility Mode applications are valid WebGPU applications, and will run unmodified on a WebGPU Core-only user agent[^1]. A Core-only user agent will not perform the validation against Compatibility Mode restrictions, but it will run the Compatibility application the same as any Core WebGPU app. Such a user agent would only ever return `GPUAdapter`s with the `"core-features-and-limits"` Feature, and always create `GPUDevice`s with it automatically enabled.

## Alternatives Considered

### Lower GPU API bar

It would be possible to set the GPU API bar lower, for example, OpenGL ES 3.0. However, this would exclude GPU Compute functionality, which the community group feels is an essential component of WebGPU and one of its distinguishing features over WebGL. It would also only marginally increase reach (e.g., by [3.3%](https://developer.android.com/about/dashboards#OpenGL) on Android at time of writing).

### Web API alternatives

The initial proposal for WebGPU Compatibility Mode added a simple boolean to `GPURequestAdapterOptions`, rather than a `featureLevel`:

```
dictionary GPURequestAdapterOptions {
    …
    boolean compatibilityMode = false;
};
```

However, it was decided that a `featureLevel` would be more future-facing, in that it would allow for the future specification of additional feature levels, composed of a collection of existing features to be tested as a single unit in a more concise way.

## Accessibility, Security, and Privacy Considerations

Since it is a lightly-restricted subset, Compatibility Mode does not introduce any accessibility or security issues over and above those introduced by WebGPU. For this reason, the [security and privacy self-review submitted for WebGPU](https://gpuweb.github.io/gpuweb/explainer/#questionnaire) also applies to Compatibility Mode.

Compatibility Mode introduces two new known fingerprinting surfaces:

1. The 'core-features-and-limits' feature, which will be exposed on Core-supporting devices but absent on Compat-only devices.

2. WebGPU limits in OpenGL ES drivers. These limits will be bucketed using the same approach is used in core WebGPU and those buckets must be chosen carefullly in order to capture OpenGL ES capabilities at a sufficient granularity. For example, storage buffers in vertex shaders are unsupported on many popular Mali devices, so Compatiblity Mode introduces a new limit ('maxStorageBuffersInVertexStage') which must be zero on those devices, and non-zero elsewhere.

Note that the presence or absence of Compatibility Mode itself is not an additional fingerprinting bit, since browsers implementing Compatibility Mode will support it on all devices, including those that don't need it. The presence of Compatiblity Mode could be used to distinguish that browser from non-Compat-implementing browers, or older versions, but these are bits that are already available via other means.

[^1]as long as they don't depend on Compatibility-specific validation errors, which can only happen explicitly and is never necessary except to verify the user agent's validation rules, like in the WebGPU Conformance Test Suite.
