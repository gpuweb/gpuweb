#!/usr/bin/env python3

# To format this file, use: python3 -m autopep8

import argparse
import collections
import difflib
import re
import sys
from pathlib import Path


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

    # Lists of tuple of (issue number, text of index line)
    Proposal = collections.namedtuple(
        'Proposal', ['issue_number', 'entry_text'])
    proposals_merged = []
    proposals_draft = []
    proposals_inactive = []

    found_invalid_status = False
    for proposal_path in proposals_dir.iterdir():
        filename = proposal_path.name
        if filename == 'README.md':
            continue

        lines = proposal_path.read_text().splitlines()
        line3 = lines[2] if len(lines) >= 3 else ''
        line4 = lines[3] if len(lines) >= 3 else ''

        match = re.match(
            r'^\* Issue: \[#(\d+)]\(https://github\.com/gpuweb/gpuweb/issues/\1\),?$', line4)
        if match == None:
            print(
                f'{filename}: Invalid issue line (must match standard format):\n{line4}\n')
            sys.exit(1)
        issue_number = int(match[1])

        entry_text = f'* #{issue_number} [{proposal_path.stem}]({filename})'
        proposal_entry = Proposal(issue_number, entry_text)

        if line3 == '* Status: [Merged](README.md#status-merged)':
            proposals_merged.append(proposal_entry)
        elif line3 == '* Status: [Draft](README.md#status-draft)':
            proposals_draft.append(proposal_entry)
        elif line3 == '* Status: [Inactive](README.md#status-inactive)':
            proposals_inactive.append(proposal_entry)
        else:
            print(
                f'{filename}: Invalid status line (line 3 must be a known status line):\n{line3}\n')
            found_invalid_status = True

    if found_invalid_status:
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
            # Sort by issue number (used a Khronos "extension number") and extract entry text
            new_list = map(lambda x: x.entry_text, sorted(proposals))
            readme_lines[start_line + 1:line_num] = new_list
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
