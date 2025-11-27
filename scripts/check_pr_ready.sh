#!/bin/bash
# Check if a PR is ready to merge
if [ $# -lt 3 ]; then
    echo "Usage: $0 <owner> <repo> <pr_number>"
    exit 1
fi

cd "$(dirname "$0")/.."
python scripts/github_pr_status.py "$1" "$2" "$3" --check-mergeable
