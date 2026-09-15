#!/bin/bash
# Post a comment to issue #281 from ChatGPT's response
# Usage: bash scripts/comment.sh "paste ChatGPT's response here"
# Or:    echo "response text" | bash scripts/comment.sh -

ISSUE=281
TOKEN=$(cat /tmp/gh_token.txt 2>/dev/null || echo "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")

if [ "$1" = "-" ]; then
    BODY=$(cat)
elif [ -n "$1" ]; then
    BODY="$1"
else
    echo "Usage: bash scripts/comment.sh \"ChatGPT's response\""
    echo "Or pipe: echo \"response\" | bash scripts/comment.sh -"
    exit 1
fi

# JSON escape
ESCAPED=$(python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))" <<< "$BODY")

curl -s -X POST "https://api.github.com/repos/yaya1738/hands-off-engine/issues/$ISSUE/comments" \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d "{\"body\": $ESCAPED}" | python3 -c "
import sys,json
d=json.loads(sys.stdin.read())
if 'id' in d:
    print(f'Posted! Comment #{d[\"id\"]}')
else:
    print(f'Failed: {d.get(\"message\",\"unknown error\")}')
"
