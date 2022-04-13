#!/usr/bin/env python3

from datetime import date
from string import Template

import os
import re
import subprocess
import sys

from tree_sitter import Language, Parser

HEADER = """
// Copyright (C) [$YEAR] World Wide Web Consortium,
// (Massachusetts Institute of Technology, European Research Consortium for
// Informatics and Mathematics, Keio University, Beihang).
// All Rights Reserved.
//
// This work is distributed under the W3C (R) Software License [1] in the hope
// that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
//
// [1] http://www.w3.org/Consortium/Legal/copyright-software

// **** This file is auto-generated. Do not edit. ****

""".lstrip()

scanner_filename = sys.argv[1]
scanner_file = open(scanner_filename, "r")
# Break up the input into lines, and skip empty lines.
scanner_lines = [j for i in [i.split("\n")
                             for i in scanner_file.readlines()] for j in i if len(j) > 0]
# Replace comments in rule text
scanner_lines = [re.sub('<!--.*-->', '', line) for line in scanner_lines]

grammar_filename = sys.argv[2]
grammar_path = os.path.dirname(grammar_filename)
os.makedirs(grammar_path, exist_ok=True)
grammar_file = open(grammar_filename, "w")


def scanner_escape_name(name):
    return name.strip().replace("`", "").replace('-', '_').lower().strip()


def scanner_escape_regex(regex):
    return re.escape(regex.strip()).strip().replace("/", "\\/").replace("\\_", "_").replace("\\%", "%").replace("\\;", ";").replace("\\<", "<").replace("\\>", ">").replace("\\=", "=").replace("\\,", ",").replace("\\:", ":").replace("\\!", "!")


# Global variable holding the current line text.
line = ""

"""
Scanner classes are used to parse contiguous sets of lines in the WGSL bikeshed
source text.
"""
class Scanner:

    @staticmethod
    def name():
        return "my scanner name"

    """
    Each of the methods below also sets the 'line' global variable with
    the i'th line, but after stripping trailing line-comments and trailing
    spaces.
    """

    """ Returns True if this scanner should be used starting at the i'th line."""
    @staticmethod
    def begin(lines, i):
        line = lines[i].rstrip()
        return False

    """ Returns True if this scanner stop being used at the i'th line."""
    @staticmethod
    def end(lines, i):
        line = lines[i].rstrip()
        return False

    """ Returns True if this scanner should start trying to parse the text starting after the i'th line."""
    @staticmethod
    def record(lines, i):
        line = lines[i].rstrip()
        return False

    """ Returns True if this scanner stop start trying to parse the text starting after the i'th line."""
    @staticmethod
    def skip(lines, i):
        line = lines[i].rstrip()
        return False

    """ Returns True if this scanner should try to parse this line. Only called when "recording" """
    @staticmethod
    def valid(lines, i):
        line = lines[i].rstrip()
        return False

    """ Returns a triple resulting from parsing the line.
      First element:  rule name, if it's a rule
      Second element:  parsed content
         For  rule, this is the list of terminals and non-terminals on the right hand side
         of the rule.
      Third element:
         0 if it's the first line of a rule (or the whole rule),
           or if this just a line of text from the example.
         -1 if it's a continuation of the previous rule.
    """
    @staticmethod
    def parse(lines, i):
        line = lines[i].rstrip()
        return False


class scanner_rule(Scanner):
    @staticmethod
    def name():
        return "rule"

    """ Returns true if this scanner should be used starting at the i'th line """
    @staticmethod
    def begin(lines, i):
        line = lines[i].rstrip()
        return (line.startswith("<div class='syntax"), None, 1)

    @staticmethod
    def end(lines, i):
        line = lines[i].rstrip()
        return (line.startswith("</div>"), 0)

    @staticmethod
    def record(lines, i):
        line = lines[i].rstrip()
        return (True, 0)

    @staticmethod
    def skip(lines, i):
        line = lines[i].rstrip()
        return (False, 0)

    @staticmethod
    def valid(lines, i):
        line = lines[i].rstrip()
        return len(line.strip()) > 0

    @staticmethod
    def parse(lines, i):
        # Exclude code point comments
        # Supports both "Code point" and "Code points"
        line = lines[i].split("(Code point")[0].rstrip()
        if line[2:].startswith("<dfn for=syntax>"):
            # When the line is
            #    <dfn for=syntax>access_mode</dfn>
            # returns ('access_mode',None,0)
            rule_name = line[2:].split("<dfn for=syntax>")[1]
            rule_name = rule_name.split("</dfn>")[0].strip()
            return (rule_name, None, 0)
        elif line[4:].startswith("| "):
            # When the line is
            #    | [=syntax/variable_decl=] [=syntax/equal=] [=syntax/expression=]
            # returns (None, ['[=syntax/variable_decl=]','[=syntax/equal=]','[=syntax/expression=]',0)
            rule_value = line[6:]
            return (None, rule_value.split(" "), 0)
        elif line[4:].startswith("  "):
            # For production rule continuation.
            # When the line is
            #      [=syntax/variable_decl=] [=syntax/equal=] [=syntax/expression=]
            # returns (None, ['[=syntax/variable_decl=]','[=syntax/equal=]','[=syntax/expression=]',-1)
            rule_value = line[6:]
            return (None, rule_value.split(" "), -1)
        return (None, None, None)


class scanner_example(Scanner):  # Not an example of a scanner, scanner of examples from specification
    @staticmethod
    def name():
        return "example"

    """
     Returns true if this scanner should be used starting at the i'th line
    """
    @staticmethod
    def begin(lines, i):
        line = lines[i].split("//")[0].rstrip()
        result = "<div class=" in line and "example" in line and "wgsl" in line
        key = None
        if result:
            key = line[5:-1]
        return (result, key, 1)

    @staticmethod
    def end(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</div>" in line, 0)

    @staticmethod
    def record(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("<xmp" in line, 1)

    @staticmethod
    def skip(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</xmp>" in line, 0)

    @staticmethod
    def valid(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return True

    @staticmethod
    def parse(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return (None, line, 0)


scanner_spans = [scanner_rule,
                 scanner_example]


scanner_components = {i.name(): {} for i in scanner_spans}

scanner_i = 0 # line number of the current line
scanner_span = None
scanner_record = False
last_key = None   # The rule name, if the most recently parsed thing was a rule.
last_value = None # The most recently parsed thing
while scanner_i < len(scanner_lines):
    # Try both the rule and the example scanners.
    for j in scanner_spans:
        scanner_begin = j.begin(scanner_lines, scanner_i)
        if scanner_begin[0]:
            # Use this scanner
            scanner_span = None
            scanner_record = False
            last_key = None
            last_value = None
            scanner_span = j
            if scanner_begin[1] != None:
                last_key = scanner_begin[1]
            scanner_i += scanner_begin[-1]
        if scanner_span == j:
            # Check if we should stop using this scanner.
            scanner_end = j.end(scanner_lines, scanner_i)
            if scanner_end[0]:
                # Yes, stop using this scanner.
                scanner_span = None
                scanner_record = False
                last_key = None
                last_value = None
                scanner_i += scanner_end[-1]
    if scanner_span != None:
        # We're are in the middle of scanning a span of lines.
        if scanner_record:
            scanner_skip = scanner_span.skip(scanner_lines, scanner_i)
            if scanner_skip[0]:
                # Stop recording
                scanner_record = False
                scanner_i += scanner_skip[-1]  # Advance past this line
        else:
            # Should we start recording?
            scanner_record_value = scanner_span.record(
                scanner_lines, scanner_i)
            if scanner_record_value[0]:
                # Start recording
                scanner_record = True
                if last_key != None and scanner_span.name() == "example":  # TODO Remove special case
                    if last_key in scanner_components[scanner_span.name()]:
                        raise RuntimeError("line " + str(scanner_i) + ": example with duplicate name: " + last_key)
                    else:
                        scanner_components[scanner_span.name()][last_key] = []
                scanner_i += scanner_record_value[-1]
        if scanner_record and scanner_span.valid(scanner_lines, scanner_i):
            # Try parsing this line
            scanner_parse = scanner_span.parse(scanner_lines, scanner_i)
            if scanner_parse[2] < 0:
                # This line continues the rule parsed on the immediately preceding lines.
                if (scanner_parse[1] != None and
                        last_key != None and
                        last_value != None and
                        last_key in scanner_components[scanner_span.name()] and
                        len(scanner_components[scanner_span.name()][last_key]) > 0):
                    scanner_components[scanner_span.name(
                    )][last_key][-1] += scanner_parse[1]
            else:
                if scanner_parse[0] != None:
                    # It's a rule, with name in the 0'th position.
                    last_key = scanner_parse[0]
                    if scanner_parse[1] != None:
                        last_value = scanner_parse[1]
                        if last_key not in scanner_components[scanner_span.name()]:
                            # Create a new entry for this rule
                            scanner_components[scanner_span.name()][last_key] = [
                                last_value]
                        else:
                            # Append to the existing entry.
                            scanner_components[scanner_span.name()][last_key].append(
                                last_value)
                    else:
                        # Reset
                        last_value = None
                        scanner_components[scanner_span.name()][last_key] = []
                else:
                    # It's example text
                    if scanner_parse[1] != None:
                        last_value = scanner_parse[1]
                        scanner_components[scanner_span.name()][last_key].append(
                            last_value)
                scanner_i += scanner_parse[-1] # Advance line index
    scanner_i += 1


grammar_source = ""

grammar_source += r"""
module.exports = grammar({
    name: 'wgsl',

    externals: $ => [
        $._block_comment,
    ],

    extras: $ => [
        $._comment,
        $._block_comment,
        $._blankspace,
    ],

    inline: $ => [
        $.global_decl,
        $._reserved,
    ],

    // WGSL has no parsing conflicts.
    conflicts: $ => [],

    word: $ => $.ident,

    rules: {
"""[1:-1]
grammar_source += "\n"


def grammar_from_rule_item(rule_item):
    result = ""
    item_choice = False
    items = []
    i = 0
    while i < len(rule_item):
        i_optional = False
        i_repeatone = False
        i_skip = 0
        i_item = ""
        if rule_item[i].startswith("[=syntax/"):
            i_item = rule_item[i].split("[=syntax/")[1].split("=]")[0]
            i_item = f"$.{i_item}"
        elif rule_item[i].startswith("`/"):
            i_item = f"token({rule_item[i][1:-1]})"
        elif rule_item[i].startswith("`'"):
            i_item = f"token({rule_item[i][1:-1]})"
        elif rule_item[i] == "(":
            j = i + 1
            j_span = 0
            rule_subitem = []
            while j < len(rule_item):
                if rule_item[j] == "(":
                    j_span += 1
                elif rule_item[j] == ")":
                    j_span -= 1
                rule_subitem.append(rule_item[j])
                j += 1
                if rule_item[j] == ")" and j_span == 0:
                    break
            i_item = grammar_from_rule_item(rule_subitem)
            i = j
        if len(rule_item) - i > 1:
            if rule_item[i + 1] == "+":
                i_repeatone = True
                i_skip += 1
            elif rule_item[i + 1] == "?":
                i_optional = True
                i_skip += 1
            elif rule_item[i + 1] == "*":
                i_repeatone = True
                i_optional = True
                i_skip += 1
            elif rule_item[i + 1] == "|":
                item_choice = True
                i_skip += 1
        if i_repeatone:
            i_item = f"repeat1({i_item})"
        if i_optional:
            i_item = f"optional({i_item})"
        items.append(i_item)
        i += 1 + i_skip
    if item_choice == True:
        result = f"choice({', '.join(items)})"
    else:
        if len(items) == 1:
            result = items[0]
        else:
            result = f"seq({', '.join(items)})"
    return result


def grammar_from_rule(key, value):
    result = f"        {key}: $ =>"
    if len(value) == 1:
        result += f" {grammar_from_rule_item(value[0])}"
    else:
        result += " choice(\n            {}\n        )".format(
            ',\n            '.join([grammar_from_rule_item(i) for i in value]))
    return result


scanner_components[scanner_rule.name()]["_comment"] = [["`'//'`", '`/.*/`']]

# Following sections are to allow out-of-order per syntactic grammar appearance of rules


rule_skip = set()

for rule in ["translation_unit", "global_directive", "global_decl"]:
    grammar_source += grammar_from_rule(
        rule, scanner_components[scanner_rule.name()][rule]) + ",\n"
    rule_skip.add(rule)


# Extract literals


for key, value in scanner_components[scanner_rule.name()].items():
    if key.endswith("_literal") and key not in rule_skip:
        grammar_source += grammar_from_rule(key, value) + ",\n"
        rule_skip.add(key)


# Extract constituents


def not_token_only(value):
    result = False
    for i in value:
        result = result or len(
            [j for j in i if not j.startswith("`/") and not j.startswith("`'")]) > 0
    return result


for key, value in scanner_components[scanner_rule.name()].items():
    if not key.startswith("_") and key != "ident" and not_token_only(value) and key not in rule_skip:
        grammar_source += grammar_from_rule(key, value) + ",\n"
        rule_skip.add(key)


# Extract tokens


for key, value in scanner_components[scanner_rule.name()].items():
    if not key.startswith("_") and key != "ident" and key not in rule_skip:
        grammar_source += grammar_from_rule(key, value) + ",\n"
        rule_skip.add(key)


# Extract underscore


for key, value in scanner_components[scanner_rule.name()].items():
    if key.startswith("_") and key != "_comment" and key != "_blankspace" and key not in rule_skip:
        grammar_source += grammar_from_rule(key, value) + ",\n"
        rule_skip.add(key)


# Extract ident


grammar_source += grammar_from_rule(
    "ident", scanner_components[scanner_rule.name()]["ident"]) + ",\n"
rule_skip.add("ident")


# Extract comment


grammar_source += grammar_from_rule(
    "_comment", scanner_components[scanner_rule.name()]["_comment"]) + ",\n"
rule_skip.add("_comment")


# Extract space


grammar_source += grammar_from_rule(
    "_blankspace", scanner_components[scanner_rule.name()]["_blankspace"])
rule_skip.add("_blankspace")


grammar_source += "\n"
grammar_source += r"""
    },
});
"""[1:-1]

headerTemplate = Template(HEADER)
grammar_file.write(headerTemplate.substitute(
    YEAR=date.today().year) + grammar_source + "\n")
grammar_file.close()

with open(grammar_path + "/package.json", "w") as grammar_package:
    grammar_package.write('{\n')
    grammar_package.write('    "name": "tree-sitter-wgsl",\n')
    grammar_package.write('    "dependencies": {\n')
    grammar_package.write('        "nan": "^2.15.0"\n')
    grammar_package.write('    },\n')
    grammar_package.write('    "devDependencies": {\n')
    grammar_package.write('        "tree-sitter-cli": "^0.20.0"\n')
    grammar_package.write('    },\n')
    grammar_package.write('    "main": "bindings/node"\n')
    grammar_package.write('}\n')

# External scanner for nested block comments
# For the API, see https://tree-sitter.github.io/tree-sitter/creating-parsers#external-scanners
# See: https://github.com/tree-sitter/tree-sitter-rust/blob/master/src/scanner.c

os.makedirs(os.path.join(grammar_path, "src"), exist_ok=True)
with open(os.path.join(grammar_path, "src", "scanner.c"), "w") as external_scanner:
    external_scanner.write(r"""
#include <tree_sitter/parser.h>
#include <wctype.h>

enum TokenType {
  BLOCK_COMMENT,
};

void *tree_sitter_wgsl_external_scanner_create() { return NULL; }
void tree_sitter_wgsl_external_scanner_destroy(void *p) {}
unsigned tree_sitter_wgsl_external_scanner_serialize(void *p, char *buffer) { return 0; }
void tree_sitter_wgsl_external_scanner_deserialize(void *p, const char *b, unsigned n) {}

static void advance(TSLexer *lexer) {
  lexer->advance(lexer, false);
}

bool tree_sitter_wgsl_external_scanner_scan(void *payload, TSLexer *lexer,
                                            const bool *valid_symbols) {
  while (iswspace(lexer->lookahead)) lexer->advance(lexer, true);

  if (lexer->lookahead == '/') {
    advance(lexer);
    if (lexer->lookahead != '*') return false;
    advance(lexer);

    bool after_star = false;
    unsigned nesting_depth = 1;
    for (;;) {
      switch (lexer->lookahead) {
        case '\0':
          /* This signals the end of input. Since nesting depth is
           * greater than zero, the scanner is in the middle of
           * a block comment. Block comments must be affirmatively
           * terminated.
           */
          return false;
        case '*':
          advance(lexer);
          after_star = true;
          break;
        case '/':
          if (after_star) {
            advance(lexer);
            after_star = false;
            nesting_depth--;
            if (nesting_depth == 0) {
              lexer->result_symbol = BLOCK_COMMENT;
              return true;
            }
          } else {
            advance(lexer);
            after_star = false;
            if (lexer->lookahead == '*') {
              nesting_depth++;
              advance(lexer);
            }
          }
          break;
        default:
          advance(lexer);
          after_star = false;
          break;
      }
    }
  }

  return false;
}
"""[1:-1])

subprocess.run(["npm", "install"], cwd=grammar_path, check=True)
subprocess.run(["npx", "tree-sitter", "generate"],
               cwd=grammar_path, check=True)
# Following are commented for future reference to expose playground
# Remove "--docker" if local environment matches with the container
# subprocess.run(["npx", "tree-sitter", "build-wasm", "--docker"],
#                cwd=grammar_path, check=True)

Language.build_library(
    grammar_path + "/build/wgsl.so",
    [
        grammar_path,
    ]
)

WGSL_LANGUAGE = Language(grammar_path + "/build/wgsl.so", "wgsl")

parser = Parser()
parser.set_language(WGSL_LANGUAGE)

error_list = []

for key, value in scanner_components[scanner_example.name()].items():
    if "expect-error" in key:
        continue
    value = value[:]
    if "function-scope" in key:
        value = ["fn function__scope____() {"] + value + ["}"]
    if "type-scope" in key:
        # Initiailize with zero-value expression.
        value = ["const type_scope____: "] + value + ["="] + value + ["()"] + [";"]
    program = "\n".join(value)
    tree = parser.parse(bytes(program, "utf8"))
    if tree.root_node.has_error:
        error_list.append((program, tree))
    # TODO Semantic CI

if len(error_list) > 0:
    for error in error_list:
        print("Example:")
        print(error[0])
        print("Tree:")
        print(error[1].root_node.sexp())
    raise Exception("Grammar is not compatible with examples!")
