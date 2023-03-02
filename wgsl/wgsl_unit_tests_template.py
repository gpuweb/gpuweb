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
    Case ("const abc=0;"),
    Case ("const z = a<b;",name="exposed <"),
    Case ("const z = a>b;",name="exposed >"),
    Case ("const z = (a<b)>c;",name="nested initial <"),
    Case ("const z = a<(b>c);",name="nested final >"),
    Case ("const z = a((b<c), d>(e));"),
    Case ("const z = a<b[c];",name="a less than b array element simple index: const"),
    XFail("alias z = a<b[c];",name="a less than b array element simple index: alias"),
    Case ("const z = a<b[select(1,2,c>(d))];",name="a less than b array element select"),
    Case ("const z = a<b[c>(d)];",name="a less than b array element complex index"),
    XFail("alias z = a<b;c>d();",name="plain ;"),
    Case ("fn z() {if a < b {} else if c > d {}}"),
    XFail("alias z = a<b&&c>;",name="&& with unexpected trailing >"),
    Case ("const z = a<b&&c>d;",name="&&"),
    XFail("alias z = a<b||c>;",name="|| with unexpected trailing >"),
    Case ("const z = a<b||c>d;",name="||"),
    XFail("alias z = a<b<c||d>>;",name="|| terminates template list"),

    Case ("const z = a<b>();",name="templated value constructor"),
    XFail("alias z = a<b>c;"),
    XFail("alias z = a<b>=c;"),
    XFail("alias z = a<b>>=c;"),
    Case ("alias z = vec3<i32>;"),
    Case ("const z = vec3<i32>();"),
    Case ("alias z = array<vec3<i32>,5>;"),
    Case ("const z = a(b<c, d>(e));"),
    Case ("const z = a<1+2>();"),
    Case ("const z = a<1,b>();"),
    XFail("const z = a<b,c>=d;"),
    Case ("const z = a<b,c>==d;",name="template equals ident"), # Not in Tint
    XFail("const z = a<b,c>=d>();"),
    XFail("alias z = a<b<c>>=;"),
    XFail("const z = a<b>c>();",name="premature end at b>c"),
    Case ("const z = a<b<c>();"),
    Case ("const z = a<b<c>>();"),
    Case ("const z = a<b<c>()>();"),
    XFail("alias z = a<b>.c;"),
    Case ("alias z = a<(b&&c)>;"),
    XFail("alias z = a<(b&&c)>d;"),
    Case ("alias z = a<(b||c)>;"),
    XFail("alias z = a<(b||c)>d;"),
    Case ("alias z = a<b<(c||d)>>;"),
    Case ("alias z = a<b<=c>;",name="template arg <="),
    Case ("alias z = a<(b<=c)>;",name="template arg nested <="),
    XFail("alias z = a<b>>c>;",name="template arg >> ends template"),
    Case ("alias z = a<b<<c>;",name="template arg << is shift"),
    Case ("alias z = a<(b>>c)>;",name="tempalte arg nested >> is shift"),
    Case ("alias z = a<(b<<c)>;",name="tempalte arg nested << is shift"),
    Case ("alias z = a<1<<c>;",name="template arg after 1 << is shift"),
    Case ("alias z = a<1<<c<d>()>;",name="template arg after 1 << is shift followed by templated value constructor"),
]
