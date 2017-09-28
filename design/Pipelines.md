# Pipeline objects

This is a document with pseudo-code for the parts of the API related to pipeline objects.
Naming and the UX of the API are just an example and could change, the important parts are what’s available and what goes where.
For example this document uses C structures when a C++ API might want to use builder objects, and a Javascript API could use dictionaries.

## Creating pipeline objects

For type safety, compute and graphics pipeline are separate types.
To create a pipeline, a structure containing all the relevant information is passed to `DeviceCreate<TYPE>Pipeline`.

## Compute pipeline creation

To create a compute pipeline the only things needed are some shader code present in a `ShaderModule` object, and a `PipelineLayout` object describing how the pipeline interacts with the binding model.

```cpp
struct ComputePipelineDescriptor {
    ShaderModule module;
    const char* entryPoint;
    PipelineLayout layout;
};

ComputePipeline CreateComputePipeline(Device device, const ComputePipelineDescriptor* descriptor);
```

Translation to the backing APIs would be the following:
 - **D3D12**: Translates to `ID3D12::CreateComputePipelineState`, a `D3D12_SHADER_BYTECODE` is created from the `(module, entryPoint)` pair, and the `ID3D12RootSignature` is equivalent to the `PipelineLayout`.
 - **Metal**: Translates to `MTLDevice::makeComputePipelineState`, the `MTLFunction` is created from the `(module, entryPoint, layout)` tuple by adapting the generated MSL to the resource slot allocation done in `layout`.
 - **Vulkan**: Translates to `vkCreateComputePipelines` with one pipeline. The `vkShaderStageInfo` corresponds to `(module, entryPoint)` and the `vkPipelineLayout` corresponds to `layout`.

Question: How do we take advantage of the pipeline caching present in D3D12 and Vulkan? Do we expose it to the application or is it done magically in the WebGPU implementation?

Answer: deferred to post-MVP.

## Render pipeline creation

Render pipelines need `ShaderModule` and a `PipelineLayout` like compute pipelines and in addition require information about:
 - Layout for vertex inputs
 - Layout for fragment outputs
 - All the fixed-function state

For simplicity we assume most fixed-function state is created in separate object.
For example a `DepthStencilState` object would be allocated and a pointer to it would be stored in the `RenderPipelineDescriptor`. This is part of the UX of the API and could be replaced with chained structure like Vulkan or member structure like D3D12.

Mismatch:
 - Metal has primitive restart always enabled.
 - D3D12 needs to know whether the primitive restart index is `0xFFFF` or `0xFFFFFFFF` at pipeline creation time.
 - Metal doesn’t have a sample mask.
 - Vulkan can have some state like scissor and viewport set on the pipeline as an optimization on some GPUs.
 - Vulkan allows creating pipelines in bulk, this is not only a UX things but allows reusing some results for faster creation.

```cpp
enum IndexFormat {
    IndexFormatUint16,
    IndexFormatUint32,
};

struct RenderPipelineDescriptor {
    // Same translation as for compute pipelines
    ShaderModule vsModule;
    const char* vsEntryPoint;
    ShaderModule fsModule;
    const char* fsEntryPoint;
    PipelineLayout layout;

    // Pipeline input / outputs
    InputState* inputState;
    IndexFormat indexFormat;
    RenderPass* renderPass;
    int subpassIndex;

    // Fixed function state
    DepthStencilState* depthStencil;
    BlendState* blend[kMaxColorAttachments];
    PrimitiveTopology topology;
    // TODO other state: rasterizer state, “multisample state”
};


RenderPipeline CreateRenderPipeline(Device device, const RenderPipelineDescriptor* descriptor);
```

Translation to the backing APIs would be the following:
 - **D3D12**: Translates to `ID3D12::CreateGraphicsPipelineState`. `IBStripCutValue` will always be set with its value being chosen depending on `indexFormat`.
 - **Metal**: Translates to `MTLDevice::makeRenderPipelineState`
 - **Vulkan**: Translates to `vkCreateGraphicsPipelines`. `VkPipelineInputAssemblyStateCreateInfo`'s `primitiveRestartEnable` is always set to true. All dynamic states are set on all pipelines.

Question: Should the type of the indices be set in `RenderPipelineDescriptor`? If not, how is the D3D12 `IBStripCutValue` chosen?

Answer: While `indexFormat` isn't necessary in any of the three APIs, we chose to include it in the pipeline state because primitive restart must always be  enabled (because of Metal) and a D3D12 needs to choose the correct `IBStripCutValue`. The alternative would have been to compile two D3D12 pipelines for every WebGPU pipelines, or defer compilation.

The translation of individual members of RenderPipelineDescriptor is described below.

### Input state

This describes how the vertex buffers are stepped through (stride, instance vs. vertex, instance divisor), and how the attributes are extracted from the buffers (buffer index, format, offset).

Mismatches:
 - D3D12 takes the stride along with the vertex buffers in `ID3D12GraphicsCommandList::IASetVertexBuffers` whereas Vulkan and Metal take it at pipeline compilation time.
 - Vulkan doesn’t support a divisor for its step rate.

```cpp
enum StepRate {
    StepRateVertex,
    StepRateInstance,
};

Enum VertexFormat {
    // TODO make a list of portable vertex formats
};

struct InputStateDescriptor {
    struct {
        bool enabled;
        VertexFormat format;
        int offsetInBuffer;
        int bufferIndex;
    } attributes[MAX_ATTRIBUTES];

    struct {
        StepRate rate;
        int stride;
    } buffers[MAX_VERTEX_BUFFERS];
};

InputState* CreateInputState(Device* device, InputStateDescriptor* descriptor);
```

Translation to the backing APIs would be the following:
 - **D3D12**: Translates to a `D3D12_INPUT_DESC`.
   Each enabled attribute corresponds to a `D3D12_INPUT_ELEMENT_DESC` with `InputSlot` being the index of the attribute.
   Other members of the `D3D12_INPUT_ELEMENT_DESC` are translated trivially.
   The stride is looked up in the pipeline state before calls to `ID3D12GraphicsCommandList::IASetVertexBuffers`.
   `IASetVertexBuffers` might be deferred until before a draw and vertex buffers might be invalidated by pipeline changes.
 - **Metal**: Translates to a `MTLVertexDescriptor`, with attributes corresponding to `MTLVertexDescriptor::attributes` and buffers corresponding to `MTLVertexDescriptor::layouts`.
   Attributes translate trivially to `MTLVertexAttributeDescriptor` structures and buffers to `MTLVertexBufferLayoutDescriptor` structures.
   Extra care only needs to be taken to translate a zero stride to a constant step rate.
 - **Vulkan**: Translates to a `VkPipelineVertexInputStateCreateInfo`.
   Buffers translate trivially to `VkVertexInputBindingDescription` and attributes to `VkVertexInputAttributeDescription`.

Question: Should the vertex attributes somehow be included in the PipelineLayout so vertex buffers are treated as other resources and changed in bulk with them?

Answer: We decided against innovating in this area.

### Render pass / render target format

The `RenderPass` will contain for each subpass a list of the attachment formats for color attachments and depth-stencil attachments.
Information from the `RenderPass` is used to fill the following:
 - **D3D12**: `RTVFormats`, `DSVFormats` and `NumRenderTargets` in `D3D12_GRAPHICS_PIPELINE_STATE_DESC`.
 - **Metal**: `colorAttachments[N].pixelFormat`, `depthAttachmentPixelFormat` and `stencilAttachmentPixelFormat` in `MTLRenderPipelineDescriptor`.
 - **Vulkan**: `renderPass` and `subpass` in `VkGraphicsPipelineCreateInfo`.

Question: does the sample count of the pipeline state come from the RenderPass too?

Answer: deferred post-MVP.

### Primitive topology

Mismatch:
 - Metal and D3D12 only require “point vs. line vs. triangle” at pipeline compilation time, the exact topology is set via `ID3D12GraphicsCommandList::IASetPrimitiveTopology` or passed in the `MTLRenderCommandEncoder::draw*`.
   Vulkan requires the exact topology at compilation time.
 - Vulkan supports triangle fans but Metal and D3D12 don’t.

```cpp
enum PrimitiveTopology {
    PrimitiveTopologyPoints,
    PrimitiveTopologyLineList,
    PrimitiveTopologyLineStrip,
    PrimitiveTopologyTriangleList,
    PrimitiveTopologyTriangleStrip,
};
```

Translation to the backing APIs would be the following:
 - **D3D12 and Metal**: The primitive topology type is set on the `D3D12_GRAPHICS_PIPELINE_STATE_DESC` and `MTLRenderPipelineDescriptor`.
   At draw-time, the exact topology is queried from the pipeline.
 - **Vulkan**: The primitive topology type is set in the `VkGraphicsPipelineCreateInfo`.

### Blend state

Mismatch:
 - In Vulkan per-attachment blending and dual source blending are exposed as optional features.
   `independentBlend` is supported almost everywhere but Adreno 4XX while `dualSrcBlend` is also not supported on Mali GPUs.
 - Metal doesn’t have logic ops.

```cpp
enum BlendOperation {
    BlendOperationAdd,
    BlendOperationSubtract,
    BlendOperationReverseSubtract,
    BlendOperationMin,
    BlendOperationMax,
};

enum BlendFactor {
    BlendFactorOne,
    BlendFactorSrcColor,
    BlendFactorOneMinusSrcColor,
    BlendFactorSrcAlpha,
    BlendFactorOneMinusSrcAlpha,
    BlendFactorDstColor,
    BlendFactorOneMinusDstColor,
    BlendFactorDstAlpha,
    BlendFactorOneMinusDstAlphe,
    BlendFactorSrcAlphaSaturated,
    BlendFactorBlendColor,
    BlendFactorOneMinusBlendColor,
};

struct BlendStateDescriptor {
    bool enabled;
    BlendFactor srcColorFactor;
    BlendFactor dstColorFactor;
    BlendFactor srcAlphaFactor;
    BlendFactor dstAlphaFactor;
    BlendOperation colorOperation;
    BlendOperation alphaOperation;
    int writeMask;
};

BlendState* CreateBlendState(Device* device, BlendStateDescriptor* descriptor);
```

Translation to backing APIs would be the following:
 - **D3D12**: when filling the `D3D12_GRAPHICS_PIPELINE_DESC`, `BlendState` will be filled with data coming from the `BlendStates` referenced in the `RenderPipelineDescriptor`.
   Translation from a `BlendState` to a `D3D12_RENDER_TARGET_BLEND_DESC` is trivial.
 - **Metal**: the `BlendStates` will be used to fill all of the data for a `MTLRenderPipelineColorAttachmentDescriptor` but `pixelFormat`.
   Translation of individual members is trivial.
 - **Vulkan**: the `BlendStates` will be translated to elements of `pAttachments` in the `VkPipelineColorBlendStateCreateInfo`.
   Translation of individual members is trivial.

Open question: Should enablement of independent attachment blend state be explicit like in D3D12 or explicit?

Open question: Should alpha to coverage be part of the multisample state or the blend state?

### Depth stencil state

Mismatch:
 - D3D12 doesn’t have per-face stencil read and write masks.
 - In Metal the depth stencil state is built and bound separately from the pipeline state.

```cpp
enum CompareFunction {
    CompareFunctionNever,
    CompareFunctionLess,
    CompareFunctionLessEqual,
    CompareFunctionGreater,
    CompareFunctionGreaterEqual,
    CompareFunctionEqual,
    CompareFunctionNotEqual,
    CompareFunctionAlways,
};

enum StencilOperation {
    StencilOperationKeep,
    StencilOperationZero,
    StencilOperationReplace,
    StencilOperationInvert,
    StencilOperationIncrementClamp,
    StencilOperationDecrementClamp,
    StencilOperationIncrementWrap,
    StencilOperationDecrementWrap,
};

struct StencilFaceDescriptor {
    CompareFunction stencilCompare;
    StencilOperation stencilPass;
    StencilOperation stencilFail;
    StencilOperation depthFail;
};

struct DepthStencilStateDescriptor {
    CompareFunction depthCompare;
    StencilFaceDescriptor front;
    StencilFaceDescriptor back;
    int stencilReadMask;
    Int stencilWriteMask;
};

DepthStencilState* CreateDepthStencilState(Device* device, DepthStencilDescriptor* descriptor);
```

Translation to backing APIs would be the following:
 - **D3D12**: `DepthStencilState` translates trivially to a `D3D12_DEPTH_STENCIL_DESC`.
   `DepthEnable` would be set as `depthCompare != Always`.
 - **Metal**: `DepthStencilState` translates trivially to `MTLDepthStencilDescriptor` except that front and back stencil masks have to be set to the single stencil mask value from WebGPU.
   When a pipeline is bound, the corresponding depth-stencil state is bound at the same time.
 - **Vulkan**: `DepthStencilState` translates trivially to `VkPipelineDepthStencilStateCreateInfoxcept` except that front and back stencil masks have to be set to the single stencil mask value from WebGPU.
   `depthTestEnable` would be set to `depthCompare != Always`.

Question: What about Vulkan’s `VkPipelineDepthStencilStateCreateInfo::depthBoundTestEnable` and D3D12's `D3D12_DEPTH_STENCIL_DESC1::DepthBoundsTestEnable`?

Answer: deferred post-MVP.

Open question: Should “depth test enable” be implicit or explicit?
