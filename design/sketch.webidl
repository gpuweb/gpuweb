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

enum GPULogEntryType {
    "device-lost",
    "validation-error",
    "recoverable-out-of-memory"
};

interface GPULogEntry {
    readonly attribute GPULogEntryType type;
    readonly attribute any sourceObject;
    readonly attribute DOMString? reason;
};

enum GPUObjectStatus {
    "valid",
    "out-of-memory",
    "invalid"
};

typedef Promise<GPUObjectStatus> GPUObjectStatusQuery;

typedef (GPUBuffer or GPUTexture) GPUStatusableObject;

callback GPULogCallback = void (GPULogEntry error);

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
    u32 size;
    GPUBufferUsageFlags usage;
};

interface GPUBuffer {
    readonly attribute ArrayBuffer? mapping;
    void unmap();

    void destroy();
};

// Texture
enum GPUTextureDimension {
    "1d",
    "2d",
    "3d"
};

enum GPUTextureFormat {
    "r8g8b8a8-unorm",
    "r8g8b8a8-uint",
    "b8g8r8a8-unorm",
    "d32-float-s8-uint"
    // TODO other formats
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
    GPUTextureView createTextureView(GPUTextureViewDescriptor desc);
    GPUTextureView createDefaultTextureView();

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
    u32 offset;
    u32 size;
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

dictionary GPUBlendStateDescriptor {
    boolean blendEnabled;
    GPUBlendDescriptor alpha;
    GPUBlendDescriptor color;
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

enum GPUVertexFormat {
    "float-r32g32b32a32",
    "float-r32g32b32",
    "float-r32g32",
    "float-r32"
    // TODO other vertex formats
};

enum GPUInputStepMode {
    "vertex",
    "instance"
};

dictionary GPUVertexAttributeDescriptor {
    u32 shaderLocation;
    u32 inputSlot;
    u32 offset;
    GPUVertexFormat format;
};

dictionary GPUVertexInputDescriptor {
    u32 inputSlot;
    u32 stride;
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

// Description of a single attachment
dictionary GPUAttachmentDescriptor {
    // Attachment data format
    GPUTextureFormat format;
};

// Description of the framebuffer attachments
dictionary GPUAttachmentsStateDescriptor {
    // Array of color attachments
    sequence<GPUAttachmentDescriptor> colorAttachments;
    // Optional depth/stencil attachment
    GPUAttachmentDescriptor? depthStencilAttachment;
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
    sequence<GPUBlendStateDescriptor> blendStates;
    GPUDepthStencilStateDescriptor depthStencilState;
    GPUInputStateDescriptor inputState;
    GPUAttachmentsStateDescriptor attachmentsState;
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
    GPUCommandBuffer endPass();
    // Allowed in both compute and render passes
    //TODO: setPushConstants() ?
    void setBindGroup(u32 index, GPUBindGroup bindGroup, optional sequence<u32> dynamicOffsets);
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

    void setIndexBuffer(GPUBuffer buffer, u32 offset);
    void setVertexBuffers(u32 startSlot, sequence<GPUBuffer> buffers, sequence<u32> offsets);

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
    GPURenderPassDepthStencilAttachmentDescriptor depthStencilAttachment;
};

dictionary GPUBufferCopyView {
    GPUBuffer buffer;
    u32 offset;
    u32 rowPitch;
    u32 imageHeight;
};

dictionary GPUTextureCopyView {
    GPUTexture texture;
    u32 mipLevel;
    u32 arrayLayer;
    GPUOrigin3D origin;
};

interface GPUCommandBuffer {
    GPURenderPassEncoder beginRenderPass(GPURenderPassDescriptor descriptor);
    GPUComputePassEncoder beginComputePass();

    // Commands allowed outside of "passes"
    void copyBufferToBuffer(
        GPUBuffer src,
        u32 srcOffset,
        GPUBuffer dst,
        u32 dstOffset,
        u32 size);

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
};

dictionary GPUCommandBufferDescriptor {
    //TODO: reusability flag?
};

// ****************************************************************************
// OTHER (Fence, Queue SwapChain, Device)
// ****************************************************************************

// Fence

dictionary GPUFenceDescriptor {
    GPUQueue signalQueue = null;
    u64 initialValue = 0;
};

interface GPUFence {
    u64 getCompletedValue();
    Promise<void> onCompletion(u64 completionValue);
};

// Queue
interface GPUQueue {
    void submit(sequence<GPUCommandBuffer> buffers);
    void signal(GPUFence fence, u64 signalValue);

    // If we have multiple-queues
    void wait(GPUFence fence, u64 valueToWait);
};

// SwapChain / RenderingContext
dictionary GPUSwapChainDescriptor {
    GPUTextureUsageFlags usage;
    GPUTextureFormat format;
};

interface GPUSwapChain {
    void configure(GPUSwapChainDescriptor descriptor);
    GPUTexture getNextTexture();
    void present();
};

interface GPURenderingContext : GPUSwapChain {
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
    GPUTexture createTexture(GPUTextureDescriptor descriptor);
    GPUSampler createSampler(GPUSamplerDescriptor descriptor);

    GPUBindGroupLayout createBindGroupLayout(GPUBindGroupLayoutDescriptor descriptor);
    GPUPipelineLayout createPipelineLayout(GPUPipelineLayoutDescriptor descriptor);
    GPUBindGroup createBindGroup(GPUBindGroupDescriptor descriptor);

    GPUShaderModule createShaderModule(GPUShaderModuleDescriptor descriptor);
    GPUComputePipeline createComputePipeline(GPUComputePipelineDescriptor descriptor);
    GPURenderPipeline createRenderPipeline(GPURenderPipelineDescriptor descriptor);

    GPUCommandBuffer createCommandBuffer(GPUCommandBufferDescriptor descriptor);
    GPUFence createFence(GPUFenceDescriptor descriptor);

    GPUQueue getQueue();

    attribute GPULogCallback onLog;
    GPUObjectStatusQuery getObjectStatus(GPUStatusableObject statusableObject);
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

    GPUDevice createDevice(GPUDeviceDescriptor descriptor);
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

GPUCommandBuffer includes GPUDebugLabel;
GPUComputePipeline includes GPUDebugLabel;
GPUFence includes GPUDebugLabel;
GPUProgrammablePassEncoder includes GPUDebugLabel;
GPUQueue includes GPUDebugLabel;
GPURenderPipeline includes GPUDebugLabel;
GPUShaderModule includes GPUDebugLabel;

partial dictionary GPUCommandBufferDescriptor {
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
