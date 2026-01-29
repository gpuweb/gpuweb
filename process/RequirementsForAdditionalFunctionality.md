# Requirements for additional functionality to WebGPU

This is a list of requirements which proposals for new functionality must adhere to in order to be standardized. New functionality is expected to usually take the form of a new [feature](https://gpuweb.github.io/gpuweb/#feature-index) to WebGPU.

Adhering to these requirements is _necessary but not sufficient_ for proposals to be standardized by the WebGPU Community Group / Working Group. A proposal which meets these requirements may still be rejected by the CG / WG for other reasons.

The list is expected to grow (or maybe even shrink!) over time. This list represents the CG's / WG's current processes. The initial version of this list was taken mostly from [this GitHub thread](https://github.com/gpuweb/gpuweb/issues/2310).

## Glossary

- "Browser engine" means "(Blink and Dawn) / (Gecko and wgpu) / (WebKit and WebGPU.framework) / etc."
- "Desktop GPU" means "a non-mobile GPU."
- ("Mobile GPU" is intentionally undefined, for now.)
- "Device vendor" means "Intel / Nvidia / AMD / Apple / Qualcomm / ARM / Imagination / VeriSilicon / etc."
- "Implementable" is according to the maintainers of the project in question.
  Note it does not always require a direct translation to every backend and may
  require some kind of "polyfill" on top of existing native features.
- "Core-Mode native API" means "D3D12 / Vulkan / Metal." (If implementations exist publicly on other APIs, like proprietary game console GPU APIs, the group may consider them too.)
- "Compatibility-Mode native API" means OpenGL ES, OpenGL, and D3D11.
- "Native APIs" means all Core-Mode native APIs and all Compatibility-Mode native APIs.
- "Standardization" means all/any of:
  - Putting proposals on the W3C recommendation track
  - Committing to the WebGPU Git repository
  - Adding anything in the WebGPU Github Team / Project / Wiki / Organization / etc.
  - Mere discussion within the CG / WG official meetings.

## Requirements

In order for a proposal for additional functionality to be standardized in the WebGPU CG / WG,

(These are numbered, so they can be referred to from other discussions.)

1. A proposal for new *optional* functionality must be implementable on at least 2 different browser engines. Rationale: One browser engine should not be able to unilaterally add functionality to the web platform.
2. A proposal for new *optional* functionality must be implementable on at least 2 different Core-Mode native APIs. Rationale: The web is intended to be OS-independent, and there is a high correlation between the native APIs and the OSes they primarily run on.
3. A proposal for new *optional* functionality must be implementable on devices created (designed? manufactured?) by at least 2 different device vendors. Rationale: The web is intended to be device-independent.
4. A proposal for new *required* functionality must be implementable on all participating browser engines on all native APIs they target. (Note: This includes both Core-Mode and Compatibility-Mode native APIs. New functionality that isn't implementable on Compatibility-Mode native APIs is considered "optional" because it will be part of `"core-features-and-limits"` or another feature.)

## Non-requirements

This is a list of items which are explicitly **not** requirements, and are thus neither necessary nor sufficient to standardize a proposal.

Of course, people making proposals can still certainly consider these items when determining if/when to make proposals.

(These are numbered, so they can be referred to from other discussions.)
1. Number/percentage of users using a particular functionality, device(s), native API, or browser engine. Rationale: Larger browsers / OSes / vendors with more users should not inherently have more privilege than smaller ones. Well-designed API proposals should be able to come from anywhere; the WebGPU CG / WG should be egalitarian in its work.
2. Number/percentage of devices using particular functionality, native API, or browser engine. Rationale: Same as above

The CG / WG can certainly deprioritize proposals due to these items, but it cannot _reject_ a proposal _solely_ because the proposal does not satisfy one these items.

## Possible future requirements

This is a set of requirements which are **not** currently part of the requirements list, but which the CG / WG is currently considering adding to the requirements list. This set is only included as an "FYI" for those who are curious.

- A proposal for new functionality _might_ have to be implementable on both desktop and mobile GPUs.
