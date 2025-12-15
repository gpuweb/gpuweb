#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../proposals"

mode="${1:-}"

proposals_merged=""
proposals_draft=""
proposals_inactive=""
status_line_checks_failed=false
for proposal in * ; do
  if [[ "$proposal" = 'README.md' ]] ; then
    continue
  fi
  line3=$(awk 'NR==3' "$proposal")
  list_line="* [${proposal%.md}](${proposal})
"
  case "$line3" in
    "* Status: [Merged](README.md#status-merged)") proposals_merged+="$list_line" ;;
    "* Status: [Draft](README.md#status-draft)") proposals_draft+="$list_line" ;;
    "* Status: [Inactive](README.md#status-inactive)") proposals_inactive+="$list_line" ;;
    *)
      echo "${proposal}: Invalid status line (line 3 must exactly match one of the known status lines):"
      echo "$line3"
      echo
      status_line_checks_failed=true
      ;;
  esac
done

if [[ "$status_line_checks_failed" = true ]] ; then
  exit 1
fi

old_readme=$(cat README.md)
new_readme=$(awk '
  # Keep original lines as long as skip=0
  !skip { print }
  # When we see one of these lines, inject new content and start skipping old content
  /-- SECTION status-merged --/ {
    while ((getline < "'<(echo "$proposals_merged")'") > 0) print
    skip = 1
    next
  }
  /-- SECTION status-draft --/ {
    while ((getline < "'<(echo "$proposals_draft")'") > 0) print
    skip = 1
    next
  }
  /-- SECTION status-inactive --/ {
    while ((getline < "'<(echo "$proposals_inactive")'") > 0) print
    skip = 1
    next
  }
  # Stop skipping when we see a blank line
  /^$/ {
    skip = 0
  }
' README.md)

case "$mode" in
  check)
    if [[ "$new_readme" != "$old_readme" ]] ; then
      diff -U3 <(echo "$old_readme") <(echo "$new_readme")
      echo
      echo 'Proposals index is out of date. To regenerate, edit manually or run:'
      echo '  tools/proposals-index.sh write'
      exit 1
    fi

    echo 'Proposals index looks good!'
    exit 0
    ;;
  write)
    echo "$new_readme" > README.md
    echo 'Done!'
    ;;
  *)
    echo 'Usage:'
    echo "  $0 check"
    echo "  $0 write"
    exit 1
esac

