#!/usr/bin/env python3

"""generate-reserved-words.py - print WGSL reserved words

Usage: python3 generate-reserved-words.py [--plain]

Output goes to the standad output stream.

By default, the list is printed as a grammar rule inside
a <div> elment, meant to be included in the Bikeshed source
for the WGSL specification.

When option --plain is used, print the words as plain text,
one word per line.
"""

from collections import defaultdict
import argparse
import sys

def make_unique(L):
    return sorted(list(set(L)))

def digest(text):
    """Converts a text blob into a sorted list of words, split by whitespace"""
    return make_unique(filter(lambda s: len(s) > 0,[s.strip() for s in text.split()]))

def deliberately_unreserved():
    """Returns a list of deliberately unreserved words"""
    result = []

    # https://github.com/gpuweb/gpuweb/issues/2632
    result.append('box')

    # https://github.com/gpuweb/gpuweb/issues/2768
    result.extend(digest("""
              buffer
              texture
              in
              out
              output
              input
              """))

    # Don't reserve context-dependent names.
    # https://github.com/gpuweb/gpuweb/issues/3166
    # See WGSL 15.4 Context-Dependent Name Tokens
    # The swizzle names are not included because nothing
    # wants to reserve them anyway.
    result.extend(digest("""
              align
              binding
              builtin
              compute
              const
              fragment
              group
              id
              interpolate
              invariant
              location
              size
              vertex
              workgroup_size

              perspective
              linear
              flat

              center
              centroid
              sample
              first
              either

              vertex_index
              instance_index
              position
              front_facing
              frag_depth
              local_invocation_id
              local_invocation_index
              global_invocation_id
              workgroup_id
              num_workgroups
              sample_index
              sample_mask

              read
              write
              read_write

              function
              private
              workgroup
              uniform
              storage
              handle

              rgba8unorm
              rgba8snorm
              rgba8uint
              rgba8sint
              rgba16uint
              rgba16sint
              rgba16float
              r32uint
              r32sint
              r32float
              rg32uint
              rg32sint
              rg32float
              rgba32uint
              rgba32sint
              rgba32float


              f16
              bgra8unorm

              """))

        # Don't reserve these keywords from C++
    result.extend(digest("""
              char
              char16_t
              char32_t
              char8_t
              double
              float
              int
              long
              short
              signed
              unsigned
              void
              wchar_t

              """))

    # Don't reserve these words from GLSL
    result.extend(digest("""
              inout
              long short half
              long short half fixed unsigned superp
              hvec2 hvec3 hvec4 fvec2 fvec3 fvec4
              sampler3DRect
              """))
    result.extend(digest("""
              atomic_uint
              int void bool float double
              vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4
              uint uvec2 uvec3 uvec4
              dvec2 dvec3 dvec4
              mat2 mat3 mat4
              mat2x2 mat2x3 mat2x4
              mat3x2 mat3x3 mat3x4
              mat4x2 mat4x3 mat4x4
              dmat2 dmat3 dmat4
              dmat2x2 dmat2x3 dmat2x4
              dmat3x2 dmat3x3 dmat3x4
              dmat4x2 dmat4x3 dmat4x4
              sampler1D sampler1DShadow sampler1DArray sampler1DArrayShadow
              isampler1D isampler1DArray usampler1D usampler1DArray
              sampler2D sampler2DShadow sampler2DArray sampler2DArrayShadow
              isampler2D isampler2DArray usampler2D usampler2DArray
              sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect
              sampler2DMS isampler2DMS usampler2DMS
              sampler2DMSArray isampler2DMSArray usampler2DMSArray
              sampler3D isampler3D usampler3D
              samplerCube samplerCubeShadow isamplerCube usamplerCube
              samplerCubeArray samplerCubeArrayShadow
              isamplerCubeArray usamplerCubeArray
              samplerBuffer isamplerBuffer usamplerBuffer
              image1D iimage1D uimage1D
              image1DArray iimage1DArray uimage1DArray
              image2D iimage2D uimage2D
              image2DArray iimage2DArray uimage2DArray
              image2DRect iimage2DRect uimage2DRect
              image2DMS iimage2DMS uimage2DMS
              image2DMSArray iimage2DMSArray uimage2DMSArray
              image3D iimage3D uimage3D
              imageCube iimageCube uimageCube
              imageCubeArray iimageCubeArray uimageCubeArray
              imageBuffer iimageBuffer uimageBuffer
              texture1D texture1DArray
              itexture1D itexture1DArray utexture1D utexture1DArray
              texture2D texture2DArray
              itexture2D itexture2DArray utexture2D utexture2DArray
              texture2DRect itexture2DRect utexture2DRect
              texture2DMS itexture2DMS utexture2DMS
              texture2DMSArray itexture2DMSArray utexture2DMSArray
              texture3D itexture3D utexture3D
              textureCube itextureCube utextureCube
              textureCubeArray itextureCubeArray utextureCubeArray
              textureBuffer itextureBuffer utextureBuffer
              sampler samplerShadow
              subpassInput isubpassInput usubpassInput
              subpassInputMS isubpassInputMS usubpassInputMS
              """))

    # Don't reserve from HLSL
    # https://github.com/gpuweb/gpuweb/pull/3615 Don't reserve: line lineadj point
    result.extend(digest("""
              AppendStructuredBuffer
              BlendState
              Buffer ByteAddressBuffer
              cbuffer
              CompileShader ComputeShader ConsumeStructuredBuffer
              DepthStencilState DepthStencilView double DomainShader
              dword
              false float
              GeometryShader
              half Hullshader
              InputPatch int
              line lineadj
              LineStream
              matrix min16float min10float min16int min12int min16uint
              OutputPatch
              point
              PixelShader PointStream
              RasterizerState RenderTargetView row_major RWBuffer RWByteAddressBuffer RWStructuredBuffer RWTexture1D RWTexture1DArray RWTexture2D RWTexture2DArray RWTexture3D
              sampler SamplerState SamplerComparisonState stateblock stateblock_state string StructuredBuffer
              tbuffer technique technique10 technique11 texture Texture1D Texture1DArray Texture2D Texture2DArray Texture2DMS Texture2DMSArray Texture3D TextureCube TextureCubeArray true triangle triangleadj TriangleStream
              uint unsigned
              vector vertexfragment VertexShader void
              texture
              sampler
              """))

    # Don't reserve type names
    # https://github.com/gpuweb/gpuweb/issues/2632
    for t in digest(""" float int uint bool
                        min10float min16float
                        min12int min16int
                        min16uint
                        """):
      result.append(t)
      for i in digest("1 2 3 4"):
          result.append("{}{}".format(t,i))
      for row in digest("1 2 3 4"):
          for col in digest("1 2 3 4"):
            result.append("{}{}{}".format(t,row,col))

    # Common scalar types, incluing bf16 for bfloat16
    result.extend(digest("""
              i8 i16 i64
              u8 u16 u64
              f64
              bf16
              """))

    # A foreseeable templated quaternion type.
    # Swift has simd_quatf and simd_quatd
    result.append('quat')

    # Don't reserve words that generate types
    # https://github.com/gpuweb/gpuweb/issues/2632
    result.extend(digest("""
              bool
              i32 u32 f32
              f16
              vec2 vec3 vec4
              mat2x2 mat2x3 mat2x4
              mat3x2 mat3x3 mat3x4
              mat4x2 mat4x3 mat4x4
              ptr
              atomic
              array

              texture_1d
              texture_2d
              texture_2d_array
              texture_3d
              texture_cube
              texture_cube_array

              texture_multisampled_2d

              texture_external

              texture_storage_1d
              texture_storage_2d
              texture_storage_2d_array
              texture_storage_3d

              texture_depth_2d
              texture_depth_2d_array
              texture_depth_cube
              texture_depth_cube_array
              texture_depth_multisampled_2d

              sampler
              sampler_comparison
              """))

    return make_unique(result)

def cpp():
    # C++ keywords
    # Extracted from working draft at https://eel.is/c++draft/
    #  https://eel.is/c++draft/gram.lex#nt:keyword
    #   "Any identifier listed in Table 5" plus import, module, export
    #        https://eel.is/c++draft/tab:lex.key
    #
    return digest("""
              export
              import
              module

              alignas
              alignof
              asm
              auto
              bool
              break
              case
              catch
              char
              char16_t
              char32_t
              char8_t
              class
              co_await
              co_return
              co_yield
              concept
              const
              const_cast
              consteval
              constexpr
              constinit
              continue
              decltype
              default
              delete
              do
              double
              dynamic_cast
              else
              enum
              explicit
              export
              extern
              false
              float
              for
              friend
              goto
              if
              inline
              int
              long
              mutable
              namespace
              new
              noexcept
              nullptr
              operator
              private
              protected
              public
              register
              reinterpret_cast
              requires
              return
              short
              signed
              sizeof
              static
              static_assert
              static_cast
              struct
              switch
              template
              this
              thread_local
              throw
              true
              try
              typedef
              typeid
              typename
              union
              unsigned
              using
              virtual
              void
              volatile
              wchar_t
              while

              """)

# Rust
# https://doc.rust-lang.org/reference/keywords.html#reserved-keywords
# We include strict, reserved, and weak
# Excludes 'strict because it starts with a single quote.

def rust():
    # Rust
    # https://doc.rust-lang.org/reference/keywords.html#reserved-keywords
    # We include strict, reserved, and weak
    # Excludes 'strict because it starts with a single quote.

    return digest("""
              as
              break
              const
              continue
              crate
              else
              enum
              extern
              false
              fn
              for
              if
              impl
              in
              let
              loop
              match
              mod
              move
              mut
              pub
              ref
              return
              self
              Self
              static
              struct
              super
              trait
              true
              type
              unsafe
              use
              where
              while

              abstract
              become
              box
              do
              final
              macro
              override
              priv
              typeof
              unsized
              virtual
              yield

              macro_rules
              union

              """)

def smalltalk():
    return digest(" nil self super true false ");

def ecmascript_5_1():
    # ECMAScript
    #  https://262.ecma-international.org/5.1/#sec-7.6.1.1
    # Keywords, Reserved, FutureReserved
    return digest("""

              break
              case
              catch
              continue
              debugger
              default
              delete
              do
              else
              finally
              for
              function
              if
              in
              instanceof
              new
              return
              switch
              this
              throw
              try
              typeof
              var
              void
              while
              with


              class
              const
              enum
              export
              extends
              import
              super


              implements
              interface
              let
              package
              private
              protected
              public
              static
              yield

              """)

def ecmascript_2022():
    # https://tc39.es/ecma262/ retrieved 2022-02-24
    return digest("""
              break case catch class const continue debugger default delete
              do else enum export extends false finally for function if import
              in instanceof new null return super switch this throw true try
              typeof var void while with

              await yield
              let static implements interface package private protected public
              as async from get meta of set target
              """)

def glsl_4_6():
    # GLSL 4.6
    return digest("""
        const uniform buffer shared attribute varying
        coherent volatile restrict readonly writeonly
        atomic_uint
        layout
        centroid flat smooth noperspective
        patch sample
        invariant precise
        break continue do for while switch case default
        if else
        subroutine
        in out inout
        int void bool true false float double
        discard return
        vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4
        uint uvec2 uvec3 uvec4
        dvec2 dvec3 dvec4
        mat2 mat3 mat4
        mat2x2 mat2x3 mat2x4
        mat3x2 mat3x3 mat3x4
        mat4x2 mat4x3 mat4x4
        dmat2 dmat3 dmat4
        dmat2x2 dmat2x3 dmat2x4
        dmat3x2 dmat3x3 dmat3x4
        dmat4x2 dmat4x3 dmat4x4
        lowp mediump highp precision
        sampler1D sampler1DShadow sampler1DArray sampler1DArrayShadow
        isampler1D isampler1DArray usampler1D usampler1DArray
        sampler2D sampler2DShadow sampler2DArray sampler2DArrayShadow
        isampler2D isampler2DArray usampler2D usampler2DArray
        sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect
        sampler2DMS isampler2DMS usampler2DMS
        sampler2DMSArray isampler2DMSArray usampler2DMSArray
        sampler3D isampler3D usampler3D
        samplerCube samplerCubeShadow isamplerCube usamplerCube
        samplerCubeArray samplerCubeArrayShadow
        isamplerCubeArray usamplerCubeArray
        samplerBuffer isamplerBuffer usamplerBuffer
        image1D iimage1D uimage1D
        image1DArray iimage1DArray uimage1DArray
        image2D iimage2D uimage2D
        image2DArray iimage2DArray uimage2DArray
        image2DRect iimage2DRect uimage2DRect
        image2DMS iimage2DMS uimage2DMS
        image2DMSArray iimage2DMSArray uimage2DMSArray
        image3D iimage3D uimage3D
        imageCube iimageCube uimageCube
        imageCubeArray iimageCubeArray uimageCubeArray
        imageBuffer iimageBuffer uimageBuffer
        struct
        texture1D texture1DArray
        itexture1D itexture1DArray utexture1D utexture1DArray
        texture2D texture2DArray
        itexture2D itexture2DArray utexture2D utexture2DArray
        texture2DRect itexture2DRect utexture2DRect
        texture2DMS itexture2DMS utexture2DMS
        texture2DMSArray itexture2DMSArray utexture2DMSArray
        texture3D itexture3D utexture3D
        textureCube itextureCube utextureCube
        textureCubeArray itextureCubeArray utextureCubeArray
        textureBuffer itextureBuffer utextureBuffer
        sampler samplerShadow
        subpassInput isubpassInput usubpassInput
        subpassInputMS isubpassInputMS usubpassInputMS
        """)


def glsl_4_6_reserved():
    # GLSL 4.6's reserved word list
    return digest("""
        common partition active
        asm
        class union enum typedef template this
        resource
        goto
        inline noinline public static extern external interface
        long short half fixed unsigned superp
        input output
        hvec2 hvec3 hvec4 fvec2 fvec3 fvec4
        filter
        sizeof cast
        namespace using
        sampler3DRect
        """)

def hlsl():
    # HLSL
    # https://docs.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-appendix-keywords
    # Retrieved 2022-02-24
    return digest("""
        asm asm_fragment
        BlendState bool break
        case cbuffer centroid class column_major compile compile_fragment CompileShader const continue ComputeShader ConsumeStructuredBuffer
        default DepthStencilState DepthStencilView discard do double DomainShader dword
        else export extern
        false float for fxgroup
        GeometryShader groupshared
        half Hullshader
        if in inline inout InputPatch int interface
        line lineadj linear LineStream
        matrix min16float min10float min16int min12int min16uint
        namespace nointerpolation noperspective NULL
        out OutputPatch
        packoffset pass pixelfragment PixelShader point PointStream precise
        RasterizerState RenderTargetView return register row_major RWBuffer RWByteAddressBuffer RWStructuredBuffer RWTexture1D RWTexture1DArray RWTexture2D RWTexture2DArray RWTexture3D
        sample sampler SamplerState SamplerComparisonState shared snorm stateblock stateblock_state static string struct switch StructuredBuffer
        tbuffer technique technique10 technique11 texture Texture1D Texture1DArray Texture2D Texture2DArray Texture2DMS Texture2DMSArray Texture3D TextureCube TextureCubeArray true typedef triangle triangleadj TriangleStream
        uint uniform unorm unsigned
        vector vertexfragment VertexShader void volatile
        while
        texture
        sampler
        """)

def wgsl():
    # Already in use by WGSL
    return digest("""
        break
        case
        centroid
        const
        continue
        continuing
        default
        diagnostic
        discard
        else
        enable
        false
        flat
        fn
        for
        function
        if
        let
        linear
        loop
        override
        private
        ptr
        return
        requires
        sample
        storage
        struct
        switch
        true
        uniform
        var
        while
        workgroup
        """)

def wgsl_reserved():
   return digest("""
        asm
        demote
        demote_to_helper
        do
        enum
        fallthrough
        noncoherent
        non_coherent
        null
        premerge
        require
        regardless
        std
        typedef
        unless
        using
        wgsl
        """)

def generate_reserved_list():
    # Key is a reserved word, value is the reason it is reserved.
    reserved_by = defaultdict(list)
    def add_from(lang, words):
        for w in words:
            reserved_by[w].append(lang)

    add_from('C++', cpp())
    add_from('ECMAScript-5.1', ecmascript_5_1())
    add_from('ECMAScript-2022', ecmascript_2022())
    add_from('Rust', rust())
    add_from('Smalltalk', smalltalk())
    add_from('HLSL', hlsl())
    add_from('GLSL-4.6', glsl_4_6())
    add_from('GLSL-4.6-reserved', glsl_4_6_reserved())
    add_from('WGSL', wgsl_reserved())

    # Remove keywords already used in WGSL, or deliberately unreserved words.
    for w in wgsl() + deliberately_unreserved():
        reserved_by.pop(w, None)

    return reserved_by
    
def generate_reserved_words(mode):
    reserved_by = generate_reserved_list()
    if mode == 'plain':
        for w in make_unique(reserved_by.keys()):
            print(f"{w}")
        return None
    if mode == 'bikeshed':
        # Emit Bikeshed text
        print("""<div class='syntax' noexport='true'>
  <dfn for=syntax>_reserved</dfn> :
""")
        for w in make_unique(reserved_by.keys()):
            print(f"    | `'{w}'`   <!-- {' '.join(reserved_by[w])} -->\n")

        print("</div>")
        return None
    raise RuntimeError("Invalid geneeration mode")


        

def main():
    argparser = argparse.ArgumentParser(
            prog="generate-reserved-words.py",
            description="Generate the reserved words list. By default it's in ")
    argparser.add_argument("--plain",
                           action='store_true',
                           help="Emit the list in plain text format, one word per line.")

    args = argparser.parse_args()
    generate_reserved_words('plain' if args.plain else 'bikeshed')


if __name__ == '__main__':
    sys.exit(main())
