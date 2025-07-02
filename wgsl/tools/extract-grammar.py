#!/usr/bin/env python3

from datetime import date
from string import Template
from tempfile import TemporaryDirectory

import argparse
import difflib
import os
import re
import subprocess
import sys
import string
import shutil

from tree_sitter import Language, Parser

# TODO: Source from spec
derivative_patterns = {
    "_comment": "/\\/\\/.*/",
    "_blankspace": "/[\\u0020\\u0009\\u000a\\u000b\\u000c\\u000d\\u0085\\u200e\\u200f\\u2028\\u2029]/u"
}

class Options():
    """
    A class to store various options including file paths and verbosity.
    """
    def __init__(self,bs_filename, tree_sitter_dir, scanner_cc_filename, syntax_filename, syntax_dir):
        self.script = os.path.basename(__file__)
        self.bs_filename = bs_filename
        self.grammar_dir = tree_sitter_dir
        self.scanner_cc_filename = scanner_cc_filename
        self.wgsl_shared_lib = os.path.join(self.grammar_dir,"dist","tree_sitter_wgsl-0.0.7.tar.gz")
        self.grammar_filename = os.path.join(self.grammar_dir,"grammar.js")
        self.syntax_filename = syntax_filename
        self.syntax_dir = syntax_dir
        self.verbose = False

    def __str__(self):
        parts = []
        parts.append("script = {}".format(self.script))
        parts.append("bs_filename = {}".format(self.bs_filename))
        parts.append("grammar_dir = {}".format(self.grammar_dir))
        parts.append("grammar_filename = {}".format(self.grammar_filename))
        parts.append("scanner_cc_filename = {}".format(self.scanner_cc_filename))
        parts.append("wgsl_shared_lib = {}".format(self.wgsl_shared_lib))
        parts.append("syntax_filename = {}".format(self.syntax_filename))
        parts.append("syntax_dir = {}".format(self.syntax_dir))
        return "Options({})".format(",".join(parts))

def newer_than(first,second,second_ext=""):
    """
    Returns true if file 'first' is newer than 'second',
    or if 'second' does not exist
    """
    if not os.path.exists(first):
        raise Exception("Missing file {}".format(first))
    if not os.path.exists(second):
        return True
    first_time = os.path.getmtime(first)
    second_time = os.path.getmtime(second)
    # Find the most recent file if second is a directory
    if os.path.isdir(second):
        for root, dirs, files in os.walk(second):
            for name in files:
                if not name.endswith(second_ext):
                    continue
                p = os.path.join(root, name)
                second_time = max(second_time, os.path.getmtime(p))
    return first_time >= second_time

def remove_files(dir, ext=""):
    """
    Removes all files in the given directory,
    optionally with the given extension.
    """
    for root, dirs, files in os.walk(dir):
        for name in files:
            if name.endswith(ext):
                p = os.path.join(root, name)
                os.remove(p)

def read_lines_from_file(filename, exclusions):
    """
    Returns the text lines from the given file.
    Processes bikeshed path includes, except for files named in the exclusion list,
    or files with ".syntax.bs.include" in their name.
    Skips empty lines.
    """
    file = open(filename, "r")
    # Break up the input into lines, and skip empty lines.
    parts = [j for i in [i.split("\n") for i in file.readlines()]
             for j in i if len(j) > 0]
    result = []
    include_re = re.compile('(?!.*\\.syntax\\.bs\\.include)path:\\s+(\\S+)')
    for line in parts:
        m = include_re.match(line)
        if m:
            included_file = m.group(1)
            if included_file not in exclusions:
                result.extend(read_lines_from_file(included_file, exclusions))
                continue
        result.append(line)
    return result


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
    """
    A scanner that reads grammar rules from bikeshed source text.
    """
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


class scanner_example(Scanner):
    """
    A scanner that reads WGSL program examples from bikeshed source text.
    """
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


class scanner_token(Scanner):
    """
    A scanner that reads WGSL syntax tokens from bikeshed source text.
    """
    @staticmethod
    def name():
        return "token"

    """
     Returns true if this scanner should be used starting at the i'th line
    """
    @staticmethod
    def begin(lines, i):
        line = lines[i].split("//")[0].rstrip()
        result = "* <dfn for=syntax_sym lt='" in line
        key = None
        if result:
            # From a line like:  "* <dfn for=syntax_sym lt='and' noexport>`'&'`..."
            # set key to "'&'"
            key = line.split(" noexport>`")[1].split("`")[0]
        return (result, key, 0)

    @staticmethod
    def end(lines, i):
        line = lines[i].split("//")[0].rstrip()
        return (True, 0) # Token definitions always start and end at the same line

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
        return True

    @staticmethod
    def parse(lines, i):
        line = lines[i].split("//")[0].rstrip()
        result = "* <dfn for=syntax_sym lt='" in line
        value = None
        if result:
            # From a line like:  "* <dfn for=syntax_sym lt='and' noexport>`'&'`..."
            # set key to "and"
            value = line.split("* <dfn for=syntax_sym lt='")[1].split("'")[0]
        return (None, value, 0)

# These fixed tokens must be parsed by the custom scanner.
# This is needed to support template disambiguation.
custom_simple_tokens = {
    '>': '_greater_than',
    '>=': '_greater_than_equal',
    '<': '_less_than',
    '<=': '_less_than_equal',
    '<<': '_shift_left',
    '>>': '_shift_right',
    '<<=': '_shift_left_assign',
    '>>=': '_shift_right_assign'
}

def reproduce_bnfdialect_source(syntax_dict):
    bnfdialect_source = """// This file is not directly compatible with existing BNF parsers. Instead, it
// uses a dialect for a concise reading experience, such as pattern literals
// for tokens and generalizing RegEx operations that reduce the need for empty
// alternatives. For details on interpreting this dialect, see 1.2. Syntax
// Notation in WebGPU Shading Language (WGSL) Specification.\n"""

    def reproduce_rule_source(production, rule_name=""):
        if production["type"] in ["symbol", "token", "pattern"]:
            return production["value"]
        elif production["type"] == "sequence":
            if len(rule_name) == 0:
                return (
                    "( "
                    + " ".join(
                        [
                            reproduce_rule_source(member)
                            for member in production["value"]
                        ]
                    )
                    + " )"
                )
            else:
                return " ".join(
                    [reproduce_rule_source(member) for member in production["value"]]
                )
        elif production["type"] == "choice":
            return (
                "( "
                + " | ".join(
                    [reproduce_rule_source(member) for member in production["value"]]
                )
                + " )"
            )
        elif production["type"] == "match_0_1":
            if len(production["value"]) == 1:
                return reproduce_rule_source(production["value"][0]) + " ?"
            else:
                return (
                    "( "
                    + " ".join(
                        [
                            reproduce_rule_source(member)
                            for member in production["value"]
                        ]
                    )
                    + " ) ?"
                )
        elif production["type"] == "match_1_n":
            if len(production["value"]) == 1:
                return reproduce_rule_source(production["value"][0]) + " +"
            else:
                return (
                    "( "
                    + " ".join(
                        [
                            reproduce_rule_source(member)
                            for member in production["value"]
                        ]
                    )
                    + " ) +"
                )
        elif production["type"] == "match_0_n":
            if len(production["value"]) == 1:
                return reproduce_rule_source(production["value"][0]) + " *"
            else:
                return (
                    "( "
                    + " ".join(
                        [
                            reproduce_rule_source(member)
                            for member in production["value"]
                        ]
                    )
                    + " ) *"
                )
        else:
            raise RuntimeError(f"Unknown production type: {production['type']}")

    for rule_name in syntax_dict.keys():
        if syntax_dict[rule_name]["type"] in ["symbol", "token", "pattern"]:
            bnfdialect_source += f"\n{rule_name} :\n  {syntax_dict[rule_name]['value']}\n;\n"
        elif syntax_dict[rule_name]["type"] == "sequence":
            subsource = " ".join(
                [
                    reproduce_rule_source(member, rule_name)
                    for member in syntax_dict[rule_name]["value"]
                ]
            )
            bnfdialect_source += f"\n{rule_name} :\n  {subsource}\n;\n"
        elif syntax_dict[rule_name]["type"] == "choice":
            subsource = "\n| ".join(
                [
                    reproduce_rule_source(member, rule_name)
                    for member in syntax_dict[rule_name]["value"]
                ]
            )
            bnfdialect_source += f"\n{rule_name} :\n  {subsource}\n;\n"
    return bnfdialect_source.strip()

def grammar_from_rule(key, value):
    def reproduce_rule_source(production, rule_name=""):
        if production["type"] in ["token", "pattern"]:
            return production["value"]
        elif production["type"] == "symbol":
            return f"$.{production['value']}"
        elif production["type"] == "sequence":
            return (
                "seq("
                + ", ".join(
                    [
                        reproduce_rule_source(member)
                        for member in production["value"]
                    ]
                )
                + ")"
            )
        elif production["type"] == "choice":
            return (
                "choice("
                + ", ".join(
                    [reproduce_rule_source(member) for member in production["value"]]
                )
                + ")"
            )
        elif production["type"] == "match_0_1":
            return (
                "optional(" + ("seq(" if len(production["value"]) > 1 else "")
                + ", ".join(
                    [
                        reproduce_rule_source(member)
                        for member in production["value"]
                    ]
                )
                + ")" + (")" if len(production["value"]) > 1 else "")
            )
        elif production["type"] == "match_1_n":
            return (
                "repeat1(" + ("seq(" if len(production["value"]) > 1 else "")
                + ", ".join(
                    [
                        reproduce_rule_source(member)
                        for member in production["value"]
                    ]
                )
                + ")" + (")" if len(production["value"]) > 1 else "")
            )
        elif production["type"] == "match_0_n":
            return (
                "repeat(" + ("seq(" if len(production["value"]) > 1 else "")
                + ", ".join(
                    [
                        reproduce_rule_source(member)
                        for member in production["value"]
                    ]
                )
                + ")" + (")" if len(production["value"]) > 1 else "")
            )
        else:
            raise RuntimeError(f"Unknown production type: {production['type']}")

    return f"\n        {key}: $ => {reproduce_rule_source(value)}"

def bs_fragment_from_rule(key, value, result):
    """
    Returns a valid Bikeshed fragment from a given rule
    """

    def reproduce_rule_source(production, rule_name=""):
        if production["type"] in ["symbol", "token", "pattern"]:
            subsource = ""
            if production["type"] == "symbol":
                affix = ""
                if production["value"].startswith("_"):
                    affix = "_sym"
                subsource = f"[=syntax{affix}/{production['value']}=]"
            elif production["type"] == "token":
                if production["value"] in result[scanner_token.name()]:
                    subsource = f"<a for=syntax_sym lt={result[scanner_token.name()][production['value']]}>`{production['value']}`</a>"
                else:
                    subsource = f"`{production['value']}`"
            elif production["type"] == "pattern":
                subsource = f"`{production['value']}`"
            return subsource
        elif production["type"] == "sequence":
            if len(rule_name) == 0:
                return (
                    "( "
                    + " ".join(
                        [
                            reproduce_rule_source(member)
                            for member in production["value"]
                        ]
                    )
                    + " )"
                )
            else:
                return " ".join(
                    [reproduce_rule_source(member) for member in production["value"]]
                )
        elif production["type"] == "choice":
            return (
                "( "
                + " | ".join(
                    [reproduce_rule_source(member) for member in production["value"]]
                )
                + " )"
            )
        elif production["type"] == "match_0_1":
            if len(production["value"]) == 1:
                return reproduce_rule_source(production["value"][0]) + " ?"
            else:
                return (
                    "( "
                    + " ".join(
                        [
                            reproduce_rule_source(member)
                            for member in production["value"]
                        ]
                    )
                    + " ) ?"
                )
        elif production["type"] == "match_1_n":
            if len(production["value"]) == 1:
                return reproduce_rule_source(production["value"][0]) + " +"
            else:
                return (
                    "( "
                    + " ".join(
                        [
                            reproduce_rule_source(member)
                            for member in production["value"]
                        ]
                    )
                    + " ) +"
                )
        elif production["type"] == "match_0_n":
            if len(production["value"]) == 1:
                return reproduce_rule_source(production["value"][0]) + " *"
            else:
                return (
                    "( "
                    + " ".join(
                        [
                            reproduce_rule_source(member)
                            for member in production["value"]
                        ]
                    )
                    + " ) *"
                )
        else:
            raise RuntimeError(f"Unknown production type: {production['type']}")

    if value["type"] in ["symbol", "token", "pattern"]:
        subsource = ""
        if value["type"] == "symbol":
            affix = ""
            if value["value"].startswith("_"):
                affix = "_sym"
            subsource = f"[=syntax{affix}/{value['value']}=]"
        elif value["type"] == "token":
            if value["value"] in result[scanner_token.name()]:
                subsource = f"<a for=syntax_sym lt={result[scanner_token.name()][value['value']]}>`{value['value']}`</a>"
            else:
                subsource = f"`{value['value']}`"
        elif value["type"] == "pattern":
            subsource = f"`{value['value']}`"
        return f"<div class='syntax' noexport='true'>\n  <dfn for=syntax>{key}</dfn> :\n\n    <span class=\"choice\"></span> {subsource}\n</div>\n"
    elif value["type"] == "sequence":
        subsource = " ".join(
            [
                reproduce_rule_source(member, key)
                for member in value["value"]
            ]
        )
        return f"<div class='syntax' noexport='true'>\n  <dfn for=syntax>{key}</dfn> :\n\n    <span class=\"choice\"></span> {subsource}\n</div>\n"
    elif value["type"] == "choice":
        subsource = "\n\n    <span class=\"choice\">|</span> ".join(
            [
                reproduce_rule_source(member, key)
                for member in value["value"]
            ]
        )
        return f"<div class='syntax' noexport='true'>\n  <dfn for=syntax>{key}</dfn> :\n\n    <span class=\"choice\"></span> {subsource}\n</div>\n"

class ScanResult(dict):
    """
    A dictionary containing the results of scanning the WGSL spec.

    self['raw']
         A list of the Bikeshed source text lines, after include expansion and before
         without further filtering
    self['rule']
         A dictionary mapping a parsed grammar rule to its definition.
    self['example']
         A dictionary mapping the name of an example to the
         WGSL source text for the example.
         The name is taken from the "heading" attriute of the <div> element.
    """
    def __init__(self):
        self[scanner_rule.name()] = dict()
        self[scanner_example.name()] = dict()
        self[scanner_token.name()] = dict()
        self['raw'] = []


def read_spec(options):
    """
    Returns a ScanResult from parsing the Bikeshed source of the WGSL spec.
    """
    result = ScanResult()

    # Get the input bikeshed text.
    scanner_lines = read_lines_from_file(
        options.bs_filename, {'wgsl.recursive.bs.include'})
    # Make a *copy* of the text input because we'll filter it later.
    result['raw'] = [x for x in scanner_lines]

    # TODO: Check if spec includes all rules
    # Skip lines like:
    #  <pre class=include>
    #  </pre>
    scanner_lines = filter(lambda s: not s.startswith(
        "</pre>") and not s.startswith("<pre class=include"), scanner_lines)

    # Replace comments in rule text
    scanner_lines = [re.sub('<!--.*-->', '', line) for line in scanner_lines]

    os.makedirs(options.grammar_dir, exist_ok=True)

    # Global variable holding the current line text.
    line = ""

    # First scan spec for examples (and in future, inclusion of rules and properties that should derive from spec)
    scanner_spans = [scanner_example, scanner_token]

    scanner_i = 0  # line number of the current line
    scanner_span = None
    scanner_record = False
    # The rule name, if the most recently parsed thing was a rule.
    last_key = None
    last_value = None  # The most recently parsed thing
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
                        if last_key in result[scanner_span.name()]:
                            raise RuntimeError(
                                "line " + str(scanner_i) + ": example with duplicate name: " + last_key)
                        else:
                            result[scanner_span.name()][last_key] = []
                    scanner_i += scanner_record_value[-1]
            if scanner_record and scanner_span.valid(scanner_lines, scanner_i):
                # Try parsing this line
                scanner_parse = scanner_span.parse(scanner_lines, scanner_i)
                if scanner_parse[2] < 0:
                    # This line continues the rule parsed on the immediately preceding lines.
                    if (scanner_parse[1] != None and
                            last_key != None and
                            last_value != None and
                            last_key in result[scanner_span.name()] and
                            len(result[scanner_span.name()][last_key]) > 0):
                        result[scanner_span.name(
                        )][last_key][-1] += scanner_parse[1]
                else:
                    if scanner_parse[0] != None:
                        # It's a rule, with name in the 0'th position.
                        last_key = scanner_parse[0]
                        if scanner_parse[1] != None:
                            last_value = scanner_parse[1]
                            if last_key not in result[scanner_span.name()]:
                                # Create a new entry for this rule
                                result[scanner_span.name()][last_key] = [
                                    last_value]
                            else:
                                # Append to the existing entry.
                                result[scanner_span.name()][last_key].append(
                                    last_value)
                        else:
                            # Reset
                            last_value = None
                            result[scanner_span.name()][last_key] = []
                    else:
                        # A token or example
                        if scanner_parse[1] != None:
                            last_value = scanner_parse[1]
                            if scanner_span.name() == scanner_example.name():
                                result[scanner_span.name()][last_key].append(
                                    last_value)
                            if scanner_span.name() == scanner_token.name():
                                result[scanner_span.name()][last_key] = last_value
                    scanner_i += scanner_parse[-1]  # Advance line index
        for j in scanner_spans:
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
        scanner_i += 1

    bnfdialect_data = ""

    # Read the contents of the bnfdialect file
    with open(options.syntax_filename, "r") as file:
        bnfdialect_data = file.read()

    syntax_dict = {}
    current_rule = None
    for line in bnfdialect_data.splitlines():
        comment = ""
        if "//" in line:
            line, comment = line.split("//", 1)
        line = line.strip() # Either blankspace is insignificant
        comment = comment.rstrip() # Right blankspace is insignificant
        if len(line) == 0:
            continue
        if current_rule is None:
            if line.endswith(":"):
                current_rule = line[:-1].strip()
                syntax_dict[current_rule] = {
                    "type": "sequence",
                    "value": []
                }
            continue
        if line.startswith(";"):
            current_rule = None
            continue
        if line.startswith("|"):
            syntax_dict[current_rule]["type"] = "choice"
            line = line[1:].strip()
        tokens = [i for i in line.split(" ") if len(i) > 0] # Strip blankspace
        def build_production(token_j):
            """
            Takes token index and returns token steps and a (sub)production
            """
            token = tokens[token_j]
            if token.startswith("/"):
                return (1, {
                    "type": "pattern",
                    "value": token
                })
            if token.startswith("'"):
                return (1, {
                    "type": "token",
                    "value": token
                })
            if token == "?":
                value = build_production(token_j - 1)
                return (1 + value[0], {
                    "type": "match_0_1",
                    "value": [value[1]]
                })
            if token == "+":
                value = build_production(token_j - 1)
                return (1 + value[0], {
                    "type": "match_1_n",
                    "value": [value[1]]
                })
            if token == "*":
                value = build_production(token_j - 1)
                return (1 + value[0], {
                    "type": "match_0_n",
                    "value": [value[1]]
                })
            if token == "|":
                return (1, {
                    "type": "__MAKE_CHOICE",
                    "value": ""
                })
            if token == ")":
                offset = 1
                production = {
                    "type": "sequence",
                    "value": []
                }
                while tokens[token_j - offset] != "(":
                    value = build_production(token_j - offset)
                    if value[1]["type"].startswith("__MAKE_CHOICE"):
                        production["type"] = "choice"
                    else:
                        production["value"].insert(0, value[1])
                    offset += value[0]
                offset += 1
                return (offset, production)
            else:
                return (1, {
                    "type": "symbol",
                    "value": token
                })
        production = {
            "type": "sequence",
            "value": []
        }
        token_i = len(tokens) - 1
        while token_i >= 0:
            value = build_production(token_i)
            production["value"].insert(0, value[1])
            token_i -= value[0]
        syntax_dict[current_rule]["value"].append(production)

    def reproduce_rule(production):
        if production["type"] in ["sequence", "choice", ""]:
            if len(production["value"]) == 1:
                if production["value"][0]["type"] in ["token", "symbol", "pattern"]:
                    return production["value"][0]
                else:
                    return reproduce_rule(production["value"][0])
            else:
                return {
                    "type": production["type"],
                    "value": [
                        reproduce_rule(member) for member in production["value"]
                    ],
                }
        elif production["type"].startswith("match_"):
            if len(production["value"]) == 1:
                if production["value"][0]["type"] == "sequence":
                    return {
                        "type": production["type"],
                        "value": [
                            reproduce_rule(member)
                            for member in production["value"][0]["value"]
                        ],
                    }
                else:
                    return {
                        "type": production["type"],
                        "value": [
                            reproduce_rule(member) for member in production["value"]
                        ],
                    }
            else:
                return {
                    "type": production["type"],
                    "value": [
                        reproduce_rule(member) for member in production["value"]
                    ],
                }
        else:
            return production

    # Simplify the syntax dictionary
    for rule_name in syntax_dict.keys():
        syntax_dict[rule_name] = reproduce_rule(syntax_dict[rule_name])

    syntax_source = "\n".join([i.strip() for i in bnfdialect_data.strip().splitlines()])
    syntax_target = "\n".join([i.strip() for i in reproduce_bnfdialect_source(syntax_dict).strip().splitlines()])
    if syntax_source != syntax_target:
        print("ERROR: Syntax source should match reproduction for styling and language")
        print("\n".join(difflib.unified_diff(syntax_source.splitlines(), syntax_target.splitlines())))
        sys.exit(1)

    result[scanner_rule.name()] = syntax_dict
    return result

def extract_rules_to_bs(options, scan_result):
    """
    Produce .syntax.bs.include files
    """

    # Extract syntax to bikeshed fragments
    remove_files(options.syntax_dir, "*.syntax.bs.include")

    for rule_name in scan_result[scanner_rule.name()].keys():
        syntax_bs = bs_fragment_from_rule(rule_name, scan_result[scanner_rule.name()][rule_name], scan_result)
        with open(
            os.path.join(options.syntax_dir, rule_name + ".syntax.bs.include"), "w"
        ) as syntax_file:
            syntax_file.write(syntax_bs)

def value_from_dotenv(key):
    if key not in os.environ:
        raise Exception(f"Missing {key} in environment! The key is present in ./tools/custom-action/dependency-versions.sh, please source before execution.")
    return os.environ[key]

def flow_extract(options, scan_result):
    """
    Write the tree-sitter grammar definition for WGSL

    Args:
        options: Options
        scan_result: the ScanResult holding rules and examples extracted from the WGSL spec
    """
    print("{}: Extract...".format(options.script))

    input_bs_is_fresh = True
    previously_scanned_bs_file = options.bs_filename + ".pre"
    if not os.path.exists(options.grammar_filename):
        # Must regenerate the tree-sitter grammar file
        pass
    else:
        # Check against previously scanned text
        if os.path.exists(previously_scanned_bs_file):
            with open(previously_scanned_bs_file,"r") as previous_file:
                previous_lines = previous_file.readlines()
                if previous_lines == scan_result['raw']:
                    input_bs_is_fresh = False

    if input_bs_is_fresh:
        rules = scan_result['rule']

        grammar_source = ""

        grammar_source += """module.exports = grammar({
    name: 'wgsl',

    externals: $ => [
        $._block_comment,
        $._disambiguate_template,
        $._template_args_start,
        $._template_args_end,
        $._less_than,
        $._less_than_equal,
        $._shift_left,
        $._shift_left_assign,
        $._greater_than,
        $._greater_than_equal,
        $._shift_right,
        $._shift_right_assign,
        $._error_sentinel,
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

    word: $ => $.ident_pattern_token,

    rules: {"""

        # Following sections are to allow out-of-order per syntactic grammar appearance of rules

        rule_skip = set()

        for rule in ["translation_unit", "global_directive", "global_decl"]:
            grammar_source += grammar_from_rule(
                rule, rules[rule]) + ",\n"
            rule_skip.add(rule)


        # Extract literals


        for key, value in rules.items():
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


        for key, value in rules.items():
            if not key.startswith("_") and not_token_only(value) and key not in rule_skip:
                grammar_source += grammar_from_rule(key, value) + ",\n"
                rule_skip.add(key)


        # Extract tokens


        for key, value in rules.items():
            if not key.startswith("_") and key not in rule_skip:
                grammar_source += grammar_from_rule(key, value) + ",\n"
                rule_skip.add(key)


        # Extract underscore


        for key, value in rules.items():
            if key.startswith("_") and key != "_comment" and key != "_blankspace" and key not in rule_skip:
                grammar_source += grammar_from_rule(key, value) + ",\n"
                rule_skip.add(key)


        # Extract ident


        grammar_source += grammar_from_rule( "ident", rules["ident"]) + ",\n"
        rule_skip.add("ident")


        # Extract comment


        grammar_source += grammar_from_rule(
            "_comment", {'type': 'pattern',
                               'value': derivative_patterns["_comment"]}) + ",\n"
        rule_skip.add("_comment")


        # Extract space


        grammar_source += grammar_from_rule(
            "_blankspace", {'type': 'pattern',
                               'value': derivative_patterns["_blankspace"]})
        rule_skip.add("_blankspace")


        grammar_source += "\n"
        grammar_source += r"""
    }
});"""[1:-1]

        HEADER = """// Copyright (C) [$YEAR] World Wide Web Consortium,
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

    if input_bs_is_fresh:
        print("{}: ...Creating tree-sitter parser".format(options.script,options.grammar_filename))
        with open(options.grammar_filename, "w") as grammar_file:
            headerTemplate = Template(HEADER)
            grammar_file.write(headerTemplate.substitute(
                YEAR=date.today().year) + grammar_source + "\n")
            grammar_file.close()

    if input_bs_is_fresh:
        # Save scanned lines for next time.
        with open(previously_scanned_bs_file,"w") as previous_file:
            for line in scan_result['raw']:
                previous_file.write(line)

    return True

def flow_build(options):
    """
    Build and install the tree_sitter_wgsl Python module, including the custom scanner
    """

    print("{}: Build tree_sitter_wgsl...".format(options.script))
    if not os.path.exists(options.grammar_filename):
        print("missing grammar file: {}")
        return False

    # Only rebuild if the grammar has changed.
    grammar_is_fresh = True
    with open(options.grammar_filename,"r") as current_file:
        current_lines = current_file.readlines()
    previously_scanned_grammar_file = options.grammar_filename + ".pre"
    if os.path.exists(previously_scanned_grammar_file):
        # Check against previously scanned text
        with open(previously_scanned_grammar_file,"r") as previous_file:
            previous_lines = previous_file.readlines()
            grammar_is_fresh = current_lines != previous_lines

    if not grammar_is_fresh:
        print("{}: ...Skip rebuilding because the grammar has not changed".format(options.script))
        return True

    # The 'build.stamp' file is touched when the parser is successfully installed.
    stampfile = os.path.join(options.grammar_dir, 'build.stamp')

    # External scanner for nested block comments
    # For the API, see https://tree-sitter.github.io/tree-sitter/creating-parsers#external-scanners
    # See: https://github.com/tree-sitter/tree-sitter-rust/blob/master/src/scanner.c

    os.makedirs(os.path.join(options.grammar_dir, "src"), exist_ok=True)
    scanner_cc_staging = os.path.join(options.grammar_dir, "src", "scanner.c")


    cmd = ["npx", "tree-sitter-cli@" + value_from_dotenv("NPM_TREE_SITTER_CLI_VERSION"), "generate"]
    print("{}:     {}".format(options.script, " ".join(cmd)))
    subprocess.run(cmd, cwd=options.grammar_dir, check=True)

    # Use "npm install" to create the tree-sitter CLI that has WGSL
    # support.  But "npm install" fetches data over the network.
    # That can be flaky, so only invoke it when needed.
    if os.path.exists("grammar/node_modules/tree-sitter-cli"):
        # "npm install" has been run already.
        print("{}:    skipping npm install: grammar/node_modules/tree-sitter-cli already exists".format(options.script))
        pass
    else:
        cmd = ["npm", "install"]
        print("{}:    {}".format(options.script, " ".join(cmd)))
        subprocess.run(cmd, cwd=options.grammar_dir, check=True)

    # Following are commented for future reference to expose playground
    # Remove "--docker" if local environment matches with the container
    # subprocess.run(["npx", "tree-sitter-cli@" + value_from_dotenv("NPM_TREE_SITTER_CLI_VERSION"), "build-wasm", "--docker"],
    #                cwd=options.grammar_dir, check=True)

    def build_library(input_files):
        """
        Build and install the tree-sitter language package
        """
        try:
            if "VIRTUAL_ENV" in os.environ:
                cmd = ["python3", "-m", "pip", "install", "-e", "."]
            else:
                cmd = ["python3", "-m", "pip", "install", "-e", ".", "--user", "--break-system-packages"]
            print("{}:    {}".format(options.script, " ".join(cmd)))
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=options.grammar_dir
            )

            # Save the grammar contents for comparing against next time.
            with open(previously_scanned_grammar_file,"w") as previous_file:
                for line in current_lines:
                    previous_file.write(line)
                previous_file.close()
            with open(stampfile, 'w') as f:
                print("created file:  {}".format(stampfile))
            print("{}: ...Successfully built and installed tree_sitter_wgsl.".format(options.script))
        except subprocess.CalledProcessError as e:
            print(f"Error installing tree_sitter_wgsl language package: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False

    if newer_than(scanner_cc_staging, stampfile) or newer_than(options.grammar_filename,stampfile):
        print("{}: ...Building custom scanner".format(options.script))
        build_library([scanner_cc_staging, os.path.join(options.grammar_dir,"src","parser.c")])
    else:
        print("{}: ...Skip building tree_sitter_wgsl: grammar/build.stamp is fresh".format(options.script))
    return True

def flow_examples(options,scan_result):
    """
    Check the tree-sitter parser can parse the examples from the WGSL spec.

    Args:
        options: Options
        scan_result: the ScanResult holding rules and examples extracted from the WGSL spec
    """
    print("{}: Examples...".format(options.script))

    examples = scan_result['example']
    import tree_sitter_wgsl
    WGSL_LANGUAGE = Language(tree_sitter_wgsl.language())

    parser = Parser(WGSL_LANGUAGE)

    errors = 0
    for key, value in examples.items():
        print(".",flush=True,end='')
        if "expect-error" in key:
            continue
        value = value[:]
        if "function-scope" in key:
            value = ["fn function__scope____() {"] + value + ["}"]
        if "type-scope" in key:
            # Initialize with zero-value expression.
            value = ["const type_scope____: "] + \
                value + ["="] + value + ["()"] + [";"]
        program = "\n".join(value)
        # print("**************** BEGIN ****************")
        # print(program)
        # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        tree = parser.parse(bytes(program, "utf8"))
        if tree.root_node.has_error:
            print("Example:")
            print(program)
            print("Tree:")
            print(tree.root_node.sexp())
            errors = errors + 1
        # print("***************** END *****************")
        # print("")
        # print("")

        # TODO Semantic CI

    if errors > 0:
        raise Exception("Grammar is not compatible with examples!")
    print("Ok",flush=True)
    return True


FLOW_HELP = """
A complete flow has the following steps, in order
    'x' (think 'extract'): Generate a tree-sitter grammar definition from the
          bikeshed source for the WGSL specification and generates
          bikeshed include fragments for syntax rules.
    'b' (think 'build'): Build the tree-sitter parser
    'e' (think 'example'): Check the examples from the WGSL spec parse correctly.
    't' (think 'test'): Run parser unit tests.

You can be more selective by specifying the --flow option followed by a word
containing the letters for the steps to run.

For example, the following will extract the grammar, build the tree-sitter parse,
and check that the examples from the spec parse correctly:

    extract-grammar --flow xbe

The order of the letters is not significant. The steps will always run in the
same relative order as the default flow.
"""
DEFAULT_FLOW="xbet"

def main():
    argparser = argparse.ArgumentParser(
            prog="extract-grammar.py",
            description="Extract the grammar from the WGSL spec and run checks",
            add_help=False # We want to print our own additional formatted help
            )
    argparser.add_argument("--help","-h",
                           action='store_true',
                           help="Show this help message, then exit")
    argparser.add_argument("--verbose","-v",
                           action='store_true',
                           help="Be verbose")
    argparser.add_argument("--flow",
                           action='store',
                           help="The flow steps to run. Default is the whole flow.",
                           default=DEFAULT_FLOW)
    argparser.add_argument("--tree-sitter-dir",
                           help="Target directory for the tree-sitter parser",
                           default="grammar")
    argparser.add_argument("--spec",
                           action='store',
                           help="Bikeshed source file for the WGSL spec",
                           default="index.bs")
    argparser.add_argument("--scanner",
                           action='store',
                           help="Source file for the tree-sitter custom scanner",
                           default="scanner.cc")
    argparser.add_argument("--syntax",
                           action='store',
                           help="Source file for the WGSL syntax",
                           default="syntax.bnf")
    argparser.add_argument("--syntax-dir",
                           help="Target directory for the WGSL Bikeshed syntax",
                           default="syntax")

    args = argparser.parse_args()
    if args.help:
        print(argparser.format_help())
        print(FLOW_HELP)
        return 0

    options = Options(args.spec,args.tree_sitter_dir,args.scanner, args.syntax, args.syntax_dir)
    options.verbose = args.verbose
    if args.verbose:
        print(options)

    if not os.path.exists(options.syntax_dir):
        print("ERROR: Syntax directory does not exist: {}".format(options.syntax_dir))
        return 1

    scan_result = None

    if 'x' in args.flow:
        scan_result = read_spec(options)
        extract_rules_to_bs(options, scan_result)
        if not flow_extract(options,scan_result):
            return 1
    if 'b' in args.flow:
        if not flow_build(options):
            return 1
    if 'e' in args.flow:
        if scan_result is None:
            scan_result = read_spec(options)
        if not flow_examples(options,scan_result):
            return 1
    if 't' in args.flow:
        import wgsl_unit_tests
        test_options = wgsl_unit_tests.Options()
        if not wgsl_unit_tests.run_tests(test_options):
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
