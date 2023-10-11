# WebGPU Compatibility Mode

This proposal is **under active development, but has not been standardized for inclusion in the WebGPU specification**. WebGPU implementations **must not** expose this functionality; doing so is a spec violation. Note however, an implementation might provide an option (e.g. command line flag) to enable a draft implementation, for developers who want to test this proposal.

The changes merged into this document are those for which the GPU for the Web Community Group has achieved **tentative** consensus prior to official standardization of the whole propsal. New items will be added to this doc as tentative consensus on further issues is achieved.

## Problem

WebGPU is a good match for modern explicit graphics APIs such as Vulkan, Metal and D3D12. However, there are a large number of devices which do not yet support those APIs. In particular, on Chrome on Windows, 31% of Chrome users do not have D3D11.1 or higher. On Android, [23% of Android users do not have Vulkan 1.1 (15% do not have Vulkan at all)](https://developer.android.com/about/dashboards). On ChromeOS, Vulkan penetration is still quite low, while OpenGL ES 3.1 is ubiquitous.

## Goals

The primary goal of WebGPU Compatibility mode is to increase the reach of WebGPU by providing an opt-in, slightly restricted subset of WebGPU which will run on older APIs such as D3D11 and OpenGL ES. The set of restrictions in Compatibility mode should be kept to a minimum in order to make it easy to port exsting WebGPU applications. This will increase adoption of WebGPU applications via a wider userbase.

Since WebGPU Compatibility mode is a subset of WebGPU, all valid Compatibility mode applications are also valid WebGPU applications. Consequently, Compatibility mode applications will also run on user agents which do not support Compatibility mode. Such user agents will simply ignore the option requesting a Compatibility mode Adapter and return a Core WebGPU Adapter instead.

## WebGPU Spec Changes

```webidl
partial dictionary GPURequestAdapterOptions {
    boolean compatibilityMode = false;
}
```

When calling `GPU.RequestAdapter()`, passing `compatibilityMode = true` in the `GPURequestAdapterOptions` will indicate to the User Agent to select the Compatibility subset of WebGPU. Any Devices created from the resulting Adapter on supporting UAs will support only Compatibility mode. Calls to APIs unsupported by Compatibility mode will result in validation errors.

Note that a supporting User Agent may return a `compatibilityMode = true` Adapter which is backed by a fully WebGPU-capable hardware adapter, such as D3D12, Metal or Vulkan, so long as it validates all subsequent API calls made on the Adapter and the objects it vends against the Compatibility subset.

```webidl
partial interface GPUAdapter {
    readonly attribute boolean isCompatibilityMode;
}
```

As a convenience to the developer, the Adapter returned will have the `isCompatibilityMode` property set to `true`.


```webidl
partial dictionary GPUTextureDescriptor {
    GPUTextureViewDimension viewDimension;
}
```

See "Texture view dimension may be specified", below.

## Compatibility mode restrictions

### 1. Texture view dimension may be specified 

When specifying a texture, a `viewDimension` property determines the views which can be bound from that texture for sampling (see "Proposed IDL changes", above). Binding a view of a different dimension for sampling than specified at texture creation time will cause a validation error. If `viewDimension` is unspecified, use the following algorithm:
```
if desc.dimension is "1d":
    set viewDimension to "1d"
if desc.dimension is "2d":
  if desc.size.depthOrArrayLayers is 1:
    set viewDimension to "2d"
  else:
    set viewDimension to "2d-array"
if desc.dimension is "3d":
  set viewDimension to "3d"
```

**Justification**: OpenGL ES 3.1 does not support texture views.

### 2. Color state `alphaBlend`, `colorBlend` and `writeMask` may not differ between color attachments in a single draw.

Color state descriptors used in a single draw must have the same alphaBlend, colorBlend and writeMask, or else an encode-time validation error will occur.

**Justification**: OpenGL ES 3.1 does not support indexed draw buffer state.
