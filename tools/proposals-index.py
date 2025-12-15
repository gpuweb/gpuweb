#!/usr/bin/env python3
import argparse
import sys
import difflib
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
    proposals_merged = []
    proposals_draft = []
    proposals_inactive = []

    found_invalid_status = False
    for proposal_path in sorted(proposals_dir.iterdir()):
        if proposal_path.name == 'README.md':
            continue

        lines = proposal_path.read_text().splitlines()
        line3 = lines[2] if len(lines) >= 3 else ''

        proposal_entry = f'* [{proposal_path.stem}]({proposal_path.name})'

        if line3 == '* Status: [Merged](README.md#status-merged)':
            proposals_merged.append(proposal_entry)
        elif line3 == '* Status: [Draft](README.md#status-draft)':
            proposals_draft.append(proposal_entry)
        elif line3 == '* Status: [Inactive](README.md#status-inactive)':
            proposals_inactive.append(proposal_entry)
        else:
            print(
                f'{proposal_path.name}: Invalid status line (line 3 must be a known status line):\n{line3}\n')
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
                new_list = proposals_merged
            elif line == '<!-- SECTION status-draft -->':
                new_list = proposals_draft
            elif line == '<!-- SECTION status-inactive -->':
                new_list = proposals_inactive
            else:
                assert False, f'Unrecognized SECTION line in README.md: {line}'

            # Replace everything from 'SECTION' to the next blank line, with the new list
            try:
                line_num = readme_lines.index('', start_line)
            except ValueError:
                line_num = len(readme_lines)
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
