#!/bin/bash
# Pre-commit hook: Ensure new docs in monitored paths are categorized
#
# This enforces the coupling between "doc created" and "bootstrap updated".
# Any new .md file in docs/, .claude/, .github/, or ai/ must be added to
# knowledge.json (either required_reading or optional_docs).
#
# Install: ln -sf ../../scripts/pre-commit-doc-check.sh .git/hooks/pre-commit

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
KNOWLEDGE_FILE="$REPO_ROOT/state/knowledge.json"

# Check if knowledge.json exists
if [ ! -f "$KNOWLEDGE_FILE" ]; then
    echo "Warning: knowledge.json not found, skipping doc categorization check"
    exit 0
fi

# Get list of staged .md files in monitored paths
STAGED_DOCS=$(git diff --cached --name-only --diff-filter=A | grep -E "^(docs/|\.claude/|\.github/|ai/).*\.md$" || true)

if [ -z "$STAGED_DOCS" ]; then
    # No new docs in monitored paths
    exit 0
fi

# Check each staged doc against knowledge.json
MISSING_DOCS=""
for doc in $STAGED_DOCS; do
    # Skip session logs and summaries (ephemeral)
    if echo "$doc" | grep -qE "(SESSION|SUMMARY|LOG)"; then
        continue
    fi

    # Skip subdirectory READMEs (except top-level monitored dirs)
    if echo "$doc" | grep -qE "/README\.md$"; then
        # Check if it's in a top-level monitored dir
        if ! echo "$doc" | grep -qE "^(docs|\.claude|\.github|ai)/README\.md$"; then
            continue
        fi
    fi

    # Check if doc is in knowledge.json
    if ! grep -q "\"$doc\"" "$KNOWLEDGE_FILE"; then
        MISSING_DOCS="$MISSING_DOCS\n  - $doc"
    fi
done

if [ -n "$MISSING_DOCS" ]; then
    echo "============================================================"
    echo "ERROR: New docs not categorized in knowledge.json"
    echo "============================================================"
    echo ""
    echo "The following docs were added but not listed in knowledge.json:"
    echo -e "$MISSING_DOCS"
    echo ""
    echo "Please add them to either:"
    echo "  - required_reading (if agents MUST read before working)"
    echo "  - optional_docs (if useful but not mandatory)"
    echo ""
    echo "This ensures the system tracks all important documentation."
    echo "Edit: state/knowledge.json"
    echo "============================================================"
    exit 1
fi

exit 0
