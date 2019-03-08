typedef long i32;
typedef unsigned long u32;
typedef unsigned long long u64;

dictionary GPUColor {
    float r;
    float g;
    float b;
    float a;
};

dictionary GPUOrigin3D {
    u32 x;
    u32 y;
    u32 z;
};

dictionary GPUExtent3D {
    u32 width;
    u32 height;
    u32 depth;
};

// ****************************************************************************
// ERROR HANDLING
// ****************************************************************************

interface GPUDeviceLostInfo {
    readonly attribute DOMString message;
};

partial interface GPUDevice {
    readonly attribute Promise<GPUDeviceLostInfo> lost;
};

[
    Constructor(DOMString type, GPUValidationErrorEventInit gpuValidationErrorEventInitDict),
    Exposed=Window
]
interface GPUValidationErrorEvent : Event {
    readonly attribute DOMString message;
};

dictionary GPUValidationErrorEventInit : EventInit {
    required DOMString message;
};

partial interface GPUDevice : EventTarget {
    attribute EventHandler onvalidationerror;
};

// ****************************************************************************
// SHADER RESOURCES (buffer, textures, texture views, samples)
// ****************************************************************************

// Buffer
typedef u32 GPUBufferUsageFlags;
interface GPUBufferUsage {
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

dictionary GPUBufferDescriptor {
    u64 size;
    GPUBufferUsageFlags usage;
};

interface GPUBuffer {
    void setSubData(u64 offset, ArrayBuffer data);

    Promise<ArrayBuffer> mapReadAsync();
    Promise<ArrayBuffer> mapWriteAsync();
    void unmap();

    void destroy();
};

// Texture
enum GPUTextureDimension {
    "1d",
    "2d",
    "3d"
};

// Texture formats
// The name of the format specifies the order of components, bits per component, and data type for
// the component.
//     r, g, b, a = red, green, blue, alpha
//     unorm = unsigned normalized
//     snorm = signed normalized
//     uint = unsigned int
//     sint = signed int
//     float = floating point
// If the format has the "-srgb" suffix, then sRGB gamma compression and decompression are
// applied during the reading and writing of color values in the pixel.
// Compressed texture formats are provided by extensions. Their naming should follow the
// convention here, with the texture name as a prefix. e.g. "etc2-rgba8unorm".

enum GPUTextureFormat {
    /* Normal 8 bit formats */
    "r8unorm",
    "r8unorm-srgb",
    "r8snorm",
    "r8uint",
    "r8sint",
    /* Normal 16 bit formats */
    "r16unorm",
    "r16snorm",
    "r16uint",
    "r16sint",
    "r16float",
    "rg8unorm",
    "rg8unorm-srgb",
    "rg8snorm",
    "rg8uint",
    "rg8sint",
    /* Packed 16 bit formats */
    "b5g6r5unorm",
    /* Normal 32 bit formats */
    "r32uint",
    "r32sint",
    "r32float",
    "rg16unorm",
    "rg16snorm",
    "rg16uint",
    "rg16sint",
    "rg16float",
    "rgba8unorm",
    "rgba8unorm-srgb",
    "rgba8snorm",
    "rgba8uint",
    "rgba8sint",
    "bgra8unorm",
    "bgra8unorm-srgb",
    /* Packed 32 bit formats */
    "rgb10a2unorm",
    "rg11b10float",
    /* Normal 64 bit formats */
    "rg32uint",
    "rg32sint",
    "rg32float",
    "rgba16unorm",
    "rgba16snorm",
    "rgba16uint",
    "rgba16sint",
    "rgba16float",
    /* Normal 128 bit formats */
    "rgba32uint",
    "rgba32sint",
    "rgba32float",
};

typedef u32 GPUTextureUsageFlags;
interface GPUTextureUsage {
    const u32 NONE = 0;
    const u32 TRANSFER_SRC = 1;
    const u32 TRANSFER_DST = 2;
    const u32 SAMPLED = 4;
    const u32 STORAGE = 8;
    const u32 OUTPUT_ATTACHMENT = 16;
};

dictionary GPUTextureDescriptor {
    GPUExtent3D size;
    u32 arrayLayerCount;
    u32 mipLevelCount;
    u32 sampleCount;
    GPUTextureDimension dimension;
    GPUTextureFormat format;
    GPUTextureUsageFlags usage;
};

// Texture view
enum GPUTextureViewDimension {
    "1d",
    "2d",
    "2d-array",
    "cube",
    "cube-array",
    "3d"
};

typedef u32 GPUTextureAspectFlags;
interface GPUTextureAspect {
    const u32 COLOR = 1;
    const u32 DEPTH = 2;
    const u32 STENCIL = 4;
};

dictionary GPUTextureViewDescriptor {
    GPUTextureFormat format;
    GPUTextureViewDimension dimension;
    GPUTextureAspectFlags aspect;
    u32 baseMipLevel;
    u32 mipLevelCount;
    u32 baseArrayLayer;
    u32 arrayLayerCount;
};

interface GPUTextureView {
};

interface GPUTexture {
    GPUTextureView createView(GPUTextureViewDescriptor desc);
    GPUTextureView createDefaultView();

    void destroy();
};

// Samplers
enum GPUAddressMode {
    "clamp-to-edge",
    "repeat",
    "mirror-repeat",
    "clamp-to-border-color"
};

enum GPUFilterMode {
    "nearest",
    "linear"
};

enum GPUCompareFunction {
    "never",
    "less",
    "equal",
    "less-equal",
    "greater",
    "not-equal",
    "greater-equal",
    "always"
};

enum GPUBorderColor {
    "transparent-black",
    "opaque-black",
    "opaque-white"
};

dictionary GPUSamplerDescriptor {
    GPUAddressMode addressModeU = "clampToEdge";
    GPUAddressMode addressModeV = "clampToEdge";
    GPUAddressMode addressModeW = "clampToEdge";
    GPUFilterMode magFilter = "nearest";
    GPUFilterMode minFilter = "nearest";
    GPUFilterMode mipmapFilter = "nearest";
    float lodMinClamp = 0;
    float lodMaxClamp = 0xffffffff; // TODO: What should this be? Was Number.MAX_VALUE.
    u32 maxAnisotropy = 1;
    GPUCompareFunction compareFunction = "never";
    GPUBorderColor borderColor = "transparentBlack";
};

interface GPUSampler {
};

// ****************************************************************************
// BINDING MODEL (bindgroup layout, bindgroup)
// ****************************************************************************

// BindGroupLayout
typedef u32 GPUShaderStageFlags;
interface GPUShaderStageBit {
    const u32 NONE = 0;
    const u32 VERTEX = 1;
    const u32 FRAGMENT = 2;
    const u32 COMPUTE = 4;
};

enum GPUBindingType {
    "uniform-buffer",
    "dynamic-uniform-buffer",
    "sampler",
    "sampled-texture",
    "storage-buffer",
    "dynamic-storage-buffer"
    // TODO other binding types
};

dictionary GPUBindGroupLayoutBinding {
    u32 binding;
    GPUShaderStageFlags visibility;
    GPUBindingType type;
};

dictionary GPUBindGroupLayoutDescriptor {
    sequence<GPUBindGroupLayoutBinding> bindings;
};

interface GPUBindGroupLayout {
};

// PipelineLayout
dictionary GPUPipelineLayoutDescriptor {
    sequence<GPUBindGroupLayout> bindGroupLayouts;
};

interface GPUPipelineLayout {
};

// BindGroup
dictionary GPUBufferBinding {
    GPUBuffer buffer;
    u64 offset;
    u64 size;
};

typedef (GPUSampler or GPUTextureView or GPUBufferBinding) GPUBindingResource;

dictionary GPUBindGroupBinding {
    u32 binding;
    GPUBindingResource resource;
};

dictionary GPUBindGroupDescriptor {
    GPUBindGroupLayout layout;
    sequence<GPUBindGroupBinding> bindings;
};

interface GPUBindGroup {
};

// ****************************************************************************
// PIPELINE CREATION (blend state, DS state, ..., pipelines)
// ****************************************************************************

// RasterizationState
enum GPUFrontFace {
    "ccw",
    "cw"
};

enum GPUCullMode {
    "none",
    "front",
    "back"
};

dictionary GPURasterizationStateDescriptor {
    GPUFrontFace frontFace;
    GPUCullMode cullMode;

    i32 depthBias;
    float depthBiasSlopeScale;
    float depthBiasClamp;
};

// BlendState
enum GPUBlendFactor {
    "zero",
    "one",
    "src-color",
    "one-minus-src-color",
    "src-alpha",
    "one-minus-src-alpha",
    "dst-color",
    "one-minus-dst-color",
    "dst-alpha",
    "one-minus-dst-alpha",
    "src-alpha-saturated",
    "blend-color",
    "one-minus-blend-color"
};

enum GPUBlendOperation {
    "add",
    "subtract",
    "reverse-subtract",
    "min",
    "max"
};

typedef u32 GPUColorWriteFlags;
interface GPUColorWriteBits {
    const u32 NONE = 0;
    const u32 RED = 1;
    const u32 GREEN = 2;
    const u32 BLUE = 4;
    const u32 ALPHA = 8;
    const u32 ALL = 15;
};

dictionary GPUBlendDescriptor {
    GPUBlendFactor srcFactor;
    GPUBlendFactor dstFactor;
    GPUBlendOperation operation;
};

dictionary GPUColorStateDescriptor {
    GPUTextureFormat format;

    GPUBlendDescriptor alphaBlend;
    GPUBlendDescriptor colorBlend;
    GPUColorWriteFlags writeMask;
};

enum GPUStencilOperation {
    "keep",
    "zero",
    "replace",
    "invert",
    "increment-clamp",
    "decrement-clamp",
    "increment-wrap",
    "decrement-wrap"
};

dictionary GPUStencilStateFaceDescriptor {
    GPUCompareFunction compare;
    GPUStencilOperation failOp;
    GPUStencilOperation depthFailOp;
    GPUStencilOperation passOp;
};

dictionary GPUDepthStencilStateDescriptor {
    GPUTextureFormat format;

    boolean depthWriteEnabled;
    GPUCompareFunction depthCompare;

    GPUStencilStateFaceDescriptor stencilFront;
    GPUStencilStateFaceDescriptor stencilBack;

    u32 stencilReadMask;
    u32 stencilWriteMask;
};

// InputState

enum GPUIndexFormat {
    "uint16",
    "uint32"
};

// Vertex formats
// The name of the format specifies the data type of the component, the number of
// values, and whether the data is normalized.
//     uchar = unsigned 8-bit value
//     char = signed 8-bit value
//     ushort = unsigned 16-bit value
//     short = signed 16-bit value
//     half = half-precision 16-bit floating point value
//     float = 32-bit floating point value
//     uint = unsigned 32-bit integer value
//     int = signed 32-bit integer value
// If no number of values is given in the name, a single value is provided.
// If the format has the "-bgra" suffix, it means the values are arranged as
// blue, green, red and alpha values.

enum GPUVertexFormat {
    "uchar",
    "uchar2",
    "uchar3",
    "uchar4",
    "char",
    "char2",
    "char3",
    "char4",
    "ucharnorm",
    "uchar2norm",
    "uchar3norm",
    "uchar4norm",
    "uchar4norm-bgra",
    "charnorm",
    "char2norm",
    "char3norm",
    "char4norm",
    "ushort",
    "ushort2",
    "ushort3",
    "ushort4",
    "short",
    "short2",
    "short3",
    "short4",
    "ushortnorm",
    "ushort2norm",
    "ushort3norm",
    "ushort4norm",
    "shortnorm",
    "short2norm",
    "short3norm",
    "short4norm",
    "half",
    "half2",
    "half3",
    "half4",
    "float",
    "float2",
    "float3",
    "float4",
    "uint",
    "uint2",
    "uint3",
    "uint4",
    "int",
    "int2",
    "int3",
    "int4"
};

enum GPUInputStepMode {
    "vertex",
    "instance"
};

dictionary GPUVertexAttributeDescriptor {
    u32 shaderLocation;
    u32 inputSlot;
    u64 offset;
    GPUVertexFormat format;
};

dictionary GPUVertexInputDescriptor {
    u32 inputSlot;
    u64 stride;
    GPUInputStepMode stepMode;
};

dictionary GPUInputStateDescriptor {
    GPUIndexFormat indexFormat;

    sequence<GPUVertexAttributeDescriptor> attributes;
    sequence<GPUVertexInputDescriptor> inputs;
};

// ShaderModule

// Note: While the choice of shader language is undecided,
// GPUShaderModuleDescriptor will temporarily accept both
// text and binary input.
typedef (ArrayBuffer or DOMString) ArrayBufferOrDOMString;

dictionary GPUShaderModuleDescriptor {
    required ArrayBufferOrDOMString code;
};

interface GPUShaderModule {
};

dictionary GPUPipelineStageDescriptor {
    GPUShaderModule module;
    DOMString entryPoint;
    // TODO other stuff like specialization constants?
};

dictionary GPUPipelineDescriptorBase {
    GPUPipelineLayout layout;
};

// GPUComputePipeline
dictionary GPUComputePipelineDescriptor : GPUPipelineDescriptorBase {
    GPUPipelineStageDescriptor computeStage;
};

interface GPUComputePipeline {
};

// GPURenderPipeline
enum GPUPrimitiveTopology {
    "point-list",
    "line-list",
    "line-strip",
    "triangle-list",
    "triangle-strip"
};

dictionary GPURenderPipelineDescriptor : GPUPipelineDescriptorBase {
    GPUPipelineStageDescriptor vertexStage;
    GPUPipelineStageDescriptor fragmentStage;

    GPUPrimitiveTopology primitiveTopology;
    GPURasterizationStateDescriptor rasterizationState;
    sequence<GPUColorStateDescriptor> colorStates;
    GPUDepthStencilStateDescriptor? depthStencilState;
    GPUInputStateDescriptor inputState;

    // Number of MSAA samples
    u32 sampleCount;
    // TODO other properties
};

interface GPURenderPipeline {
};

// ****************************************************************************
// COMMAND RECORDING (Command buffer and all relevant structures)
// ****************************************************************************

/// Common interface for render and compute pass encoders.
interface GPUProgrammablePassEncoder {
    void endPass();

    // Allowed in both compute and render passes
    void setBindGroup(u32 index, GPUBindGroup bindGroup, optional sequence<u64> dynamicOffsets);
    void setPipeline((GPUComputePipeline or GPURenderPipeline) pipeline);
};

interface GPURenderPassEncoder : GPUProgrammablePassEncoder {
    void setBlendColor(GPUColor color);
    void setStencilReference(u32 reference);

    // The default viewport is (0.0, 0.0, w, h, 0.0, 1.0), where w and h are the dimensions of back buffer
    void setViewport(float x, float y, float width, float height, float minDepth, float maxDepth);

    // The default scissor rectangle is (0, 0, w, h), where w and h are the dimensions of back buffer.
    // Width and height must be greater than 0. Otherwise, an error will be generated.
    void setScissorRect(u32 x, u32 y, u32 width, u32 height);

    void setIndexBuffer(GPUBuffer buffer, u64 offset);
    void setVertexBuffers(u32 startSlot, sequence<GPUBuffer> buffers, sequence<u64> offsets);

    void draw(u32 vertexCount, u32 instanceCount, u32 firstVertex, u32 firstInstance);
    void drawIndexed(u32 indexCount, u32 instanceCount, u32 firstIndex, i32 baseVertex, u32 firstInstance);

    // TODO add missing commands
};

interface GPUComputePassEncoder : GPUProgrammablePassEncoder {
    void dispatch(u32 x, u32 y, u32 z);

    // TODO add missing commands
};


enum GPULoadOp {
    "clear",
    "load"
};

enum GPUStoreOp {
    "store"
};

dictionary GPURenderPassColorAttachmentDescriptor {
    GPUTextureView attachment;
    GPUTextureView? resolveTarget;

    GPULoadOp loadOp;
    GPUStoreOp storeOp;
    GPUColor clearColor;
};

dictionary GPURenderPassDepthStencilAttachmentDescriptor {
    GPUTextureView attachment;

    GPULoadOp depthLoadOp;
    GPUStoreOp depthStoreOp;
    float clearDepth;

    GPULoadOp stencilLoadOp;
    GPUStoreOp stencilStoreOp;
    u32 clearStencil;
};

dictionary GPURenderPassDescriptor {
    sequence<GPURenderPassColorAttachmentDescriptor> colorAttachments;
    GPURenderPassDepthStencilAttachmentDescriptor? depthStencilAttachment;
};

dictionary GPUBufferCopyView {
    GPUBuffer buffer;
    u64 offset;
    u64 rowPitch;
    u32 imageHeight;
};

dictionary GPUTextureCopyView {
    GPUTexture texture;
    u32 mipLevel;
    u32 arrayLayer;
    GPUOrigin3D origin;
};

interface GPUCommandBuffer {
};

interface GPUCommandEncoder {
    GPURenderPassEncoder beginRenderPass(GPURenderPassDescriptor descriptor);
    GPUComputePassEncoder beginComputePass();

    // Commands allowed outside of "passes"
    void copyBufferToBuffer(
        GPUBuffer src,
        u64 srcOffset,
        GPUBuffer dst,
        u64 dstOffset,
        u64 size);

    void copyBufferToTexture(
        GPUBufferCopyView source,
        GPUTextureCopyView destination,
        GPUExtent3D copySize);

    void copyTextureToBuffer(
        GPUTextureCopyView source,
        GPUBufferCopyView destination,
        GPUExtent3D copySize);

    void copyTextureToTexture(
        GPUTextureCopyView source,
        GPUTextureCopyView destination,
        GPUExtent3D copySize);

    GPUCommandBuffer finish();
};

dictionary GPUCommandEncoderDescriptor {
    //TODO: reusability flag?
};

// ****************************************************************************
// OTHER (Fence, Queue SwapChain, Device)
// ****************************************************************************

// Fence

dictionary GPUFenceDescriptor {
    u64 initialValue = 0;
};

interface GPUFence {
    u64 getCompletedValue();
    Promise<void> onCompletion(u64 completionValue);
};

// Queue
interface GPUQueue {
    void submit(sequence<GPUCommandBuffer> buffers);

    GPUFence createFence(GPUFenceDescriptor descriptor);
    void signal(GPUFence fence, u64 signalValue);
};

// SwapChain / CanvasContext
interface GPUCanvasContext {
};

dictionary GPUSwapChainDescriptor {
    required GPUCanvasContext context;
    required GPUTextureFormat format;
    GPUTextureUsageFlags usage = GPUTextureUsage.OUTPUT_ATTACHMENT;
};

interface GPUSwapChain {
    GPUTexture getCurrentTexture();
};

// Web GPU "namespace" used for device creation
dictionary GPUExtensions {
    boolean anisotropicFiltering;
};

dictionary GPULimits {
    u32 maxBindGroups;
};

// Device
interface GPUDevice {
    readonly attribute GPUExtensions extensions;
    readonly attribute GPULimits limits;
    readonly attribute GPUAdapter adapter;

    GPUBuffer createBuffer(GPUBufferDescriptor descriptor);
    (GPUBuffer, ArrayBuffer) createBufferMapped(GPUBufferDescriptor descriptor);
    Promise<(GPUBuffer, ArrayBuffer)> createBufferMappedAsync(GPUBufferDescriptor descriptor);
    GPUTexture createTexture(GPUTextureDescriptor descriptor);
    GPUSampler createSampler(GPUSamplerDescriptor descriptor);

    GPUBindGroupLayout createBindGroupLayout(GPUBindGroupLayoutDescriptor descriptor);
    GPUPipelineLayout createPipelineLayout(GPUPipelineLayoutDescriptor descriptor);
    GPUBindGroup createBindGroup(GPUBindGroupDescriptor descriptor);

    GPUShaderModule createShaderModule(GPUShaderModuleDescriptor descriptor);
    Promise<GPUShaderModule> createReadyShaderModule(GPUShaderModuleDescriptor descriptor);

    GPUComputePipeline createComputePipeline(GPUComputePipelineDescriptor descriptor);
    GPURenderPipeline createRenderPipeline(GPURenderPipelineDescriptor descriptor);

    Promise<GPUComputePipeline> createReadyComputePipeline(GPUComputePipelineDescriptor descriptor);
    Promise<GPURenderPipeline> createReadyRenderPipeline(GPUPipelineDescriptor descriptor);

    GPUCommandEncoder createCommandEncoder(GPUCommandEncoderDescriptor descriptor);

    // Calling createSwapChain a second time for the same GPUCanvasContext
    // invalidates the previous one, and all of the textures it’s produced.
    GPUSwapChain createSwapChain(GPUSwapChainDescriptor descriptor);

    GPUQueue getQueue();

    GPUObjectStatusQuery getObjectStatus(GPUStatusableObject statusableObject);

    Promise<GPUTextureFormat> getSwapChainPreferredFormat(GPUCanvasContext context);
};

dictionary GPUDeviceDescriptor {
    GPUExtensions extensions;
    //GPULimits limits; Don't expose higher limits for now.

    // TODO are other things configurable like queues?
};

interface GPUAdapter {
    readonly attribute DOMString name;
    readonly attribute GPUExtensions extensions;
    //readonly attribute GPULimits limits; Don't expose higher limits for now.

    // May reject with DOMException  // TODO: DOMException("OperationError")?
    Promise<GPUDevice> requestDevice(GPUDeviceDescriptor descriptor);
};

enum GPUPowerPreference {
    "low-power",
    "high-performance"
};

dictionary GPURequestAdapterOptions {
    GPUPowerPreference powerPreference;
};

[Exposed=Window]
namespace gpu {
    // May reject with DOMException  // TODO: DOMException("OperationError")?
    Promise<GPUAdapter> requestAdapter(optional GPURequestAdapterOptions options);
};

// ****************************************************************************
// DEBUGGING HELPERS
// ****************************************************************************

partial interface GPUProgrammablePassEncoder {
    void pushDebugGroup(DOMString groupLabel);
    void popDebugGroup();
    void insertDebugMarker(DOMString markerLabel);
};

interface mixin GPUDebugLabel {
    attribute DOMString label;
};

GPUBindGroup includes GPUDebugLabel;
GPUBindGroupLayout includes GPUDebugLabel;
GPUBuffer includes GPUDebugLabel;
GPUCommandBuffer includes GPUDebugLabel;
GPUCommandEncoder includes GPUDebugLabel;
GPUComputePipeline includes GPUDebugLabel;
GPUFence includes GPUDebugLabel;
GPUPipelineLayout includes GPUDebugLabel;
GPUProgrammablePassEncoder includes GPUDebugLabel;
GPUQueue includes GPUDebugLabel;
GPURenderPipeline includes GPUDebugLabel;
GPUSampler includes GPUDebugLabel;
GPUShaderModule includes GPUDebugLabel;
GPUTexture includes GPUDebugLabel;
GPUTextureView includes GPUDebugLabel;

partial dictionary GPUCommandEncoderDescriptor {
    DOMString label;
};

partial dictionary GPUFenceDescriptor {
    DOMString label;
};

partial dictionary GPUPipelineDescriptorBase {
    DOMString label;
};

partial dictionary GPUShaderModuleDescriptor {
    DOMString label;
};
