#!/bin/bash
# INTEGRAFIX: Protect sacred processes from being killed
# This hook runs BEFORE any Bash command and blocks kill commands targeting loops

# Read the command from stdin (JSON format)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('input',{}).get('command',''))" 2>/dev/null)

# Protected processes - NEVER KILL
PROTECTED="backend_loop|hardware_brain|scaling_engine|infra_manager|self_healer"

# Check if this is a kill command targeting protected processes
if echo "$COMMAND" | grep -qE "(kill|pkill|killall)" && echo "$COMMAND" | grep -qE "$PROTECTED"; then
    echo '{"error": "INTEGRAFIX BLOCKED: Cannot kill sacred background loops (backend_loop, hardware_brain, scaling_engine, infra_manager, self_healer). These processes run the autonomous system."}'
    exit 1
fi

exit 0
