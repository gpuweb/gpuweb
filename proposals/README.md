# WebGPU Extension Proposals

The documents in this directory are
[WebGPU extension documents](https://gpuweb.github.io/gpuweb/#extension-documents)
which describe **non-normative, non-standardized draft proposals** to add functionality to WebGPU.

These proposals **may or may not be under active consideration**.
Check the "roadmap" of an extension document to understand its status.

These proposals are **not stable** and may change at any time. They may be:

- In-development proposals which are not easily contained in a GitHub pull request, HackMD, or similar.
- Inactive proposals which are not under active consideration but could be considered later.

If the group agrees that it never intends to consider a proposal in the future, it should be
removed from this directory (and may be migrated outside of the WebGPU community group).

## New Proposals

Copy the format of an existing proposal. Proposals may be informal, as they are never normative.

Be sure to follow the header style of other proposals. Additionally, as appropriate, include:

- WebGPU spec changes (including feature flags)
- WGSL spec changes (including enable directives)
- Links to context (like corresponding Vulkan/D3D12/Metal features) and past discussions

## Proposals Index

<!-- PR checks ensure that the sections below are up-to-date; you can update them manually
     or use `tools/proposals-index.py write` -->

<h3 id=status-merged>Merged</h3>

These proposals are **complete** and have been merged into the WebGPU and/or WGSL specifications.
These documents are kept as explainers and historical artifacts, but may not be 100% accurate.
Always refer to the specifications as the source of truth.

<!-- SECTION status-merged -->
* [compatibility-mode](compatibility-mode.md)
* [primitive-index](primitive-index.md)
* [subgroups](subgroups.md)
* [texture-component-swizzle](texture-component-swizzle.md)

<h3 id=status-draft>Draft</h3>

These proposals are **works in progress** and may be under active development.
For recent activity, look at the Git history of the file.

These proposals have **not** been standardized for inclusion in the WebGPU specification, and are
likely to change before they are standardized (*if accepted*).
WebGPU implementations must not expose these proposed changes; doing so is a spec violation.
Note however, an implementation might provide an option (e.g. command line flag) to enable a
draft implementation, for developers who want to test this proposal.

<!-- SECTION status-draft -->
* [atomic-64-min-max](atomic-64-min-max.md)
* [bindless](bindless.md)
* [buffer-view](buffer-view.md)
* [explicit_bindgroup_layout_parameters](explicit_bindgroup_layout_parameters.md)
* [fragment-depth](fragment-depth.md)
* [immediate-data](immediate-data.md)
* [sized-binding-arrays](sized-binding-arrays.md)
* [subgroup-id](subgroup-id.md)
* [subgroup-matrix](subgroup-matrix.md)
* [texel-buffers](texel-buffers.md)
* [transient-attachments](transient-attachments.md)

<h3 id=status-inactive>Inactive</h3>

These are Draft proposals (see above) that are **not under active consideration**.
They may be considered later.

<!-- SECTION status-inactive -->
* [pipeline-statistics-query](pipeline-statistics-query.md)
* [timestamp-query-inside-passes](timestamp-query-inside-passes.md)
