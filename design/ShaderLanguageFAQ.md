# FAQ: WebGPU direction on shader language

## What is the shader language for WebGPU?

WebGPU will use a new shader language “WebGPU Shader Language”,
or “WGSL” for short. This is a shading language which is designed specifically
for, and in tandem with, WebGPU.

It is under development, but will have the following traits:

*   It is a text-based language.
*   It is suitable for humans to read and write.
*   It is strongly typed.
*   It directly represents block-structured programming, including
    sequence, selection (if/else), and repetition (looping).
*   It can be faithfully and simply converted to and from SPIR-V
    which only uses features available in WebGPU.
*   It can be faithfully and simply converted to Metal Shading Language
    which only uses features available in WebGPU.
*   It can be faithfully and simply converted to HLSL
    which only uses features available in WebGPU.

The W3C WebGPU community group agreed to this direction during the
February 2020 face-to-face meeting in Redmond.


## How do you pronounce “WGSL”?

The W3C WebGPU Community Group does not prescribe a particular
pronunciation of “WGSL”.

You can say it letter-by-letter, like “W G S L” or you can say it as a single word, like “wiggzle”, “wiggles”, or “wigsel”.


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

This syntax is still under heavy development.
If you have ideas for improvement, or constructive criticism,
please file issues on the [issue tracker](https://github.com/gpuweb/gpuweb/issues/new?assignees=&labels=wgsl&template=wgsl.md&title=).

## Where can I find the spec?

The WGSL spec will be developed on the WebGPU Community Group area on GitHub.
See https://github.com/gpuweb/gpuweb/tree/master/wgsl


## What browsers support WGSL?

WGSL is the shader language for WebGPU.
Any browser implementing WebGPU will be required to accept shaders in WGSL.
Specifically, the WebGPU conformance test suite will only use shaders written
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

The WebGPU Community Group itself is not working on any compilers or other tooling which produce WGSL.
However, WGSL is intentionally designed to not deviate much from the facilities, concepts,
syntax, and behavior of existing shading languages (see the language design
goals above), in order to enable the rapid and easy development of compilers to and from WGSL.

For developers invested in the SPIR-V ecosystem for Vulkan and OpenGL will benefit convertibility between WGSL and SPIR-V. For shaders that only use WebGPU features, some WebGPU Community Group members expect to develop tooling to faithfully convert between WGSL and "Shader" SPIR-V. By "faithful", we mean that all salient properties of a shader should be preserved by a round trip conversion between the two ways of writing the shader: e.g. it should retain its general semantics and performance characteristics. Furthermore, those WebGPU Community Group members plan to add an option to existing mainstream SPIR-V compilers to emit WGSL directly.

For developers invested in HLSL for DirectX or Metal Shading Language for Metal, the WebGPU Community Group welcomes the community to create new compilers or extend existing tools to produce WGSL.

WGSL is a new language. Over time, we expect a collection of compilers will
be created to compile between WGSL and most/all other popular shading
languages. We also expect an ecosystem of shading language tools, like
optimizers, compressors, preprocessors, fuzzers, etc. will be created for WGSL.
