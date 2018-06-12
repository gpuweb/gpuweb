# API Term correspondence

## Resources

|D3D|Metal|OpenGL / Vulkan|
|---|-----|---------------|
|CBV (Constant Buffer View)|Constant memory buffer|Uniform Buffer|
|SRV (Shader Resource View)|Texture binding (textures and texture views are the same thing) with sample access|Sampled texture/image or texel buffers|
|UAV (Unordered Access View)|Device texture with read / write access, device memory buffers|Storage buffers, storage texel buffers and storage textures/images|
|Sub-resource index|Cube-face and array element|Cube-face and layer index|
 

