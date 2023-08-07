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
    Case("const z = a<c;",name="plain <"),
    Case("const z = a<<c;",name="plain <<"),
    Case("const z = a<=c;",name="plain <="),
    XFail("const z = a<=c>;",name="plain <= extra >: const"),
    XFail("alias z = a<=c>;",name="plain <= extra >: alias"),
    Case("fn foo() { a<<=c; }",name="plain <<="),
    Case("const z = a>c;",name="plain >"),
    Case("const z = a>>c;",name="plain >>"),
    Case("const z = a>=c;",name="plain >="),
    Case("fn foo() { a>>=c; }",name="plain >>="),
    Case("alias z = a<b<=c>;",name="template arg <="),
    Case("alias z = a<(b<=c)>;",name="template arg nested <="),
    XFail("alias z = array<f32,select(1,2,x=b)>;",name="nested assignment ="),
    XFail("alias z = array<f32,select(1,2,x+=b)>;",name="nested assignment +="),
    XFail("alias z = array<f32,select(1,2,x-=b)>;",name="nested assignment -="),
    XFail("alias z = array<f32,select(1,2,x*=b)>;",name="nested assignment *="),
    XFail("alias z = array<f32,select(1,2,x/=b)>;",name="nested assignment /="),
    XFail("alias z = array<f32,select(1,2,x%=b)>;",name="nested assignment %="),
    XFail("alias z = array<f32,select(1,2,x&=b)>;",name="nested assignment &="),
    XFail("alias z = array<f32,select(1,2,x|=b)>;",name="nested assignment |="),
    XFail("alias z = array<f32,select(1,2,x^=b)>;",name="nested assignment ^="),
    XFail("alias z = array<f32,select(1,2,x>>=b)>;",name="nested assignment >>="),
    XFail("alias z = array<f32,select(1,2,x<<=b)>;",name="nested assignment <<="),
    Case("alias z = array<f32,1<<2>;",name="exposed <<"),
    XFail("alias z = array<f32,2>>1>;",name="exposed >> prematurely closes template"),
    XFail("alias z = a<2>1>;",name="exposed > prematurely closes template"),
    Case("alias z = a<1!=2>;",name="exposed !="),
    Case("alias z = a<!2>;",name="exposed !"),
    Case("alias z = a<1==2>;",name="exposed =="),
    Case("alias a = array<f32,(2>>1)>;",name="nested >>"),
    Case("alias a = array<f32,(2<<1)>;",name="nested <<"),
    Case("alias z = array<f32,select(1,2,x>b)>;",name="nested >"),
    Case("alias z = array<f32,select(1,2,x<b)>;",name="nested <"),
    Case("alias z = array<f32,select(1,2,x==b)>;",name="nested =="),
    Case("alias z = array<f32,select(1,2,x>=b)>;",name="nested >="),
    Case("alias z = array<f32,select(1,2,x<=b)>;",name="nested <="),
    Case("alias z = array<f32,select(1,2,x!=b)>;",name="nested !="),
    XFail("alias z = a<=>;",name="if <= is skipped too early, should still fail parse"),
    XFail("alias z = a<b>=c>;",name=">= prematurely ends template"),
    Case("alias z = a<(b>=c)>;",name="template arg nested >="),
    XFail("alias z = a<b<c>>=;"),
]
