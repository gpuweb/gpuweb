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
};

// Texture view
dictionary WebGPUTextureViewDescriptor {
    // TODO Investigate what goes in there.
};

interface WebGPUTextureView {
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
    WebGPUTextureDimensionEnum dimension;
    WebGPUTextureFormatEnum format;
    WebGPUTextureUsageFlags usage;
};

interface WebGPUTexture {
    WebGPUTextureView createTextureView(WebGPUTextureViewDescriptor desc);
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
    WebGPUddressMode rAddressMode = "clampToEdge";
    WebGPUddressMode sAddressMode = "clampToEdge";
    WebGPUddressMode tAddressMode = "clampToEdge";
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

dictionary WebGPUBindGroupBinding {
    u32 binding;
    WebGPUShaderStageFlags visibility;
    WebGPUBindingType type;
};

dictionary WebGPUBindGroupLayoutDescriptor {
    sequence<WebGPUBindGroupBinding> bindingTypes;
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
    sequence<WebGPUBindingResource> resources;
    u32 start;
    u32 count;
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
    "substract",
    "reverseSubstract",
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

interface WebGPUBlendState {
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
    WebGPUCompareFunctionEnum depthCompare;

    WebGPUStencilStateFaceDescriptor front;
    WebGPUStencilStateFaceDescriptor back;

    u32 stencilReadMask;
    u32 stencilWriteMask;
};

interface WebGPUDepthStencilState {
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

interface WebGPUInputState {
};

// ShaderModule
dictionary WebGPUShaderModuleDescriptor {
    ArrayBuffer code;
};

interface WebGPUShaderModule {
};

// AttachmentState
dictionary WebGPUAttachmentStateDescriptor {
    sequence<WebGPUTextureFormatEnum> formats;
    // TODO other stuff like sample count etc.
};

interface WebGPUAttachmentState {
};

// Common stuff for ComputePipeline and RenderPipeline
typedef u32 WebGPUShaderStageEnum;
interface WebGPUShaderStage {
    const u32 VERTEX = 0;
    const u32 FRAGMENT = 1;
    const u32 COMPUTE = 2;
};

dictionary WebGPUPipelineStageDescriptor {
    WebGPUShaderModule module;
    WebGPUShaderStageEnum stage;
    DOMString entryPoint;
    // TODO other stuff like specialization constants?
};

dictionary WebGPUPipelineDescriptorBase {
    WebGPUPipelineLayout layout;
    sequence<WebGPUPipelineStageDescriptor> stages;
};

// ComputePipeline
dictionary WebGPUComputePipelineDescriptor : WebGPUPipelineDescriptorBase{
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

dictionary WebGPURenderPipelineDescriptor : WebGPUPipelineDescriptorBase{
    WebGPUPrimitiveTopologyEnum primitiveTopology;
    sequence<WebGPUBlendState> blendState;
    WebGPUDepthStencilState depthStencilState;
    WebGPUInputState inputState;
    WebGPUAttachmentState attachmentState;
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

interface WebGPURenderPassEncoder: WebGPUProgrammablePassEncoder {
    void setBlendColor(float r, float g, float b, float a);
    void setIndexBuffer(WebGPUBuffer buffer, u32 offset);
    void setVertexBuffers(u32 startSlot, sequence<WebGPUBuffer> buffers, sequence<u32> offsets);

    void draw(u32 vertexCount, u32 instanceCount, u32 firstVertex, u32 firstInstance);
    void drawIndexed(u32 indexCount, u32 instanceCount, u32 firstIndex, u32 firstInstance, u32 firstVertex);

    // TODO add missing commands
};

interface WebGPUComputePassEncoder: WebGPUProgrammablePassEncoder {
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
    uint32_t clearStencil;
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
    WebGPUTextureAspect aspect;
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
interface WebGPUFence {
    bool wait(Number milliseconds);
    readonly attribute Promise<void> promise;
};

// Queue
interface WebGPUQueue {
    void submit(sequence<WebGPUCommandBuffer> buffers);
    WebGPUFence insertFence();
};

// SwapChain / RenderingContext
dictionary WebGPUSwapChainDescriptor {
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

    WebGPUBlendState createBlendState(WebGPUBlendStateDescriptor descriptor);
    WebGPUDepthStencilState createDepthStencilState(WebGPUDepthStencilStateDescriptor descriptor);
    WebGPUInputState createInputState(WebGPUInputStateDescriptor descriptor);
    WebGPUShaderModule createShaderModule(WebGPUShaderModuleDescriptor descriptor);
    WebGPUAttachmentState createAttachmentState(WebGPUAttachmentStateDescriptor descriptor);
    WebGPUComputePipeline createComputePipeline(WebGPUComputePipelineDescriptor descriptor);
    WebGPURenderPipeline createRenderPipeline(WebGPURenderPipelineDescriptor descriptor);

    WebGPUCommandBuffer createCommandBuffer(WebGPUCommandBufferDescriptor descriptor);
    WebGPUFence createFence(WebGPUFenceDescriptor descriptor);

    WebGPUQueue getQueue();

    attribute WebGPULogCallback onLog;
    WebGPUObjectStatusQuery getObjectStatus(StatusableObject object);
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

enum WebGPUPowerPreference { "default", "low-power", "high-performance" };

dictionary WebGPUAdapterDescriptor {
    WebGPUPowerPreference powerPreference;
};

interface WebGPU {
    WebGPUAdapter getAdapter(WebGPUAdapterDescriptor desc);
};

// Add a "webgpu" member to Window that contains the global instance of a "WebGPU"
interface mixin WebGPUProvider {
    [Replaceable, SameObject] readonly attribute WebGPU webgpu;
};
Window includes WebGPUProvider;
