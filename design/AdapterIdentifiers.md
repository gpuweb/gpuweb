# WebGPU Adapter Identifiers

**This document is outdated. `adapter.requestAdapterInfo()` has been replaced with
`adapter.info` and `unmaskHints` doesn't exist anymore. See:
[#4536](https://github.com/gpuweb/gpuweb/issues/4536),
[#4316](https://github.com/gpuweb/gpuweb/pull/4316).

## Introduction

The WebGL extension [WEBGL_debug_renderer_info](https://www.khronos.org/registry/webgl/extensions/WEBGL_debug_renderer_info/) reports identifying information about a device's graphics driver for the purposes of debugging or detection and avoidance of bugs or performance pitfalls on a particular driver or piece of hardware.

These identifiers have proven to be a valuable tool for developers over the years (See [Appendix B: Motivating real-world use cases](#Appendix-B-Motivating-real-world-use-cases)), but have also been observed to be frequently used as a source of high-entropy fingerprinting data. Additionally, the format that WebGL returns the identifiers in (a string of undefined structure) is difficult to work with, akin to the user agent string.

For WebGPU we need mechanisms which report similar data about the GPU hardware (called an "adapter" in WebGPU) to enable legitimate development use cases, such as driver bug workarounds, while minimizing the amount of fingerprintable data that is exposed without user consent. This document will refer to that data as "adapter identifiers".

## Use Cases:

### Bug workarounds
A WebGPU developer wants to ensure that their content works on all devices, but is aware of a bug on a specific family of GPUs that causes corrupted rendering. Using a minimal subset of adapter identifiers they can identify when a user's GPUs is part of a group which includes the known-buggy hardware and switch to a slower code path that doesn't provoke the issue.

### Filing issue reports
A WebGPU developer has included a "Report an issue" button on their page. Normally they have found that they need very little adapter information to operate, but when users experience a problem they want to gather as much data as they can about the problem. On the report filing page they include UI to allow the user to include their GPU information in the report, which when checked causes the browser to confirm that they want to let the page know their full adapter details.

### Performance optimization
A WebGPU developer wants all users to experience good performance on their page, but has developed some effects that are not practical on mobile GPUs. They check the adapter identifiers on page load to get a broad idea of what family of GPU the user has to start them off with a reasonable set of defaults. On a settings page, however, they can include a button which detects the best settings for their device. Clicking it may prompt the user for consent to see more detailed GPU information so that ideal settings for their device can be selected.

### WebGPU developer community assets
A common and useful asset for developers is sites such as https://gpuinfo.org/, which visualize your current devices capabilities in an easy to read format and (with user's consent) can collect information about GPU capabilities to report in aggregate to other developers, giving them a sense of how widespread various capabilities are. Offering a way for users to opt-in to contributing to such a database is desirable.

## Goals:
 - Offer a mechanism to report GPU adapter identifiers in a scalable way.
 - Allow for reporting no information (tracking prevention modes, privacy-oriented UAs).
 - Enable UAs to decide for themselves how much information to expose by default.
 - Allow developers to have some input on how much information they need, especially with respect to triggering user prompts.
    - Any such feature needs to be invocable late in the device lifetime, to allow for cases like filing bug reports.
    - Developers need to know when a call may cause a user prompt to be shown so that they can avoid that path if desired.
 - Offer control over how much data is exposed to embedded content/iframes.
 - Minimize string parsing for accuracy and developer convenience.

## API usage

> Full details of how to use WebGPU will not be covered here. Please refer to the [WebGPU explainer](https://gpuweb.github.io/gpuweb/explainer/) or [WebGPU spec](https://gpuweb.github.io/gpuweb) for further information.

### Masked adapter identifiers

The first step when using WebGPU is to query a `GPUAdapter`, of which there may be several available to the system. This will typically correspond to a physical or software emulated GPU.

```js
const gpuAdapter = await navigator.gpu.requestAdapter();
```

WebGPU applications often require a significant amount of resource initialization at startup, and it's possible that the resources being initialized may need to be altered depending on the adapter in use. For example: Shader sources may need to be re-written to avoid a known bug or lower detail meshes and textures may need to be fetched to avoid overtaxing a slower device. In these cases some amount of adapter identifiers need to be queried very early in the application's lifetime, and preferably without invoking a user consent prompt. (Nobody likes to be asked for permission immediately on navigation, at which point they likely have little to know context for why the permission is needed.)

In this case, the developer would call the `requestAdapterInfo()` method of the `GPUAdapter`, which returns a `GPUAdapterInfo` interface containing several potential identifiers for the adapter, and may contain values similar to the following:

```js
const adapterInfo = await gpuAdapter.requestAdapterInfo();
console.log(adapterInfo);

// Output:
{
    vendor: 'nvidia',
    architecture: 'turing',
    device: '',
    description: ''
}
```

Note that some values of the interface are the empty string, because the UA deemed that they were too high-entropy to return without explicit user consent. If the UA wished, it would have the ability to return empty string for all values. This would be most commonly expected in "enhanced privacy" modes like [Edge's strict tracking prevention](https://support.microsoft.com/en-us/microsoft-edge/learn-about-tracking-prevention-in-microsoft-edge-5ac125e8-9b90-8d59-fa2c-7f2e9a44d869) or [Firefox's Enhanced Tracking Protection](https://support.mozilla.org/en-US/kb/enhanced-tracking-protection-firefox-desktop). Ideally returning little to no identifiers is common enough that user agents that wish to expose very little information by default can do so without severe compatibility concerns.

The information that _is_ returned should be helpful in identifying broad buckets of adapters with similar capabilities and performance characteristics. For example, Nvidia's "Turing" architecture [covers a range of nearly 40 different GPUs](https://en.wikipedia.org/wiki/Turing_(microarchitecture)#Products_using_Turing) across a wide range of prices and form factors. Identifing the adapter as an Turing device is enough to allow developers to activate broad workarounds aimed at that family of hardware and make some assumptions about baseline performance, but is also broad enough to not give away too much identifiable information about the user.

Additionally, in some cases the UA may find it beneficial to return a value that is not the most accurate one that could be reported but still gives developers a reasonable reference point with a lower amount of entropy.

Finally, it may not always be possible or practical to determine a value for some fields (like a GPU's architecture) and in those cases returning empty string is acceptable even if the user agent would have considered the information low-entropy.

### Unmasked adapter identifiers

At some point during the lifetime of the application the developer may determine that they need more information about the user's specific adapter. A common scenario would be filing a bug report. The developer will be able to best respond to the user's issue if they know exactly what device is being used. In this case, they can request an "unmasked" version any fields of the `GPUAdapterInfo`:

```js
feedbackButton.addEventListener('click', async ()=> {
    const unmaskHints = ['architecture', 'device', 'description'];
    const unmaskedAdapterInfo = await gpuAdapter.requestAdapterInfo(unmaskHints);
    generateUserFeedback(unmaskedAdapterInfo);
});
```

The resolved value is the adapter's `GPUAdapterInfo` with any fields specified by `unmaskHints` that were previously omitted or reported with a less accurate value now populated with the most accurate information the UA will deliver. For example:

```js
console.log(unmaskedAdapterInfo);

// Output:
{
    vendor: 'nvidia',
    architecture: 'turing',
    device: '0x8644',
    description: 'NVIDIA GeForce GTX 1660 SUPER'
}
```

Because the unmasked values may contain higher entropy identifying information, the bar for querying it is quite a bit higher. Calling `requestAdapterInfo()` with any `unmaskHints` requires user activation, and will reject the promise otherwise. If the `unmaskHints` array contains any previously masked value it also requires that user consent be given before returning, and as such may display a prompt to the user asking if the page can access the newly requested GPU details before allowing the promise to resolve. If the user declines to give consent then the promise is rejected.

Once the user has given their consent any future calls to `requestAdapterInfo()` should return the unmasked fields even if no `unmaskHints` are specified, and future instances of the same underlying adapter returned from `navigator.gpu.requestAdapter()` on that page load should also return unmasked data without requiring hints to be passed.

Even after `unmaskHints` have been passed to `requestAdapterInfo()` the UA is still allowed to return empty string for attributes requested in the `unmaskHints` array if the UA cannot determine the value in question or decides not to reveal it. (UAs should not request user consent when unmasking is requested for attributes that will be left empty.)

### Identifier formatting

To minimize developer work and reduce the chances of fingerprinting via casing differences between platforms, and string values reported as part of the `GPUAdapterInfo` conform to strict formatting rules. They must be lowercase ASCII strings containing no spaces, with separate words concatenated with a hyphen ("-") character.

The exception to this is `description`, which may be a string reported directly from the driver without modification. As a result, however, `description` should always be omitted from masked adapters. Additionally, enough information should be offered via other fields that developers don't feel the need to attempt parsing the `description` string.

User agents should also make an effort to normalize the strings returned, ideally through a public registry. This especially applies to fields like `vendor` which are presumed to have a relatively low number of possible values.

Some values, such as `architecture`, are unlikely to be directly provided by the driver. As such, User Agents are expected to make a best-effort at identifying and reporting common architectures, and report empty string otherwise.

### Iframe controls

In addition to using the above mechanisms to hit a balance between offering developers useful information and mitigating fingerprinting concerns, [Permissions Policy](https://w3c.github.io/webappsec-permissions-policy/) should be used to control whether or not WebGPU features are exposed to iframes.

The recommended feature identifier is `"webgpu"`, and the [default allowlist](https://w3c.github.io/webappsec-permissions-policy/#default-allowlist) for this feature would be `["self"]`. This allows documents from the top level browsing context use the feature by default, but requires documents included in iframes to be explicitly granted permission from the top level context in order to use WebGPU, like so:

```html
<iframe src="https://example.com/embed" allow="webgpu"></iframe>
```

If the `"webgpu"` feature is not granted to a page, all calls that page makes to `navigator.gpu.requestAdapter()` will resolve to `null`.

This helps strike a balance between enabling powerful rendering and computation capabilities on the web and a desire to mitigate abuse by bad actors.

## Proposed IDL

```webidl
partial interface GPUAdapter {
  Promise<GPUAdapterInfo> requestAdapterInfo(optional sequence<DOMString> unmaskHints = []);
};

interface GPUAdapterInfo {
  DOMString vendor;
  DOMString architecture;
  DOMString device;
  DOMString description;
};
```

## Appendix A: Alternatives considered

### A single identifier string
Previously the WebGPU spec had a single string identifier, `GPUAdapter.name`, which would have reported a string very similar to the values reported by `WEBGL_debug_renderer_info`. [Concerns were raised about this approach](https://github.com/gpuweb/gpuweb/issues/2191), and the group generally agreed that we wanted something with finer grained control over the values reported and that was less problematic to parse for developers.

### Force reliance on feature detection
It was suggested that, similar to other web platform features, no identifiers should be exposed at all and instead developers should rely on feature tests to determine if they need to take a different code path. Unfortunately this is impractical for GPU APIs such as WebGPU or WebGL. There have been multiple documented bugs in the past that are not trivially detectable, such as bugs which are only provoked under high memory usage situations or which only occur intermittently over long time periods. In addition, reading back information from the GPU in order to detect certain classes of issues is not trivial, and in some cases may actually change the driver's behavior.

This means that realtime bug detection can be extremely costly, and may incur performance penalties or add significantly to startup time. As such it is not desirable or practical to ask developers to try and provoke any known driver issues on application startup.

### Rely on the UA, etc. to fix bugs
It was also suggested that developers should generally not be the ones shouldering the burden of detecting and working around driver or hardware issues, and instead that responsibility should lie with the hardware manufacturer, OS, or User Agent. In general we agree with this sentiment! User agents, in particular, have a history of implementing workarounds for issues observed on a specific OS, GPU, or driver, as well as working with the appropriate parties to ensure that the problems are fixed upstream. (For example, you can see the [list of bugs that Chromium works around currently here](https://source.chromium.org/chromium/chromium/src/+/main:gpu/config/gpu_driver_bug_list.json). All modern browsers have some variation of this type of workaround list.) This is work we expect to continue in perpetuity.

However, we have also observed that developers cannot rely on platform owners alone to resolve issues. For one, no matter how quickly a user agent or hardware manufacturer responds to bug reports there will always be some period of development, testing, and deployment before developers can rely on the fix, and even then they will likely have to contend with users on older software versions for a long time. This effect is exaggerated when considering that in some cases user agents only release new updates on a yearly cadence.

In some other cases, the issue may not be one of correctness, but of performance. If a certain technique is performed by the GPU in a conformant manner but performs poorly compared to other devices it is generally not the User Agent's place to intervene. An individual developer, however, can make quality vs. performance tradeoffs that are appropriate for their application as long as they are given sufficient information to know when the tradeoff in necessary.

### Inference from other signals
There are some other properties, such as a `GPUAdapter`'s limits and available features, that could be used in some cases to infer what kind of device a developer is using. Additionally, developers could use other platform signals (user agent string, screen resolution, etc) to infer that they are on a known device which has a certain class of GPU. (For example, a specific generation iPhone.) The concern with this approach is that it encourages developers to collect _more_ identifiable user information for a less reliable result.

In practical terms it's likely that not providing adapter identifiers via WebGPU will simply encourage developers to initialize and tear down a WebGL context prior to initializing WebGPU simply to get the `WEBGL_debug_renderer_info` strings, which may return info from the incorrect adapter and is not a pattern we want to encourage.

## Appendix B: Motivating real-world use cases

These are some known use cases for GPU identifiers that we have heard of in the past. These refer to WebGL applications specifically, but we have every reason to expect that they will be applicable to WebGPU as well.

### Developer feedback on WEBGL\_debug\_renderer\_info:
Ken Russell (@kenrussell) collected quotes from various WebGL developers and reported them to the WebGL Working Group in 2019.

The following are some quoted reasons why various pages use `WEBGL_debug_renderer_info`:

**Unity**
 - Using exact GPU info+device+OS+browser to ... identify weak fillrate systems for whether to use "SD" or "HD" rendering

**Uber**
 - Use this feature to activate nVidia/Intel specific GLSL workarounds.
 - Print the driver in the console when we create contexts, so that when remote operators (e.g. in Asia/Australia) report problems we can ... unblock them with minimal effort.

**[Sketchfab](https://sketchfab.com)**
 - Report user GPU in our automatic error reporting tools. When we need to reproduce shader bugs it's invaluable.
 - Warn users when they are switched to software webgl acceleration. "Otherwise users might think the Sketchfab render is very slow, using their laptop batteries, and pushing laptop fan to the max where just restarting/reloading chrome fixes it."

**[Scirra](https://www.construct.net/en)**
 - identifying GPUs affected by driver bugs, and working around it
 - analytics on the unmasked renderer to identify the impact of such bugs and help us decide how to respond
 - identifying which GPU is really in use on dual-GPU systems
 - displaying it to the user as a diagnostic (also for them to identify which GPU is in use)."

**[Figma](https://www.figma.com/)**
 - Rely on this feature to be able to track down and detect obscure GPU issues with users that have old unreliable hardware.
 - "Without this information, we would have been unable to debug and fix these WebGL implementation bugs that we've been encountering."
 - Use this information to enable workarounds for WebGL implementation bugs. "The workarounds are not enabled by default because they are slower, and in some cases actually even incorrect (but less incorrect than when the bug is triggered)."

**[noclip.website](https://noclip.website/)**
 - detect and work around known bugs in drivers
 - provide better error messages to users
 - "The immediate impact if this extension was removed would be that all Apple devices would fail to render." (Due to a driver bug at the time.)

### Tweets replying to [Dean Jackson's](https://twitter.com/grorgwork/status/1062395616867700736) inquiry about removing WEBGL\_debug\_renderer\_info:

 - Google maps, [to identify poorly performing devices.](https://twitter.com/gfxprogrammer/status/1062422760662528000?s=20)
 - [Active Theory](https://activetheory.net/), [to scale visual quality](https://twitter.com/michaeltheory/status/1062402110396874752?s=20)
 - [2DKit](http://2dkit.com/), [to estimate available memory and scale quality](https://twitter.com/b_garcia/status/1062413508212600832?s=20)
 - [Matterport](https://matterport.com/), [to identify when to serve higher resolution textures](https://twitter.com/haeric/status/1134155677411110913?s=20)

## Appendix C: API Prior Art

### Native equivalents:
The following structures are what expose similar information in the various native libraries, though they obviously don't have the same privacy considerations. Included here as reference.
 - [VkPhysicalDeviceProperties](https://www.khronos.org/registry/vulkan/specs/1.2-extensions/man/html/VkPhysicalDeviceProperties.html)
 - [DXGI_ADAPTER_DESC](https://docs.microsoft.com/en-us/windows/win32/api/dxgi/ns-dxgi-dxgi_adapter_desc)
 - [MTLDevice](https://developer.apple.com/documentation/metal/mtldevice)

### Prior art on the Web Platform:
[User-Agent client hints](https://web.dev/user-agent-client-hints/), and especially [NavigatorUAData.getHighEntropyValues()](https://developer.mozilla.org/en-US/docs/Web/API/NavigatorUAData/getHighEntropyValues), have been introduced previously as a more privacy preserving and developer friendly alternative to UA string parsing.
