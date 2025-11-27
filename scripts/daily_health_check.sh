#!/bin/bash
# Daily health check for monitored repositories
cd "$(dirname "$0")/.."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="reports/health"
mkdir -p "$OUTPUT_DIR"

echo "Running daily health check..."
python scripts/github_batch.py health github_repos.json --output "$OUTPUT_DIR/health_$TIMESTAMP.json"

echo "Health report saved to: $OUTPUT_DIR/health_$TIMESTAMP.json"

# Keep only last 30 days of reports
find "$OUTPUT_DIR" -name "health_*.json" -mtime +30 -delete
