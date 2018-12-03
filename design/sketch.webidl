typedef long i32;
typedef unsigned long u32;
typedef unsigned long long u64;

dictionary WebGPUColor {
    float r;
    float g;
    float b;
    float a;
};

dictionary WebGPUOrigin3D {
    u32 x;
    u32 y;
    u32 z;
};

dictionary WebGPUExtent3D {
    u32 width;
    u32 height;
    u32 depth;
};

// ****************************************************************************
// ERROR HANDLING
// ****************************************************************************

enum WebGPULogEntryType {
    "device-lost",
    "validation-error",
    "recoverable-out-of-memory",
};

interface WebGPULogEntry {
    readonly attribute WebGPULogEntryType type;
    readonly attribute any sourceObject;
    readonly attribute DOMString? reason;
};

enum WebGPUObjectStatus {
    "valid",
    "out-of-memory",
    "invalid",
};

typedef Promise<WebGPUObjectStatus> WebGPUObjectStatusQuery;

typedef (WebGPUBuffer or WebGPUTexture) StatusableObject;

callback WebGPULogCallback = void (WebGPULogEntry error);

// ****************************************************************************
// SHADER RESOURCES (buffer, textures, texture views, samples)
// ****************************************************************************

// Buffer
typedef u32 WebGPUBufferUsageFlags;
interface WebGPUBufferUsage {
    const u32 NONE = 0;
    const u32 MAP_READ = 1;
    const u32 MAP_WRITE = 2;
    const u32 TRANSFER_SRC = 4;
    const u32 TRANSFER_DST = 8;
    const u32 INDEX = 16;
    const u32 VERTEX = 32;
    const u32 UNIFORM = 64;
    const u32 STORAGE = 128;
};

dictionary WebGPUBufferDescriptor {
    u32 size;
    WebGPUBufferUsageFlags usage;
};

interface WebGPUBuffer {
    readonly attribute ArrayBuffer? mapping;
    void unmap();

    void destroy();
};

// Texture
enum WebGPUTextureDimension {
    "1d",
    "2d",
    "3d",
};

enum WebGPUTextureFormat {
    "R8G8B8A8Unorm",
    "R8G8B8A8Uint",
    "B8G8R8A8Unorm",
    "D32FloatS8Uint",
    // TODO other formats
};

typedef u32 WebGPUTextureUsageFlags;
interface WebGPUTextureUsage {
    const u32 NONE = 0;
    const u32 TRANSFER_SRC = 1;
    const u32 TRANSFER_DST = 2;
    const u32 SAMPLED = 4;
    const u32 STORAGE = 8;
    const u32 OUTPUT_ATTACHMENT = 16;
    const u32 PRESENT = 32;
};

dictionary WebGPUTextureDescriptor {
    WebGPUExtent3D size;
    u32 arraySize;
    u32 levelCount;
    WebGPUTextureDimensionEnum dimension;
    WebGPUTextureFormatEnum format;
    WebGPUTextureUsageFlags usage;
};

// Texture view
enum WebGPUTextureViewDimension {
    "1d",
    "2d",
    "2darray",
    "cube",
    "cubearray",
    "3d"
};

typedef u32 WebGPUTextureAspectFlags;
interface WebGPUTextureAspect {
    const u32 COLOR = 1;
    const u32 DEPTH = 2;
    const u32 STENCIL = 4;
};

dictionary WebGPUTextureViewDescriptor {
    WebGPUTextureFormat format;
    WebGPUTextureViewDimension dimension;
    WebGPUTextureAspectFlags aspect;
    u32 baseMipLevel;
    u32 levelCount;
    u32 baseArrayLayer;
    u32 layerCount;
};

interface WebGPUTextureView {
};

interface WebGPUTexture {
    WebGPUTextureView createTextureView(WebGPUTextureViewDescriptor desc);
    WebGPUTextureView createDefaultTextureView();

    void destroy();
};

// Samplers
enum WebGPUAddressMode {
    "clampToEdge",
    "repeat",
    "mirrorRepeat",
    "clampToBorderColor"
};

enum WebGPUFilterMode {
    "nearest",
    "linear"
};

enum WebGPUCompareFunction {
    "never",
    "less",
    "equal",
    "lessEqual",
    "greater",
    "notEqual",
    "greaterEqual",
    "always"
};

enum WebGPUBorderColor {
    "transparentBlack",
    "opaqueBlack",
    "opaqueWhite"
};

dictionary WebGPUSamplerDescriptor {
    WebGPUAddressMode rAddressMode = "clampToEdge";
    WebGPUAddressMode sAddressMode = "clampToEdge";
    WebGPUAddressMode tAddressMode = "clampToEdge";
    WebGPUFilterModeEnum magFilter = "nearest";
    WebGPUFilterModeEnum minFilter = "nearest";
    WebGPUFilterModeEnum mipmapFilter = "nearest";
    float lodMinClamp = 0;
    float lodMaxClamp = Number.MAX_VALUE;
    unsigned long maxAnisotropy = 1;
    WebGPUCompareFunction compareFunction = "never";
    WebGPUBorderColor borderColor = "transparentBlack";
};

interface WebGPUSampler {
};

// ****************************************************************************
// BINDING MODEL (bindgroup layout, bindgroup)
// ****************************************************************************

// BindGroupLayout
typedef u32 WebGPUShaderStageFlags;
interface WebGPUShaderStageBit {
    const u32 NONE = 0;
    const u32 VERTEX = 1;
    const u32 FRAGMENT = 2;
    const u32 COMPUTE = 4;
};

enum WebGPUBindingType {
    "uniformBuffer",
    "sampler",
    "sampledTexture",
    "storageBuffer",
    // TODO other binding types
};

dictionary WebGPUBindGroupLayoutBinding {
    u32 binding;
    WebGPUShaderStageFlags visibility;
    WebGPUBindingType type;
};

dictionary WebGPUBindGroupLayoutDescriptor {
    sequence<WebGPUBindGroupLayoutBinding> bindings;
};

interface WebGPUBindGroupLayout {
};

// PipelineLayout
dictionary WebGPUPipelineLayoutDescriptor {
    sequence<WebGPUBindGroupLayout> bindGroupLayouts;
};

interface WebGPUPipelineLayout {
};

// BindGroup
dictionary WebGPUBufferBinding {
    WebGPUBuffer buffer;
    u32 offset;
    u32 size;
};

typedef (WebGPUSampler or WebGPUTextureView or WebGPUBufferBinding) WebGPUBindingResource;

dictionary WebGPUBinding {
    u32 binding;
    WebGPUBindingResource resource;
};

dictionary WebGPUBindGroupDescriptor {
    WebGPUBindGroupLayout layout;
    sequence<WebGPUBinding> bindings;
};

interface WebGPUBindGroup {
};

// ****************************************************************************
// PIPELINE CREATION (blend state, DS state, ..., pipelines)
// ****************************************************************************

// BlendState
enum WebGPUBlendFactor {
    "zero",
    "one",
    "srcColor",
    "oneMinusSrcColor",
    "srcAlpha",
    "oneMinusSrcAlpha",
    "dstColor",
    "oneMinusDstColor",
    "dstAlpha",
    "oneMinusDstAlpha",
    "srcAlphaSaturated",
    "blendColor",
    "oneMinusBlendColor",
};

enum WebGPUBlendOperation {
    "add",
    "subtract",
    "reverseSubtract",
    "min",
    "max",
};

typedef u32 WebGPUColorWriteFlags;
interface WebGPUColorWriteBits {
    const u32 NONE = 0;
    const u32 RED = 1;
    const u32 GREEN = 2;
    const u32 BLUE = 4;
    const u32 ALPHA = 8;
    const u32 ALL = 15;
};

dictionary WebGPUBlendDescriptor {
    WebGPUBlendFactorEnum srcFactor;
    WebGPUBlendFactorEnum dstFactor;
    WebGPUBlendOperationEnum operation;
};

dictionary WebGPUBlendStateDescriptor {
    bool blendEnabled;
    WebGPUBlendDescriptor alpha;
    WebGPUBlendDescriptor color;
    WebGPUColorWriteFlags writeMask;
};

enum WebGPUStencilOperation {
    "keep",
    "zero",
    "replace",
    "invert",
    "incrementClamp",
    "decrementClamp",
    "incrementWrap",
    "decrementWrap",
};

dictionary WebGPUStencilStateFaceDescriptor {
    WebGPUCompareFunction compare;
    WebGPUStencilOperation stencilFailOp;
    WebGPUStencilOperation depthFailOp;
    WebGPUStencilOperation passOp;
};

dictionary WebGPUDepthStencilStateDescriptor {
    bool depthWriteEnabled;
    WebGPUCompareFunction depthCompare;

    WebGPUStencilStateFaceDescriptor front;
    WebGPUStencilStateFaceDescriptor back;

    u32 stencilReadMask;
    u32 stencilWriteMask;
};

// InputState
typedef u32 WebGPUIndexFormatEnum;
interface WebGPUIndexFormat {
    const u32 UINT16 = 0;
    const u32 UINT32 = 1;
};

typedef u32 WebGPUVertexFormatEnum;
interface WebGPUVertexFormat {
    const u32 FLOAT_R32_G32_B32_A32 = 0;
    const u32 FLOAT_R32_G32_B32 = 1;
    const u32 FLOAT_R32_G32 = 2;
    const u32 FLOAT_R32 = 3;
    // TODO other vertex formats
};

typedef u32 WebGPUInputStepModeEnum;
interface WebGPUInputStepMode {
    const u32 VERTEX = 0;
    const u32 INSTANCE = 1;
};

dictionary WebGPUVertexAttributeDescriptor {
    u32 shaderLocation;
    u32 inputSlot;
    u32 offset;
    WebGPUVertexFormatEnum format;
};

dictionary WebGPUVertexInputDescriptor {
    u32 inputSlot;
    u32 stride;
    WebGPUInputStepModeEnum stepMode;
};

dictionary WebGPUInputStateDescriptor {
    WebGPUIndexFormatEnum indexFormat;

    sequence<WebGPUVertexAttributeDescriptor> attributes;
    sequence<WebGPUVertexInputDescriptor> inputs;
};

// ShaderModule

// Note: While the choice of shader language is undecided,
// WebGPUShaderModuleDescriptor will temporarily accept both
// text and binary input.
typedef (ArrayBuffer or DOMString) ArrayBufferOrDOMString;

dictionary WebGPUShaderModuleDescriptor {
    required ArrayBufferOrDOMString code;
};

interface WebGPUShaderModule {
};

// Description of a single attachment
dictionary WebGPUAttachmentDescriptor {
    // Attachment data format
    WebGPUTextureFormatEnum format;
    // Number of MSAA samples
    u32 samples;
};

// Description of the framebuffer attachments
dictionary WebGPUAttachmentsStateDescriptor {
    // Array of color attachments
    sequence<WebGPUAttachmentDescriptor> colorAttachments;
    // Optional depth/stencil attachment
    WebGPUAttachment? depthStencilAttachment;
};

dictionary WebGPUPipelineStageDescriptor {
    WebGPUShaderModule module;
    DOMString entryPoint;
    // TODO other stuff like specialization constants?
};

dictionary WebGPUPipelineDescriptorBase {
    WebGPUPipelineLayout layout;
};

// WebGPUComputePipeline
dictionary WebGPUComputePipelineDescriptor : WebGPUPipelineDescriptorBase {
    WebGPUPipelineStageDescriptor computeStage;
};

interface WebGPUComputePipeline {
};

// WebGPURenderPipeline
enum WebGPUPrimitiveTopology {
    "pointList",
    "lineList",
    "lineStrip",
    "trangleList",
    "triangleStrip",
};

dictionary WebGPURenderPipelineDescriptor : WebGPUPipelineDescriptorBase {
    WebGPUPipelineStageDescriptor vertexStage;
    WebGPUPipelineStageDescriptor fragmentStage;

    WebGPUPrimitiveTopologyEnum primitiveTopology;
    sequence<WebGPUBlendStateDescriptor> blendStates;
    WebGPUDepthStencilStateDescriptor depthStencilState;
    WebGPUInputStateDescriptor inputState;
    WebGPUAttachmentsStateDescriptor attachmentsState;
    // TODO other properties
};

interface WebGPURenderPipeline {
};

// ****************************************************************************
// COMMAND RECORDING (Command buffer and all relevant structures)
// ****************************************************************************

/// Common interface for render and compute pass encoders.
interface WebGPUProgrammablePassEncoder {
    WebGPUCommandBuffer endPass();
    // Allowed in both compute and render passes
    //TODO: setPushConstants() ?
    void setBindGroup(u32 index, WebGPUBindGroup bindGroup);
    void setPipeline((WebGPUComputePipeline or WebGPURenderPipeline) pipeline);
};

interface WebGPURenderPassEncoder : WebGPUProgrammablePassEncoder {
    void setBlendColor(float r, float g, float b, float a);
    void setStencilReference(u32 reference);

    // The default viewport is (0.0, 0.0, w, h, 0.0, 1.0), where w and h are the dimensions of back buffer
    void setViewport(float x, float y, float width, float height, float minDepth, float maxDepth);

    // The default scissor rectangle is (0, 0, w, h), where w and h are the dimensions of back buffer.
    // Width and height must be greater than 0. Otherwise, an error will be generated.
    void setScissorRect(u32 x, u32 y, u32 width, u32 height);

    void setIndexBuffer(WebGPUBuffer buffer, u32 offset);
    void setVertexBuffers(u32 startSlot, sequence<WebGPUBuffer> buffers, sequence<u32> offsets);

    void draw(u32 vertexCount, u32 instanceCount, u32 firstVertex, u32 firstInstance);
    void drawIndexed(u32 indexCount, u32 instanceCount, u32 firstIndex, i32 baseVertex, u32 firstInstance);

    // TODO add missing commands
};

interface WebGPUComputePassEncoder : WebGPUProgrammablePassEncoder {
    void dispatch(u32 x, u32 y, u32 z);

    // TODO add missing commands
};


enum WebGPULoadOp {
    "clear",
    "load",
};

enum WebGPUStoreOp {
    "store",
};

dictionary WebGPURenderPassColorAttachmentDescriptor {
    WebGPUTextureView attachment;

    WebGPULoadOp loadOp;
    WebGPUStoreOp storeOp;
    WebGPUColor clearColor;
};

dictionary WebGPURenderPassDepthStencilAttachmentDescriptor {
    WebGPUTextureView attachment;

    WebGPULoadOp depthLoadOp;
    WebGPUStoreOp depthStoreOp;
    float clearDepth;

    WebGPULoadOp stencilLoadOp;
    WebGPUStoreOp stencilStoreOp;
    u32 clearStencil;
};

dictionary WebGPURenderPassDescriptor {
    sequence<WebGPURenderPassColorAttachmentDescriptor> colorAttachments;
    WebGPURenderPassDepthStencilAttachmentDescriptor depthStencilAttachment;
};

dictionary WebGPUBufferCopyView {
    WebGPUBuffer buffer;
    u32 offset;
    u32 rowPitch;
    u32 imageHeight;
};

dictionary WebGPUTextureCopyView {
    WebGPUTexture texture;
    u32 level;
    u32 slice;
    WebGPUOrigin3D origin;
    WebGPUTextureAspectFlags aspect;
};

interface WebGPUCommandBuffer {
    WebGPURenderPassEncoder beginRenderPass(WebGPURenderPassDescriptor descriptor);
    WebGPUComputePassEncoder beginComputePass();

    // Commands allowed outside of "passes"
    void copyBufferToBuffer(
        WebGPUBuffer src,
        u32 srcOffset,
        WebGPUBuffer dst,
        u32 dstOffset,
        u32 size);

    void copyBufferToTexture(
        WebGPUBufferCopyView source,
        WebGPUTextureCopyView destination,
        WebGPUExtent3D copySize);

    void copyTextureToBuffer(
        WebGPUTextureCopyView source,
        WebGPUBufferCopyView destination,
        WebGPUExtent3D copySize);

    void copyTextureToTexture(
        WebGPUTextureCopyView source,
        WebGPUTextureCopyView destination,
        WebGPUExtent3D copySize);

    // TODO figure which other commands are needed
    void blit();
};

dictionary WebGPUCommandBufferDescriptor {
    //TODO: reusability flag?
};

// ****************************************************************************
// OTHER (Fence, Queue SwapChain, Device)
// ****************************************************************************

// Fence

dictionary WebGPUFenceDescriptor {
    WebGPUQueue signalQueue = null;
    u64 initialValue = 0;
};

interface WebGPUFence {
    u64 getCompletedValue();
    Promise<void> onCompletion(u64 completionValue);
};

// Queue
interface WebGPUQueue {
    void submit(sequence<WebGPUCommandBuffer> buffers);
    void signal(WebGPUFence fence, u64 signalValue);

    // If we have multiple-queues
    void wait(WebGPUFence fence, u64 valueToWait);
};

// SwapChain / RenderingContext
dictionary WebGPUSwapChainDescriptor {
    WebGPUDevice? device;
    WebGPUTextureUsageFlags usage;
    WebGPUTextureFormatEnum format;
    u32 width;
    u32 height;
};

interface WebGPUSwapChain {
    void configure(WebGPUSwapChainDescriptor descriptor);
    WebGPUTexture getNextTexture();
    void present();
};

interface WebGPURenderingContext : WebGPUSwapChain {
};

// WebGPU "namespace" used for device creation
dictionary WebGPUExtensions {
    bool anisotropicFiltering;
};

dictionary WebGPULimits {
    u32 maxBindGroups;
};

// Device
interface WebGPUDevice {
    readonly attribute WebGPUExtensions extensions;
    readonly attribute WebGPULimits limits;
    readonly attribute WebGPUAdapter adapter;

    WebGPUBuffer createBuffer(WebGPUBufferDescriptor descriptor);
    WebGPUTexture createTexture(WebGPUTextureDescriptor descriptor);
    WebGPUSampler createSampler(WebGPUSamplerDescriptor descriptor);

    WebGPUBindGroupLayout createBindGroupLayout(WebGPUBindGroupLayoutDescriptor descriptor);
    WebGPUPipelineLayout createPipelineLayout(WebGPUPipelineLayoutDescriptor descriptor);
    WebGPUBindGroup createBindGroup(WebGPUBindGroupDescriptor descriptor);

    WebGPUShaderModule createShaderModule(WebGPUShaderModuleDescriptor descriptor);
    WebGPUComputePipeline createComputePipeline(WebGPUComputePipelineDescriptor descriptor);
    WebGPURenderPipeline createRenderPipeline(WebGPURenderPipelineDescriptor descriptor);

    WebGPUCommandBuffer createCommandBuffer(WebGPUCommandBufferDescriptor descriptor);
    WebGPUFence createFence(WebGPUFenceDescriptor descriptor);

    WebGPUQueue getQueue();

    attribute WebGPULogCallback onLog;
    WebGPUObjectStatusQuery getObjectStatus(StatusableObject statusableObject);
};

dictionary WebGPUDeviceDescriptor {
    WebGPUExtensions extensions;
    //WebGPULimits limits; Don't expose higher limits for now.

    // TODO are other things configurable like queues?
};

interface WebGPUAdapter {
    readonly attribute DOMString name;
    readonly attribute WebGPUExtensions extensions;
    //readonly attribute WebGPULimits limits; Don't expose higher limits for now.

    WebGPUDevice createDevice(WebGPUDeviceDescriptor descriptor);
};

enum WebGPUPowerPreference {
    "low-power",
    "high-performance"
};

dictionary WebGPURequestAdapterOptions {
    WebGPUPowerPreference powerPreference;
};

[Exposed=Window]
namespace gpu {
    Promise<WebGPUAdapter> requestAdapter(optional WebGPURequestAdapterOptions options);
};

// ****************************************************************************
// DEBUGGING HELPERS
// ****************************************************************************

partial WebGPUProgrammablePassEncoder {
    void pushDebugGroup(DOMString groupLabel);
    void popDebugGroup(DOMString groupLabel);
    void insertDebugMarker(DOMString markerLabel);
};

interface mixin WebGPUDebugLabel {
    attribute DOMString label;
};

WebGPUCommandBuffer includes WebGPUDebugLabel;
WebGPUComputePipeline includes WebGPUDebugLabel;
WebGPUFence includes WebGPUDebugLabel;
WebGPUProgrammablePassEncoder includes WebGPUDebugLabel;
WebGPUQueue includes WebGPUDebugLabel;
WebGPURenderPipeline includes WebGPUDebugLabel;
WebGPUShaderModule includes WebGPUDebugLabel;

partial dictionary WebGPUCommandBufferDescriptor {
    DOMString label;
};

partial dictionary WebGPUFenceDescriptor {
    DOMString label;
};

partial dictionary WebGPUPipelineDescriptorBase {
    DOMString label;
};

partial dictionary WebGPUShaderModuleDescriptor {
    DOMString label;
};
