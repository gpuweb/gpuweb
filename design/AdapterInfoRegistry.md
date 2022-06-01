# WebGPU Adapter Info Registry

This living document lists `"vendor"` and `"architecture"` adapter information values in the WebGPU API returned by the `requestAdapterInfo()` method on a `GPUAdapter` instance (See more at [AdapterIdentifiers.md](https://github.com/gpuweb/gpuweb/blob/main/design/AdapterIdentifiers.md)).

## JS example

```js
const gpuAdapter = await navigator.gpu.requestAdapter();
const adapterInfo = await gpuAdapter.requestAdapterInfo();
console.log(adapterInfo);

// Output:
{
    vendor: "nvidia",
    architecture: "turing",
    device: "",
    description: ""
}
```

## Values for `"vendor"` and `"architecture"` in Chromium

`"vendor"` | `"architecture"`
--- | ---
`"amd"` | `"gcn-1"`, `"gcn-2"`, `"gcn-3"`, `"gcn-4"`, `"gcn-5"`, `"rdna-1"`, `"rdna-2"`
`"apple"` | `"common-3"`, `"common-2"`, `"common-1"`
`"arm"` | `"midgard"`, `"bifrost"`, `"valhall"`
`"ati"`
`"geforce"`
`"google"` | `"swiftshader"`
`"img-tec"`
`"imagination"`
`"intel"` | `"gen-7"`, `"gen-8"`, `"gen-9"`, `"gen-11"`, `"xe"`
`"mesa"`
`"microsoft"` | `"warp"`
`"nvidia"` | `"fermi"`, `"kepler"`, `"maxwell"`, `"pascal"`, `"turing"`, `"ampere"`
`"qualcomm"` | `"adreno-4xx"`, `"adreno-5xx"`, `"adreno-6xx"`, `"adreno-7xx"`
`"quadro"`
`"radeon"`
`"samsung"` | `"rdna-2"`

Sources: 

- https://dawn.googlesource.com/dawn/+/refs/heads/main/gpu_info.json
- https://dawn.googlesource.com/dawn/+/refs/heads/main/src/dawn/native/metal/BackendMTL.mm
- https://dawn.googlesource.com/dawn/+/refs/heads/main/src/dawn/native/opengl/BackendGL.cpp