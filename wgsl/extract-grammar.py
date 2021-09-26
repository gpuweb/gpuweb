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
scanner_lines = [j for i in [i.split("\n")
                             for i in scanner_file.readlines()] for j in i if len(j) > 0]

grammar_filename = sys.argv[2]
grammar_path = os.path.dirname(grammar_filename)
os.makedirs(grammar_path, exist_ok=True)
grammar_file = open(grammar_filename, "w")


def scanner_escape_name(name):
    return name.strip().replace("`", "").replace('-', '_').lower().strip()


def scanner_escape_regex(regex):
    return re.escape(regex.strip()).strip().replace("/", "\\/").replace("\\_", "_").replace("\\%", "%").replace("\\;", ";").replace("\\<", "<").replace("\\>", ">").replace("\\=", "=").replace("\\,", ",").replace("\\:", ":").replace("\\!", "!")


class scanner_rule:
    @staticmethod
    def name():
        return "rule"

    @staticmethod
    def begin(lines, i):
        line = lines[i].rstrip()
        return (line.startswith("<div class='syntactic-rule"), None, 1)

    @staticmethod
    def end(lines, i):
        line = lines[i].rstrip()
        return (line.startswith("</div> <!-- syntactic-rule"), 0)

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
        line = lines[i].rstrip()
        if line[2:].startswith("<dfn dfn for=syntactic_rule>"):
            rule_name = line[2:].split("<dfn dfn for=syntactic_rule>")[1]
            rule_name = rule_name.split("</dfn>")[0].strip()
            return (rule_name, None, 0)
        elif line[4:].startswith("| "):
            rule_value = line[6:]
            return (None, rule_value.split(" "), 0)
        elif line[4:].startswith("  "):
            rule_value = line[6:]
            return (None, rule_value.split(" "), -1)
        return (None, None, None)


class scanner_example:  # Not an example of a scanner, scanner of examples from specification
    @staticmethod
    def name():
        return "example"

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

scanner_i = 0
scanner_span = None
scanner_record = False
last_key = None
last_value = None
while scanner_i < len(scanner_lines):
    for j in scanner_spans:
        scanner_begin = j.begin(scanner_lines, scanner_i)
        if scanner_begin[0]:
            scanner_span = None
            scanner_record = False
            last_key = None
            last_value = None
            scanner_span = j
            if scanner_begin[1] != None:
                last_key = scanner_begin[1]
            scanner_i += scanner_begin[-1]
        if scanner_span == j:
            scanner_end = j.end(scanner_lines, scanner_i)
            if scanner_end[0]:
                scanner_span = None
                scanner_record = False
                last_key = None
                last_value = None
                scanner_i += scanner_end[-1]
    if scanner_span != None:
        if scanner_record:
            scanner_skip = scanner_span.skip(scanner_lines, scanner_i)
            if scanner_skip[0]:
                scanner_record = False
                scanner_i += scanner_skip[-1]
        else:
            scanner_record_value = scanner_span.record(
                scanner_lines, scanner_i)
            if scanner_record_value[0]:
                scanner_record = True
                if last_key != None and scanner_span.name() == "example":  # TODO Remove special case
                    if last_key in scanner_components[scanner_span.name()]:
                        last_key += "_next"
                        if last_key not in scanner_components[scanner_span.name()]:
                            scanner_components[scanner_span.name()][last_key] = [
                            ]
                    else:
                        scanner_components[scanner_span.name()][last_key] = []
                scanner_i += scanner_record_value[-1]
        if scanner_record and scanner_span.valid(scanner_lines, scanner_i):
            scanner_parse = scanner_span.parse(scanner_lines, scanner_i)
            if scanner_parse[2] < 0:
                if (scanner_parse[1] != None and
                        last_key != None and
                        last_value != None and
                        last_key in scanner_components[scanner_span.name()] and
                        len(scanner_components[scanner_span.name()][last_key]) > 0):
                    scanner_components[scanner_span.name(
                    )][last_key][-1] += scanner_parse[1]
            else:
                if scanner_parse[0] != None:
                    if scanner_parse[1] != None:
                        last_key = scanner_parse[0]
                        last_value = scanner_parse[1]
                        if last_key not in scanner_components[scanner_span.name()]:
                            scanner_components[scanner_span.name()][last_key] = [
                                last_value]
                        else:
                            scanner_components[scanner_span.name()][last_key].append(
                                last_value)
                    else:
                        last_key = scanner_parse[0]
                        last_value = None
                        scanner_components[scanner_span.name()][last_key] = []
                else:
                    if scanner_parse[1] != None:
                        last_value = scanner_parse[1]
                        scanner_components[scanner_span.name()][last_key].append(
                            last_value)
                scanner_i += scanner_parse[-1]
    scanner_i += 1


grammar_source = ""

grammar_source += r"""
module.exports = grammar({
    name: 'wgsl',

    extras: $ => [
        $._comment,
        $._space,
    ],

    inline: $ => [
        $.global_decl_or_directive,
        $._reserved,
    ],

    conflicts: $ => [
        [$.array_type_decl],
        [$.type_decl,$.primary_expression],
        [$.type_decl,$.primary_expression,$.func_call_statement],
    ],

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
        if rule_item[i].startswith("[=syntactic_rule/"):
            i_item = rule_item[i].split("[=syntactic_rule/")[1].split("=]")[0]
            if i_item.endswith("s") and i_item[:-1] in scanner_components[scanner_rule.name()]:
                i_item = i_item[:-1]
                i_repeatone = True
            elif i_item.endswith("es") and i_item[:-2] in scanner_components[scanner_rule.name()]:
                i_item = i_item[:-2]
                i_repeatone = True
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


# Following sections are to allow out-of-order per syntactic grammar appearance of rules


rule_skip = set()


# Extract translation_unit


grammar_source += grammar_from_rule(
    "translation_unit", scanner_components[scanner_rule.name()]["translation_unit"]) + ",\n"
rule_skip.add("translation_unit")


# Extract global_decl_or_directive


grammar_source += grammar_from_rule(
    "global_decl_or_directive", scanner_components[scanner_rule.name()]["global_decl_or_directive"]) + ",\n"
rule_skip.add("global_decl_or_directive")


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
    if key.startswith("_") and key != "_comment" and key != "_space" and key not in rule_skip:
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
    "_space", scanner_components[scanner_rule.name()]["_space"])
rule_skip.add("_space")


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

subprocess.run(["npm", "install"], cwd=grammar_path, check=True)
subprocess.run(["npx", "tree-sitter", "generate"],
               cwd=grammar_path, check=True)
subprocess.run(["npx", "tree-sitter", "build-wasm"],
               cwd=grammar_path, check=True)

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
        value = ["let type_scope____: "] + value + [";"]
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
