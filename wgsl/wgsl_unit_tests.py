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
from TSPath import TSPath

SCRIPT='wgsl_unit_tests.py'

class Case:
    """
    A test case
    """
    def __init__(self,text,expect_pass=True,name=""):
        self.text = text
        self.expect_pass = (expect_pass == True)
        self.name = name

    def __str__(self):
        expectation = "expect_pass" if self.expect_pass else "expect_fail"
        return "Case:{}:{}\n---\n{}\n---".format(expectation,self.name,self.text)

    def run(self,parser):
        tree = parser.parse(bytes(self.text,"utf8"))
        if self.expect_pass == tree.root_node.has_error:
            return (False,"parsing failed: {}".format(tree.root_node.sexp()))
        return (True,tree)

class XFail(Case):
    def __init__(self,text,name=''):
        super().__init__(text,expect_pass=False,name=name)

class MatchCase(Case):
    def __init__(self,text,path,expect,name=""):
        super().__init__(text,expect_pass=True,name=name)
        self.path = TSPath(path)
        self.expect = expect

    def run(self,parser):
        (ok,tree) = super().run(parser)
        if ok:
            matched_nodes = self.path.match(tree)
            got = " ".join(["{}:{}".format(x.type,x.text.decode("utf-8")) for x in matched_nodes])
            if got != self.expect:
                return (False, "\n{}\nexpect {}\ngot    {}\nin {}".format(str(self.path),self.expect,got,tree.root_node.sexp()))
        return (ok,tree)

def GetCases():
    import wgsl_unit_tests_simple
    import wgsl_unit_tests_enable
    import wgsl_unit_tests_equals
    import wgsl_unit_tests_template
    cases = []
    cases.extend(wgsl_unit_tests_simple.cases)
    cases.extend(wgsl_unit_tests_enable.cases)
    cases.extend(wgsl_unit_tests_equals.cases)
    cases.extend(wgsl_unit_tests_template.cases)
    return cases

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
    for case in GetCases():
        num_cases += 1
        print(".",flush=True,end='')
        if options.verbose:
            print(case)
        (ok,err) = case.run(parser)
        if not ok:
            num_errors += 1
            print("FAIL:", case, err)
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
