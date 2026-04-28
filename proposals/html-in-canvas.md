# HTML in Canvas

* Status: [Draft](README.md#status-draft)
* Created: 2026-04-28
* Issue: [#5251](https://github.com/gpuweb/gpuweb/issues/5251)

This proposal adds `copyElementImageToTexture` to `GPUQueue` to allow using HTML elements as a WebGPU texture.

## Motivation

As stated in the [HTML-in-Canvas](https://github.com/WICG/html-in-canvas) explainer, there is no web API to easily render complex layouts of text and other content into a `<canvas>`. As a result, `<canvas>`-based content suffers in accessibility, internationalization, performance, and quality.

The shared infrastructure and support in 2D canvas is being added in [WHATWG HTML PR #11588](https://github.com/whatwg/html/pull/11588). Support in WebGPU would bring the same capabilities to WebGPU applications.

## Proposed API

```webidl
typedef GPUCopyExternalImageDestInfo GPUImageCopyTextureTagged;

partial interface GPUQueue {
    undefined copyElementImageToTexture(
        (Element or ElementImage) source,
        GPUImageCopyTextureTagged destination);

    undefined copyElementImageToTexture(
        (Element or ElementImage) source,
        GPUIntegerCoordinate width,
        GPUIntegerCoordinate height,
        GPUImageCopyTextureTagged destination);

    undefined copyElementImageToTexture(
        (Element or ElementImage) source,
        float sx, float sy, float swidth, float sheight,
        GPUImageCopyTextureTagged destination);
};
```

### Parameters

* `source`: The `Element` or `ElementImage` to copy from. The algorithms for creating, updating and retreiving an "element image snapshot" from an `Element` or `ElementImage` are defined in HTML.
* `destination`: A `GPUImageCopyTextureTagged` dictionary describing the destination texture and its properties (like color space and alpha premultiplication).
* `width`, `height`: Optional destination dimensions. If not provided, the source's natural dimensions are used.
* `sx`, `sy`, `swidth`, `sheight`: Optional source rectangle. If not provided, the source's natural dimensions are used.

## Security and privacy

The HTML spec defines how security- or privacy-sensitive information is handled in the section on [exposing sensitive information](https://whatpr.org/html/11588/canvas.html#exposing-sensitive-information). This is part of creating the element image snapshots, and is shared between all canvas contexts.
