# [WebCodecs](https://www.w3.org/TR/webcodecs/) Integration

**Roadmap:** This extension describes the integration between WebGPU and WebCodecs.
Its inclusion is contingent on the recommendation status of the WebCodecs spec.
It is intended to be implemented by any user agent that implements both WebGPU
and WebCodecs, though is not yet formally standardized.

## WebGPU Spec Changes

**Feature flags:** None; always enabled when WebGPU and WebCodecs are available.

When WebGPU and WebCodecs are both available, WebGPU allows importing `VideoFrame` objects via
`GPUDevice.importExternalTexture()`, producing opaque `GPUExternalTexture` objects, which can be
read from WebGPU shaders. The definition of the `source` member of `GPUExternalTextureDescriptor`
is modified to allow `VideoFrames`:

```webidl
partial dictionary GPUExternalTextureDescriptor {
    required (HTMLVideoElement or VideoFrame) source;
};
```

The lifetime of such a `GPUExternalTexture` object is implicitly tied to the
lifetime of the source `VideoFrame` object. When the `VideoFrame` is
[closed](https://www.w3.org/TR/webcodecs/#close-videoframe) (e.g. via
[`VideoFrame.close()`](https://www.w3.org/TR/webcodecs/#dom-videoframe-close) or
[transferring the `VideoFrame`](https://www.w3.org/TR/webcodecs/#videoframe-transfer-serialization)),
the `GPUExternalTexture` is
[destroyed](https://gpuweb.github.io/gpuweb/#dom-gpuexternaltexture-destroyed-slot),
so no further operations using it can be issued.

## WGSL Spec Changes

**Enable directive(s):** N/A

None. This uses the usual `texture_external` object.

## References

- <https://github.com/gpuweb/gpuweb/issues/2498>
