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
Represent and process a grammar:
- Canonicalize
- Compute First and Follow sets
- Compute LL(1) parser table and associated conflicts
- Verify a language is LALR(1) with context-sensitive lookahead
  - Compute the ParseTable for an LALR(1) grammar, and any
    conflicts if they exist.
"""

import json
import functools
import sys
from ObjectRegistry import RegisterableObject, ObjectRegistry
from collections import defaultdict

EPSILON = u"\u03b5"
MIDDLE_DOT = u"\u00b7"
LBRACE = "{"
RBRACE = "}"
# The name of the nonterminal for the entire language
LANGUAGE = "language"

# These just have to be different.
CLASS_FIXED=0
CLASS_PATTERN=1
CLASS_SYMBOL=2
CLASS_CHOICE=3
CLASS_SEQ=4
CLASS_REPEAT1=5
CLASS_EMPTY=6
CLASS_END_OF_TEXT=7
CLASS_ITEM=8
CLASS_ITEM_SET=9
CLASSES_BUCKET_SIZE=10 # Use 10 for readability

def raiseRE(s):
    raise RuntimeError(s)

# Definitions:
#
#  Token: A non-empty sequence of code points. Parsing considers tokens to
#    be indivisibl.
#
#  Empty: A unique object representing the empty string. Sometimes shown as
#    epsilon.
#
#  EndOfText: A unique object representing the end of input. No more text may
#    appear after it.
#
#  Fixed: A Token with fixed spelling.
#
#  Pattern: A Token matching a particular regular expression.
#    We always assume patterns never map to the empty string.
#
#  Terminal: One of: Token, EndOfText
#
#  Nonterminal: A named grammar object which maps to a Production.
#    In a Phrase, a nonterminal is represented by SymbolName
#    whose content is the (Python string) name of the nonterminal.
#    Conventionally, a single Nonterminal can have several productions.
#    In our grammar representation, that is encoded as a Choice over those
#    productions.
#
#  Symbol: a Terminal or a Nonterminal.
#
#  SymbolName: A name for a Terminal or Nonterminal.
#
#  Choice: A Rule which matches when any of several children matches
#
#  Seq (Sequence): A Rule which matches when all children are matched, one after
#    another
#
#  Repeat1: A Rule which matches when its child matches one or more times.
#
#  ContainerRule: One of Choice, Seq, or Repeat1
#
#  Production: An expression of Choice, Sequence, Repeat1 expressions over
#    Terminals, Nonterminals, and Empty.  In these expressions, a Nonterminal is
#    represented by a SymbolName for its name.
#
#  Flat: A Production is "Flat" if it is one of:
#      - a Terminal
#      - a SymbolName
#      - Empty
#      - a Sequence over Terminals and SymbolNames
#
#  GrammarDict: a dictionary mapping over Python strings mapping:
#    A Terminal name to its definition.
#    A Nonterminal name to its Production.
#
#  Grammar:
#    A Python object of class Grammar, including members:
#      .rules: a GrammarDict
#      .empty: the unique Empty object
#      .end_of_text: the unique EndOfText object
#      .start_symbol: the Python string name of the start symbol
#
#  Canonical Form: a GrammarDict where the Productions for Nonterminals are:
#    A Choice over Flat Productions
#
#  Phrase: A single Empty, or a sequence of a mixture of Terminals or SymbolNames.
#    It might have length 0, i.e. no objects at all.
#
#  Sentence: A sequence of Tokens. (Each Sentence is a Phrase.)
#
#  Language: The set of Sentences which may be derived from the start
#    symbol of a Grammar.
#
#  First(X):  Where X is a Phrase, First(X) is the set over Terminals or Empty that
#    begin the Phrases that may be derived from X.

class PrintOption:
    def __init__(self,multi_line_choice=True):
        self.multi_line_choice = multi_line_choice
        self.is_canonical = False
        self.more_newlines = False # Extra newline between rules
        self.print_terminals = True
        # Should emission inline rules that were created during canonicalization?
        # They contain a '/' in their name.
        self.inline_synthetic = True
        # Emit Bikeshed source
        self.bikeshed = False

        def MakeNone():
            return None

        # Maps 'A' to 'B' when A is of the form:
        #   A -> gamma | epsilon
        # Anywhere you want to print 'A', print '(gamma) ?' instead
        self.replace_with_optional = dict()
        # Maps 'A' to phrase 'gamma' when A is of the form:
        #   A -> gamma A | epsilon
        # Anywhere you want to print 'A', print '(gamma) *' instead
        self.replace_with_starred = dict()
        # Maps 'A' to phrase 'gamma' when A is of the form:
        #   A -> gamma
        # Anywhere you want to print 'A', print 'gamma' instead
        # Expect this to be populated where gamma is `X | Y`
        self.replace_with_nested = dict()

        # Must be a grammar if either .replace_with_optional or .replace_with_starred
        # are non-empty.
        self.grammar = None

    def clone(self):
        result = PrintOption()
        result.multi_line_choice = self.multi_line_choice
        result.is_canonical = self.is_canonical
        result.more_newlines = self.more_newlines
        result.print_terminals = self.print_terminals
        result.inline_synthetic = self.inline_synthetic
        result.bikeshed = self.bikeshed
        result.replace_with_optional = self.replace_with_optional
        result.replace_with_starred = self.replace_with_starred
        result.replace_with_nested = self.replace_with_nested
        result.grammar = self.grammar
        return result

class Rule(RegisterableObject):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.name = self.__class__.__name__
        self.reset_first_follow()

    def reset_first_follow(self):
        self.first_data = set()
        self.first_data_initialized_for_terminals = False
        self.follow = set()
        self.known_to_derive_empty = False

    def first(self):
        if self.is_terminal() or self.is_empty():
            if not self.first_data_initialized_for_terminals:
                # If X is a terminal, then First(X) is {X}
                self.first_data = set({self})
            self.first_data_initialized_for_terminals = True
        return self.first_data

    def is_empty(self):
        return isinstance(self, Empty)

    def is_token(self):
        return isinstance(self, Token)

    def is_end_of_text(self):
        return isinstance(self, EndOfText)

    def is_terminal(self):
        return isinstance(self, (EndOfText, Token))

    def is_container(self):
        return isinstance(self, ContainerRule)

    def as_container(self):
        return self if self.is_container() else [self]

    def is_symbol_name(self):
        return isinstance(self, SymbolName)

    def derives_empty(self):
        """Returns True if this object is known to generate the empty string"""
        if self.known_to_derive_empty:
            return True
        for item in self.first():
            if item.is_empty():
                self.known_to_derive_empty = True
                return True
        return False

    def _class_less(self,other):
        rank = { Choice: 1, Seq: 2, Repeat1: 3, SymbolName: 5, Fixed: 10, Pattern: 20, Empty: 100, EndOfText: 1000 }
        return rank[self.__class__] < rank[other.__class__]


    # Runs a given function 'fn' on this node and its descendants.
    # The fn(self,True) is called on entry and fn(self,False) on exit.
    def traverse(self,fn):
        fn(self,True)
        if "children" in dir(self):
            for c in self.children:
                c.traverse(fn)
        fn(self,False)

    def string_internal(self):
        parts = []
        def f(parts,obj,on_entry):
            if "content" in dir(obj):
                if on_entry:
                    if isinstance(obj, SymbolName):
                        parts.append(obj.content)
                    elif isinstance(obj, Fixed):
                        parts.append("'{}'".format(obj.content))
                    elif isinstance(obj, Pattern):
                        parts.append("/{}/".format(obj.content))
                    elif obj.is_empty():
                        parts.append(EPSILON)
                    elif isinstance(obj, EndOfText):
                        parts.append(obj.name)
                    else:
                        parts.extend(["(",obj.name, str(obj.content),")"])
            else:
                if on_entry:
                    parts.extend(["(",obj.name])
                else:
                    parts.append(")")
        self.traverse(lambda obj, on_entry: f(parts,obj,on_entry))
        return " ".join(parts)

    def __str__(self):
        return self.string_internal()

    def combine_class_id(self,i):
        # Combine class_id and i into a single number, hiding the class ID
        # in the bottom decimal digit.
        assert isinstance(i,int)
        return self.class_id + CLASSES_BUCKET_SIZE * i

    def pretty_str(rule,print_option=PrintOption()):
        """Returns a pretty string for a node"""
        if rule.is_terminal() or rule.is_empty():
            content = str(rule)
            if print_option.bikeshed:
                return "`{}`".format(content)
            return content
        if rule.is_symbol_name():
            name = rule.content
            def with_meta(phrase,metachar,print_option):
                content = " ".join([x.pretty_str(print_option) for x in phrase])
                if len(phrase) > 1:
                    return "( {} ){}".format(content, metachar)
                return "{} {}".format(content, metachar)
            if name in print_option.replace_with_starred:
                phrase = print_option.replace_with_starred[name]
                return with_meta(phrase,'*',print_option)
            if name in print_option.replace_with_optional:
                phrase = print_option.replace_with_optional[name]
                return with_meta(phrase,'?',print_option)
            if name in print_option.replace_with_nested:
                po = print_option.clone()
                po.multi_line_choice = False
                content = po.replace_with_nested[name].pretty_str(po)
                return "( {} )".format(content)
            if print_option.inline_synthetic and name.find("/") >=0:
                po = print_option.clone()
                po.multi_line_choice = False
                content = po.grammar.rules[name].pretty_str(po)
                return "( {} )".format(content)

            # Print ourselves
            if print_option.bikeshed:
                context = 'recursive descent syntax'
                g = print_option.grammar
                if g.rules[name].is_token():
                    context = 'syntax'
                if name in g.extra_externals:
                    context = 'syntax_sym'
                    if name == '_disambiguate_template':
                        # This is an implementation detail, so make it invisible.
                        return ''
                    else:
                        without_underscore = ['_less_than',
                                              '_less_than_equal',
                                              '_greater_than',
                                              '_greater_than_equal',
                                              '_shift_left',
                                              '_shift_left_assign',
                                              '_shift_right',
                                              '_shift_right_assign']
                        if name in without_underscore:
                            name = name[1:]
                return "[={}/{}=]".format(context,name)
            return name
        if isinstance(rule,Choice):
            parts = [i.pretty_str(print_option) for i in rule]
            if print_option.multi_line_choice:
                parts.sort()

            if print_option.multi_line_choice:
                if print_option.bikeshed:
                    nl = "\n\n"
                    prefixer = "\n | "
                else:
                    nl = "\n"
                    prefixer = "\n   "
            else:
                nl = ""
                prefixer = ""
            joiner = nl + " | "
            inside = prefixer + joiner.join([p for p in parts])
            if print_option.is_canonical:
                return inside
            else:
                # If it's not canonical, then it can have nesting.
                return "(" + inside + nl + ")"
        if isinstance(rule,Seq):
            return " ".join(filter(lambda i: len(i)>0, [i.pretty_str(print_option) for i in rule]))
        if isinstance(rule,Repeat1):
            return "( " + "".join([i.pretty_str(print_option) for i in rule]) + " )+"
        raise RuntimeError("unexpected node: {}".format(str(rule)))

    def partition(self,rule_name):
        """
        Partitions a rule into four lists:
            Sequences that start with nonterminal rule_name
            Sequences that start with nonterminal other than rule_name
            Sequences that start with terminal
            Empty
        """
        start_with_rule = []
        start_with_other_rule = []
        start_with_terminal = []
        empties = []
        #print("partitioning {}".format(" ".join([str(x) for x in rule.as_container()])))
        for x in self.as_container():
            first = x.as_container()[0]
            if first.is_symbol_name():
                #print( "    first.content |{}| vs |{}|".format(first.content,rule_name))
                if first.content == rule_name:
                    start_with_rule.append(x)
                else:
                    start_with_other_rule.append(x)
            else:
                if x.is_terminal():
                    start_with_terminal.append(x)
                else:
                    empties.append(x)
        return (start_with_rule, start_with_other_rule, start_with_terminal, empties)

    def partition_epsilon(self):
        non_empties = []
        empties = []
        for x in self.as_container():
            if x.is_empty():
                empties.append(x)
            else:
                non_empties.append(x)
        return (non_empties,empties)

    def as_starred(self, name):
        """
        Returns whether this rule is equivalent to:

            A -> (alpha1 ... alphaN)*

        That is, if the rule is of the form:

            A -> alpha1 ... alphaN A | epsilon

        then return [ alpha1 ... alphaN ]
        Otherwise return None
        """
        (nonempties,empties) = self.partition_epsilon()
        if len(nonempties)==1 and len(empties)==1:
            # Looks like:   A -> alpha | empty
            phrase = nonempties[0].as_container()
            last = phrase[-1]
            if last.is_symbol_name() and last.content == name:
                # Looks like:   A -> alpha A | empty
                return phrase[0:-1]
        return None

    def as_optional(self):
        """
        Returns whether this rule is equivalent to:

            A -> (alpha1 ... alphaN)?

        That is, if the rule is of the form:

            A -> alpha1 ... alphaN | epsilon

        then return [ alpha1 ... alphaN ]
        Otherwise return None
        """
        (nonempties,empties) = self.partition_epsilon()
        if len(nonempties)==1 and len(empties)==1:
            # Looks like:   A -> alpha | empty
            return nonempties[0].as_container()
        return None


class ContainerRule(Rule):
    """
    A ContainerRule is a rule with children

    Once created, it must not change: don't add, replace, reorder, or remove
    its objects.
    """
    def __init__(self,children,**kwargs):
        super().__init__(**kwargs)
        self.children = children

    def ordered(self):
        return self.ordered_children if ('ordered_children' in dir(self)) else self.children

    # Emulate an indexable sequence by adding certain standard methods:
    def __len__(self):
        return self.children.__len__()

    def __length_hint__(self):
        return self.children.__length_hint__()

    def __getitem__(self,key):
        return self.children.__getitem__(key)

    def __setitem__(self,key,value):
        self.children.__setitem__(key,value)

    def __delitem__(self,key):
        self.children.__setitem__(key)

    def __missing__(self,key):
        return self.children.__missing__(key)

    def __iter__(self):
        return self.children.__iter__()

    def __contains__(self,item):
        return self.children.__contains__(item)

class Choice(ContainerRule):
    def __init__(self,children,**kwargs):
        self.class_id = CLASS_CHOICE
        # Order does not matter among the children.
        # Children must have been registered.
        self.key = (self.class_id, frozenset([i.reg_info.index for i in children]))
        super().__init__(children,**kwargs)

class Seq(ContainerRule):
    def __init__(self,children,**kwargs):
        self.class_id = CLASS_SEQ
        # Order does matter among the children.
        # Store the tuple.
        # Children must have been registered.
        self.key = (self.class_id, tuple([i.reg_info.index for i in children]))
        super().__init__(children,**kwargs)

class Repeat1(ContainerRule):
    def __init__(self,children,**kwargs):
        if len(children) != 1:
            raise RuntimeError("Repeat1 must have exactly one child: {}".format(str(children)))
        self.class_id = CLASS_REPEAT1
        # Children must have been registered.
        self.key = (self.class_id,children[0].reg_info.index)
        super().__init__(children,**kwargs)

@functools.total_ordering
class LeafRule(Rule):
    """
    A LeafRule is a rule without children

    Once created, it must not be changed.
    """
    def __init__(self,content,**kwargs):
        super().__init__(**kwargs)
        self.content = content

class SymbolName(LeafRule):
    def __init__(self,content,**kwargs):
        self.class_id = CLASS_SYMBOL
        self.key = self.combine_class_id(self.register_string(content,**kwargs))
        super().__init__(content,**kwargs)

class Empty(LeafRule):
    def __init__(self,**kwargs):
        self.class_id = CLASS_EMPTY
        self.key = self.combine_class_id(0)
        super().__init__(None,**kwargs)

class EndOfText(LeafRule):
    def __init__(self,**kwargs):
        self.class_id = CLASS_END_OF_TEXT
        self.key = self.combine_class_id(0)
        super().__init__(None,**kwargs)

class Token(LeafRule):
    """
    A Token is a non-empty contiguous sequence of code points
    """
    def __init__(self,content,**kwargs):
        self.key = self.combine_class_id(self.register_string(content,**kwargs))
        super().__init__(content,**kwargs)

class Fixed(Token):
    """
    A Fixed is a token with a given sequence of code points.
    """
    def __init__(self,content,**kwargs):
        self.class_id = CLASS_FIXED
        super().__init__(content,**kwargs)

class Pattern(Token):
    """
    A Pattern represents a token matched by a regular expression.
    """
    def __init__(self,content,**kwargs):
        self.class_id = CLASS_PATTERN
        super().__init__(content,**kwargs)


@functools.total_ordering
class Action:
    """
    A parser action for a bottom-up LR or LALR(1) parser.
    """

    def __lt__(self,other):
        return self.compare_value() < other.compare_value()

    def __eq__(self,other):
        return self.compare_value() == other.compare_value()

    def __hash__(self):
        return self.compare_value().__hash__()

    def compare_value(self):
        return (-1,0)

    def __str__(self):
        return "<action>"

    def pretty_str(self):
        # Overridden sometimes
        return str(self)

class Accept(Action):
    """
    An Accept action represents acceptance of the input string.

    That is, the input string is part of the langauge, as we have
    successfully matched it against the start symbol of the language.
    """
    def __str__(self):
        return "acc"

    def compare_value(self):
        return (0,0)

class Shift(Action):
    """
    A Shift is an parser shift action.

    It represents the event where:
    - the parser has matched the next token against a lookahead token
    - the parser should:
       - consume that token,
       - push that token onto its stack, and
       - change state to the given state.
    """
    def __init__(self,item_set):
        isinstance(item_set,ItemSet) or raiseRE("expected ItemSet")
        self.item_set = item_set # item_set is assumed closed, and has core index
        self.index = item_set.core_index

    def __str__(self):
        return "s#{}".format(self.index)

    def compare_value(self):
        return (1,self.index)

class Reduce(Action):
    """
    A Reduce is an LR parser reduction action.

    It represents the event where:
    - the parser has just recognized the full right hand side of some production
      for a nonterminal
    - the parser should, where the production is [ N -> alpha ]:
       - remove the top len(alpha) symbols and state IDs on its stack
       - match those len(alpha) symbols to the symbols in alpha
       - read the state id S on top of the stack, and push onto the stack:
           nonterminal N, and
           goto[S, N] as the next state ID
    """
    def __init__(self,item,index):
        """
        Args:
            item: An Item representing a reduction. We ignore the position.
            index: A unique index
        """
        isinstance(item,Item) or raiseRE("expected Item")
        isinstance(index,int) or raiseRE("expected integer index")
        self.item = item # item_set is assumed closed, and has core index
        self.index = index

    def __str__(self):
        return "r#{}".format(self.index)

    def pretty_str(self):
        return "r#{} {}".format(self.index,str(self.item))

    def compare_value(self):
        return (2,self.index)

class Conflict:
    """
    A Conflict is a parser conflict
    """
    def __init__(self,item_set,terminal,prev_action,action):
        isinstance(item_set,ItemSet) or raiseRE("expected ItemSet")
        terminal.is_terminal() or raiseRE("expected terminal")
        isinstance(prev_action,Action) or raiseRE("expected Action")
        isinstance(action,Action) or raiseRE("expected Action")
        self.item_set = item_set
        self.terminal = terminal
        self.prev_action = prev_action
        self.action = action

    def __str__(self):
        return "[#{} {}] {} vs. {}".format(self.item_set.core_index,str(self.terminal),self.prev_action.pretty_str(),self.action.pretty_str())

class LLReduce:
    """
    An LLReduce is an LL parser reduction action.

    It represents an event where the
    - the parser should, where the production is [ A -> rhs ]:
       - remove the top len(rhs) symbols on its stack
       - match those len(rhs) symbols to the symbols in rhs
       - place A on the stack
    """
    def __init__(self,A,rhs):
        """
        Args:
            A: a string naming the nonterminal
            rhs: a Rule
        """
        isinstance(A,str) or raiseRE("expected nonterminal name as a string")
        isinstance(rhs,Rule) or raiseRE("expected rule")
        self.A = A
        self.rhs = rhs

        po = PrintOption()
        po.is_canonical = True
        po.inline_synthetic = False
        self.print_option = po

    def __str__(self):
        if isinstance(self.rhs,Rule):
            return "{} -> {}".format(self.A,self.rhs.pretty_str(self.print_option))
        return "{} -> {}".format(self.A,str(self.rhs))

    def pretty_str(self,options=PrintOption()):
        return "{} -> {}".format(self.A,self.rhs.pretty_str(options))

@functools.total_ordering
class Item(RegisterableObject):
    """
    An Item is a non-terminal name, and a Flat Production with a
    single position marker.

    If there are N objects in the production, the marked position
    is an integer between 0 and N inclusive, indicating the number
    of objects that precede the marked position.

    Once created, it must not be changed.

    Internally:
       self.lhs: a SymbolName naming the LHS of the grammar production
       self.rule: the Rule that is the RHS of the grammar production
       self.items: a list: sequence of items (Rules) in the production
       self.position: an integer index: the "dot" representing the current position
           in the rule appears to the left of the item at this indexed position.
    """
    def __init__(self,lhs,rule,position,**kwargs):
        """
        Args:
            lhs: the name of the nonterminal, as a SymbolName. Preregistered
            rule: the Flat Production. Preregistered
            position: Index of the position, where 0 is to the left
              of the first item in the choice
        """
        self.class_id = CLASS_ITEM
        self.lhs = lhs
        self.rule = rule
        self.position = position
        self.key = (self.class_id, lhs.reg_info.index, rule.reg_info.index, position)
        super().__init__(**kwargs)

        if rule.is_empty():
            num_items = 0
        elif isinstance(rule, LeafRule):
            num_items = 1
        elif isinstance(rule, Seq):
            num_items = len(rule)
        else:
            raise RuntimeError("invalid item object: {}".format(str(rule)))

        if (self.position < 0) or (self.position > num_items):
            raise RuntimeError("invalid position {} for production: {}".format(position,str(rule)))

        # Build the item list lazily. We may spend a lot of effort making an Item
        # but immediately throw it away as a duplicate
        self.the_items = None

    def precompute(self,grammar):
        if self.the_items is None:
            self.the_items = self.compute_items()
            self.the_next = self.the_items[self.position] if self.position < len(self.the_items) else None
            self.the_rest = self.the_items[self.position+1:]
            self.rest_derives_empty = derives_empty(grammar.rules, self.the_rest)
            self.rest_firsts_without_empty = without_empty(first(grammar, self.the_rest))
            self.grammar = grammar
            self.the_items_generated_by_next = None
        return self

    def rest_lookahead_with_other_lookahead(self,other_la):
        """
        Returns a new LookaheadSet containing:
           - the firsts tokens of the 'rest' of the production after the 'next' symbol,
             but without the empty token
           - and when that rest of the production can derive empty, also add the
             tokens from the other lookahead set 'other_la'
        This is needed for closing an ItemSet.
        """
        # First make a copy
        result = LookaheadSet(self.rest_firsts_without_empty)
        if self.rest_derives_empty:
            # When the_rest can derive an empty string, then the result could depend on the
            # contents of the other lookahead
            result.merge(other_la)
        return result

    def items_generated_by_next(self):
        """
        Returns the list of items generated by expanding nonterminal B,
        where B is the "next" terminal/nonterminal.  Assumes the 'dot' is not
        at the end of the list of items, and therefore B exists, and B is a symbol.
        Cache the result, as it does not change over time.
        """
        def lookup(rule):
            return self.grammar.rules[rule.content] if rule.is_symbol_name() else rule
        if self.the_items_generated_by_next is None:
            self.the_items_generated_by_next = []
            rhs = lookup(self.grammar.rules[self.the_next.content])
            rhs = [rhs] if rhs.is_terminal() else rhs
            # iterate over the alternatives of a Choice
            for production in rhs:
                if production.is_empty():
                    # Avoid creating useless productions that have no right-hand-side
                    # They can only lead to redundant reductions, and sometimes useless
                    # conflicts.
                    continue
                new_item = self.grammar.MakeItem(self.the_next,production,0)
                self.the_items_generated_by_next.append(new_item)
        return self.the_items_generated_by_next


    def items(self):
        # The ordered list of terminals/nonterminals in the production
        return self.the_items

    def next(self):
        # Returns the terminal/nonterminal immediately after the dot, or None if the dot
        # is at the ene
        return self.the_next

    def compute_items(self):
        """"
        Returns the sub-items, as a list.
        """
        rule = self.rule
        # self.items is the sub-objects, as a list
        if rule.is_terminal():
            self.the_items = [rule]
        elif rule.is_symbol_name():
            self.the_items = [rule]
        elif rule.is_empty():
            self.the_items = []
        elif isinstance(rule, Seq):
            self.the_items = [i for i in rule]
        else:
            raise RuntimeError("invalid item object: {}".format(str(rule)))
        return self.the_items

    def string_internal(self):
        parts = ["{} ->".format(self.lhs.content)]
        parts.extend([str(i) for i in self.items()])
        parts.insert(1 + self.position, MIDDLE_DOT)
        return " ".join(parts)

    def __str__(self):
       return self.string_internal()

    def is_kernel(self):
        # A kernel item either:
        # - has the dot not at the left end, or:
        # - is the production representing the entire language:
        #   LANGUAGE => Seq( Grammar.start_symbol, EndOfText )
        return (self.position > 0) or (self.lhs.content == LANGUAGE)

    def is_accepting(self):
        """
        Returns True when this item represents having accepted a valid
        sentence in the language

        Note: The agumented grammar always has 1 element:
           [ LANGUAGE -> translation_unit . EndOfText ]
        """
        return (self.position == 1) and (self.lhs.content == LANGUAGE)

    def at_end(self):
        return self.position == len(self.items())

def json_externals(json):
    """
    Returns the set of names of symbols in the "externals" section of the
    Treesitter JSON grammar.

    Data looks like this, for section "externals".
        {
          "externals": [
            { "type": "SYMBOL", name: "_block_comment" },
            { "type": "SYMBOL", name: "_error_sentinel" }
          }
        }
    """
    return set([ x["name"] for x in json.get("externals",[]) ])


def json_hook(grammar,memo,tokens_only,dct):
    """
    Translates a JSON dictionary into a corresponding grammar node, based on
    the 'type' entry.
    Returns 'dct' itself when 'dct' has no type entry or has an unrecognized
    type entry.

    We use Treesitter's conventions for representing a grammar in JSON form.

    Args:
      grammar: The grammar in which this node is created.
      memo: A memoization dictionary of previously created nodes.
        It's a dictionary mapping the Python string name of a node to
        the previously created node, if any.
      tokens_only: if true, only resolve tokens
      dct: A JSON dictionary

    Returns: A grammar node if recognized, otherwise 'dct' itself.
    """

    def memoize(memo,name,node):
        if name in memo:
            return memo[name]
        memo[name] = node
        return node

    result = dct
    if "type" in dct:
        type_entry = dct["type"]
        if isinstance(type_entry,str):
            if  type_entry == "TOKEN":
                result = dct["content"]
            elif  type_entry == "STRING":
                result = memoize(memo,dct["value"],grammar.MakeFixed(dct["value"]))
            elif  type_entry == "PATTERN":
                result = memoize(memo,dct["value"],grammar.MakePattern(dct["value"]))
            elif not tokens_only:
                if  type_entry == "BLANK":
                    result = grammar.empty
                elif  type_entry == "CHOICE":
                    result = grammar.MakeChoice(dct["members"])
                elif  type_entry == "SEQ":
                    result = grammar.MakeSeq(dct["members"])
                elif  type_entry == "REPEAT1":
                    result = grammar.MakeRepeat1([dct["content"]])
                elif  type_entry == "REPEAT":
                    # This node type was introduced in a later version of treesitter.
                    # REPEAT { X } is the same as CHOICE { REPEAT1 {X} | BLANK }
                    result = grammar.MakeRepeat1([dct["content"]])
                    result = grammar.MakeChoice([result, grammar.empty])
                elif  type_entry == "SYMBOL":
                    result = memoize(memo,dct["name"],grammar.MakeSymbolName(dct["name"]))
                else:
                    raise RuntimeError("unknown node type: {}".format(type_entry))
    return result

def canonicalize_grammar(grammar,empty):
    """
    Computes the Canonical Form of a GrammarDict

    Args:
        rules: A dictionary mapping rule names to Rule objects
        empty: the unique Empty object to use

    Returns:
        A GrammarDict matching the same language, but in Canonical Form.
    """

    rules = grammar.rules

    # First ensure right-hand sides of containers are Choice nodes.
    result = {}
    for key, value in rules.items():
        if isinstance(value,ContainerRule):
            if isinstance(value,Choice):
                # Choice nodes are unchanged
                result[key] = value
            else:
                result[key] = grammar.MakeChoice([value])
        else:
            result[key] = value

    # Now iteratively simplify rules.
    # Replace a complex sub-component with a new rule.
    # Repeat until settling.
    keep_going = True
    while keep_going:
        keep_going = False
        rules = dict(result)

        for key, value in rules.items():
            if isinstance(value,LeafRule):
                result[key] = value
            else:
                # The value is a Choice
                made_a_new_one = False
                parts = []
                def add_rule(key,*values):
                    """
                    Records a new rule with the given key and value.

                    Args:
                        key: A SymbolName whose name is the key into the result
                            dictionary
                        values: A list of alternatives

                    Returns: The key's Symbol
                    """
                    rhs = grammar.MakeChoice(list(values))
                    result[key.content] = rhs
                    return key
                for i in range(len(value)):
                    item = value[i]
                    item_key = grammar.MakeSymbolName("{}/{}".format(key,str(i)))
                    if isinstance(item,LeafRule):
                        parts.append(item)
                    elif isinstance(item,Repeat1):
                        #   value[i] -> X+
                        # becomes
                        #   value[i] -> value.i
                        #   value.i -> X value.i
                        #   value.i -> epsilon
                        x = item[0]
                        parts.append(add_rule(item_key,
                                              grammar.MakeSeq([x,item_key]),
                                              empty))
                        made_a_new_one = True
                    elif isinstance(item,Choice):
                        # Sub-Choices expand in place.
                        parts.extend(item)
                        made_a_new_one = True
                    elif isinstance(item,Seq):
                        # Expand non-leaf elements
                        made_a_new_seq_part = False
                        seq_parts = []
                        for j in range(len(item)):
                            seq_item = item[j]
                            seq_item_key = grammar.MakeSymbolName(
                                    "{}/{}.{}".format(key,str(i),str(j)))
                            if isinstance(seq_item,LeafRule):
                                seq_parts.append(seq_item)
                            else:
                                seq_parts.append(
                                        add_rule(seq_item_key,seq_item))
                                made_a_new_seq_part = True
                        if made_a_new_seq_part:
                            parts.append(grammar.MakeSeq(seq_parts))
                            made_a_new_one = True
                        else:
                            parts.append(item)
                if made_a_new_one:
                    rhs = grammar.MakeChoice(parts)
                    result[key] = rhs
                    keep_going = True
                else:
                    result[key] = value

    return result

def compute_first_sets(grammar,rules):
    """
    Computes the First set for each node in the grammar.
    Populates the `first` attribute of each node.

    Args:
        rules: a GrammarDict in Canonical Form
    """
    grammar.reset_first_follow()

    names_of_non_terminals = []
    grammar.end_of_text.first_data = set({grammar.end_of_text})
    grammar.empty.first_data = set({grammar.empty})
    for key, rule in rules.items():
        if rule.is_terminal() or rule.is_empty():
            # If X is a terminal, then First(X) is {X}
            # Lazy load it.
            dummy = rule.first()
        elif rule.is_symbol_name():
            names_of_non_terminals.append(key)
        else:
            # rule is a Choice node
            for rhs in rule:
                # If X -> empty is a production, then add Empty
                if rhs.is_empty():
                    rule.first_data = set({rhs})
            names_of_non_terminals.append(key)

    def lookup(rule):
        return rules[rule.content] if isinstance(rule,SymbolName) else rule

    def dynamic_first(rule,depth):
        """
        Returns the currently computed approximation to the First set for a
        rule.

        The rule is from a Canonical grammar, so a non-terminal can be as
        complex as a Choice over Sequences over symbols that may reference
        other non-terminals.  Gather updated First set info for at most
        those first two levels, and use a previous-computed approximation for
        the nonterminals at that second level.

        Args:
            rule: the Rule in question
            depth: recursion depth

        Returns:
            A new approximation to the First set for the given rule.
        """

        if rule.is_symbol_name():
            return rules[rule.content].first()
        if rule.is_empty():
            return rule.first()
        if rule.is_terminal():
            # The terminal isn't registered in the dictionary.
            return set({rule})
        if isinstance(rule,Choice):
            result = rule.first()
            #for item in [lookup(i) for i in rule]:
            for item in rule:
                result = result.union(dynamic_first(item,depth+1))
            return result
        if isinstance(rule,Seq):
            result = rule.first()

            # Only recurse 2 levels deep
            if depth < 2:
                items = [lookup(item) for item in rule]
            else:
                items = rule
            # Add the first sets for Yi if all the earlier items can derive
            # empty.  But don't add empty itself from this prefix.
            for item in items:
                from_first = dynamic_first(item,depth+1)
                from_first = without_empty(from_first)
                result = result.union(from_first)
                if not item.derives_empty():
                    # Not known to derive empty. Stop here.
                    break
            # If all the items derive empty, then add Empty to the first set.
            if all([lookup(item).derives_empty() for item in rule]):
                result = result.union({grammar.empty})
            return result
        raise RuntimeError("trying to dynamically compute the First set of: "
                + str(rule))

    # Repeat until settling.
    keep_going = True
    while keep_going:
        keep_going = False
        for key in names_of_non_terminals:
            rule = rules[key]
            # Accumulate First items from right-hand sides
            df = dynamic_first(rule,0)
            new_items = df - rule.first()
            if len(new_items) > 0:
                rule.first_data = rule.first().union(new_items)
                keep_going = True


def without_empty(s):
    """
    Returns a copy of set s without Empty
    """
    return {i for i in s if not i.is_empty()}

def list_without_empty(L):
    """
    Returns a copy of list s without Empty
    """
    return [i for i in L if not i.is_empty()]

def derives_empty(rules,phrase):
    """
    Args:
        args: a GrammarDict in Canonical form, with First sets computed
        phrase: a sequence of rules

    Returns:
        True if the phrase derives the empty string.
    """
    def lookup(rule):
        return rules[rule.content] if isinstance(rule,SymbolName) else rule

    # Write out the loop so we can exit early.
    for i in phrase:
        if not lookup(i).derives_empty():
            return False
    return True

def first(grammar,phrase):
    """
    Computes the First set for a Phrase, in the given grammar

    Args:
        grammar: a Grammar
        phrase: a sequence of terminals and non-terminals

    Returns:
        The First set for the phrase
    """
    def lookup(rule):
        return grammar.rules[rule.content] if isinstance(rule,SymbolName) else rule

    # Map names of nonterminals to the nonterminals themselves
    phrase = [lookup(i) for i in phrase]

    result = set()
    for item in phrase:
        we = without_empty(item.first())
        result = result.union(we)
        if not item.derives_empty():
            break
    if derives_empty(grammar.rules,phrase):
        result.add(grammar.empty)
    return result


def compute_follow_sets(grammar):
    """
    Computes the Follow set for each node in the grammar.
    Assumes First sets have been computed.
    Populates the `follow` attribute of each node.

    Args:
        grammar: a Grammar in Canonical Form, with First sets populated
    """

    # 1. Place $ in FOLLOW(S), where S is the start symbol and $ is the input
    # right end marker.
    grammar.rules[grammar.start_symbol].follow = set({grammar.end_of_text})

    def lookup(rule):
        return grammar.rules[rule.content] if isinstance(rule,SymbolName) else rule

    def process_seq(key,seq,keep_going):
        """
        Add to Follow sets by processing the given Seq node.

        Args:
            key: Python string name for the production
            seq: a Seq rule for the production
            keep_going: A boolean

        Returns:
            True if a Follow set was modified.
            keep_going otherwise
        """

        # Process indirections through symbols
        seq = [lookup(i) for i in seq]

        last_index = len(seq)-1
        for bi in range(0,len(seq)):
            b = seq[bi]
            # We only care about nonterminals in the sequence
            if b.is_terminal() or b.is_empty():
                continue

            # If there is a production A -> alpha B beta
            # then everything in First(beta) except Empty is
            # added to Follow(B)
            beta = seq[bi+1:len(seq)]
            first_beta = first(grammar, beta)
            new_items = without_empty(first_beta) - b.follow
            if len(new_items) > 0:
                keep_going = True
                b.follow = b.follow.union(new_items)

            # If A -> alpha B, or A -> alpha B beta, where First(beta)
            # contains epsilon, then add Follow(A) to Follow(B)
            if (bi==last_index) or derives_empty(grammar.rules,beta):
                new_items = grammar.rules[key].follow - b.follow
                if len(new_items) > 0:
                    keep_going = True
                    b.follow = b.follow.union(new_items)

        return keep_going

    # Iterate until settled
    keep_going = True
    while keep_going:
        keep_going = False
        for key, rule in grammar.rules.items():
            if rule.is_terminal() or rule.is_empty():
                continue

            if isinstance(rule,Seq):
                keep_going = process_seq(key,rule,keep_going)
                continue

            if rule.is_symbol_name():
                keep_going = process_seq(key,[rule],keep_going)
                continue

            # Now process Choice over sequences:
            if isinstance(rule,Choice):
                for seq in [i.as_container() for i in rule]:
                    keep_going = process_seq(key,seq,keep_going)


def dump_rule_parts(key,rule):
    parts = []
    parts.append("{}  -> {}".format(key,str(rule)))
    parts.append("{} .reg_info.index: {}".format(key, str(rule.reg_info.index)))
    parts.append("{} .first: {}".format(key, str(LookaheadSet(rule.first()))))
    parts.append("{} .derives_empty: {}".format(key, str(rule.derives_empty())))
    parts.append("{} .follow: {}".format(key, str(LookaheadSet(rule.follow))))
    return parts

def dump_rule(key,rule):
    print("\n".join(dump_rule_parts(key,rule)))

def dump_grammar(rules):
    for key, rule in rules.items():
        dump_rule(key,rule)

def walk(obj,dict_fn):
    """
    Walk a JSON structure, yielding a new copy of the object.
    But for any dictionary 'd', first walk its contents, and then
    yield the result of calling dict_fn(d).
    """
    if isinstance(obj,dict):
        result = dict()
        for key, value in obj.items():
            result[key] = walk(value, dict_fn)
        return dict_fn(result)
    if isinstance(obj,list):
        return [walk(i,dict_fn) for i in obj]
    return obj


class LookaheadSet(set):
    """
    A LookaheadSet is a set of terminals

    Once created, it must not change except via the merge method.
    """
    def __init__(self,*args):
        super().__init__(*args)
        self.reset()

    def reset(self):
        self.str = None
        self.hash = None
        self.has_end_of_text = None

    def includesEndOfText(self):
        if self.has_end_of_text is None:
            self.rehash()
        return self.has_end_of_text

    def rehash(self):
        """Recomputes self.str and self.hash"""
        self.str = "{}{}{}".format(LBRACE, " ".join(sorted([str(i) for i in self])), RBRACE)
        self.hash = self.str.__hash__()
        self.has_end_of_text = any([isinstance(i,EndOfText) for i in self])

    def __str__(self):
        if self.str is None:
            self.rehash()
        return self.str

    def __hash__(self):
        if self.hash is None:
            self.rehash()
        return self.hash

    def merge(self, other):
        """
        Adds the members of the other set.
        Returns: True when something was added to the current set.
        """
        extras = other.difference(self)
        if len(extras) > 0:
            self.update(extras)
            self.reset()
            return True
        return False

    def add(self, element):
        raise RuntimeError("Don't do Lookahead.add")

    def remove(self, element):
        raise RuntimeError("Don't do Lookahead.remove")


@functools.total_ordering
class ItemSet:
    """
    An ItemSet is an LR(1) set of Items, where each item maps to its lookahead set.

    An ItemSet can only be mutated via methods:
        - close, which can add items and modify lookaheads
    """
    class GotoEdge:
        """
        A GotoEdge represents a transition from a source ItemSet
        to a destination ItemSet.  The transition embodies the state change
        that occurs when matching a grammar terminal or nonterminal.
        """
        def __init__(self,x):
            self.x = x
            # Maps source item ID to (next item, lookahead).
            # When    [ A -> alpha . x beta ] is the source item,
            # then    [ A -> alpha x . beta ] is the destination item
            self.next = dict()

            self.next_item_set_cache = None

        def add(self,item,next_item,lookahead):
            assert isinstance(item,Item)
            assert isinstance(next_item,Item)
            assert isinstance(lookahead,LookaheadSet)
            assert item.reg_info.index not in self.next
            self.next[item.reg_info.index] = (next_item, lookahead)

        def NextItemSet(self,grammar,by_index_memo=None):
            """
            Lazily creates an unclosed ItemSet out of the next_items tracked by this edge.
            If by_index_memo is not None, then find and return the previously saved
            ItemSet with the same core items, if one exists there.

            Returns a pair (bool,ItemSet)
               - True if the ItemSet was newly created
               - the destination ItemSet when following this edge
            """
            changed = False
            if self.next_item_set_cache is None:
                # Create the item set from the "next" items and associated lookaheads.
                d = dict()
                for item_id, next_and_lookahead in self.next.items():
                    d[next_and_lookahead[0]] = next_and_lookahead[1]

                next_IS = ItemSet(grammar,d).close(grammar)
                if (by_index_memo is None) or (next_IS.core_index not in by_index_memo):
                    self.next_item_set_cache = next_IS
                    changed = True
                else:
                    original_IS = by_index_memo[next_IS.core_index]
                    self.next_item_set_cache = original_IS
            return (changed, self.next_item_set_cache)


    def __init__(self,grammar,*args):
        assert isinstance(grammar,Grammar)
        self.grammar = grammar
        # Maps item ID to item
        self.id_to_item = dict()
        # Maps item ID to its lookahead
        self.id_to_lookahead = dict()
        for item, lookahead in dict(*args).items():
            self.internal_add(item, lookahead)

        # Create a hashable fingerprint of the core of this ItemSet
        # We always expect every initial item to be a kernel item. But filter anyway.
        self.kernel_item_ids = frozenset(filter(lambda x: x.is_kernel(), self.id_to_item.values()))

        # self.core_index is the unique index within the grammar for the core of this
        # item set.  Well defined only after calling the close() method.
        self.core_index = grammar.register_item_set(self)

        # In the LALR1 case, this is the goto function for this ItemSet.
        # Maps the ID of a nonterminal X to its GotoEdge.
        self.goto = None

    def internal_add(self,item,lookahead):
        """
        Adds an item-to-lookahead mapping.
        """
        assert isinstance(item, Item)
        assert isinstance(lookahead, LookaheadSet)
        index = item.reg_info.index
        assert isinstance(index,int)
        assert index not in self.id_to_item
        self.id_to_item[index] = item
        self.id_to_lookahead[index] = lookahead

    def as_ordered_parts(self):
        # For readability, put the kernel parts first
        kernel_parts = []
        non_kernel_parts = []
        for item_id, lookahead in self.id_to_lookahead.items():
            item = self.id_to_item[item_id]
            the_str = "{} : {}".format(str(item), str(lookahead))
            if item.is_kernel():
                kernel_parts.append(the_str)
            else:
                non_kernel_parts.append(the_str)
        return sorted(kernel_parts) + sorted(non_kernel_parts)

    def content_str(self):
        return "\n".join(self.as_ordered_parts())

    def __str__(self):
        content = self.content_str()
        return "#{}\n{}".format(self.core_index,content)

    def short_str(self):
        """
        Returns a short string, based only on core_index.
        Assumes core_index has been computed.
        """
        return "#{}".format(self.core_index)

    def __lt__(self,other):
        # Note: This is slow. Only use this for tests and printing.
        return self.content_str() < other.content_str()

    def __hash__(self):
        # Note: This is slow. Only use this for tests and printing.
        return self.content_str().__hash__()

    def __eq__(self,other):
        # Note: This is slow. Only use this for tests and printing.
        return self.content_str() == other.content_str()

    def pretty_key(self):
        # Use this for sorting for output
        return "#{:8d}{}".format(self.core_index,self.content_str())

    # Make sure we don't use ItemSet as a raw dictionary
    def keys(self):
        raise RuntimeError("don't call keys on ItemSet")
    def __getitem__(self,*args):
        raise RuntimeError("don't call __getitem__ on ItemSet")
    def __setitem__(self,*args):
        raise RuntimeError("don't call __setitem__ on ItemSet")
    def __delitem__(self,*args):
        raise RuntimeError("don't call __delitem__ on ItemSet")

    def is_accepting(self):
        """
        Returns True if the parser action for this item set should be 'accept'.
        """
        for item_id, lookahead in self.id_to_lookahead.items():
            if lookahead.includesEndOfText():
                item = self.id_to_item[item_id]
                if item.is_accepting():
                    return True
        return False

    def close(self,grammar):
        """
        Computes the closure of this item set, including propagation of lookaheads
        from the core items to the items they generate
        Updates this ItemSet in place.

        That is:
            if   [A -> alpha . B beta , x ] is in the item set, and
                 [ B -> gamma ] is a grammar rule,
            then add
                 [ B -> . gamma, x ]  to this item set.
            There may be many such B's, rules containing them, productions for B,
            and lookahead tokens 'x'.

        Returns: self
        """
        def lookup(rule):
            return grammar.rules[rule.content] if isinstance(rule,SymbolName) else rule

        dirty_dict = self.id_to_lookahead.copy()
        while len(dirty_dict) > 0:
            # From the dragon book, 1st ed. 4.38 Sets of LR(1) items construction.
            #
            # For each item [ A -> alpha . B beta, a ] in I,
            # and each production " B -> gamma " in the grammar,
            # and each terminal b in FIRST(beta a),
            # add [ B -> . gamma, b ] to I if it is not already there.
            work_list = dirty_dict
            dirty_dict = dict()
            for item_id, lookahead in work_list.items():
                item = self.id_to_item[item_id]
                if item.at_end():
                    continue
                B = item.next()
                if not B.is_symbol_name():
                    continue

                # Compute lookahead. (A fresh LookaheadSet)
                new_item_lookahead = item.rest_lookahead_with_other_lookahead(lookahead)

                # Iterate over items  [ B -> . B_prod ]
                # for each production   B -> B_prod   in the grammar.
                for candidate in item.items_generated_by_next():
                    candidate_id = candidate.reg_info.index
                    if candidate_id not in self.id_to_item:
                        la = LookaheadSet(new_item_lookahead)
                        self.internal_add(candidate, LookaheadSet(new_item_lookahead))
                        dirty_dict[candidate_id] = la
                    else:
                        if self.id_to_lookahead[candidate_id].merge(new_item_lookahead):
                            dirty_dict[candidate_id] = self.id_to_lookahead[candidate_id]
        return self

    def gotos_internal(self,grammar,by_index_memo=None):
        """
        Computes the goto mapping for this item set.

        Returns a pair (changed,goto_list) where:
            changed is True when
                by_index_memo is not None and new item sets were created or lookaheads were modified.
            goto_list is is a list of pairs (X, item_set_X), where:
                X is a grammar symbol X (terminal or non-terminal), and
                item_set_X is the closed ItemSet goto(self,X)
                   representing the next parser state after having successfully recognized
                   grammar symbol X
                where X ranges over all grammar symbols X such that goto(self,X) is non-empty.

        On first execution, this populates self.goto, which caches the GotoEdges.  That connectivity changes.
        On subsequent executions, only propagates lookaheads from core items to the items
        derived from those core items.

        Args:
           self
           grammar: The grammar being traversed
           by_index_memo: None, or a dictionary mapping an item-set's core index to the unique
              LALR1 item set with that core.

        Assumes self is closed.

        That is, for any X, collect all items [A -> alpha . X beta, a] in the
        current item set, and produce an ItemSet ISX from of the union of
        [A -> alpha X . beta, a].

        Here X may be a terminal or a nonterminal.

        When by_index_memo is None, collect these ISX.
        When by_index_memo is a dictionary mapping an item set's core index to an item set,
        set ISX to by_index_memo[ISX.core_index], i.e. reuse the pre-existing item set
        with the same core.

        """

        # Partition items according to the next symbol to be consumed, X,
        # i.e. the symbol immediately to the right of the dot.
        changed_initial = False
        if self.goto is None:
            self.goto = dict()
            # Create the initial set of edges, copying lookaheads
            for item_id, item in self.id_to_item.items():
                if item.at_end():
                    continue
                X = item.next()
                if X.is_end_of_text():
                    continue
                xid = X.reg_info.index
                if xid not in self.goto:
                    self.goto[xid] = self.GotoEdge(X)
                edge = self.goto[xid]
                next_item = grammar.MakeItem(item.lhs, item.rule, item.position+1)
                edge.add(item,next_item,LookaheadSet(self.id_to_lookahead[item_id]))
            changed_initial = True

        # The first time around, construct the destination item sets for each edge.
        # On subsequent rounds, propagate lookaheads from our own ItemSet to next item sets.
        goto_list = []
        changed = changed_initial
        for edge in self.goto.values():
            (created, next_item_set) = edge.NextItemSet(grammar,by_index_memo=by_index_memo)
            if created:
                next_item_set.close(grammar)
            else:
                # Propagate lookaheads
                for src_item_id, (dest_item,stale_lookahead) in edge.next.items():
                    src_lookahead = self.id_to_lookahead[src_item_id]
                    dest_lookahead = next_item_set.id_to_lookahead[dest_item.reg_info.index]
                    changed = changed | dest_lookahead.merge(src_lookahead)
                # Propagate to non-kernel items
                next_item_set.close(grammar)

            changed = changed | created
            goto_list.append((edge.x, next_item_set))

        return (changed,goto_list)

    def gotos(self,grammar,by_index_memo=None):
        # TODO(dneto): I'm keeping this indirection as a convenient place
        # to insert debug output.
        result = self.gotos_internal(grammar,by_index_memo=by_index_memo)
        return result

class ParseTable:
    """
    An LALR(1) parser table with fields:

      .grammar:    The Grammar.  Use this to look up symbols and item sets by index.
      .states:     The list of parser states, where each state is identified with
                   an LALR(1) item set. Each ItemSet is closed and has a core index.
      .action:     The parser action table, mapping (state.core_index,token) to an Action object.
                   Any combination not in the table is a parse error.
      .goto:       The goto table, mapping (state.core_index,nonterminal) to another state.
      .reductions: A list of Reduce objects, in index order.
      .conflicts:  A list of Conflicts
    """
    def __init__(self,grammar,states,action_table,goto,reductions,conflicts):
        self.grammar = grammar
        self.states = states
        self.action = action_table
        self.goto = goto
        self.reductions = reductions
        self.conflicts = conflicts

        self.core_index_to_state = dict()
        for s in self.states:
            self.core_index_to_state[s.core_index] = s

    def has_conflicts(self):
        return len(self.conflicts) > 0

    def raw_rule_parts(self):
        parts = []
        for key, rule in self.grammar.rules.items():
            parts.extend(dump_rule_parts(key,rule))
        return [ "{}\n".format(str(x)) for x in parts ]

    def states_parts(self):
        parts = []
        for i in self.states:
            parts.append(str(i))
            parts.append("\n\n")
        return parts

    def reductions_parts(self):
        parts = []
        for r in self.reductions:
            parts.append("{}\n".format(r.pretty_str()))
        return parts

    def action_parts(self):
        parts = []
        def action_key_sort_value(state_id_terminal_id):
            (state_id,terminal_id) = state_id_terminal_id
            terminal_str = str(self.grammar.findByIndex(terminal_id))
            return (state_id,terminal_str)
        # Map terminal ids to terminal strings
        for (state_id,terminal_id) in sorted(self.action, key=action_key_sort_value):
            state_str = self.core_index_to_state[state_id].short_str()
            terminal_str = str(self.grammar.findByIndex(terminal_id))
            action = self.action[(state_id,terminal_id)]
            parts.append("[{} {}]: {}\n".format(state_str,terminal_str,action))
        return parts

    def goto_parts(self):
        parts = []
        for state_id_nonterminal in sorted(self.goto, key = lambda st: (st[0],str(st[1]))):
            short_state = self.core_index_to_state[state_id_nonterminal[0]].short_str()
            nonterminal = str(state_id_nonterminal[1])
            next_state_str = self.goto[state_id_nonterminal].short_str()
            parts.append("[{} {}]: {}\n".format(short_state,nonterminal,next_state_str))
        return parts

    def conflict_parts(self):
        parts = []
        for c in self.conflicts:
            parts.append("{}\n".format(str(c)))
        return parts

    def all_parts(self):
        parts = []
        parts.append("\n=Raw rules:\n")
        parts.extend(self.raw_rule_parts())
        parts.append("\n=LALR1 item sets:\n")
        parts.extend(self.states_parts())
        parts.append("\n=Reductions:\n")
        parts.extend(self.reductions_parts())
        parts.append("\n=Action:\n")
        parts.extend(self.action_parts())
        parts.append("\n=Goto:\n")
        parts.extend(self.goto_parts())
        if self.has_conflicts():
            parts.append("\n=Conflicts: {} conflicts\n".format(len(self.conflicts)))
            parts.extend(self.conflict_parts())
        return parts

    def write(self,file):
        for s in self.all_parts():
            print(s,file=file,end='')

    def __str__(self):
        return "".join(self.all_parts())


class Grammar:
    """
    A Grammar represents a language generated from a start symbol via
    a set of rules.
    Rules are either Terminals or Nonterminals.
    """

    def Load(json_text, start_symbol, ignore='_reserved'):
        """
        Loads a grammar from text.

        The text format is assumed to be JSON object representing a
        Treesitter grammar.

        Args:
           json_text: The grammar in JSON form, as emitted by
             a Treesitter generation step.
           start_symbol: The name of the start symbol, as a Python string
           ignore: the name of a rule to ignore completely

        Returns:
            A canonical grammar with first and follow sets
        """
        g = Grammar(json_text, start_symbol, ignore=ignore)
        g.canonicalize()
        g.compute_first()
        g.compute_follow()
        return g

    def find(self, rule_name):
        """
        Finds a Rule by its Python string name.
        """
        return self.rules[rule_name]

    def findByIndex(self, obj_index):
        """
        Finds a registered object by its index.
        Registered objects are either Item or Rule (including Token)
        """
        return self.registry.findByIndex(obj_index)

    def __init__(self, json_text, start_symbol, ignore='_reserved'):
        """
        Args:
           json_text: The grammar in JSON form, as emitted by
             a Treesitter generation step.
           start_symbol: The name of the start symbol, as a Python string
           ignore: the name of a rule to ignore completely
        """
        # Registry for key grammar objects, so we can use integer-based
        # keys for them.
        self.registry = ObjectRegistry()

        self.json_text = json_text
        self.start_symbol = start_symbol
        self.empty = Empty(reg=self)
        self.end_of_text = EndOfText(reg=self)

        # Maps an item set core (ie. no lookaheads) to its sequential index.
        self.item_set_core_index = dict()

        # First decode it without any interpretation.
        pass0 = json.loads(json_text)

        # Get the external tokens, these are not necessarily represented in the rules.
        external_tokens = json_externals(pass0)
        #print(external_tokens,file=sys.stderr)
        defined_rules = set(pass0["rules"].keys())
        # The set of external tokens that don't have an ordinary definition in the grammar.
        self.extra_externals = external_tokens - defined_rules
        for e in self.extra_externals:
            content = "\\u200B{}".format(e)
            if e == '_disambiguate_template':
                # This is a zero-width token used for Treesitter's benefit
                #content = ''
                pass
            # Create a placholder definition
            pass0["rules"][e] = {"type":"TOKEN","content":{"type":"PATTERN","value":content}}

        # Remove any rules that should be ignored
        # The WGSL grammar has _reserved, which includes 'attribute' but
        # that is also the name of a different grammar rule.
        if ignore in pass0["rules"]:
            del pass0["rules"][ignore]

        # Now decode, transforming leaves and nonterminals to Rule objects.
        memo = {} # memoization table used during construction
        pass1 = walk(pass0, lambda dct: json_hook(self,memo,True,dct))
        pass2 = walk(pass1, lambda dct: json_hook(self,memo,False,dct))
        self.json_grammar = pass2

        self.rules = self.json_grammar["rules"]

        # Augment the grammar:
        self.rules[LANGUAGE] = self.MakeSeq([self.MakeSymbolName(start_symbol), self.end_of_text])

        self.is_canonical = False # Updated during canonicalization

    def MakeEmpty(self):
        return self.empty

    def MakeEndOfText(self):
        return self.end_of_text

    def MakeFixed(self,content):
        """
        Returns a new Fixed object, unique up to equivalence of its string text.
        """
        return self.register(Fixed(content,reg=self))

    def MakePattern(self,content):
        """
        Returns a new Pattern object, unique up to equivalence of its pattern text.
        """
        return self.register(Pattern(content,reg=self))

    def MakeChoice(self,content):
        """
        Returns a new Choice object, unique up to equivalence of its members.
        """
        return self.register(Choice(content,reg=self))

    def MakeSeq(self,content):
        """
        Returns a new Seq object, unique up to equivalence of its member sequence.
        """
        return self.register(Seq(content,reg=self))

    def MakeRepeat1(self,content):
        """
        Returns a new Repeat1 object, unique up to equivalence of its member.
        """
        return self.register(Repeat1(content,reg=self))

    def MakeSymbolName(self,content):
        """
        Returns a new SymbolName, unique up to equivalence of its string name.
        """
        return self.register(SymbolName(content,reg=self))

    def MakeItem(self,lhs,rule,position):
        """
        Returns a new Item, unique up to equivalence of its left-hand side
        nonterminal, right-hand side production rule, and its position within
        that right-hand side.
        """
        # Upconvert a lhs to a SymbolName if it's a Python string.
        lhs = lhs if isinstance(lhs,SymbolName) else self.MakeSymbolName(lhs)
        candidate = Item(lhs,rule,position,reg=self)
        # Avoid double-registering.
        result = self.register(candidate)
        if result is candidate:
            result.precompute(self)
        return result

    def canonicalize(self):
        """
        Rewrites this Grammar's rules so they are in Canonical Form.
        """
        self.rules = canonicalize_grammar(self,self.empty)
        self.is_canonical = True

    def reset_first_follow(self):
        for _, rule in self.rules.items():
            rule.reset_first_follow()

    def compute_first(self):
        """
        Computes the First set for each rule, saving the result on each rule node.
        Also computes .derives_empty
        """
        compute_first_sets(self, self.rules)

    def compute_follow(self):
        """
        Computes the Follow set for each rule, saving the result on each rule node.
        Assumes First sets have been computed.
        """
        compute_follow_sets(self)

    def dump(self):
        """
        Emits the internal representation of the grammar to stdout
        """
        dump_grammar(self.rules)
        print(self.registry)

    def pretty_str(self,print_option=PrintOption()):
        """
        Returns a pretty string form of the grammar.
        It's still in canonical form: nonterminals are at most a choice over
        a sequence of leaves.
        """

        po = print_option.clone()
        po.is_canonical = self.is_canonical
        po.grammar = self

        token_rules = set()

        # Look for defined rules that look better as absorbed into their uses.
        for name, rule in self.rules.items():
            # Star-able is also optional-able, so starrable must come first.
            starred_phrase = rule.as_starred(name)
            if starred_phrase is not None:
                po.replace_with_starred[name] = starred_phrase
                continue
            optional_phrase = rule.as_optional()
            if optional_phrase is not None:
                po.replace_with_optional[name] = optional_phrase
                continue
            options = rule.as_container()
            if len(options)==1:
                phrase = options[0].as_container()
                if len(phrase)==1 and phrase[0].is_token():
                    token_rules.add(name)

        # A rule that was generated to satisfy canonicalization is better
        # presented as absorbed in its original parent.
        for name, rule in self.rules.items():
            # We only care about rules generated during canonicalization
            if name.find('.') > 0 or name.find('/') > 0:
                options = rule.as_container()
                if len(options) != 2:
                    continue
                if any([len(x.as_container())!=1 for x in options]):
                    continue
                if any([(not x.as_container()[0].is_symbol_name()) for x in options]):
                    continue
                # Rule looks like   A -> X | Y
                po.replace_with_nested[name] = rule

        parts = []
        for key in sorted(self.rules):
            if key == LANGUAGE:
                # This is synthetic, for analysis
                continue
            rule_content = self.rules[key].pretty_str(po)
            if key in po.replace_with_optional:
                continue
            if key in po.replace_with_starred:
                continue
            if key in po.replace_with_nested:
                continue
            if (not po.print_terminals) and (key in token_rules):
                continue
            space = "" if po.multi_line_choice else " "
            if po.bikeshed:
                key_content = "  <dfn for='recursive descent syntax'>{}</dfn>".format(key)
                content = "<div class='syntax' noexport='true'>\n{}:\n{}\n</div>".format(key_content,rule_content)
            else:
                content = "{}:{}{}".format(key,space,rule_content)
            parts.append(content)
        content = ("\n\n" if po.more_newlines else "\n").join(parts)
        return content

    def register_item_set(self,item_set):
        """
        Registers an item set, and return an index such that any item set with
        the same core will map to the same index.
        Indices start at 0 and go up by 1.

        Returns its index.
        """
        assert isinstance(item_set,ItemSet)
        core = item_set.kernel_item_ids
        if core in self.item_set_core_index:
            return self.item_set_core_index[core]
        # Register it
        result = len(self.item_set_core_index)
        self.item_set_core_index[core] = result
        return result

    def register(self,registerable):
        """
        Register an object to give it a unique integer-based key.
        Return the first object registered with its key.
        """
        result = self.registry.register(registerable)
        if result.reg_info.index is None:
            raise RuntimeError("failed to register {}".format(str(registerable)))
        return result

    def register_string(self,string):
        """Returns a unique integer for the string"""
        return self.registry.register_string(string)

    def preorder(self):
        """
        Returns the names of rules, in order, based on the preorder traversal
        starting from the LANGUAGE start node.

        Assumes the grammar is in canonical form
        """
        assert self.is_canonical
        # Names of visited nodes
        visited = set()
        # Names of nodes to visit
        worklist = [LANGUAGE]

        result = []
        while len(worklist) > 0:
            successors = []
            for rule_name in worklist:
                if rule_name in visited:
                    continue
                result.append(rule_name)
                visited.add(rule_name)

                rule = self.rules[rule_name].as_container()
                for rhs in rule:
                    phrase = rhs.as_container()
                    # Note: this tolerates duplicates among siblings.
                    successors.extend([x.content for x in phrase if x.is_symbol_name() and x.content not in visited])
            worklist = successors
        return result

    def eliminate_left_recursion(self,stop_at_set):
        """
        Algorithm 4.1 from the Dragon Book.

        Assume the grammar has no cycles. A cycle exists if there is a rule
            X ->+ X

        Adapted to handle epsilon rules.

        Algorithm (but avoiding updating rules in stop_at_set)
        1. Arrange the nonterminals into a defined ordering A1 ... An
        2. Break self-cycles in the first position via more than one step.
           for i = 1 to n:
              for j = 1 to i-1:
                 # Break backedges from Ai to Aj:
                 replace production of the form Ai -> Aj gamma
                 by productions   Ai -> delta1 gamma | delta2 gamma | ... | deltaK gamma
                 where   Aj -> delta1 | delta2 | ... | deltaK
                 are all the current Aj productions
        3. Eliminate immediate left recursion
        """
        assert self.is_canonical

        # Determine a definite ordering of the rules.
        # Use a DFS so we only have essential backedges.
        preorder_names = self.preorder()
        preorder_index = dict()
        for name in preorder_names:
            preorder_index[name] = len(preorder_index)

        # Break self-cycles via more than one step
        for i in range(1,len(preorder_names)):
            rule_name = preorder_names[i]
            if rule_name in stop_at_set:
                continue
            rule = self.rules[rule_name]
            replacement = []
            changed = False
            for rhs in rule.as_container():
                phrase = rhs.as_container()
                first = phrase[0]
                rest = phrase[1:]
                if first.is_symbol_name():
                    first_name = first.content
                    j = preorder_index[first_name]
                    if (j < i) and (first_name not in stop_at_set):
                        # Break this backedge
                        Aj = self.rules[first_name].as_container()
                        if len(rest) == 0:
                            # Add Aj's alternatives to  Ai's alternatives.
                            # Aj is a choice node
                            # The elements of Aj are already of suitable class.
                            replacement.extend([delta for delta in Aj])
                        else:
                            # Rest is non-empty
                            for delta in Aj:
                                replacement.append(self.MakeSeq(list_without_empty(delta.as_container()) + rest))
                        changed = True
                    else:
                        # Pass it through. It's not a backedge, or we've been
                        # asked to stop here.
                        replacement.append(rhs)
                else:
                    # First thing is not a symbol name. Pass it through
                    replacement.append(rhs)
            if changed:
                # Update with the new rule.
                self.rules[rule_name] = self.MakeChoice(replacement)

        # Finally, eliminate immediate left recursion.
        self.eliminate_immediate_recursion(self)


    def eliminate_immediate_recursion(self):
        """
        Algorithm 4.1 from the Dragon Book.

        Assume the grammar has no cycles. A cycle exists if there is a rule
            X ->+ X

        Adapted to handle epsilon rules.
        """
        assert self.is_canonical
        # Eliminate immediate left recursion
        #    Replace rules
        #            A -> A alpha1 | A alpha2 | beta1 | beta2
        #    with
        #            A -> beta1 A' | beta2 A'
        #            A' -> alpha1 A' | alpha2 A' | epsilon
        #
        #    When A can produce epsilon directly:
        #            A -> A alpha1 | A alpha2 | beta1 | beta2 | epsilon
        #    with
        #            A -> beta1 A' | beta2 A' | A'
        #            A' -> alpha1 A' | alpha2 A' | epsilon
        preorder_names = self.preorder()
        for rule_name in preorder_names:
            rule = self.rules[rule_name]
            changed = False
            has_immediate_left_recursion =  False
            for rhs in rule.as_container():
                first = rhs.as_container()[0]
                if first.is_symbol_name() and first.content is rule_name:
                    has_immediate_left_recursion = True
                    break
            if has_immediate_left_recursion:
                self_parts = []  # Becomes new right-hand-side for A
                rest_name = "{}.rest".format(rule_name)
                assert rest_name not in self.rules
                rest_parts = []  # Becomes new right-hand-side for A'
                for rhs in rule.as_container():
                    phrase = rhs.as_container()
                    first = phrase[0]
                    rest = phrase[1:]
                    if first.is_symbol_name() and first.content is rule_name:
                        rest_parts.append(self.MakeSeq(rest + [self.MakeSymbolName(rest_name)]))
                    else:
                        # TODO: use list_without_empty to shorten this
                        if len(phrase) > 0 and phrase[0].is_empty():
                            # beta is epsilon
                            assert len(phrase) == 1
                            self_parts.append( self.MakeSymbolName(rest_name) )
                        else:
                            self_parts.append( self.MakeSeq([x for x in phrase] + [self.MakeSymbolName(rest_name)]) )
                rest_parts.append(self.MakeEmpty())
                self.rules[rule_name] = self.MakeChoice(self_parts)
                self.rules[rest_name] = self.MakeChoice(rest_parts)


    def left_refactor(self,target_rule_name,stop_at_set):
        """
        Refactor the grammar, shifting uses of 'target_rule_name' in the first
        position out to the invoking context.

        That is, when 'target_rule_name' names nonterminal X,
        and 'A' is not in 'stop_at_set',
        and when:

            A -> X alpha1 | ... | X alphaN
            B -> A beta1 | A beta2 | gamma

        where no options in gamma begins with A.

        Then create/update rules:

            A.post.X -> alpha1 | ... | alphaN
            B -> X A.post.X beta1 | X A.post.X beta2 | gamma

        Repeat until settling.

        Remove unreachable rules.
        """
        name_suffix = ".post.{}".format(target_rule_name)

        # Map a rule name X to a set of rules Y where X appears
        # as a first nonterminal in one of Y's options.
        appears_first_in = defaultdict(set)
        for name, rule in self.rules.items():
            for option in rule.as_container():
                first = option.as_container()[0]
                if first.is_symbol_name():
                    appears_first_in[first.content].add(name)
        #print("appears first dict\n{}\n\n".format(appears_first_in))

        po = PrintOption()
        po.is_canonical = self.is_canonical
        po.inline_synthetic = False
        candidates = set(self.rules.keys())
        while len(candidates) > 0:
            for A in list(candidates):
                candidates.remove(A)
                if A in stop_at_set:
                    continue
                rule = self.rules[A]
                (starts,others,terms,empties) = rule.partition(target_rule_name)
                if len(starts) > 0 and (len(others)+len(terms)+len(empties) == 0):
                    #print("processing {}".format(A))
                    # Create the new rule.
                    new_rule_name = "{}{}".format(A,name_suffix)
                    # Form alpha1 ... alphaN
                    new_options = []
                    for option in rule:
                        if len(option.as_container()) == 1:
                            new_options.append(self.MakeEmpty())
                        else:
                            assert option.is_container() and (len(option)>1)
                            new_options.append(self.MakeSeq(option[1:]))
                    self.rules[new_rule_name] = self.MakeChoice(new_options)

                    # Rewrite A itself.
                    self_parts = [self.MakeSymbolName(x) for x in [target_rule_name,new_rule_name]]
                    self.rules[A] = self.MakeChoice([self.MakeSeq(self_parts)])

                    # Update bookkeeping for appears_first_in
                    for option in new_options:
                        first = option.as_container()[0]
                        if first.is_symbol_name():
                            appears_first_in[first.content].add(new_rule_name)

                    # Replace the old rule everywhere it appears in the first
                    # position
                    for parent_name in list(appears_first_in[A]):
                        if parent_name == A:
                            # Already processed above
                            continue
                        parent = self.rules[parent_name]
                        (starts,others,terms,empties) = parent.partition(A)
                        new_options = []
                        for option in starts:
                            parts = []
                            parts.append(self.MakeSymbolName(target_rule_name))
                            parts.append(self.MakeSymbolName(new_rule_name))
                            parts.extend(option.as_container()[1:])
                            new_options.append(self.MakeSeq(parts))
                        new_options.extend(others+terms+empties)
                        self.rules[parent_name] = self.MakeChoice(new_options)
                        appears_first_in[A].remove(parent_name)
                        appears_first_in[target_rule_name].add(parent_name)
                        # Set up transitive closure.
                        candidates.add(parent_name)

                    #print()
            #print()
        #print()

        #self.absorb_post(target_rule_name)
        self.remove_unused_rules()



    def left_absorb_post(self,target_rule_name):
        # Look for opportunities to reabsorb.
        #
        # If we have a rule like:
        #
        #   B -> X A.post.X beta1 | ... | X A.post.X beta2
        # where B is not A
        #
        # Then replace it with:
        #
        #   B -> A beta1 | ... | A beta2
        #
        name_suffix = ".post.{}".format(target_rule_name)
        for name, rule in self.rules.items():
            (starts,others,terms,empties) = rule.partition(target_rule_name)
            # Each options must start with X
            if len(others) + len(terms) + len(empties) > 0:
                continue
            assert len(starts) > 0
            # Each option must have at least two symbols
            if any([len(option.as_container()) < 2 for option in starts]):
                continue
            # The second element must be the same across all options
            if len(set([option.as_container()[1].reg_info.index for option in starts])) > 1:
                continue
            common = starts[0].as_container()[1]
            if not common.is_symbol_name() or common.content.find(name_suffix) < 0:
                continue
            # Find the 'A' as in 'A.post.X'
            replace_with_name = common.content[0:common.content.find(name_suffix)]
            if replace_with_name == name:
                # Don't create a left-recursion
                continue
            replace_with = self.MakeSymbolName(replace_with_name)
            # Rewrite the rule
            parts = []
            for option in starts:
                parts.append(self.MakeSeq([replace_with] + option[2:]))
            self.rules[name] = self.MakeChoice(parts)
        self.remove_unused_rules()


    def remove_unused_rules(self):
        reachable = set(self.preorder())
        for name in list(self.rules.keys()):
            if name not in reachable:
                del self.rules[name]

    def epsilon_refactor(self):
        """
        Inline the following kinds of cases:

        When this occurs:

            A ->  B | epsilon
            B ->  beta1 | beta2 | epsilon

        Then replace A by B in all rules.
        """

        has_empty = set()
        # Map a rule name to the rule name it should be replaced by.
        replacement = dict()

        for A in reversed(self.preorder()):
            A_rule = self.rules[A]
            (non_empties,empties) = A_rule.partition_epsilon()
            if len(empties) > 0:
                has_empty.add(A)
                # We've visited descendants already. See if this is an inlining case.
                if len(non_empties) == 1:
                    # Does it look like 'B'?
                    option = non_empties[0].as_container()
                    if len(option) == 1:
                        first = option[0]
                        if first.is_symbol_name() and first.content in has_empty:
                            replacement[A] = first.content
                            #print("  replacing {} with {}".format(A,first.content))

            # Update this rule with any scheduled replacements.
            changed_rule = False
            new_options = []
            for option in A_rule.as_container():
                changed_parts = False
                parts = []
                for x in option.as_container():
                    if x.is_symbol_name() and x.content in replacement:
                        parts.append(self.MakeSymbolName(replacement[x.content]))
                        changed_parts = True
                        changed_rule = True
                    else:
                        parts.append(x)
                new_options.append(self.MakeSeq(parts) if changed_parts else option)
            if changed_rule:
                self.rules[A] = self.MakeChoice(new_options)

        self.remove_unused_rules()

    def dedup_rhs(self,inline_stop=set(),verbose=False):
        """
        If two nonterminals have the same right hand side, combine them.

        Don't combine any rules named in inline_stop.
        """

        # Map an object index to the nonterminal that first defines it.
        index_to_name = dict()
        # Map a rule name to the rule name it should be replaced by.
        replacement = dict()

        def process_replacement(grammar,name,replacement_dict):
            # Update this rule with any scheduled replacements.
            rule = self.rules[name]
            changed_rule = False
            new_options = []
            for option in rule.as_container():
                changed_parts = False
                parts = []
                for x in option.as_container():
                    if x.is_symbol_name() and x.content in replacement:
                        parts.append(self.MakeSymbolName(replacement[x.content]))
                        changed_parts = True
                        changed_rule = True
                    else:
                        parts.append(x)
                new_options.append(self.MakeSeq(parts) if changed_parts else option)
            if changed_rule:
                self.rules[name] = self.MakeChoice(new_options)

        for A in reversed(self.preorder()):
            if A not in inline_stop:
                A_rule = self.rules[A]
                A_index = A_rule.reg_info.index
                if verbose:
                    print("   {} {} ".format(A,A_index))
                if A_index in index_to_name:
                    if verbose:
                        print("Replace {} with {}".format(A,index_to_name[A_index]))
                    replacement[A] = index_to_name[A_index]
                else:
                    index_to_name[A_index] = A
            process_replacement(self,A,replacement)


        for A in self.preorder():
            process_replacement(self,A,replacement)

        self.remove_unused_rules()

    def inline_single_choice_with_nonterminal(self,excepting_set=set()):
        """
        Inline a rule when it only has one option, and at least one of the
        symbols is a symbol name.

        Don't inline any symbol named by excepting_set.
        """

        # Map a rule name to the phrase it should be replaced with.
        replacement = dict()

        # Needed for computing follow sets
        excepting_set = set(excepting_set) | {self.start_symbol}

        # Process descendants first
        for A in reversed(self.preorder()):
            A_rule = self.rules[A].as_container()
            if (len(A_rule) == 1) and (A not in excepting_set):
                # There is only one option in the choice
                rhs = A_rule[0].as_container()
                # Skip inlining token definitions.
                if any([x.is_symbol_name() for x in rhs]):
                    replacement[A] = rhs

            # Update this rule with any scheduled replacements.
            changed_rule = False
            new_options = []
            for option in A_rule:
                changed_parts = False
                parts = []
                for x in option.as_container():
                    if x.is_symbol_name() and x.content in replacement:
                        parts.extend(replacement[x.content])
                        changed_parts = True
                        changed_rule = True
                    else:
                        parts.append(x)
                new_options.append(self.MakeSeq(parts) if changed_parts else option)
            if changed_rule:
                self.rules[A] = self.MakeChoice(new_options)

        self.remove_unused_rules()

    def inline_single_starrable(self):
        """
        Inline a rule when it only has one option, and its content starrable.

            A -> B
            B -> beta B | epsilon

        Replace A by B
        """

        # Map a rule name to the phrase it should be replaced with.
        replacement = dict()

        # Process descendants first
        for A in reversed(self.preorder()):
            A_rule = self.rules[A].as_container()
            if len(A_rule) == 1:
                option = A_rule[0].as_container()
                if len(option) == 1:
                    first = option[0]
                    if first.is_symbol_name():
                        first_name = first.content
                        if self.rules[first_name].as_starred(first_name) is not None:
                            replacement[A] = [first]

            # Update this rule with any scheduled replacements.
            changed_rule = False
            new_options = []
            for option in A_rule:
                changed_parts = False
                parts = []
                for x in option.as_container():
                    if x.is_symbol_name() and x.content in replacement:
                        parts.extend(replacement[x.content])
                        changed_parts = True
                        changed_rule = True
                    else:
                        parts.append(x)
                new_options.append(self.MakeSeq(parts) if changed_parts else option)
            if changed_rule:
                self.rules[A] = self.MakeChoice(new_options)

        self.remove_unused_rules()

    def inline_specific(self,specific_set):
        """
        Inline a set of rules. They must have only one option in the choice.
        """

        # Map a rule name to the phrase it should be replaced with.
        replacement = dict()

        # Process descendants first
        for A in reversed(self.preorder()):
            A_rule = self.rules[A].as_container()
            if A in specific_set:
                assert(len(A_rule)==1)
                replacement[A] = A_rule.as_container()[0].as_container()

            # Update this rule with any scheduled replacements.
            changed_rule = False
            new_options = []
            for option in A_rule:
                changed_parts = False
                parts = []
                for x in option.as_container():
                    if x.is_symbol_name() and x.content in replacement:
                        parts.extend(replacement[x.content])
                        changed_parts = True
                        changed_rule = True
                    else:
                        parts.append(x)
                new_options.append(self.MakeSeq(parts) if changed_parts else option)
            if changed_rule:
                self.rules[A] = self.MakeChoice(new_options)

        self.remove_unused_rules()

    def inline_when_toplevel_prefix(self,specific_set):
        """
        When:

          'A' is in specific_set, and

            A -> alpha1 | alpha2

          'A' appears first as a choice in another rule:

            B -> A beta | others...

          Inline A into B:

            B -> alpha1 beta | alpha2 beta | others...

        """

        # Map a rule name to the phrase it should be replaced with.
        replacement = dict()

        # Process descendants first
        for A in reversed(self.preorder()):
            A_rule = self.rules[A].as_container()
            if A in specific_set:
                replacement[A] = A_rule

            # Update this rule with any scheduled replacements.
            changed_rule = False
            new_options = []
            for option in A_rule:
                option_parts = option.as_container()
                first = option_parts[0]
                if first.is_symbol_name() and first.content in replacement:
                    for repl_option in replacement[first.content]:
                        parts = [x for x in repl_option.as_container()]
                        parts = parts + option_parts[1:]
                        new_options.append(self.MakeSeq(parts))
                    changed_rule = True
                else:
                    new_options.append(option)
            if changed_rule:
                self.rules[A] = self.MakeChoice(new_options)

        self.remove_unused_rules()

    def refactor_post(self,post_name):
        """
        If there are rules
            X -> ...
            X.post.POST

        Then set
            X -> POST X.post.POST
        """
        for name in list(self.rules):
            related_post = "{}.post.{}".format(name,post_name)
            if related_post in self.rules:
                parts = [self.MakeSymbolName(x) for x in [post_name, related_post]]
                self.rules[name] = self.MakeChoice([self.MakeSeq(parts)])


    def hoist_until(self,target_rule_name,stop_at_set):
        """
        Hoists the rules for a a nonterminal into its ancestors.

        When target_rule_name holds the name for nonterminal X, and
        there is a rule:

            A -> X alpha1 | B alpha2 | rest
            B -> beta1 | beta2

        and 'B' is a nonterminal that is not X,
        and 'A' is not in stop_at_set,

        Then replace A with:

            A -> X alpha1 | beta1 alpha2 | beta2 alpha2 | rest

        Repeat until settling.
        Eventually all options in A will start with X:

            A -> X alpha1 | X ...1 | X ...2 | rest

        The target_rule_name must be chosen to avoid infinite replacement.
        """
        assert self.is_canonical


        def expand_first(grammar,rule):
            """
                When rule is
                    Seq(A rest)
                and A -> A1 | ... | An
                Return [ A1 rest | ... | An rest ]

                If Ai is epsilon, then its corresponding term is just 'rest'
            """
            result = []
            # Hoist the rule for 'other' nonterminal.
            phrase = rule.as_container()
            first = phrase[0]
            assert first.is_symbol_name() and (first.content != target_rule_name)
            #print("  elaborating rule for {} ".format(first.content))
            rest = phrase[1:]
            other_rule = self.rules[first.content]
            for other_rhs in other_rule.as_container():
                result.append(grammar.MakeSeq(list_without_empty(other_rhs.as_container()) + rest))
            return result


        # Process in reverse order to reduce duplication.
        order_of_attack = list(reversed(self.preorder()))
        keep_going = True
        ancestors = set()
        while keep_going:
            keep_going = False
            #print("hoisting worklist: {}".format(" ".join(order_of_attack)))

            for candidate_rule_name in order_of_attack:
                rule = self.rules[candidate_rule_name]
                #print("consider {}".format(candidate_rule_name))
                (with_target_rule_name,other_rules,term,empty) = rule.partition(target_rule_name)
                #print("  {}   {}  {}  {}".format(len(with_target_rule_name),len(other_rules),len(term), len(empty)))
                if len(with_target_rule_name) > 0 and len(other_rules) > 0:
                    #print("  need to hoist")
                    # Need to hoist
                    replacement = with_target_rule_name
                    for other in other_rules:
                        replacement.extend(expand_first(self,other))
                    replacement.extend(term)
                    replacement.extend(empty)
                    self.rules[candidate_rule_name] = self.MakeChoice(replacement)
                    #print("setting {} to {}".format(candidate_rule_name,str(self.rules[candidate_rule_name])))
                    keep_going = True
                    if candidate_rule_name not in stop_at_set:
                        ancestors.add(candidate_rule_name)

            for candidate_rule_name in order_of_attack:
                for ancestor in ancestors:
                    rule = self.rules[candidate_rule_name]
                    (with_ancestor,other_rules,term,empty) = rule.partition(ancestor)
                    #print("  {}   {}  {}  {}".format(len(with_ancestor),len(other_rules),len(term), len(empty)))
                    if len(with_ancestor) > 0:
                        #print("    expanding ancestor {}".format(ancestor))
                        replacement = []
                        for a_rule in with_ancestor:
                            replacement.extend(expand_first(self,a_rule))
                        replacement.extend(other_rules)
                        replacement.extend(term)
                        replacement.extend(empty)
                        self.rules[candidate_rule_name] = self.MakeChoice(replacement)
                        #print("setting {} to {}".format(candidate_rule_name,str(self.rules[candidate_rule_name])))
                        keep_going = True

    def rotate_one_or_mores(self):
        """
        When a rule looks like:

            A -> prefix (a1 ... aN)* a1 ... aN suffix

        then rewrite it as:

            A -> prefix a1 ... aN (a1 ... aN)* suffix
        """

        for name in self.rules:
            changed_rule = False
            new_options = []
            for raw_option in [x for x in self.rules[name].as_container()]:
                option = raw_option.as_container()
                keep_going = True
                while keep_going:
                    keep_going = False
                    # See if we can rotate option[pivot] with what follows it.
                    for ipivot in range(0,len(option)-1):
                        (prefix,pivot,rest) = (option[0:ipivot],option[ipivot],option[ipivot+1:])
                        if pivot.is_symbol_name():
                            pivot_as_starred = self.rules[pivot.content].as_starred(pivot.content)
                            if pivot_as_starred is None:
                                continue
                            rest_prefix = rest[0:len(pivot_as_starred)]
                            rest_tail = rest[len(pivot_as_starred):]
                            # Compare keys
                            pivot_keys = [x.reg_info.index for x in pivot_as_starred]
                            rest_prefix_keys = [x.reg_info.index for x in rest_prefix]
                            if pivot_keys == rest_prefix_keys:
                                # Rotate
                                option = self.MakeSeq(prefix + rest_prefix + [pivot] + rest_tail)
                                changed_rule = True
                                keep_going = True
                                #print("  rotated")
                                break
                new_options.append(option)
            if changed_rule:
                self.rules[name] = self.MakeChoice(new_options)


    def LL1(self):
        """
        Constructs an LL(1) parser table and associated conflicts (if any).

        Args:
            self: Grammar in canonical form with First and Follow
            sets computed.

        Returns: a 2-tuple:
            an LL(1) parser table
                Key is tuple (lhs,rhs) where lhs is the name of the nonterminal
                and rhs is the Rule for the right-hand side being reduced:
                It may be a SymbolName, a Token, or a Sequence of Symbols and Tokens
            a list of conflicts
        """

        conflicts = []
        table = dict()
        def add(lhs,terminal,action):
            action_key = (lhs,terminal)
            if action_key in table:
                # Record the conflict, and only keep the original.
                prev = table[action_key]
                conflicts.append((lhs,terminal,prev,action))
            else:
                table[action_key] = action

        for lhs, rule in self.rules.items():
            if rule.is_container():
                # Top-level rules are Choice nodes.
                if not isinstance(rule,Choice):
                    raise RuntimeError("expected Choice node for "+
                       +"'{}' rule, got: {}".format(lhs,rule))
                # For each rule A -> alpha,
                for rhs in rule:
                    for x in first(self,rhs.as_container()):
                        if x.is_empty():
                            # Add A -> alpha to M[A,b] for each terminal
                            # b in Follow(A)
                            for f in rule.follow:
                                add(lhs,f,LLReduce(lhs,rhs))
                        else:
                            # For each terminal x in First(alpha), add
                            # A -> alpha to M[A,x]
                            add(lhs,x,LLReduce(lhs,rhs))
        return (table,conflicts)

    def LR1_ItemSets(self):
        """
        Constructs the LR(1) sets of items.

        Args:
            self: Grammar in canonical form, with computed First
                and Follow sets.

        Returns: a list of the LR1(1) item-sets for the grammar.
        """

        # The root item is the one representing the entire language.
        # Since the grammar is in canonical form, it's a Choice over a
        # single sequence.
        root_item = self.MakeItem(LANGUAGE, self.rules[LANGUAGE][0],0)

        # An ItemSet can be found by any of the items in its core.
        # Within an ItemSet, an item maps to its lookahead set.

        root_item_set = ItemSet(self, {root_item: LookaheadSet({self.end_of_text})}).close(self)

        LR1_item_sets_result = set({root_item_set})

        dirty_set = LR1_item_sets_result.copy()
        while len(dirty_set) > 0:
            work_list = dirty_set.copy()
            dirty_set = set()
            # Sort the work list so we get deterministic ordering, and therefore
            # deterministic itemset core numbering.
            for item_set in sorted(work_list):
                (_,gotos) = item_set.gotos(self)
                for (X, dest_item_set) in gotos:
                    if dest_item_set not in LR1_item_sets_result:
                        LR1_item_sets_result.add(dest_item_set)
                        dirty_set.add(dest_item_set)

        return sorted(LR1_item_sets_result,key=ItemSet.pretty_key)

    def LALR1(self, max_item_sets=None):
        """
        Constructs an LALR(1) parser table.

        Args:
            self: Grammar in canonical form, with computed First
                and Follow sets.
            max_item_sets:
                An artificial limit on the number of item set cores created.
                May terminate the algorithm before it has computed the full answer.

        Returns: a tuple:
            - a list of the LALR1(1) item-sets for the grammar.
            - an action table, mapping (item_set, terminal) to an Action
            - an array of Reduction objects, where the ith has index i
            - a list of conflicts
        """

        # Part 1. Compute LALR(1) item sets

        # Mapping from a core index to an already-discovered item set.
        by_index = dict()

        root_item = self.MakeItem(LANGUAGE, self.rules[LANGUAGE][0],0)

        # An ItemSet can be found by any of the items in its core.
        # Within an ItemSet, an item maps to its lookahead set.

        root_item_set = ItemSet(self, {root_item: LookaheadSet({self.end_of_text})}).close(self)
        by_index[root_item_set.core_index] = root_item_set

        item_set_core_ids = set({root_item_set.core_index})

        dirty_set = item_set_core_ids.copy()
        keep_going = True
        #while len(dirty_set) > 0:
        while keep_going:
            keep_going = False
            #work_list = dirty_set.copy()
            #dirty_set = set()
            if max_item_sets is not None:
                if len(by_index) > max_item_sets:
                    break
            # Sort the work list so we get deterministic ordering, and therefore
            # deterministic itemset core numbering.
            # Go backwards to try to explore the most recently changed items first.
            work_list = sorted(item_set_core_ids, reverse=True)
            for core_index in work_list:
                item_set = by_index[core_index]
                (changed,gotos) = item_set.gotos(self,by_index_memo=by_index)
                keep_going = keep_going | changed
                for (X, item_set_for_X) in gotos:
                    if item_set_for_X.core_index not in by_index:
                        item_set_core_ids.add(item_set_for_X.core_index)
                        by_index[item_set_for_X.core_index] = item_set_for_X
                        dirty_set.add(item_set_for_X.core_index)
                        keep_going = True

        # Now this is a list of item_sets
        sorted_item_set_core_ids = sorted(item_set_core_ids)

        # Part 2. Compute the action table and conflicts.
        # Do this as a second pass because it's conceivable that an item set may
        # go from non-accepting to accepting during initial exploration
        # of the item sets.

        conflicts = []
        # Maps (item_set.core_index, terminal.reg_info.index) to an Action.
        action_table = dict()
        def addAction(item_set, terminal, action):
            isinstance(item_set, ItemSet) or raiseRE("expected ItemSet")
            terminal.is_terminal() or raiseRE("expected terminal: " + str(terminal))
            isinstance(action,Action) or raiseRE("expected action")

            # Use indices, for speed.
            # But also keep the terminal prompting this action.
            action_key = (item_set.core_index,terminal.reg_info.index)
            if action_key not in action_table:
                action_table[action_key] = action
            else:
                prev_action = action_table[action_key]
                if prev_action != action:
                    # Record the conflict, and only keep the original.
                    conflicts.append(Conflict(item_set,terminal,prev_action,action))

        # Maps an item index to its reduction index.
        reduced_items = dict()
        # List, where element i is the Reduce object with index i
        reductions = []
        def make_reduce(item):
            if item.reg_info.index in reduced_items:
                return reductions[reduced_items[item.reg_info.index]]
            index = len(reduced_items)
            reduced_items[item.reg_info.index] = index
            result = Reduce(item,index)
            reductions.append(result)
            return result

        # The goto table for noterminals
        # Maps (item_set, nonterminal) to the next item set
        nonterminal_goto = dict()

        for item_set_core_id in sorted_item_set_core_ids:
            item_set = by_index[item_set_core_id]
            # Register Reduce and Accept actions
            for item_id, lookahead in item_set.id_to_lookahead.items():
                item = item_set.id_to_item[item_id]
                if item.is_accepting() and lookahead.includesEndOfText():
                    addAction(item_set, self.end_of_text, Accept())
                if item.at_end() and (item.lhs.content != LANGUAGE):
                    # Register reductions
                    for terminal in lookahead:
                        addAction(item_set, terminal, make_reduce(item))

            # Register Shift actions
            for xid, edge in item_set.goto.items():
                X = self.findByIndex(xid)
                item_set_for_X = edge.NextItemSet(self)[1]
                if X.is_terminal():
                    # Can't be EndOfText by construction of the goto result
                    isinstance(X,Token) or raiseRE("internal error: expected a token")
                    addAction(item_set, X, Shift(item_set_for_X))
                elif X.is_symbol_name():
                    nonterminal_goto[(item_set.core_index,X)] = item_set_for_X

        item_sets = [by_index[i] for i in sorted_item_set_core_ids]

        return ParseTable(self,item_sets, action_table, nonterminal_goto, reductions, conflicts)

    def LALR1_ItemSets(self, max_item_sets=None):
        """
        Constructs an LALR(1) parser table and associated conflicts (if any).

        Args:
            self: Grammar in canonical form with, with compute  First
                and Follow sets computed.
            max_item_sets:
                An artificial limit on the number of item set cores created.
                May terminate the algorithm before it has computed the full answer.

        Returns: a list of the LALR1(1) item-sets for the grammar.
        """

        item_sets = self.LALR1(max_item_sets=max_item_sets).states
        return item_sets

