#!/bin/bash
# ABCFC Human-Machine Synergy Loop
# Runs the coordination cycle and logs results

PYTHONPATH=/root/hands-off-engine

cd /root/hands-off-engine

# Run the orchestrator cycle
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Running ABCFC synergy cycle..."
PYTHONPATH=$PYTHONPATH python3 -c "
from integrafix.abcfc_orchestrator import ABCFCOrchestrator
from integrafix.human_machine_synergy import HumanMachineSynergy, wire_wisdom_to_live_nexus
import json

# 1. Wire any pending human wisdom
wire_wisdom_to_live_nexus()

# 2. Run orchestrator cycle
orch = ABCFCOrchestrator(dry_run=True)
result = orch.run_cycle()

# 3. Check for pending human reviews
synergy = HumanMachineSynergy()
synergy.min_edge_for_action = 0.03
opps = synergy.scan_markets()

# Request estimates for opportunities needing human input
needs_input = [o for o in opps if o.get('needs_human_input')]
for opp in needs_input[:5]:
    synergy.request_probability_estimate(opp)

pending = synergy.get_pending_for_human()

print(f'Cycle complete:')
print(f'  Hierarchy: {result[\"state\"][\"hierarchy_nodes\"]} nodes')
print(f'  Sources: {len(result[\"state\"][\"sources\"])}')
print(f'  Decision: {result[\"decision\"][\"action\"]} on {result[\"decision\"][\"target_node\"]}')
print(f'  Live trades ready: {result[\"result\"].get(\"live_trades_proposed\", 0)}')
print(f'  Pending human input: {pending[\"summary\"][\"total_pending\"]}')
"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Synergy cycle complete"
