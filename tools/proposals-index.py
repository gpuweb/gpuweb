#!/usr/bin/env python3
# To format this file, use: python3 -m autopep8

import argparse
import collections
import difflib
import re
import sys
from pathlib import Path

# Status line must be on line 3 and EXACTLY one of these strings
STATUSES = {
    '* Status: [Merged](README.md#status-merged)': 'merged',
    '* Status: [Draft](README.md#status-draft)': 'draft',
    '* Status: [Inactive](README.md#status-inactive)': 'inactive',
}
# Created line must be on line 4 and match this regex
CREATED_REGEX = re.compile(r'^\* Created: (\d\d\d\d-\d\d-\d\d)$')
# Issue line must be on line 5 and match this regex
ISSUE_STARTER = '* Issue: [#'


# Special sections of the README
STATUS_SECTION_MARKER_REGEX = re.compile(r'^<!-- SECTION status-(\w+) -->$')


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
    proposals = {
        'merged': [],
        'draft': [],
        'inactive': [],
    }

    found_invalid_header = False
    for proposal_path in proposals_dir.iterdir():
        filename = proposal_path.name
        if filename == 'README.md':
            continue

        lines = proposal_path.read_text().splitlines()
        line3 = lines[2] if len(lines) >= 3 else ''
        line4 = lines[3] if len(lines) >= 4 else ''
        line5 = lines[4] if len(lines) >= 5 else ''

        if line3 in STATUSES:
            proposals_section = proposals[STATUSES[line3]]
        else:
            print(f'{filename}: Invalid "Status" line (line 3):\n{line3}')
            print('Should be one of:')
            for status in STATUSES.keys():
                print(status)
            print()
            found_invalid_header = True

        match_date = CREATED_REGEX.match(line4)
        if match_date:
            date = match_date[1]
        else:
            print(f'{filename}: Invalid "Created" line (line 4"):\n{line4}')
            print('Should match:\n* Created: YYYY-MM-DD\n')
            found_invalid_header = True

        if not line5.startswith(ISSUE_STARTER):
            print(f'{filename}: Invalid "Issue" first line (line 5):\n{line5}')
            print(f'Should start with:\n{ISSUE_STARTER}\n')
            found_invalid_header = True

        if found_invalid_header:
            continue

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
        match_marker = STATUS_SECTION_MARKER_REGEX.match(line)
        if match_marker:
            start_line = line_num
            proposal_type = match_marker[1]
            if proposal_type in proposals:
                proposals_section = proposals[proposal_type]
            else:
                print(f'{filename}: Unrecognized SECTION line in README.md: {line}')
                sys.exit(1)

            # Replace everything from 'SECTION' to the next blank line, with the new list
            try:
                line_num = readme_lines.index('', start_line)
            except ValueError:
                line_num = len(readme_lines)
            new_lines = map(lambda p: p.list_line, sorted(proposals_section))
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
