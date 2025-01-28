#!/bin/bash
set -euo pipefail

usage()
{
    echo "Usage: $0 input_file output_file"
    echo
    echo "Copies input_file to output_file if output_file does not exist or"
    echo "is different from input_file"
    exit 1
}

[ $# -eq 2 ] || usage
input="$1"
output="$2"
if [ ! -f "$input" ]; then
  echo "input file does not exist: $input"
  usage
fi

if [ ! -f "$output" ] || ! diff "$input" "$output" >/dev/null; then
  cp "$input" "$output"
fi
