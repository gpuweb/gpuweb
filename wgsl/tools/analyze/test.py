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
Unit tests for Grammar.py
"""

import unittest
import Grammar
import sys

def first_str(g,name):
    return str(Grammar.LookaheadSet(g.find(name).first()))
def follow_str(g,name):
    return str(Grammar.LookaheadSet(g.find(name).follow))

# Like Aho, Sethi, Ullman Example 4.17, but with E changed
DRAGON_BOOK_EXAMPLE_4_17 = """
{
  "name": "dragon_book_ex_4_17",
  "word": "id",
  "rules": {
    "E": {
      "type": "SEQ",
      "members": [
        {
          "type": "SYMBOL",
          "name": "T"
        },
        {
          "type": "SYMBOL",
          "name": "Eprime"
        }
      ]
    },
    "Eprime": {
      "type": "CHOICE",
      "members": [
        {
          "type": "SEQ",
          "members": [
            {
              "type": "SYMBOL",
              "name": "plus"
            },
            {
              "type": "SYMBOL",
              "name": "T"
            },
            {
              "type": "SYMBOL",
              "name": "Eprime"
            }
          ]
        },
        {
          "type": "BLANK"
        }
      ]
    },
    "T": {
      "type": "SEQ",
      "members": [
        {
          "type": "SYMBOL",
          "name": "F"
        },
        {
          "type": "SYMBOL",
          "name": "Tprime"
        }
      ]
    },
    "Tprime": {
      "type": "CHOICE",
      "members": [
        {
          "type": "SEQ",
          "members": [
            {
              "type": "SYMBOL",
              "name": "times"
            },
            {
              "type": "SYMBOL",
              "name": "F"
            },
            {
              "type": "SYMBOL",
              "name": "Tprime"
            }
          ]
        },
        {
          "type": "BLANK"
        }
      ]
    },
    "F": {
      "type": "CHOICE",
      "members": [
        {
          "type": "SEQ",
          "members": [
            {
              "type": "SYMBOL",
              "name": "paren_left"
            },
            {
              "type": "SYMBOL",
              "name": "E"
            },
            {
              "type": "SYMBOL",
              "name": "paren_right"
            }
          ]
        },
        {
          "type": "SYMBOL",
          "name": "id"
        }
      ]
    },
    "id": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "id"
      }
    },
    "plus": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "+"
      }
    },
    "times": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "*"
      }
    },
    "paren_left": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "("
      }
    },
    "paren_right": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": ")"
      }
    }
  },
  "extras": [],
  "conflicts": [],
  "precedences": [],
  "externals": [],
  "inline": [],
  "supertypes": []
}
"""

DRAGON_BOOK_EXAMPLE_4_42 = """
{
  "name": "dragon_book_ex_4_42",
  "word": "id",
  "rules": {
    "translation_unit": {
      "type": "SEQ",
      "members": [
        {
          "type": "SYMBOL",
          "name": "C"
        },
        {
          "type": "SYMBOL",
          "name": "C"
        }
      ]
    },
    "C": {
      "type": "CHOICE",
      "members": [
        {
          "type": "SEQ",
          "members": [
            {
              "type": "SYMBOL",
              "name": "c"
            },
            {
              "type": "SYMBOL",
              "name": "C"
            }
          ]
        },
        {
          "type": "SYMBOL",
          "name": "d"
        }
      ]
    },
    "c": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "c"
      }
    },
    "d": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "d"
      }
    }
  },
  "extras": [],
  "conflicts": [],
  "precedences": [],
  "externals": [],
  "inline": [],
  "supertypes": []
}
"""


SIMPLE_WGSL = """
{
  "name": "firsts",
  "word": "ident",
  "rules": {
    "translation_unit": {
      "type": "SEQ",
      "members": [
        {
          "type": "CHOICE",
          "members": [
            {
              "type": "REPEAT1",
              "content": {
                "type": "SYMBOL",
                "name": "global_decl"
              }
            },
            {
              "type": "BLANK"
            }
          ]
        }
      ]
    },
    "type_alias_decl": {
      "type": "SEQ",
      "members": [
        {
          "type": "SYMBOL",
          "name": "type"
        },
        {
          "type": "SYMBOL",
          "name": "ident"
        },
        {
          "type": "SYMBOL",
          "name": "equal"
        },
        {
          "type": "SYMBOL",
          "name": "ident"
        }
      ]
    },
    "global_decl": {
      "type": "CHOICE",
      "members": [
        {
          "type": "SYMBOL",
          "name": "semicolon"
        },
        {
          "type": "SEQ",
          "members": [
            {
              "type": "SYMBOL",
              "name": "type_alias_decl"
            },
            {
              "type": "SYMBOL",
              "name": "semicolon"
            }
          ]
        },
        {
          "type": "SYMBOL",
          "name": "function_decl"
        }
      ]
    },
    "function_decl": {
      "type": "SEQ",
      "members": [
        {
          "type": "CHOICE",
          "members": [
            {
              "type": "REPEAT1",
              "content": {
                "type": "SYMBOL",
                "name": "at"
              }
            },
            {
              "type": "BLANK"
            }
          ]
        },
        {
          "type": "SYMBOL",
          "name": "function_header"
        },
        {
          "type": "SYMBOL",
          "name": "brace_left"
        },
        {
          "type": "SYMBOL",
          "name": "brace_right"
        }
      ]
    },
    "function_header": {
      "type": "SEQ",
      "members": [
        {
          "type": "SYMBOL",
          "name": "fn"
        },
        {
          "type": "SYMBOL",
          "name": "ident"
        },
        {
          "type": "SYMBOL",
          "name": "paren_left"
        },
        {
          "type": "SYMBOL",
          "name": "paren_right"
        }
      ]
    },
    "ident": {
      "type": "TOKEN",
      "content": {
        "type": "PATTERN",
        "value": "[a-z]+"
      }
    },
    "at": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "@"
      }
    },
    "_blankspace": {
      "type": "TOKEN",
      "content": {
        "type": "PATTERN",
        "value": "\\\\s+"
      }
    },
    "fn": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "fn"
      }
    },
    "type": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "type"
      }
    },
    "equal": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "="
      }
    },
    "semicolon": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": ";"
      }
    },
    "brace_left": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "{"
      }
    },
    "brace_right": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "}"
      }
    },
    "paren_left": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "("
      }
    },
    "paren_right": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": ")"
      }
    }
  },
  "extras": [
    {
      "type": "SYMBOL",
      "name": "_blankspace"
    }
  ],
  "conflicts": [],
  "precedences": [],
  "externals": [
  ],
  "inline": [
  ],
  "supertypes": []
}
"""


def _fixed(content):
    return """
    {{
      "type": "TOKEN",
      "content": {{
        "type": "STRING",
        "value": "{}"
      }}
    }}""".format(content,content)
def _pattern(content):
    return """
    {{
      "type": "TOKEN",
      "content": {{
        "type": "PATTERN",
        "value": "{}"
      }}
    }}""".format(content)
def _sym(content):
    return """
    {{
      "type": "SYMBOL",
      "name": "{}"
    }}""".format(content)
def _empty():
    return """{ "type": "BLANK" }"""

def _def(name,content):
    return """ "{}":
      {}
    """.format(name,content)

def _seq(*args):
    return """{{
      "type": "SEQ",
      "members": [
        {}
      ]
    }}""".format(",".join([*args]))
def _choice(*args):
    return """{{
      "type": "CHOICE",
      "members": [
        {}
      ]
    }}""".format(",".join([*args]))
def _rep1(content):
    return """
    {{
      "type": "REPEAT1",
      "content":
        {}
    }}""".format(content)

def _rep(content):
    return """
    {{
      "type": "REPEAT",
      "content":
        {}
    }}""".format(content)

def _optional(content):
    return _choice(content,_empty())

def _star(content): # Kleene star
    return _rep(content)

def _g(*args):
    pre = """
{
  "name": "generated",
  "word": "ident",
  "rules": {
"""

    post = """
  },
  "extras": [
    {
      "type": "SYMBOL",
      "name": "_blankspace"
    }
  ],
  "conflicts": [],
  "precedences": [],
  "externals": [
  ],
  "inline": [
  ],
  "supertypes": []
}
"""
    return "{}{}{}".format(pre,",".join([*args]),post)

def _gl(start_symbol,*args):
    s = _g(*args)
    #print(s)
    return Grammar.Grammar.Load(s,start_symbol)


EPSILON=u"\u03b5"

def strset(s):
    return " ".join(sorted([str(i) for i in s]))

class DragonBook(unittest.TestCase):
    def setUp(self):
        self.g = Grammar.Grammar.Load(DRAGON_BOOK_EXAMPLE_4_17,'E')

    # Check First sets
    def test_E_first(self):
        r = self.g.find("E")
        self.assertEqual(strset(r.first()), "'(' 'id'")

    def test_T_first(self):
        r = self.g.find("T")
        self.assertEqual(strset(r.first()), "'(' 'id'")

    def test_F_first(self):
        r = self.g.find("F")
        self.assertEqual(strset(r.first()), "'(' 'id'")

    def test_Eprime_first(self):
        r = self.g.find("Eprime")
        self.assertEqual(strset(r.first()), "'+' {}".format(EPSILON))

    def test_Tprime_first(self):
        r = self.g.find("Tprime")
        self.assertEqual(strset(r.first()), "'*' {}".format(EPSILON))

    # Check Follow sets
    def test_E_follow(self):
        r = self.g.find("E")
        self.assertEqual(strset(r.follow), "')' EndOfText")

    def test_Eprime_follow(self):
        r = self.g.find("Eprime")
        self.assertEqual(strset(r.follow), "')' EndOfText")

    def test_T_follow(self):
        r = self.g.find("T")
        self.assertEqual(strset(r.follow), "')' '+' EndOfText")

    def test_Tprime_follow(self):
        r = self.g.find("Tprime")
        self.assertEqual(strset(r.follow), "')' '+' EndOfText")

    def test_F_follow(self):
        r = self.g.find("F")
        self.assertEqual(strset(r.follow), "')' '*' '+' EndOfText")


class SimpleWgsl_First(unittest.TestCase):

    def setUp(self):
        self.g = Grammar.Grammar.Load(SIMPLE_WGSL,'translation_unit')

    def test_token_string(self):
        r = self.g.find('at')
        self.assertEqual(1,len(r.first()))
        self.assertEqual("'@'",strset(r.first()))
        self.assertFalse(r.derives_empty())

    def test_token_pattern(self):
        r = self.g.find('ident')
        self.assertEqual("/[a-z]+/",strset(r.first()))
        self.assertFalse(r.derives_empty())

    def test_empty(self):
        r = self.g.empty
        self.assertEqual(EPSILON,strset(r.first()))
        self.assertTrue(r.derives_empty())

    def test_end_of_text(self):
        r = self.g.end_of_text
        self.assertEqual("EndOfText",strset(r.first()))
        self.assertFalse(r.derives_empty())

    def test_function_header(self):
        # A Sequence rule with definite first symbol
        r = self.g.find('function_header')
        self.assertEqual("'fn'",strset(r.first()))
        self.assertFalse(r.derives_empty())

    def test_function_decl(self):
        # A sequence with an optional first symbol
        r = self.g.find('function_decl')
        self.assertEqual("'@' 'fn'",strset(r.first()))
        self.assertFalse(r.derives_empty())

    def test_translation_unit_0_0(self):
        # Can be empty.
        r = self.g.find('translation_unit/0.0')
        self.assertEqual("';' '@' 'fn' 'type' {}".format(EPSILON),strset(r.first()))
        self.assertTrue(r.derives_empty())

    def test_translation_unit(self):
        # Can be empty.
        r = self.g.find('translation_unit')
        self.assertEqual("';' '@' 'fn' 'type' {}".format(EPSILON),strset(r.first()))
        self.assertTrue(r.derives_empty())


class SimpleWgsl_Follow(unittest.TestCase):

    def setUp(self):
        self.g = Grammar.Grammar.Load(SIMPLE_WGSL,'translation_unit')

    def test_token_string(self):
        r = self.g.find('at')
        self.assertEqual(set(), r.follow)

    def test_token_pattern(self):
        r = self.g.find('ident')
        self.assertEqual(set(), r.follow)

    def test_empty(self):
        r = self.g.empty
        self.assertEqual(set(), r.follow)

    def test_end_of_text(self):
        r = self.g.end_of_text
        self.assertEqual(set(), r.follow)

    def test_function_decl_0_0(self):
        # Attribute list is followed by 'fn'
        r = self.g.find('function_decl/0.0')
        self.assertEqual("'fn'",strset(r.follow))

    def test_function_decl(self):
        r = self.g.find('function_decl')
        self.assertEqual("';' '@' 'fn' 'type' EndOfText",strset(r.follow))

    def test_global_decl(self):
        # A global decl can be followed by another global decl.
        # So the non-Empty symbols from global-decl's First set
        # is what is in its Follow set.
        r = self.g.find('global_decl')
        self.assertEqual("';' '@' 'fn' 'type' EndOfText",strset(r.follow))

    def test_translation_unit(self):
        # Can be empty.
        r = self.g.find('translation_unit')
        self.assertEqual("EndOfText",strset(r.follow))


class Item_Basics(unittest.TestCase):
    def make_item(self,g,*args):
        return g.MakeItem(*args)

    def test_Item_OfEmpty_Good(self):
        g = _gl("e",_def("e",_empty()))
        it = g.MakeItem("e",g.MakeEmpty(),0)
        self.assertEqual(it.items(), [])
        self.assertEqual(it.lhs, g.MakeSymbolName("e"))
        self.assertEqual(it.position, 0)

    def test_Item_OfEmpty_PosTooSmall(self):
        g = _gl("e",_def("e",_empty()))
        self.assertRaises(RuntimeError, self.make_item, g, "e", g.MakeEmpty(), -1)

    def test_Item_OfEmpty_PosTooBig(self):
        g = _gl("e",_def("e",_empty()))
        self.assertRaises(RuntimeError, self.make_item, g, "e", g.MakeEmpty(), 1)

    def test_Item_OfFixed_Pos0(self):
        g = _gl("t",_def("t",_fixed('x')))
        t = g.MakeFixed('x')
        it = g.MakeItem("t",t,0)
        self.assertEqual(it.rule, t)
        self.assertEqual(it.position, 0)
        self.assertEqual(it.items(), [t])

    def test_Item_OfFixed_Pos1(self):
        g = _gl("t",_def("t",_fixed('x')))
        t = g.MakeFixed('x')
        it = g.MakeItem("t",t,1)
        self.assertEqual(it.lhs, g.MakeSymbolName("t"))
        self.assertEqual(it.rule, t)
        self.assertEqual(it.position, 1)
        self.assertEqual(it.items(), [t])

    def test_Item_OfFixed_PosTooSmall(self):
        g = _gl("t",_def("t",_fixed('x')))
        self.assertRaises(RuntimeError, self.make_item, g, "t", g.MakeFixed('x'), -1)

    def test_Item_OfFixed_PosTooBig(self):
        g = _gl("t",_def("t",_fixed('x')))
        self.assertRaises(RuntimeError, self.make_item, g, "t", g.MakeFixed('x'), 2)

    def test_Item_OfPattern_Pos0(self):
        g = _gl("t",_def("t",_pattern('[a-z]+')))
        t = g.MakePattern('[a-z]+')
        it = g.MakeItem("t",t,0)
        self.assertEqual(it.rule, t)
        self.assertEqual(it.position, 0)
        self.assertEqual(it.items(), [t])

    def test_Item_OfPattern_Pos1(self):
        g = _gl("t",_def("t",_pattern('[a-z]+')))
        t = g.MakePattern('[a-z]+')
        it = g.MakeItem("t",t,1)
        self.assertEqual(it.rule, t)
        self.assertEqual(it.position, 1)
        self.assertEqual(it.items(), [t])

    def test_Item_OfPattern_PosTooSmall(self):
        g = _gl("t",_def("t",_pattern('[a-z]+')))
        self.assertRaises(RuntimeError, self.make_item, g, "t", g.MakePattern('[a-z]+'), -1)

    def test_Item_OfPattern_PosTooBig(self):
        g = _gl("t",_def("t",_pattern('[a-z]+')))
        self.assertRaises(RuntimeError, self.make_item, g, "t", g.MakePattern('[a-z]+'), 2)

    def test_Item_OfSymbol_Pos0(self):
        g = _gl("t",_def("t",_sym('x')),_def("x",_fixed("X")))
        t = g.MakeSymbolName('x')
        it = g.MakeItem("t",t,0)
        self.assertEqual(it.rule, t)
        self.assertEqual(it.position, 0)
        self.assertEqual(it.items(), [t])

    def test_Item_OfSymbol_Pos1(self):
        g = _gl("t",_def("t",_sym('x')),_def("x",_fixed("X")))
        t = g.MakeSymbolName('x')
        it = g.MakeItem("t",t,1)
        self.assertEqual(it.rule, t)
        self.assertEqual(it.position, 1)
        self.assertEqual(it.items(), [t])

    def test_Item_OfSymbol_PosTooSmall(self):
        g = _gl("t",_def("t",_sym('x')),_def("x",_fixed("X")))
        self.assertRaises(RuntimeError, self.make_item, g, "t", g.MakeSymbolName('x'), -1)

    def test_Item_OfSymbol_PosTooBig(self):
        g = _gl("t",_def("t",_sym('x')),_def("x",_fixed("X")))
        self.assertRaises(RuntimeError, self.make_item, g, "t", g.MakeSymbolName('x'), 2)

    def example_seq(self,g):
        return g.MakeSeq([g.MakeFixed('x'), g.MakeSymbolName('blah')])

    def test_Item_OfSeq_Pos0(self):
        g = _gl("t",_def("t", _seq(_fixed('x'),_sym('blah'))),_def("blah",_fixed("blah")))
        t = self.example_seq(g)
        it = g.MakeItem("t",t,0)
        self.assertEqual(it.rule, t)
        self.assertEqual(it.position, 0)
        self.assertEqual(it.items(), [i for i in t])

    def test_Item_OfSeq_Pos1(self):
        g = _gl("t",_def("t", _seq(_fixed('x'),_sym('blah'))),_def("blah",_fixed("blah")))
        t = self.example_seq(g)
        it = g.MakeItem("t",t,1)
        self.assertEqual(it.rule, t)
        self.assertEqual(it.position, 1)
        self.assertEqual(it.items(), [i for i in t])

    def test_Item_OfSeq_Pos2(self):
        g = _gl("t",_def("t", _seq(_fixed('x'),_sym('blah'))),_def("blah",_fixed("blah")))
        t = self.example_seq(g)
        it = g.MakeItem("t",t,2)
        self.assertEqual(it.rule, t)
        self.assertEqual(it.position, 2)
        self.assertEqual(it.items(), [i for i in t])

    def test_Item_OfSeq_PosTooSmall(self):
        g = _gl("t",_def("t", _seq(_fixed('x'),_sym('blah'))),_def("blah",_fixed("blah")))
        self.assertRaises(RuntimeError, self.make_item, g, "t", self.example_seq(g), -1)

    def test_Item_OfSeq_PosTooBig(self):
        g = _gl("t",_def("t", _seq(_fixed('x'),_sym('blah'))),_def("blah",_fixed("blah")))
        self.assertRaises(RuntimeError, self.make_item, g, "t", self.example_seq(g), 3)

    def test_Item_OfChoice(self):
        g = _gl("c",_def("c", _choice("")))
        self.assertRaises(RuntimeError, self.make_item, g, "c", g.MakeChoice([]), 0)

    def test_Item_OfRepeat1(self):
        g = _gl("c",_def("c", _rep1(_sym("ddd"))),_def("ddd",_fixed("ddd")))
        self.assertRaises(RuntimeError, self.make_item, g, "c", g.MakeRepeat1([g.MakeSymbolName("ddd")]), 0)

    def test_Item_is_accepting(self):
        g = _gl("translation_unit",_def("translation_unit",_sym("S")),_def("S",_fixed("abc")))
        tu = g.MakeSeq([g.MakeFixed('translation_unit')])
        l0 = g.MakeItem(Grammar.LANGUAGE,tu,0)
        l1 = g.MakeItem(Grammar.LANGUAGE,tu,1)
        s0 = g.MakeItem("S",tu,0)
        s1 = g.MakeItem("S",tu,1)
        self.assertFalse(l0.is_accepting())
        self.assertTrue(l1.is_accepting())
        self.assertFalse(s0.is_accepting())
        self.assertFalse(s1.is_accepting())

class Rule_Equality(unittest.TestCase):
    def test_Empty(self):
        g = _gl("a",_def("a",_empty()))
        a = g.MakeEmpty()
        a2 = g.MakeEmpty()
        self.assertEqual(a,a)
        self.assertTrue(a == a)
        self.assertTrue(a == a2)

    def test_EndOfText(self):
        g = _gl("a",_def("a",_empty()))
        a = g.MakeEndOfText()
        a2 = g.MakeEndOfText()
        self.assertEqual(a,a)
        self.assertTrue(a == a)
        self.assertTrue(a == a2)

    def test_Fixed(self):
        g = _gl("a",_def("a",_fixed("a")),_def("b",_fixed("b")))
        a = g.MakeFixed('a')
        a2 = g.MakeFixed('a')
        b = g.MakeFixed('b')
        self.assertEqual(a,a)
        self.assertTrue(a == a)
        self.assertTrue(a == a2)
        self.assertFalse(a == b)

    def test_SymbolName(self):
        g = _gl("a",_def("a",_sym("a")),_def("b",_sym("b")))
        a = g.MakeSymbolName('a')
        a2 = g.MakeSymbolName('a')
        b = g.MakeSymbolName('b')
        self.assertEqual(a,a)
        self.assertTrue(a == a)
        self.assertTrue(a == a2)
        self.assertFalse(a == b)

    def test_Pattern(self):
        g = _gl("a",_def("a",_pattern("a")),_def("b",_pattern("b")))
        a = g.MakePattern('a')
        a2 = g.MakePattern('a')
        b = g.MakePattern('b')
        self.assertEqual(a,a)
        self.assertTrue(a == a)
        self.assertTrue(a == a2)
        self.assertFalse(a == b)

    def test_Repeat1(self):
        g = _gl("a",_def("a",_pattern("a")),_def("b",_pattern("b")))
        a = g.MakeRepeat1([g.MakePattern('a')])
        a2 = g.MakeRepeat1([g.MakePattern('a')])
        b = g.MakeRepeat1([g.MakePattern('b')])
        self.assertEqual(a,a)
        self.assertTrue(a == a)
        self.assertTrue(a == a2)
        self.assertFalse(a == b)

    def test_Choice(self):
        g = _gl("a",_def("a",_pattern("a")),_def("b",_pattern("b")))
        a = g.MakeChoice([g.MakePattern('a'), g.MakeEmpty()])
        a2 = g.MakeChoice([g.MakePattern('a'), g.MakeEmpty()])
        b = g.MakeChoice([g.MakePattern('a')])
        c = g.MakeChoice([g.MakePattern('a'), g.MakeEndOfText()])
        d = g.MakeChoice([g.MakeFixed('a'), g.MakeEmpty()])
        self.assertEqual(a,a)
        self.assertTrue(a == a)
        self.assertTrue(a == a2)
        self.assertFalse(a == b)
        self.assertFalse(a == c)
        self.assertFalse(a == d)

    def test_Seq(self):
        g = _gl("a",_def("a",_pattern("a")),_def("b",_pattern("b")))
        a = g.MakeSeq([g.MakePattern('a'), g.MakeEmpty()])
        a2 = g.MakeSeq([g.MakePattern('a'), g.MakeEmpty()])
        b = g.MakeSeq([g.MakePattern('a')])
        c = g.MakeSeq([g.MakePattern('a'), g.MakeEndOfText()])
        d = g.MakeSeq([g.MakeFixed('a'), g.MakeEmpty()])
        self.assertEqual(a,a)
        self.assertTrue(a == a)
        self.assertTrue(a == a2)
        self.assertFalse(a == b)
        self.assertFalse(a == c)
        self.assertFalse(a == d)

    def test_CrossProduct(self):
        g = _gl("a",_def("a",_pattern("a")))
        empty = g.MakeEmpty()
        end = g.MakeEndOfText()
        fixed = g.MakeFixed('a')
        symbol = g.MakeSymbolName('a')
        pattern = g.MakePattern('a')
        choice = g.MakeChoice([g.MakePattern('a')])
        repeat1 = g.MakeRepeat1([g.MakePattern('a')])
        seq = g.MakeSeq([g.MakePattern('a')])

        self.assertTrue( empty == empty )
        self.assertFalse( empty == end )
        self.assertFalse( empty == fixed )
        self.assertFalse( empty == symbol )
        self.assertFalse( empty == pattern )
        self.assertFalse( empty == choice )
        self.assertFalse( empty == repeat1 )
        self.assertFalse( empty == seq )

        self.assertFalse( end == empty )
        self.assertTrue( end == end )
        self.assertFalse( end == fixed )
        self.assertFalse( end == symbol )
        self.assertFalse( end == pattern )
        self.assertFalse( end == choice )
        self.assertFalse( end == repeat1 )
        self.assertFalse( end == seq )

        self.assertFalse( fixed == empty )
        self.assertFalse( fixed == end )
        self.assertTrue( fixed == fixed )
        self.assertFalse( fixed == symbol )
        self.assertFalse( fixed == pattern )
        self.assertFalse( fixed == choice )
        self.assertFalse( fixed == repeat1 )
        self.assertFalse( fixed == seq )

        self.assertFalse( symbol == empty )
        self.assertFalse( symbol == end )
        self.assertFalse( symbol == fixed )
        self.assertTrue( symbol == symbol )
        self.assertFalse( symbol == pattern )
        self.assertFalse( symbol == choice )
        self.assertFalse( symbol == repeat1 )
        self.assertFalse( symbol == seq )

        self.assertFalse( pattern == empty )
        self.assertFalse( pattern == end )
        self.assertFalse( pattern == fixed )
        self.assertFalse( pattern == symbol )
        self.assertTrue( pattern == pattern )
        self.assertFalse( pattern == choice )
        self.assertFalse( pattern == repeat1 )
        self.assertFalse( pattern == seq )

        self.assertFalse( choice == empty )
        self.assertFalse( choice == end )
        self.assertFalse( choice == fixed )
        self.assertFalse( choice == symbol )
        self.assertFalse( choice == pattern )
        self.assertTrue( choice == choice )
        self.assertFalse( choice == repeat1 )
        self.assertFalse( choice == seq )

        self.assertFalse( repeat1 == empty )
        self.assertFalse( repeat1 == end )
        self.assertFalse( repeat1 == fixed )
        self.assertFalse( repeat1 == symbol )
        self.assertFalse( repeat1 == pattern )
        self.assertFalse( repeat1 == choice )
        self.assertTrue( repeat1 == repeat1 )
        self.assertFalse( repeat1 == seq )

        self.assertFalse( seq == empty )
        self.assertFalse( seq == end )
        self.assertFalse( seq == fixed )
        self.assertFalse( seq == symbol )
        self.assertFalse( seq == pattern )
        self.assertFalse( seq == choice )
        self.assertFalse( seq == repeat1 )
        self.assertTrue( seq == seq )

    def test_Choice_internal_order(self):
        g = _gl("a",_def("a",_fixed("a")),_def("b",_fixed("b")))
        a1 = g.MakeChoice([g.MakeFixed('a'), g.MakeFixed('b')])
        a2 = g.MakeChoice([g.MakeFixed('b'), g.MakeFixed('a')])
        self.assertTrue(a1 == a2)

    def test_Seq_internal_order(self):
        g = _gl("a",_def("a",_fixed("a")))
        a1 = g.MakeSeq([g.MakeFixed('a'), g.MakeFixed('b')])
        a2 = g.MakeSeq([g.MakeFixed('b'), g.MakeFixed('a')])
        self.assertFalse(a1 == a2)


class Item_is_kernel(unittest.TestCase):

    def test_Item_OfEmpty(self):
        g = _gl("e",_def("e",_empty()))
        it = g.MakeItem("e",g.MakeEmpty(),0)
        self.assertFalse(it.is_kernel())

    def test_Item_OfFixed_Pos0(self):
        g = _gl("e",_def("e",_fixed("a")))
        it = g.MakeItem("e",g.MakeFixed('a'),0)
        self.assertFalse(it.is_kernel())

    def test_Item_OfFixed_Pos1(self):
        g = _gl("e",_def("e",_fixed("a")))
        it = g.MakeItem("e",g.MakeFixed('a'),1)
        self.assertTrue(it.is_kernel())

    def test_Item_OfPattern_Pos0(self):
        g = _gl("e",_def("e",_pattern("a")))
        it = g.MakeItem("e",g.MakePattern('a'),0)
        self.assertFalse(it.is_kernel())

    def test_Item_OfPattern_Pos1(self):
        g = _gl("e",_def("e",_pattern("a")))
        it = g.MakeItem("e",g.MakePattern('a'),1)
        self.assertTrue(it.is_kernel())

    def test_Item_OfSymbol_Pos0(self):
        g = _gl("e",_def("e",_sym("a")),_def("a",_fixed("a")))
        it = g.MakeItem("e",g.MakeSymbolName('a'),0)
        self.assertFalse(it.is_kernel())

    def test_Item_OfSymbol_Pos1(self):
        g = _gl("e",_def("e",_sym("a")),_def("a",_fixed("a")))
        it = g.MakeItem("e",g.MakeSymbolName('a'),1)
        self.assertTrue(it.is_kernel())

    def test_Item_OfSeq_Pos0(self):
        g = _gl("s",_def("s",_fixed("a")))
        it = g.MakeItem("s",g.MakeSeq([g.MakeFixed('a')]),0)
        self.assertFalse(it.is_kernel())

    def test_Item_OfSeq_Pos1(self):
        g = _gl("s",_def("s",_fixed("a")))
        it = g.MakeItem("s",g.MakeSeq([g.MakeFixed('a')]),1)
        self.assertTrue(it.is_kernel())

    def test_Item_OfLanguage_Pos0(self):
        g = _gl("a",_def("a",_fixed("a")))
        it = g.MakeItem(Grammar.LANGUAGE,g.MakeSeq([g.MakeFixed('a'),g.MakeEndOfText()]),0)
        self.assertTrue(it.is_kernel())

    def test_Item_OfLanguage_Pos1(self):
        g = _gl("a",_def("a",_fixed("a")))
        it = g.MakeItem(Grammar.LANGUAGE,g.MakeSeq([g.MakeFixed('a'),g.MakeEndOfText()]),1)
        self.assertTrue(it.is_kernel())

    def test_Item_OfLanguage_Pos2(self):
        g = _gl("a",_def("a",_fixed("a")))
        it = g.MakeItem(Grammar.LANGUAGE,g.MakeSeq([g.MakeFixed('a'),g.MakeEndOfText()]),2)
        self.assertTrue(it.is_kernel())

class ItemSet_Less(unittest.TestCase):

    def setUp(self):
        self.g = Grammar.Grammar.Load(DRAGON_BOOK_EXAMPLE_4_42,'translation_unit')
        self.C = self.g.rules["C"]
        self.c = self.g.rules["c"]
        self.d = self.g.rules["d"]
        self.el = Grammar.LookaheadSet({})

    def iC(self,pos=0):
        return self.g.MakeItem("C",self.C[0],pos)
    def ic(self,pos=0):
        return self.g.MakeItem("c",self.c,0)
    def id(self,pos=0):
        return self.g.MakeItem("d",self.c,0)

    def is_C_0(self,closed=True,la=Grammar.LookaheadSet({})):
        result = Grammar.ItemSet(self.g,{self.iC():la})
        result = result.close(self.g) if closed else result
        return result
    def is_C_1(self,closed=True,la=Grammar.LookaheadSet({})):
        result = Grammar.ItemSet(self.g,{self.iC(1):la})
        result = result.close(self.g) if closed else result
        return result

    def test_Equal(self):
        i0 = self.is_C_0()
        i1 = self.is_C_1()
        self.assertEqual(i0,i0)
        self.assertEqual(i1,i1)
        self.assertFalse(i0==i1)
        self.assertFalse(i1==i0)

    def test_Less(self):
        i0 = self.is_C_0()
        i1 = self.is_C_1()
        # The "dot" character is higher than '
        self.assertLess(i1,i0)
        self.assertGreater(i0,i1)

    def test_Less_Lookahead(self):
        i0c = self.is_C_0(la=Grammar.LookaheadSet({self.c}))
        i0d = self.is_C_0(la=Grammar.LookaheadSet({self.d}))
        self.assertLess(i0c,i0d)
        self.assertGreater(i0d,i0c)

    def test_Equal_Lookahead(self):
        i0c = self.is_C_0(la=Grammar.LookaheadSet({self.c}))
        i0d = self.is_C_0(la=Grammar.LookaheadSet({self.d}))
        self.assertEqual(i0c,i0c)
        self.assertEqual(i0d,i0d)
        self.assertFalse(i0c==i0d)
        self.assertFalse(i0d==i0c)

    def test_Less_Lookahead_Unclosed(self):
        i0c = self.is_C_0(closed=False,la=Grammar.LookaheadSet({self.c}))
        i0d = self.is_C_0(closed=False,la=Grammar.LookaheadSet({self.d}))
        self.assertLess(i0c,i0d)
        self.assertGreater(i0d,i0c)

    def test_Equal_Lookahead_Unclosed(self):
        i0c = self.is_C_0(closed=False,la=Grammar.LookaheadSet({self.c}))
        i0d = self.is_C_0(closed=False,la=Grammar.LookaheadSet({self.d}))
        self.assertEqual(i0c,i0c)
        self.assertEqual(i0d,i0d)
        self.assertFalse(i0c==i0d)
        self.assertFalse(i0d==i0c)

    def test_Less_Lookahead_ClosedFT(self):
        i0c = self.is_C_0(closed=False,la=Grammar.LookaheadSet({self.c}))
        i0d = self.is_C_0(closed=True,la=Grammar.LookaheadSet({self.d}))
        self.assertLess(i0c,i0d)
        self.assertGreater(i0d,i0c)

    def test_Equal_Lookahead_ClosedFT(self):
        i0c = self.is_C_0(closed=False,la=Grammar.LookaheadSet({self.c}))
        i0d = self.is_C_0(closed=True,la=Grammar.LookaheadSet({self.d}))
        self.assertEqual(i0c,i0c)
        self.assertEqual(i0d,i0d)
        self.assertFalse(i0c==i0d)
        self.assertFalse(i0d==i0c)

    def test_Less_Lookahead_ClosedTF(self):
        i0c = self.is_C_0(closed=True,la=Grammar.LookaheadSet({self.c}))
        i0d = self.is_C_0(closed=False,la=Grammar.LookaheadSet({self.d}))
        # We only compare on content, never by the index. So closure
        # doesn't matter here.
        self.assertLess(i0c,i0d)
        self.assertGreater(i0d,i0c)

    def test_Equal_Lookahead_ClosedTF(self):
        i0c = self.is_C_0(closed=True,la=Grammar.LookaheadSet({self.c}))
        i0d = self.is_C_0(closed=False,la=Grammar.LookaheadSet({self.d}))
        self.assertEqual(i0c,i0c)
        self.assertEqual(i0d,i0d)
        self.assertFalse(i0c==i0d)
        self.assertFalse(i0d==i0c)

class ItemSet_is_accepting(unittest.TestCase):

    def setUp(self):
        self.g = Grammar.Grammar.Load(DRAGON_BOOK_EXAMPLE_4_42,'translation_unit')
        self.L = self.g.rules[Grammar.LANGUAGE]
        self.C = self.g.rules["C"]
        self.c = self.g.rules["c"]
        self.d = self.g.rules["d"]
        self.l_empty = Grammar.LookaheadSet({})
        self.l_end = Grammar.LookaheadSet({self.g.MakeEndOfText()})
        self.l_end_and = Grammar.LookaheadSet({self.g.MakeFixed('end'),self.g.MakeEndOfText()})

    def iL(self,pos=0):
        return self.g.MakeItem(Grammar.LANGUAGE,self.L[0],pos)
    def iC(self,pos=0):
        return self.g.MakeItem("C",self.C[0],pos)

    def test_L_empty(self):
        i0 = self.iL()
        i0_ = Grammar.ItemSet(self.g,{i0:self.l_empty}).close(self.g)
        self.assertFalse(i0_.is_accepting())
        i1 = self.iL(1)
        i1_ = Grammar.ItemSet(self.g,{i1:self.l_empty})
        self.assertFalse(i1_.is_accepting())

    def test_L_end_alone(self):
        i0 = self.iL()
        i0_ = Grammar.ItemSet(self.g,{i0:self.l_end}).close(self.g)
        self.assertFalse(i0_.is_accepting())
        i1 = self.iL(1)
        i1_ = Grammar.ItemSet(self.g,{i1:self.l_end})
        self.assertTrue(i1_.is_accepting())

    def test_L_end_and(self):
        i0 = self.iL()
        i0_ = Grammar.ItemSet(self.g,{i0:self.l_end_and}).close(self.g)
        self.assertFalse(i0_.is_accepting())
        i1 = self.iL(1)
        i1_ = Grammar.ItemSet(self.g,{i1:self.l_end_and})
        self.assertTrue(i1_.is_accepting())

    def test_C_empty(self):
        i0 = self.iC()
        i0_ = Grammar.ItemSet(self.g,{i0:self.l_empty}).close(self.g)
        self.assertFalse(i0_.is_accepting())
        i1 = self.iC(1)
        i1_ = Grammar.ItemSet(self.g,{i1:self.l_empty}).close(self.g)
        self.assertFalse(i1_.is_accepting())

    def test_C_end_alone(self):
        i0 = self.iC()
        i0_ = Grammar.ItemSet(self.g,{i0:self.l_end}).close(self.g)
        self.assertFalse(i0_.is_accepting())
        i1 = self.iC(1)
        i1_ = Grammar.ItemSet(self.g,{i1:self.l_end}).close(self.g)
        self.assertFalse(i1_.is_accepting())

    def test_C_end_and(self):
        i0 = self.iC()
        i0_ = Grammar.ItemSet(self.g,{i0:self.l_end_and}).close(self.g)
        self.assertFalse(i0_.is_accepting())
        i1 = self.iC(1)
        i1_ = Grammar.ItemSet(self.g,{i1:self.l_end_and}).close(self.g)
        self.assertFalse(i1_.is_accepting())

class Lookahead_is_a_set(unittest.TestCase):
    def test_init_empty(self):
        x = Grammar.LookaheadSet()
        self.assertTrue(x == set())

    def test_init_single(self):
        x = Grammar.LookaheadSet({1})
        self.assertTrue(x == set({1}))

    def test_init_several(self):
        x = Grammar.LookaheadSet({1,2,9})
        self.assertTrue(x == set({9,2,1}))

    def test_str_empty(self):
        x = Grammar.LookaheadSet({})
        self.assertEqual(str(x),"{}")

    def test_str_several_is_ordered(self):
        x = Grammar.LookaheadSet({9,2,1})
        self.assertEqual(str(x),"{1 2 9}")

class Lookahead_merge(unittest.TestCase):
    def test_merge_empty(self):
        x = Grammar.LookaheadSet({1,2,3})
        b = x.merge(Grammar.LookaheadSet({}))
        self.assertEqual(str(x),"{1 2 3}")
        self.assertFalse(b)

    def test_merge_same(self):
        x = Grammar.LookaheadSet({1,2,3})
        b = x.merge(Grammar.LookaheadSet({1,2,3}))
        self.assertEqual(str(x),"{1 2 3}")
        self.assertFalse(b)

    def test_merge_disjoint(self):
        x = Grammar.LookaheadSet({-1,9,4})
        b = x.merge(Grammar.LookaheadSet({1,2,3}))
        self.assertEqual(str(x),"{-1 1 2 3 4 9}")
        self.assertTrue(b)

    def test_merge_overlap(self):
        x = Grammar.LookaheadSet({1,2,4})
        b = x.merge(Grammar.LookaheadSet({1,2,3}))
        self.assertEqual(str(x),"{1 2 3 4}")
        self.assertTrue(b)


EX442_LR1_ITEMS_CLOSED_EXPECTED = sorted(map(lambda x: x.rstrip(), """#0
language -> · translation_unit EndOfText : {EndOfText}
C -> · 'c' C : {'c' 'd'}
C -> · 'd' : {'c' 'd'}
translation_unit -> · C C : {EndOfText}
===
#1
language -> translation_unit · EndOfText : {EndOfText}
===
#2
translation_unit -> C · C : {EndOfText}
C -> · 'c' C : {EndOfText}
C -> · 'd' : {EndOfText}
===
#3
C -> 'c' · C : {'c' 'd'}
C -> · 'c' C : {'c' 'd'}
C -> · 'd' : {'c' 'd'}
===
#3
C -> 'c' · C : {EndOfText}
C -> · 'c' C : {EndOfText}
C -> · 'd' : {EndOfText}
===
#4
C -> 'd' · : {'c' 'd'}
===
#4
C -> 'd' · : {EndOfText}
===
#5
C -> 'c' C · : {'c' 'd'}
===
#5
C -> 'c' C · : {EndOfText}
===
#6
translation_unit -> C C · : {EndOfText}
""".split("===\n")))

EX442_LALR1_ITEMS_CLOSED_EXPECTED = sorted(map(lambda x: x.rstrip(), """#0
language -> · translation_unit EndOfText : {EndOfText}
C -> · 'c' C : {'c' 'd'}
C -> · 'd' : {'c' 'd'}
translation_unit -> · C C : {EndOfText}
===
#1
language -> translation_unit · EndOfText : {EndOfText}
===
#2
translation_unit -> C · C : {EndOfText}
C -> · 'c' C : {EndOfText}
C -> · 'd' : {EndOfText}
===
#3
C -> 'c' · C : {'c' 'd' EndOfText}
C -> · 'c' C : {'c' 'd' EndOfText}
C -> · 'd' : {'c' 'd' EndOfText}
===
#4
C -> 'd' · : {'c' 'd' EndOfText}
===
#5
C -> 'c' C · : {'c' 'd' EndOfText}
===
#6
translation_unit -> C C · : {EndOfText}
""".split("===\n")))


#   translation_unit -> @ *
STAR_GRAMMAR = """ {
  "name": "firsts",
  "rules": {
    "s": {
      "type": "SEQ",
      "members": [
        {
          "type": "CHOICE",
          "members": [
            {
              "type": "REPEAT1",
              "content": {
                "type": "SYMBOL",
                "name": "at"
              }
            },
            {
              "type": "BLANK"
            }
          ]
        }
      ]
    },
    "at": {
      "type": "TOKEN",
      "content": {
        "type": "STRING",
        "value": "@"
      }
    }
  },
  "extras": [],
  "conflicts": [],
  "precedences": [],
  "externals": [
  ],
  "inline": [
  ],
  "supertypes": []
}
"""
STAR_ITEMS_EXPECTED = sorted(map(lambda x: x.rstrip(), """#0
language -> · s EndOfText : {EndOfText}
at -> · '@' : {'@' EndOfText}
s -> · s/0.0 : {EndOfText}
s/0.0 -> · s/0.0/0 : {EndOfText}
s/0.0/0 -> · at s/0.0/0 : {EndOfText}
===
#1
language -> s · EndOfText : {EndOfText}
===
#2
s -> s/0.0 · : {EndOfText}
===
#3
s/0.0 -> s/0.0/0 · : {EndOfText}
===
#4
s/0.0/0 -> at · s/0.0/0 : {EndOfText}
at -> · '@' : {'@' EndOfText}
s/0.0/0 -> · at s/0.0/0 : {EndOfText}
===
#5
at -> '@' · : {'@' EndOfText}
===
#6
s/0.0/0 -> at s/0.0/0 · : {EndOfText}
""".split("===\n")))

class LR1_items(unittest.TestCase):
    def test_ex442(self):
        g = Grammar.Grammar.Load(DRAGON_BOOK_EXAMPLE_4_42,'translation_unit')
        expected = EX442_LR1_ITEMS_CLOSED_EXPECTED
        got = g.LR1_ItemSets()
        got_str = [str(i) for i in got]
        self.assertEqual(got_str, expected)

class LALR1_items(unittest.TestCase):
    def test_ex442(self):
        g = Grammar.Grammar.Load(DRAGON_BOOK_EXAMPLE_4_42,'translation_unit')
        expected = EX442_LALR1_ITEMS_CLOSED_EXPECTED
        got = g.LALR1_ItemSets()
        got_str = [str(i) for i in got]
        #print("got\n")
        #print("\n===\n".join(got_str))
        #print("end got\n")
        #print("\nexpected\n")
        #print("\n===\n".join(expected))
        #print("end expected\n")
        self.maxDiff = None
        self.assertEqual(got_str, expected)

    def test_star(self):
        g = Grammar.Grammar.Load(STAR_GRAMMAR,'s')
        expected = STAR_ITEMS_EXPECTED
        got = g.LALR1_ItemSets()
        got_str = [str(i) for i in got]
        self.assertEqual(got_str, expected)

SIMPLE_WGSL_ITEM_0_CLOSED = """#0
language -> · translation_unit EndOfText : {EndOfText}
at -> · '@' : {'@' 'fn'}
function_decl -> · function_decl/0.0 function_header brace_left brace_right : {';' '@' 'fn' 'type' EndOfText}
function_decl/0.0 -> · function_decl/0.0/0 : {'fn'}
function_decl/0.0/0 -> · at function_decl/0.0/0 : {'fn'}
global_decl -> · function_decl : {';' '@' 'fn' 'type' EndOfText}
global_decl -> · semicolon : {';' '@' 'fn' 'type' EndOfText}
global_decl -> · type_alias_decl semicolon : {';' '@' 'fn' 'type' EndOfText}
semicolon -> · ';' : {';' '@' 'fn' 'type' EndOfText}
translation_unit -> · translation_unit/0.0 : {EndOfText}
translation_unit/0.0 -> · translation_unit/0.0/0 : {EndOfText}
translation_unit/0.0/0 -> · global_decl translation_unit/0.0/0 : {EndOfText}
type_alias_decl -> · 'type' ident equal ident : {';'}"""

class ItemSet_Close(unittest.TestCase):
    def test_simple_wgsl_close_0(self):
        g = Grammar.Grammar.Load(SIMPLE_WGSL,'translation_unit')
        expected = SIMPLE_WGSL_ITEM_0_CLOSED
        got = g.LALR1_ItemSets()
        self.assertGreater(len(got),0)
        item0_closed = str(got[0])
        self.assertEqual(item0_closed, expected)


EX442_ACTIONS = """[#0 'c']: s#3
[#0 'd']: s#4
[#1 EndOfText]: acc
[#2 'c']: s#3
[#2 'd']: s#4
[#3 'c']: s#3
[#3 'd']: s#4
[#4 'c']: r#0
[#4 'd']: r#0
[#4 EndOfText]: r#0
[#5 'c']: r#1
[#5 'd']: r#1
[#5 EndOfText]: r#1
[#6 EndOfText]: r#2
"""

class LALR1_actions(unittest.TestCase):
    def test_ex442(self):
        g = Grammar.Grammar.Load(DRAGON_BOOK_EXAMPLE_4_42,'translation_unit')
        expected = EX442_ACTIONS
        parse_table = g.LALR1()
        got = "".join(parse_table.action_parts())
        #print("got actions\n"+got+"end got\n")
        #print("expected actions\n"+expected+"end expected\n")
        self.assertEqual(got, expected)

EX442_GOTOS = """[#0 C]: #2
[#0 translation_unit]: #1
[#2 C]: #6
[#3 C]: #5
"""

class LALR1_gotos(unittest.TestCase):
    def test_ex442(self):
        g = Grammar.Grammar.Load(DRAGON_BOOK_EXAMPLE_4_42,'translation_unit')
        expected = EX442_GOTOS
        parse_table = g.LALR1()
        got = "".join(parse_table.goto_parts())
        self.assertEqual(got, expected)

class Grammar_registers_objects(unittest.TestCase):
    def test_star(self):
        g = Grammar.Grammar.Load(STAR_GRAMMAR,'s')
        at = g.find('at')
        self.assertEqual(at.reg_info.registry, g.registry)
        self.assertEqual(at.reg_info.obj, at)
        self.assertEqual(at.reg_info.index, 2)

# Example 4.21
class DragonBook_4_21(unittest.TestCase):
    def toy_grammar(self):
        # Grammar 4.21 in Example 4.42 with table shown example 4.43
        """
        language = S
        S = C C
        C = 'c' C | 'd'
        """
        # Tokens
        c = _fixed("c")
        d = _fixed("d")

        S = _sym("S")
        C = _sym("C")

        SDef = _def("S", _seq(C,C))
        CDef = _def("C", _choice(_seq(c,C),d))
        g = _gl("S", SDef, CDef)
        return g

    def test_first(self):
        g = self.toy_grammar()
        Sfirst = Grammar.LookaheadSet(g.find("S").first())
        self.assertEqual(str(Sfirst),"{'c' 'd'}")
        Cfirst = Grammar.LookaheadSet(g.find("C").first())
        self.assertEqual(str(Cfirst),"{'c' 'd'}")

    def test_follow(self):
        g = self.toy_grammar()
        Sfollow = Grammar.LookaheadSet(g.find("S").follow)
        self.assertEqual(str(Sfollow),"{EndOfText}")
        Cfollow = Grammar.LookaheadSet(g.find("C").follow)
        self.assertEqual(str(Cfollow),"{'c' 'd' EndOfText}")

# Example 4.34
class DragonBook_4_34(unittest.TestCase):
    def toy_grammar(self):
        # Grammar 4.19 in example 4.34
        # Canonical LR(0) collections are in Fig 4.35
        """
        language = E
        E = E '+' T | T
        T = T '*' F | F
        F = '(' E ')' | 'id'
        """

        # Tokens

        Id = _fixed("id")
        E = _sym("E")
        T = _sym("T")
        F = _sym("F")
        LParen = _sym("LParen")
        RParen = _sym("RParen")
        Plus = _sym("Plus")
        Times = _sym("Times")

        LParenDef = _def("LParen",_fixed("("))
        RParenDef = _def("RParen",_fixed(")"))
        PlusDef = _def("Plus",_fixed("+"))
        TimesDef = _def("Times",_fixed("*"))
        EDef = _def("E", _choice(_seq(E,Plus,T),T))
        TDef = _def("T", _choice(_seq(T,Times,F),F))
        FDef = _def("F", _choice(_seq(LParen,E,RParen),Id))
        g = _gl("E", EDef,TDef,FDef,LParenDef,RParenDef,PlusDef,TimesDef)
        return g

    def toy_grammar_inline_fixed(self):
        # Like toy_grammar, but fixed tokens are inlined.
        """
        language = E
        E = E '+' T | T
        T = T '*' F | F
        F = '(' E ')' | 'id'
        """

        # Tokens

        Id = _fixed("id")
        E = _sym("E")
        T = _sym("T")
        F = _sym("F")

        LParen = _fixed("(")
        RParen = _fixed(")")
        Plus = _fixed("+")
        Times = _fixed("*")
        EDef = _def("E", _choice(_seq(E,Plus,T),T))
        TDef = _def("T", _choice(_seq(T,Times,F),F))
        FDef = _def("F", _choice(_seq(LParen,E,RParen),Id))
        g = _gl("E", EDef,TDef,FDef)
        return g

    def dont_test_dump(self):
        g = self.toy_grammar()
        g.dump()
        g = self.toy_grammar_inline_fixed()
        g.dump()
        print(file=sys.stdout,flush=True)

    def test_first(self):
        g = self.toy_grammar()

        self.assertEqual(first_str(g,"E"),"{'(' 'id'}")
        self.assertEqual(first_str(g,"T"),"{'(' 'id'}")
        self.assertEqual(first_str(g,"F"),"{'(' 'id'}")

    def test_follow(self):
        g = self.toy_grammar()

        self.assertEqual(follow_str(g,"E"),"{')' '+' EndOfText}")
        self.assertEqual(follow_str(g,"T"),"{')' '*' '+' EndOfText}")
        self.assertEqual(follow_str(g,"F"),"{')' '*' '+' EndOfText}")

    def test_flat_first(self):
        g = self.toy_grammar_inline_fixed()

        self.assertEqual(first_str(g,"E"),"{'(' 'id'}")
        self.assertEqual(first_str(g,"T"),"{'(' 'id'}")
        self.assertEqual(first_str(g,"F"),"{'(' 'id'}")

    def test_flat_follow(self):
        g = self.toy_grammar_inline_fixed()

        self.assertEqual(follow_str(g,"E"),"{')' '+' EndOfText}")
        self.assertEqual(follow_str(g,"T"),"{')' '*' '+' EndOfText}")
        self.assertEqual(follow_str(g,"F"),"{')' '*' '+' EndOfText}")

class RhsIsJustSymbol(unittest.TestCase):
    # Check first and follow set computation when there is a rule like:
    #    A -> B
    # where B is a nonterminal.
    # For example, the Follow set for A propagates into B.
    def toy_grammar(self,E_as_seq):
        # A simplified switch-case grammar
        """
        language = S
        S = '{' Case '}'
        Case = E ':'
        E = R
        R = Id '<' Id
        """

        # Tokens

        Id = _fixed("id")
        Less = _fixed("<")
        Colon = _fixed(":")
        LBrace = _fixed("{")
        RBrace = _fixed("}")

        S = _sym("S")
        Case = _sym("Case")
        E = _sym("E")
        R = _sym("R")

        SDef = _def("S",_seq(LBrace,Case,RBrace))
        CaseDef = _def("Case",_seq(E,Colon))
        if E_as_seq:
            EDef = _def("E",_seq(R))
        else:
            EDef = _def("E",R)
        RDef = _def("R",_seq(Id,Less,Id))
        g = _gl("S", SDef,CaseDef,EDef,RDef)
        return g

    def xtest_dump(self):
        g = self.toy_grammar(True)
        g.dump()
        g = self.toy_grammar(False)
        g.dump()
        print(file=sys.stdout,flush=True)

    def test_first(self):
        g = self.toy_grammar(True)
        self.assertEqual(first_str(g,"S"),"{'{'}")
        self.assertEqual(first_str(g,"Case"),"{'id'}")
        self.assertEqual(first_str(g,"E"),"{'id'}")
        self.assertEqual(first_str(g,"R"),"{'id'}")
        g = self.toy_grammar(False)
        self.assertEqual(first_str(g,"S"),"{'{'}")
        self.assertEqual(first_str(g,"Case"),"{'id'}")
        self.assertEqual(first_str(g,"E"),"{'id'}")
        self.assertEqual(first_str(g,"R"),"{'id'}")

    def test_follow(self):
        g = self.toy_grammar(True)
        self.assertEqual(follow_str(g,"S"),"{EndOfText}")
        self.assertEqual(follow_str(g,"Case"),"{'}'}")
        self.assertEqual(follow_str(g,"E"),"{':'}")
        self.assertEqual(follow_str(g,"R"),"{':'}")
        g = self.toy_grammar(False)
        self.assertEqual(follow_str(g,"S"),"{EndOfText}")
        self.assertEqual(follow_str(g,"Case"),"{'}'}")
        self.assertEqual(follow_str(g,"E"),"{':'}")
        self.assertEqual(follow_str(g,"R"),"{':'}")

class RhsIsChoiceWithASymbolAlternative(unittest.TestCase):
    # Check first and follow set computation when there is a rule like:
    #    A -> B | 'finite'
    # where B is a nonterminal.
    # For example, the Follow set for A propagates into B.
    def toy_grammar(self,choice_over_sequence):
        """
        language = S
        S = '{' Case '}'
        Case = CaseSelector ':'
        CaseSelector = E | 'default'
        E = R
        R = Id '<' Id
        """

        # Tokens

        Id = _fixed("id")
        Default = _fixed("default")
        Less = _fixed("<")
        Colon = _fixed(":")
        LBrace = _fixed("{")
        RBrace = _fixed("}")

        S = _sym("S")
        Case = _sym("Case")
        CaseSelector = _sym("CaseSelector")
        E = _sym("E")
        R = _sym("R")

        SDef = _def("S",_seq(LBrace,Case,RBrace))
        CaseDef = _def("Case",_seq(CaseSelector,Colon))
        if choice_over_sequence:
            CaseSelectorDef = _def("CaseSelector",_choice(_seq(E),_seq(Default)))
        else:
            CaseSelectorDef = _def("CaseSelector",_choice(E,Default))
        EDef = _def("E",_seq(R))
        RDef = _def("R",_seq(Id,Less,Id))
        g = _gl("S", SDef,CaseDef,CaseSelectorDef,EDef,RDef)
        return g

    def xtest_dump(self):
        g = self.toy_grammar(False)
        g.dump()
        g = self.toy_grammar(True)
        g.dump()
        print(file=sys.stdout,flush=True)

    def test_first(self):
        g = self.toy_grammar(False)
        self.assertEqual(first_str(g,"S"),"{'{'}")
        self.assertEqual(first_str(g,"Case"),"{'default' 'id'}")
        self.assertEqual(first_str(g,"CaseSelector"),"{'default' 'id'}")
        self.assertEqual(first_str(g,"E"),"{'id'}")
        self.assertEqual(first_str(g,"R"),"{'id'}")
        g = self.toy_grammar(True)
        self.assertEqual(first_str(g,"S"),"{'{'}")
        self.assertEqual(first_str(g,"Case"),"{'default' 'id'}")
        self.assertEqual(first_str(g,"CaseSelector"),"{'default' 'id'}")
        self.assertEqual(first_str(g,"E"),"{'id'}")
        self.assertEqual(first_str(g,"R"),"{'id'}")

    def test_follow(self):
        g = self.toy_grammar(False)
        self.assertEqual(follow_str(g,"S"),"{EndOfText}")
        self.assertEqual(follow_str(g,"Case"),"{'}'}")
        self.assertEqual(follow_str(g,"E"),"{':'}")
        self.assertEqual(follow_str(g,"R"),"{':'}")
        g = self.toy_grammar(True)
        self.assertEqual(follow_str(g,"S"),"{EndOfText}")
        self.assertEqual(follow_str(g,"Case"),"{'}'}")
        self.assertEqual(follow_str(g,"E"),"{':'}")
        self.assertEqual(follow_str(g,"R"),"{':'}")

if __name__ == '__main__':
    unittest.main()
