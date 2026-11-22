#!/bin/bash
# Post a comment to issue #281 using an explicitly configured GitHub token.
# Usage: GITHUB_TOKEN=... bash scripts/comment.sh "comment text"
# Or:    echo "comment text" | GITHUB_TOKEN=... bash scripts/comment.sh -

set -euo pipefail

ISSUE=281
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
if [ -z "$TOKEN" ]; then
    echo "Blocked: set GH_TOKEN or GITHUB_TOKEN in the environment."
    exit 2
fi

if [ "${1:-}" = "-" ]; then
    BODY=$(cat)
elif [ -n "${1:-}" ]; then
    BODY="$1"
else
    echo "Usage: GITHUB_TOKEN=... bash scripts/comment.sh \"comment text\""
    echo "Or pipe: echo \"comment\" | GITHUB_TOKEN=... bash scripts/comment.sh -"
    exit 1
fi

ESCAPED=$(python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))" <<< "$BODY")

curl --fail-with-body -sS -X POST "https://api.github.com/repos/yaya1738/hands-off-engine/issues/$ISSUE/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d "{\"body\": $ESCAPED}" | python3 -c "
import sys,json
d=json.loads(sys.stdin.read())
if 'id' in d:
    print(f'Posted! Comment #{d[\"id\"]}')
else:
    print(f'Failed: {d.get(\"message\",\"unknown error\")}')
"
