#!/usr/bin/env python3
"""
Postprocessing grammar.js for tree-sitter-wgsl repository

Exposes block_comment, template_args_start, and template_args_end as named nodes
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Postprocessing for grammar.js for tree-sitter-wgsl"
    )
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")

    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1

    content = content.replace("_block_comment", "block_comment")
    content = content.replace("_template_args_start", "template_args_start")
    content = content.replace("_template_args_end", "template_args_end")

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Wrote processed file to '{args.output}'")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
