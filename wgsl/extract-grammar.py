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


class scanner_constituent:
    @staticmethod
    def name():
        return "constituent"

    @staticmethod
    def begin(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("<pre class='def'>" in line, None, 1)

    @staticmethod
    def end(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</pre>" in line, 0)

    @staticmethod
    def record(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return (True, 0)

    @staticmethod
    def skip(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return (False, 0)

    @staticmethod
    def valid(lines, i):
        line = lines[i].split("//")[0].rstrip()
        result = len(line.strip()) > 0
        if not result:
            return result
        result = result and line[0] != "`"
        result = result and not line.startswith("TODO")
        if line[0] == " ":
            result = result and (line.lstrip()[0] in [":", "|"] or
                                 (line.startswith("     ") and
                                  line[5] != " " and
                                  lines[i-1].rstrip().endswith("SEMICOLON")))
        else:
            if len(lines) > i+1:
                result = result and scanner_constituent.valid(lines, i+1)
            else:
                result = False
        return result

    @staticmethod
    def parse(lines, i):
        line = lines[i].split("//")[0].rstrip()
        if line[0] != " ":
            # Append new key
            return (scanner_escape_name(line.strip()), None, 0)
        else:
            if line.lstrip()[0] in [":", "|"]:
                # Append new value
                return (None, scanner_escape_name(
                    line.strip()[1:].strip())
                    .replace("(", " ( ")
                    .replace(")", " ) ")
                    .replace("*", " * ")
                    .replace("+", " + ")
                    .replace("?", " ? ")
                    .replace("|", " | ")
                    .replace(" ", "  "), 0)
            else:
                # Extend last value
                return (None, " " + scanner_escape_name(line.strip())
                        .replace("(", " ( ")
                        .replace(")", " ) ")
                        .replace("*", " * ")
                        .replace("+", " + ")
                        .replace("?", " ? ")
                        .replace("|", " | ")
                        .replace(" ", "  "), -1)


class scanner_literal:
    @staticmethod
    def name():
        return "literal"

    @staticmethod
    def begin(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("## Literals" in line, None, 1)

    @staticmethod
    def end(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</table>" in line, 0)

    @staticmethod
    def record(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</thead>" in line, 1)

    @staticmethod
    def skip(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return (False, 0)

    @staticmethod
    def valid(lines, i):
        line = lines[i].split("//")[0].rstrip()
        result = len(line.strip()) > 0
        result = result and "Token<td>Definition" not in line
        return result

    @staticmethod
    def parse(lines, i):
        line = lines[i].split("//")[0].rstrip()
        split = line.split("<td>")
        return (scanner_escape_name(split[1]), "/" + split[2].replace("`", "") + "/", 0)


class scanner_identifier:
    @staticmethod
    def name():
        return "identifier"

    @staticmethod
    def begin(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("## Identifiers" in line, None, 1)

    @staticmethod
    def end(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</table>" in line, 0)

    @staticmethod
    def record(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</thead>" in line, 1)

    @staticmethod
    def skip(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return (False, 0)

    @staticmethod
    def valid(lines, i):
        line = lines[i].split("//")[0].rstrip()
        result = len(line.strip()) > 0
        result = result and "Token<td>Definition" not in line
        return result

    @staticmethod
    def parse(lines, i):
        line = lines[i].split("//")[0].rstrip()
        split = line.split("<td>")
        return (scanner_escape_name(split[1]), "/" + split[2].replace("`", "") + "/", 0)


class scanner_keyword:
    @staticmethod
    def name():
        return "keyword"

    @staticmethod
    def begin(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("## Keyword Summary" in line, None, 1)

    @staticmethod
    def end(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return (False, 0)  # TODO Recognize end of keywords

    @staticmethod
    def record(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("<table class='data'>" in line, 1)

    @staticmethod
    def skip(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</table>" in line, 0)

    @staticmethod
    def valid(lines, i):
        line = lines[i].split("//")[0].rstrip()
        result = len(line.strip()) > 0
        result = result and "Token<td>Definition" not in line
        result = result and len(line.split("<td>")) > 2
        return result

    @staticmethod
    def parse(lines, i):
        line = lines[i].split("//")[0].rstrip()
        split = line.split("<td>")
        return (scanner_escape_name(split[1]), "/" + scanner_escape_regex(split[2].replace("`", "")) + "/", 0)


class scanner_reserved:
    @staticmethod
    def name():
        return "reserved"

    @staticmethod
    def begin(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("## Reserved Words" in line, None, 1)

    @staticmethod
    def end(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</table>" in line, 0)

    @staticmethod
    def record(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("<table class='data'>" in line, 1)

    @staticmethod
    def skip(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return (False, 0)

    @staticmethod
    def valid(lines, i):
        line = lines[i].split("//")[0].rstrip()
        result = len(line.strip()) > 0
        result = result and "Token<td>Definition" not in line
        result = result and not line.strip().startswith("<tr>")
        result = result and len(line.split("<td>")) > 1
        return result

    @staticmethod
    def parse(lines, i):
        line = lines[i].split("//")[0].rstrip()
        split = line.split("<td>")
        return ("_reserved", "/" + scanner_escape_regex(split[1].replace("`", "")) + "/", 0)


class scanner_token:
    @staticmethod
    def name():
        return "token"

    @staticmethod
    def begin(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("## Syntactic Tokens" in line, None, 1)

    @staticmethod
    def end(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("</table>" in line, 0)

    @staticmethod
    def record(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return ("<table class='data'>" in line, 1)

    @staticmethod
    def skip(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return (False, 0)

    @staticmethod
    def valid(lines, i):
        line = lines[i].split("//")[0].rstrip()
        result = len(line.strip()) > 0
        result = result and "Token<td>Definition" not in line
        result = result and len(line.split("<td>")) > 2
        return result

    @staticmethod
    def parse(lines, i):
        line = lines[i].split("//")[0].rstrip()
        split = line.split("<td>")
        return (scanner_escape_name(split[1]), "/" + scanner_escape_regex(split[2].replace("`", "")) + "/", 0)


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


scanner_spans = [scanner_constituent,
                 scanner_literal,
                 scanner_identifier,
                 scanner_keyword,
                 scanner_reserved,
                 scanner_token,
                 scanner_example]


scanner_components = {i.name(): {} for i in scanner_spans}
scanner_components["comment"] = {"_comment": ["/\\/\\// /.*/"]}
scanner_components["space"] = {"_space": ["/\\s/"]}

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


grammar_constituents_optional = {key for key, value in scanner_components[scanner_constituent.name(
)].items() if "" in value or value[0].rstrip().endswith("*")}


def grammar_sequence_from_element(element):
    sequence = ""
    subsequences = element.split()
    sequence_i = 0
    sequence_type = "seq"
    while sequence_i < len(subsequences):
        if "(" in subsequences[sequence_i]:
            subelements = [subsequences[sequence_i].replace("(", "")]
            sequence_i += 1
            subexpressions = 1
            while subexpressions > 0:
                if "(" in subsequences[sequence_i]:
                    subexpressions += 1
                if ")" in subsequences[sequence_i]:
                    subexpressions -= 1
                subelements.append(subsequences[sequence_i])
                sequence_i += 1
            sequence_i -= 1
            subelements = [i for i in subelements if len(i.strip()) > 0]
            if sequence_i + 1 < len(subsequences):
                if subsequences[sequence_i + 1] == "*":
                    subsequence = grammar_sequence_from_element(
                        " ".join(subelements))
                    sequence += "optional(repeat("
                    if subsequence[1] == "choice":
                        sequence += "choice("
                    elif subsequence[1] == "seq":
                        sequence += "seq("
                    sequence += subsequence[0]
                    if subsequence[1] == "choice":
                        sequence += "),"
                    elif subsequence[1] == "seq":
                        sequence += "),"
                    sequence += ")),"
                    sequence_i += 1
                elif subsequences[sequence_i + 1] == "+":
                    subsequence = grammar_sequence_from_element(
                        " ".join(subelements))
                    sequence += "repeat1("
                    if subsequence[1] == "choice":
                        sequence += "choice("
                    elif subsequence[1] == "seq":
                        sequence += "seq("
                    sequence += subsequence[0]
                    if subsequence[1] == "choice":
                        sequence += "),"
                    elif subsequence[1] == "seq":
                        sequence += "),"
                    sequence += "),"
                    sequence_i += 1
                elif subsequences[sequence_i + 1] == "?":
                    subsequence = grammar_sequence_from_element(
                        " ".join(subelements))
                    sequence += "optional("
                    if subsequence[1] == "choice":
                        sequence += "choice("
                    elif subsequence[1] == "seq":
                        sequence += "seq("
                    sequence += subsequence[0]
                    if subsequence[1] == "choice":
                        sequence += "),"
                    elif subsequence[1] == "seq":
                        sequence += "),"
                    sequence += "),"
                    sequence_i += 1
                else:
                    subsequence = grammar_sequence_from_element(
                        " ".join(subelements))
                    if subsequence[1] == "choice":
                        sequence += "choice("
                    elif subsequence[1] == "seq":
                        sequence += "seq("
                    sequence += subsequence[0]
                    if subsequence[1] == "choice":
                        sequence += "),"
                    elif subsequence[1] == "seq":
                        sequence += "),"
            else:
                subsequence = grammar_sequence_from_element(
                    " ".join(subelements))
                if subsequence[1] == "choice":
                    sequence += "choice("
                elif subsequence[1] == "seq":
                    sequence += "seq("
                sequence += subsequence[0]
                if subsequence[1] == "choice":
                    sequence += "),"
                elif subsequence[1] == "seq":
                    sequence += "),"
        else:
            if "|" in subsequences[sequence_i]:
                sequence_type = "choice"
            else:
                enforce_optional = subsequences[sequence_i] in grammar_constituents_optional
                if enforce_optional:
                    sequence += "optional("
                if sequence_i + 1 < len(subsequences):
                    if subsequences[sequence_i + 1] == "*":
                        sequence += "optional(repeat("
                        sequence += "$." + subsequences[sequence_i] + ","
                        sequence += ")),"
                        sequence_i += 1
                    elif subsequences[sequence_i + 1] == "+":
                        sequence += "repeat1("
                        sequence += "$." + subsequences[sequence_i] + ","
                        sequence += "),"
                        sequence_i += 1
                    elif subsequences[sequence_i + 1] == "?":
                        sequence += "optional("
                        sequence += "$." + subsequences[sequence_i] + ","
                        sequence += "),"
                        sequence_i += 1
                    else:
                        if len(subsequences[sequence_i].strip()) > 0 and ")" not in subsequences[sequence_i]:
                            sequence += "$." + subsequences[sequence_i] + ","
                else:
                    if len(subsequences[sequence_i].strip()) > 0 and ")" not in subsequences[sequence_i]:
                        sequence += "$." + subsequences[sequence_i] + ","
                if enforce_optional:
                    sequence += "),"
        sequence_i += 1
    sequence += ""
    return (sequence, sequence_type)


def grammar_from_constituent(key, value):
    return "        {}: $ => choice(\n            {}\n        ),".format(key, ",\n            ".join(["seq(" + grammar_sequence_from_element(element)[0] + ")" for element in value if len(element.strip()) > 0]))


grammar_source += grammar_from_constituent(
    "translation_unit", scanner_components[scanner_constituent.name()]["translation_unit"]) + "\n"
del scanner_components[scanner_constituent.name()]["translation_unit"]


grammar_source += grammar_from_constituent("global_decl_or_directive",
                                           scanner_components[scanner_constituent.name()]["global_decl_or_directive"]) + "\n\n"
del scanner_components[scanner_constituent.name()]["global_decl_or_directive"]


def grammar_from_literal(key, value):
    return "        {}: $ => token({}),".format(key, value)


grammar_source += "\n".join([grammar_from_literal(key, value[0])
                            for key, value in scanner_components[scanner_literal.name()].items()]) + "\n\n"


grammar_source += "\n".join([grammar_from_constituent(key, value)
                             for key, value in scanner_components[scanner_constituent.name()].items()]) + "\n\n"


grammar_source += "\n".join([grammar_from_literal(key, value[0])
                            for key, value in scanner_components[scanner_keyword.name()].items()]) + "\n\n"


grammar_source += "\n".join([grammar_from_literal(key, value[0])
                            for key, value in scanner_components[scanner_token.name()].items()]) + "\n\n"


def grammar_from_reserved(key, value):
    return "        {}: $ => choice(\n            {}\n        ),".format(key, ",\n            ".join(value))


grammar_source += "\n".join([grammar_from_reserved(key, value)
                            for key, value in scanner_components[scanner_reserved.name()].items()]) + "\n\n"


def grammar_from_identifier(key, value):
    return "        ident: $ => token({}),".format(",".join(value))


grammar_source += "\n".join([grammar_from_identifier(key, value)
                            for key, value in scanner_components[scanner_identifier.name()].items()]) + "\n\n"


def grammar_from_comment(key, value):
    return "        _comment: $ => seq({}),".format(",".join(value[0].split()))


grammar_source += "\n".join([grammar_from_comment(key, value)
                            for key, value in scanner_components["comment"].items()]) + "\n"


def grammar_from_space(key, value):
    return "        _space: $ => {},".format(",".join(value))


grammar_source += "\n".join([grammar_from_space(key, value)
                            for key, value in scanner_components["space"].items()])


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
