#!/usr/bin/env python3
#
# Copyright 2022 Google LLC
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

"""
Analyze a grammar, given in Treesitter JSON form
"""

import argparse
import inspect
import json
import os
import re
import subprocess
import sys

from Grammar import Grammar, PrintOption


def main():
    argparser = argparse.ArgumentParser(
            description=inspect.getdoc(sys.modules[__name__]))
    argparser.add_argument('json_file',
                           nargs='?',
                           default='grammar/src/grammar.json',
                           help='file holding the JSON form of the grammar')
    argparser.add_argument('-v', '--verbose',
                           help='increase output verbosity',
                           action="store_true")
    argparser.add_argument('-simple',
                           help='dump the grammar without canonicalization',
                           action="store_true")
    argparser.add_argument('-recursive',
                           help='dump a grammar suitable for recursive descent parsing',
                           action="store_true")
    argparser.add_argument('-bs',
                           help='output of -recursive as bikeshed source',
                           action="store_true")
    argparser.add_argument('-terminals',
                           help='print terminals in output of -recursive',
                           default=False,
                           dest='print_terminals',
                           action="store_true")
    argparser.add_argument('-aggressive',
                           help='aggressively inline single uses',
                           default=True,
                           dest='aggressive',
                           action="store_true")
    argparser.add_argument('-ll',
                           help='compute LL(1) parser table and associated conflicts',
                           action="store_true")
    argparser.add_argument('-lalr',
                           help='compute LALR(1) parser table and associated conflicts',
                           action="store_true")
    argparser.add_argument('-lr',
                           help='compute LR(1) item sets',
                           action="store_true")
    argparser.add_argument('-limit', type=int,
                           help='limit on number of LALR(1) item sets')
    args = argparser.parse_args()
    with open(args.json_file) as infile:
        json_text = "".join(infile.readlines())

    if args.simple:
        g = Grammar(json_text, 'translation_unit')
        print(g.pretty_str(multi_line_choice=True))
        sys.exit(0)

    po = PrintOption(multi_line_choice=True)
    po.more_newlines = True
    po.print_terminals = args.print_terminals
    po.bikeshed = args.bs

    printed = False
    if args.recursive:
        g = Grammar(json_text, 'translation_unit')

        g.canonicalize()

        g.eliminate_immediate_recursion()
        stop_at = {'expression','element_count_expression'}
        g.left_refactor('unary_expression',stop_at)
        g.left_refactor('ident',set())


        g.epsilon_refactor()

        inline_stop = {'ident','member_ident','ident_pattern_token','optionally_typed_ident'}
        if args.aggressive:
            g.inline_single_choice_with_nonterminal(inline_stop)
            g.dedup_rhs(inline_stop)
            g.inline_single_choice_with_nonterminal(inline_stop)
        else:
            g.inline_specific({ 'short_circuit_and_expression.post.unary_expression', 'short_circuit_or_expression.post.unary_expression'})

        # Bring together with other (star|and)* rules
        g.inline_when_toplevel_prefix({'assignment_statement'})

        # Bring together with other rules starting with attribute
        g.inline_when_toplevel_prefix({'global_constant_decl'})

        g.inline_single_starrable()

        g.refactor_post('ident')
        g.rotate_one_or_mores()

        # Get ready for potential LL analysis
        g.compute_first()
        g.compute_follow()

        print(g.pretty_str(po))
        printed = True

    else:
        g = Grammar.Load(json_text, 'translation_unit')

    if args.lalr:
        print("=Grammar:\n")
        print(g.pretty_str())
        parse_table = g.LALR1(max_item_sets=args.limit)
        parse_table.write(sys.stdout)
        if parse_table.has_conflicts():
            sys.exit(1)
        sys.exit(0)
    if args.lr:
        lr1_itemsets = g.LR1_ItemSets()
        for IS in lr1_itemsets:
            print("\n{}".format(str(IS)))
        sys.exit(0)

    elif args.ll:

        (table,conflicts) = g.LL1()

        for key, reduction in table.items():
            (non_terminal,token) = key
            print("{} {}: {}".format(non_terminal,str(token),str(reduction)))

        for (lhs,terminal,action,action2) in conflicts:
            print("conflict: {}->{}: {}  {}".format(lhs,terminal,action,action2))
        if len(conflicts) > 0:
            sys.exit(1)
    else:
        if args.verbose:
            g.dump()
        else:
            if not printed:
                print(g.pretty_str(po))

    sys.exit(0)


if __name__ == '__main__':
    main()
