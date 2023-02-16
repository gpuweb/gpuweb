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


import argparse
import os
import sys
from tree_sitter import Language, Parser

SCRIPT='wgsl_unit_tests.py'

class Case:
    """
    A test case
    """
    def __init__(self,text,expect_pass=True):
        self.text = text
        self.expect_pass = (expect_pass == True)

    def __str__(self):
        expectation = "expect_pass" if self.expect_pass else "expect_fail"
        return "Case:{}:\n---\n{}\n---".format(expectation,self.text)

class XFail(Case):
    def __init__(self,text):
        super().__init__(text,expect_pass=False)

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
    XFail("var<workgroup> w: array<vec3<f32>,(vec<i32>(1).x)>;"),
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
    XFail("var c : array<(a>b)>;"), # Type specifier must start with identifier
    Case("fn f(p: ptr<function,i32>) {}"),
    Case("fn m(){x++;}"),
    Case("fn m(){x--;}"),
    Case("fn m(){x();}"),
]

class Options:
    def __init__(self,shared_lib):
        self.shared_lib = shared_lib
        self.verbose = False

def run_tests(options):
    """
    Returns True if all tests passed
    """
    global cases
    if not os.path.exists(options.shared_lib):
        raise RuntimeException("missing shared library {}",options.shared_lib)

    language = Language(options.shared_lib, "wgsl")
    parser = Parser()
    parser.set_language(language)

    print("{}: ".format(SCRIPT),flush=True,end='')

    num_cases = 0
    num_errors = 0
    for case in cases:
        num_cases += 1
        print(".",flush=True,end='')
        if options.verbose:
            print(case)
        tree = parser.parse(bytes(case.text,"utf8"))
        if case.expect_pass == tree.root_node.has_error:
            num_errors += 1
            print("**Error**")
            print(case)
            print(tree.root_node.sexp())
            print("---Case end\n",flush=True)

    print("{} pass {} fail ".format(num_cases-num_errors,num_errors),flush=True)

    return num_errors == 0

def main():
    argparser = argparse.ArgumentParser(
            prog='wgsl_grammar_test.py',
            description='Unit tests for the tree-sitter WGSL parser')
    argparser.add_argument("--verbose","-v",
                           action='store_true',
                           help="be verbose")
    argparser.add_argument("--parser",
                           help="path the shared library for the WGSL tree-sitter parser",
                           default="grammar/build/wgsl.so")

    args = argparser.parse_args()
    options = Options(args.parser)
    options.verbose = args.verbose

    if not run_tests(options):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
