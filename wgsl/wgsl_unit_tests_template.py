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

from wgsl_unit_tests import Case, XFail, MatchCase

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
    Case ("const z = a<b,c>==d;",name="template equals ident"),
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

UNMATCHED = ''
match_cases = [
    # Match result of UNMATCHED, i.e. the empty string, means there were no 'template_list'
    # nodes in the tree.
    MatchCase("const z = a<b;","template_list",UNMATCHED,name="exposed <"),
    MatchCase("const z = a>b;","template_list",UNMATCHED,name="exposed >"),
    MatchCase("const z = (a<b)>c;","template_list",UNMATCHED,name="nested initial <"),
    MatchCase("const z = a<(b>c);","template_list",UNMATCHED,name="nested final >"),

    MatchCase("const z = a( b<c,  d>(e));","template_list","template_list:<c,  d>"),
    MatchCase("const z = a((b<c), d>(e));","template_list",UNMATCHED,"nested initial <, exposed final >"),

    MatchCase("const z = a<b[c];","temlate_list",UNMATCHED),
    MatchCase("const z = a<b[select(1,2,c>(d))];","template_list",UNMATCHED),
    MatchCase("const z = a<b[c>(d)];","template_list",UNMATCHED),
    MatchCase("fn z() {if a < b {} else if c > d {}}","template_list",UNMATCHED,name="stop at braces"),

    # Test interaction with lower-precedence expression operators: && and ||
    MatchCase("const z = a<b&&c>(d);","template_list",UNMATCHED,name="&&"),
    MatchCase("const z = a<b||c>(d);","template_list",UNMATCHED,name="||"),
    MatchCase("const z = a<(b&&c)>(d);","template_list","template_list:<(b&&c)>",name="(&&)"),
    MatchCase("const z = a<(b||c)>(d);","template_list","template_list:<(b||c)>",name="(||)"),

    MatchCase("const z = a<b>();","template_list","template_list:<b>",name="templated value constructor"),
    # e.g. This next test says the outermost template_list node exists, and corresponds to <vec3<i32,5> in the source.
    MatchCase("alias z = array<vec3<i32>,5>;","template_list","template_list:<vec3<i32>,5>",name="nested outer"),
    # E.g. This next test syas there is a template_list node that has an inner template_list node, and that inner node maps to the source text <i32>
    MatchCase("alias z = array<vec3<i32>,5>;","//template_list//template_list","template_list:<i32>",name="nested inner"),
    MatchCase("const z = a<1+2>();","template_list","template_list:<1+2>"),
    MatchCase("const z = a<1,b>();","template_list","template_list:<1,b>"),
    MatchCase("const z = a<b,c>==d;","template_list","template_list:<b,c>"),

    # Check valid parses with things that start with '<' in a template list.

    # This is a comparison of a less-than b<c>()
    MatchCase("const z = a<b<c>();","ident","ident:z ident:a ident:b ident:c"),
    MatchCase("const z = a<b<c>();","template_elaborated_ident","template_elaborated_ident:a template_elaborated_ident:b<c>"),
    MatchCase("const z = a<b<c>();","template_list","template_list:<c>"),
    # This is a nested template list
    MatchCase("const z = a<b<c>>();","template_list","template_list:<b<c>>"),
    MatchCase("const z = a<b<c>>();","template_list//template_list","template_list:<c>"),
    MatchCase("const z = a<b<c>()>();","template_list","template_list:<b<c>()>"),
    MatchCase("const z = a<b<c>()>();","template_list//template_list","template_list:<c>"),
    # Check '<='
    #   There is a template_list in the parse tree, corresponding to <b<=c> in the source text.
    #   The point is that the code points <= is recognized as an operator in the middle of an expression b<=c.
    MatchCase("alias z = a<b<=c>;",  "template_list","template_list:<b<=c>",name="template arg <="),
    MatchCase("alias z = a<(b<=c)>;","template_list","template_list:<(b<=c)>",name="template arg nested <="),
    # Check shifts
    XFail("alias z = a<b>>c>;",name="template arg >> ends template"),
    MatchCase("alias z = a<b<<c>;",     "template_list","template_list:<b<<c>",name="template arg << is shift"),
    MatchCase("alias z = a<(b>>c)>;",   "template_list","template_list:<(b>>c)>",name="tempalte arg nested >> is shift"),
    MatchCase("alias z = a<(b<<c)>;",   "template_list","template_list:<(b<<c)>",name="tempalte arg nested << is shift"),
    # The Treesitter scanner handles identifier..shift differently from number..shift
    MatchCase("alias z = a<1<<c>;",     "template_list","template_list:<1<<c>", name="template arg after 1 << is shift"),
    MatchCase("alias z = a<1<<c<d>()>;","template_list","template_list:<1<<c<d>()>",name="template arg after 1 << is shift followed by templated value constructor"),
    MatchCase("alias z = a<1<<c<d>()>;","template_list//template_list","template_list:<d>",name="template arg after 1 << is shift followed by templated value constructor"),
]

cases.extend(match_cases)
