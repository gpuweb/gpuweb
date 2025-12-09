# WebGPU Extension Proposals

The documents in this directory are
[WebGPU extension documents](https://gpuweb.github.io/gpuweb/#extension-documents)
which describe **draft proposals** to add functionality to WebGPU.
g
The proposals are organized into three categories:

- This directory contains proposals **under active consideration**. These proposals are **not
  stable, non-normative, non-standardized** and may change at any time.

- The `accepted` subdirectory contains proposals that have been **accepted and incorporated into the
  main specification**. We retain them here to keep the design rationale and investigation notes
  easily available.

- The `inactive` subdirectory contains proposals that are not under active consideration but could
  be considered later.

Check the "roadmap" of an extension document to understand its status.

The committee generally handles smaller changes to the WebGPU or WGSL specifications with GitHub
issues and pull requestions. We use documents in this directory for proposals which are larger or
require extended discussion, and are thus not easily contained in more direct forms.

If the group agrees that it never intends to consider a proposal in the future, it should be removed
from this directory (and may be migrated outside of the WebGPU community group).

## New Proposals

Copy the format of an existing proposal. Proposals may be informal, as they are never normative.
However, be sure to include a **detailed roadmap** to set expectations for developers, and, as
appropriate, include:

- WebGPU spec changes (including feature flags)
- WGSL spec changes (including enable directives)
- Links to context (like corresponding Vulkan/D3D12/Metal features) and past discussions
