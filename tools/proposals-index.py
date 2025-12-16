#!/usr/bin/env python3
# To format this file, use: python3 -m autopep8

import argparse
import collections
import difflib
import re
import sys
from pathlib import Path

# Status line must be on line 3 and EXACTLY one of these strings
STATUS_MERGED = '* Status: [Merged](README.md#status-merged)'
STATUS_DRAFT = '* Status: [Draft](README.md#status-draft)'
STATUS_INACTIVE = '* Status: [Inactive](README.md#status-inactive)'


def main():
    proposals_dir = (Path(__file__).parent / '..' / 'proposals').resolve()
    assert proposals_dir.exists(), "Can't find the proposals directory"

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'mode',
        choices=['check', 'write'],
        help="'check' to check the index is up-to-date; 'write' to update it"
    )
    args = parser.parse_args()

    # Collect proposals and group them by status
    Proposal = collections.namedtuple('Proposal', ['created', 'list_line'])
    proposals_merged = []
    proposals_draft = []
    proposals_inactive = []

    found_invalid_header = False
    for proposal_path in proposals_dir.iterdir():
        filename = proposal_path.name
        if filename == 'README.md':
            continue

        lines = proposal_path.read_text().splitlines()
        line3 = lines[2] if len(lines) >= 3 else ''
        line4 = lines[3] if len(lines) >= 4 else ''

        if line3.startswith(STATUS_MERGED):
            proposals_section = proposals_merged
        elif line3.startswith(STATUS_DRAFT):
            proposals_section = proposals_draft
        elif line3.startswith(STATUS_INACTIVE):
            proposals_section = proposals_inactive
        else:
            print(f'{filename}: Invalid "Status" line (line 3):\n{line3}\n')
            found_invalid_header = True
            continue

        match_date = re.fullmatch(r'\* Created: (\d\d\d\d-\d\d-\d\d)', line4)
        if match_date == None:
            print(f'{filename}: Invalid "Created" line (line 4):\n{line4}\n')
            found_invalid_header = True
            continue
        date = match_date[1]

        proposals_section.append(
            Proposal(date, f'* [{proposal_path.stem}]({filename})'))

    if found_invalid_header:
        sys.exit(1)

    # Load the README
    readme_path = proposals_dir / 'README.md'
    assert readme_path.exists(), "Can't find proposals/README.md"
    old_content = readme_path.read_text()

    # Generate new README with the proposals lists updated
    readme_lines = old_content.splitlines()
    line_num = 0
    while line_num < len(readme_lines):
        line = readme_lines[line_num]
        if line.startswith('<!-- SECTION'):
            start_line = line_num
            if line == '<!-- SECTION status-merged -->':
                proposals = proposals_merged
            elif line == '<!-- SECTION status-draft -->':
                proposals = proposals_draft
            elif line == '<!-- SECTION status-inactive -->':
                proposals = proposals_inactive
            else:
                print(f'{filename}: Unrecognized SECTION line in README.md: {line}')
                sys.exit(1)

            # Replace everything from 'SECTION' to the next blank line, with the new list
            try:
                line_num = readme_lines.index('', start_line)
            except ValueError:
                line_num = len(readme_lines)
            new_lines = map(lambda p: p.list_line, sorted(proposals))
            readme_lines[start_line + 1:line_num] = new_lines
        else:
            line_num += 1
    new_content = '\n'.join(readme_lines) + '\n'

    # Check or write the result
    if new_content == old_content:
        print('Proposals index looks good!')
    else:
        if args.mode == 'write':
            readme_path.write_text(new_content)
            print('Updated!')
        elif args.mode == 'check':
            diff = difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile='README.md (old)',
                tofile='README.md (new)',
                n=3
            )
            sys.stdout.writelines(diff)
            print('\nProposals index is out of date. To regenerate, run:')
            print('  tools/proposals-index.py write')
            sys.exit(1)
        else:
            assert False


if __name__ == '__main__':
    main()
