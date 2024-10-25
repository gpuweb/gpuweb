#!/usr/bin/env python3
#
# Copyright 2023 Google LLC
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of works must retain the original copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the original
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#
# 3. Neither the name of the W3C nor the names of its contributors
# may be used to endorse or promote products derived from this work
# without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from wgsl_unit_tests import Case, XFail

cases = [
    XFail("this fails"),
    XFail("#version 450"),
    Case("const pi = 3.14;"),
    Case("const b = bitcast<i32>(1u);"),
    Case("var s: sampler;"),
    Case("@group(0) @binding(0) var s: sampler;"),
    Case("var<workgroup> w: i32;"),
    Case("fn foo() {var f: i32;}"),
    Case("var<workgroup> w: array<vec3<f32>,1>;"),
    Case("var<workgroup> w: array<vec3<f32>,(vec<i32>(1).x)>;"), # vec<i32> treated like generic template invocation. Should fail in semantic checks.
    Case( "var<workgroup> w: array<vec3<f32>,(vec3<i32>(1).x)>;"),
    XFail("const c = array<a>b>;"),
    Case("var c : array<f32,(a>b)>;"),
    Case("const a = array<i32,select(1,2,(a>b))>();"),
    Case("const b = array<i32,select(1,2,a>b)>();"),
    XFail("const d : array<select(1,2,a>b)>();"),
    Case("fn main(){i=1;}"),
    Case("fn main(){var i:i32; i=1;}"),
    Case("var w: array<f32,1>;"),
    Case("var w: array<vec3<f32>,1>;"),
    Case("var w: vec3<f32>;"),
    Case("alias t = vec3<f32>;"),
    Case("alias t = vec3<float>;"),
    Case("alias t = array<t,(1<2)>;"),
    Case("var c : array<t,(1<2)>;"),
    Case("var c : array<(a>b)>;"), # Parses ok, but should fail in semantic check: (a>b) is not a type.
    Case("fn f(p: ptr<function,i32>) {}"),
    Case("fn m(){x++;}"),
    Case("fn m(){x--;}"),
    Case("fn m(){x();}"),
]
