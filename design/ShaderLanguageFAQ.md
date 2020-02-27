# FAQ: WebGPU direction on shader language

## What is the shader language for WebGPU?

WebGPU will use a new shader language “WebGPU Shader Language”,
or “WGSL” for short.

It is under development, but will have the following traits:

*   It is a text-based language.
*   It is suitable for humans to read and write.
*   It is strongly typed.
*   It directly represents block-structured programming, including
    sequence, selection (if/else), and repetition (looping).
*   It can be faithfully and simply converted to and from SPIR-V
    “Shader” modules that only use GPU features available in WebGPU.

The W3C WebGPU community group agreed to this direction during the
February 2020 face-to-face meeting in Redmond.


## How do you pronounce “WGSL”?

The W3C WebGPU Community Group does not prescribe a particular
pronunciation of “WGSL”.

You can say it letter-by-letter, like “W G S L”.

You can say it as a single word, like “wiggzle”, “wiggles”, or “wigsel”.


## What does a WGSL shader look like?

WGSL has not yet been specified.
However, early prototyping work indicates the language can have a look
and feel as represented in the following examples:

A simple fragment shader:


```
[[location 0]] var<out> gl_FragColor : vec4<f32>;

fn main() -> void {
    gl_FragColor = vec4<f32>(0.4, 0.4, 0.8, 1.0);
    return;
}
entry_point fragment = main;
```


A code fragment showing if/else:


```
  if (value > 5) {
    wvar = 14;
  } elseif (value > 2) {
    wvar = 12;
  } else {
    wvar = 0;
  }
```


A code fragment showing a switch:


```
switch (a) {
  case 1: {
    # The break is implicit
  }
  case 2: {
     fallthrough;
  }
  default: {
  }
}
```


A code fragment showing a loop:


```
var i : i32 = 0;
var b : f32 = 2.4;
loop {
  break if (i == 4);

  b = b * 3.2;
  continuing {
     i = i + 1;
  }
}
```



## Where can I find the spec?

The WGSL spec will be developed on the WebGPU Community Group area on GitHub.
See https://github.com/gpuweb/gpuweb/tree/master/wgsl


## What browsers support WGSL?

WGSL is the shader language for WebGPU.
Any browser implementing WebGPU will be required to accept shaders in WGSL.
Specifically, the WebGPU conformance test suite will use shaders written
in WGSL.

Browser support for WGSL is expected to be developed over time, along
with the development of WGSL itself.


## Will browsers accept other shader languages for WebGPU?

Accepting a shader language other than WGSL is not part of WebGPU.
Doing so harms interoperability, as a shader in that other language is
not portable across browsers.


## Where can I find WGSL tooling?

The WebGPU Community Group does not deliver tooling for WGSL.
However, WebGPU implementers are expected to develop tooling
for handling WGSL, including parsing, validation, and compilation.

At this time, we expect at least three essentially independent
implementations of WGSL ingestion as part of browser support for WebGPU.
Independent implementation serves as an important check on the quality
of the WGSL and WebGPU specifications.


## What about my existing shaders, compilers, and other tooling?

This is also expressed as “the last thing I need is another shader language”.
(See https://xkcd.com/927/)

For developers invested in the SPIR-V ecosystem for Vulkan and OpenGL,
the key will be convertibility between WGSL and SPIR-V.
For shaders that only use WebGPU features, WebGPU Community Group
members expect to develop tooling to faithfully convert between WGSL
and “Shader” SPIR-V.
By “faithful”, we mean that all salient properties of a shader should
be preserved by a round trip conversion between the two ways of writing
the shader: e.g. it should retain its semantics and its performance
characteristics.
Furthermore, those WebGPU Community Group members plan to add an option
to existing mainstream SPIR-V compilers to emit WGSL directly.
We expect other SPIR-V tooling (e.g. fuzzers, optimizers) can be reused,
via the addition of a conversion step between WGSL and SPIR-V at their
I/O boundaries.


