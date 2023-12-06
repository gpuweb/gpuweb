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

"""
A TSPath is a declarative way to describe one or more nodes in a
Treesitter parse tree.  It is inspired by W3C's XPath.

Examples:

    /translation_unit 
        The translation_unit node at the top of the tree

    //enable_directive
        The nodes for enable directives, appearing somewhere
        in the tree, not necessarily at the root.

    //assignment_statement/lhs_expression
        The list of lhs_expression nodes that are immediate children of
        an assignment_statement.

    //assignment_statement/(lhs_expression expression)
        The list of lhs_expression and expression nodes that siblings, and both
        of which are children of an assignment, where the assignment appears
        anywhere.

    //assignment_statement[1]
        The second child of an assignment, where the assignment appears anywhere.

    //assignment_statement/(0 2)
        The first and third children of an assignment
"""

import re
import tree_sitter
import unittest

class ExprNodeKind:
    """Define some named constants"""
    def __init__(self):
        self.root = 'Root'
        self.descendant = 'Descendant'
        self.child = 'Child'
        self.named = 'Named'
        self.indexed_child = 'IndexedChild'
        self.indexed = 'Indexed'
        self.seq = 'Seq'
        self.ok = 'Ok'

ENKind = ExprNodeKind()

class ExprNode:
    """
    An ExprNode is a parsed TSPath.
    It can be matched against a Treesitter node, yielding a list of
    nodes that match the expression.
    """
    def __init__(self,kind,param=None):
        self.kind = kind

    def match(self,ts_node):
        """
        Returns the list of treesitter nodes in ts_node matching the expression.
        """
        raise Exception("unimplemented expr match")

    def __str__(self):
        raise Exception("unimplemented __str__")

class RootNode(ExprNode):
    """An ExprNode matching an expression at the root of the tree"""
    def __init__(self,subexpr):
        super().__init__(ENKind.root)
        self.expr = subexpr

    def match(self,ts_node):
        return self.expr.match(ts_node)

    def __str__(self):
        return "{}( {} )".format(self.kind,str(self.expr))

class DescendantNode(ExprNode):
    """An ExprNode that matches against any descendant of a node"""
    def __init__(self,subexpr):
        super().__init__(ENKind.descendant)
        self.expr = subexpr

    def match(self,ts_node):
        result = []
        # Stack of treesitter nodes to explore
        stack = list(reversed(ts_node.children))
        while len(stack) > 0:
            top = stack.pop()
            top_result = self.expr.match(top)
            if len(top_result) == 0:
                # Explore children instead
                stack.extend(list(reversed(top.children)))
            else:
                result.extend(top_result)
        return result

    def __str__(self):
        return "{}( {} )".format(self.kind,str(self.expr))

class ChildNode(ExprNode):
    """An ExprNode matching against immediate children of a node"""
    def __init__(self,subexpr):
        super().__init__(ENKind.child)
        self.expr = subexpr

    def match(self,ts_node):
        result = []
        for c in ts_node.children:
            result.extend(self.expr.match(c))
        return result

    def __str__(self):
        return "{}( {} )".format(self.kind,str(self.expr))

class NamedNode(ExprNode):
    """An ExprNode matching a node for given grammar rule (Treesitter "type")"""
    def __init__(self,name,subexpr):
        super().__init__(ENKind.named)
        self.name = name
        self.expr = subexpr

    def match(self,ts_node):
        if ts_node.type == self.name:
            result = self.expr.match(ts_node)
            return result
        else:
            return []

    def __str__(self):
        return "{}'{}'( {} )".format(self.kind,self.name,str(self.expr))

class IndexedChildNode(ExprNode):
    """An ExprNode matching an indexed child of a node"""
    def __init__(self,index,subexpr):
        super().__init__(ENKind.indexed_child)
        self.index = index
        self.expr = subexpr

    def match(self,ts_node):
        return ts_node.children[self.index:self.index+1]

    def __str__(self):
        return "{}[{}]( {} )".format(self.kind,self.index,str(self.expr))

class IndexedNode(ExprNode):
    """An ExprNode for an node that must be in a specific position in its parent"""
    def __init__(self,index,subexpr):
        super().__init__(ENKind.indexed)
        self.index = index
        self.expr = subexpr

    def match(self,ts_node):
        raise Exception("not implemented here!")

    def __str__(self):
        return "{}({})( {} )".format(self.kind,self.index,str(self.expr))

class SeqNode(ExprNode):
    """
    An ExprNode matching a sequence of expressions against a subsequence of children of a node.
    The matched children must be in order, but may have gaps between.
    """
    def __init__(self,children):
        super().__init__(ENKind.seq)
        self.exprs = children
    
    def match(self,ts_node):
        result = []
        # Walk through both lists
        iexpr = 0
        inode = -1
        for node in ts_node.children:
            inode += 1
            if iexpr == len(self.exprs):
                break
            subexpr = self.exprs[iexpr]
            if isinstance(subexpr,IndexedNode):
                # The node can only match a particular node, by position.
                if subexpr.index < inode:
                    # It's too late.
                    # Missed the match. Invalidate all results.
                    return []
                if subexpr.index > inode:
                    # It's too early.
                    # Wait for the node to come up.
                    continue
                # Just right. Check the subexpression.
                here_result = subexpr.expr.match(node)
            else:
                here_result = subexpr.match(node)
            if len(here_result) > 0:
                # We matched the current subexpr to this node.
                iexpr += 1
                result.extend(here_result)
        if iexpr == len(self.exprs):
            # We've matched all expressions
            return result
        # Missed matching something
        return []

    def __str__(self):
        return "{}[{}]".format(self.kind," ".join([str(x) for x in self.exprs]))

class OkNode(ExprNode):
    """An ExprNode matching any node"""
    def __init__(self):
        super().__init__(ENKind.ok)

    def match(self,ts_node):
        return [ts_node]

    def __str__(self):
        return "{}".format(self.kind)


class TSPath:
    """
    A TSPath is an expression for matching parts of a Treesitter tree.
    Inspired by W3C XPath

    In the following, things like $X denote a generic TSPath, and $k denotes
    an integer literal.

        Expression: /$Y
        Result:     The root node matches $Y

        Expression: //$Y
        Result:     The node matching $Y, anywhere in the tree.

        Expression: $X//$Y
        Result:     The node matching $Y, as a descendent of nodes matching $X.

        Expression: $X/$Y
        Result:     Nodes matching $Y as a child of a node matching expression $X.

        Expression: $X[$k]
        Result:     Where $k is a non-negative integer:
                    The node that is the $k'th child of a node matching $X.

        Expression: $A($B $C $D)
        Result:     Nodes matching $B, then $C, then $D as children of nodes matching $A

        Expression: $A($B $j $k)
        Result:     Nodes matching $B, then the j'th and k'th nodes that are children of $A
    """
    def __init__(self,path):
        self.path = path
        self.expr = self.parse_from_root(path)

    def __str__(self):
        return "TSPath({} {})".format(self.path,str(self.expr))

    def match(self,parsed_tree):
        """
        Returns the list of nodes from the given tree that match this XPath.
        """
        return self.expr.match(parsed_tree.root_node)

    def parse_from_root(self,path):
        """
        Returns a parsed XPath, as an ExprNode, with a heuristic default
        when the path does not begin with '/'.
        """
        if path.startswith('/'):
            return RootNode(self.parse(path))
        else:
            # Implicitly use '//', so that 'foo' is implicitly '//foo'
            return RootNode(DescendantNode(self.parse(path)))

    def parse(self,path):
        """Returns a parsed XPath, as an ExprNode"""
        path = path.strip()

        # Bottom out recursion
        if path == '':
            return OkNode()

        # Descendant
        m = re.fullmatch('//(.*)',path)
        if m:
            child = self.parse(m.group(1))
            if isinstance(child,DescendantNode):
                return child
            return DescendantNode(child)

        # Child
        m = re.fullmatch('/(.*)',path)
        if m:
            return ChildNode(self.parse(m.group(1)))

        # Indexed
        # These are only valid inside parens.
        m = re.fullmatch('(\d+)(.*)',path)
        if m:
            return IndexedNode(int(m.group(1)),self.parse(m.group(2)))

        # IndexedChild
        m = re.fullmatch('\[(\d+)\](.*)',path)
        if m:
            return IndexedChildNode(int(m.group(1)),self.parse(m.group(2)))

        # Named
        m = re.fullmatch('(\w+)(.*)',path)
        if m:
            return NamedNode(m.group(1),self.parse(m.group(2)))

        # Parenthesized sequence.
        # If we see
        #    (abc [1])/$X
        # Then parse it as a sequence of:
        #     abc/$X     [1]/$X
        if path.startswith('('):
            (depth,path_parts,rest) = (0,[],None)
            for i in range(0,len(path)):
                if path[i] == '(':
                    depth += 1
                    if depth == 1:
                        part_start = i+1
                elif (path[i] == ' ') and (depth == 1):
                    if i == part_start:
                        # Skip successive spaces
                        part_start = i+1
                    else:
                        # Parse the term we just finished seeing.
                        path_parts.append(path[part_start:i])
                        part_start = i+1
                elif path[i] == ')':
                    depth -= 1
                    if depth == 0:
                        last = i
                        if i == part_start:
                            # Skip trailing spaces
                            pass
                        else:
                            path_parts.append(path[part_start:i])
                        rest = path[i+1:]
                        break
            if rest is None:
                raise Exception("unbalanced parentheses: {}".format(path))
            if len(path_parts) < 1:
                raise Exception("missing terms: {}".format(path[0:last+1]))
            return SeqNode([self.parse(p+rest) for p in path_parts])

        raise Exception("unrecognized subpath: '{}'".format(path))

class TestTSPathParse(unittest.TestCase):
    def test_parse_from_root_heuristic(self):
        self.assertEqual(str(TSPath('abc')),"TSPath(abc Root( Descendant( Named'abc'( Ok ) ) ))")
        self.assertEqual(str(TSPath('/abc')),"TSPath(/abc Root( Child( Named'abc'( Ok ) ) ))")
        self.assertEqual(str(TSPath('//abc')),"TSPath(//abc Root( Descendant( Named'abc'( Ok ) ) ))")

    def test_empty(self):
        self.assertEqual(str(TSPath('')),"TSPath( Root( Descendant( Ok ) ))")
        self.assertEqual(str(TSPath('/')),"TSPath(/ Root( Child( Ok ) ))")

    def test_descendant(self):
        self.assertEqual(str(TSPath('//abc//def')),"TSPath(//abc//def Root( Descendant( Named'abc'( Descendant( Named'def'( Ok ) ) ) ) ))")
        # Adjacent descendants collapse.
        self.assertEqual(str(TSPath('//abc////def')),"TSPath(//abc////def Root( Descendant( Named'abc'( Descendant( Named'def'( Ok ) ) ) ) ))")
        self.assertEqual(str(TSPath('//abc//////def')),"TSPath(//abc//////def Root( Descendant( Named'abc'( Descendant( Named'def'( Ok ) ) ) ) ))")

    def test_child(self):
        self.assertEqual(str(TSPath('/abc/def')),"TSPath(/abc/def Root( Child( Named'abc'( Child( Named'def'( Ok ) ) ) ) ))")

    def test_indexed(self):
        self.assertEqual(str(TSPath('/1')),"TSPath(/1 Root( Child( Indexed(1)( Ok ) ) ))")

    def test_indexed_child(self):
        self.assertEqual(str(TSPath('/[1][2]')),"TSPath(/[1][2] Root( Child( IndexedChild[1]( IndexedChild[2]( Ok ) ) ) ))")

    def test_paren(self):
        self.assertEqual(str(TSPath('/(a b c)')),"TSPath(/(a b c) Root( Child( Seq[Named'a'( Ok ) Named'b'( Ok ) Named'c'( Ok )] ) ))")

    def test_paren_indexed(self):
        self.assertEqual(str(TSPath('/(a 1 c)')),"TSPath(/(a 1 c) Root( Child( Seq[Named'a'( Ok ) Indexed(1)( Ok ) Named'c'( Ok )] ) ))")

    def test_paren_extra_spaces(self):
        self.assertEqual(str(TSPath('/(  a b  c )')),"TSPath(/(  a b  c ) Root( Child( Seq[Named'a'( Ok ) Named'b'( Ok ) Named'c'( Ok )] ) ))")

    def test_paren_nesting(self):
        self.assertEqual(str(TSPath('/((a) b (c))')),"TSPath(/((a) b (c)) Root( Child( Seq[Seq[Named'a'( Ok )] Named'b'( Ok ) Seq[Named'c'( Ok )]] ) ))")

    def test_indexed_with_child(self):
        self.assertEqual(str(TSPath('/1/a')),"TSPath(/1/a Root( Child( Indexed(1)( Child( Named'a'( Ok ) ) ) ) ))")

if __name__ == '__main__':
    unittest.main()
