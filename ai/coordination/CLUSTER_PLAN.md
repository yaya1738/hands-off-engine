# Cluster Architecture Plan

**Created:** 2025-12-02
**Status:** DRAFT - Needs collaborative input from all agents

---

## MANDATORY RULES (NON-NEGOTIABLE)

1. **NEVER destroy droplets**
2. **NEVER restart services without explicit user approval**
3. **NEVER reset passwords**
4. **NEVER delete infrastructure**
5. **NEVER modify credentials without explicit user approval**
6. **All changes must be coordinated via messages.jsonl**

---

## Current State

### Nodes (9 total)

| Node | IP | Role | Status | Processes |
|------|-----|------|--------|-----------|
| pm-helper | 138.68.103.156 | PRIMARY | Active | 17 (all agents) |
| ho-cli-main | 165.22.176.190 | CLI | Active | 2 Claude sessions |
| ho-compute-1 | 206.189.226.242 | compute | IDLE | 2 (system only) |
| ho-compute-2 | 142.93.63.109 | compute | IDLE | 2 (system only) |
| ho-compute-2 | 159.203.184.188 | compute | IDLE | 2 (system only) |
| ho-scale | 162.243.175.211 | compute | IDLE | 2 (system only) |
| ho-topdawg-4 | 157.245.134.228 | compute | IDLE | 2 (system only) |
| ho-mega-1 | 147.182.172.241 | compute | IDLE | 2 (system only) |
| ho-mega-2 | 167.99.144.133 | compute | IDLE | 2 (system only) |

### Cost
- Total: $944/month
- 7 idle nodes = ~$784/month doing nothing

---

## Questions To Resolve

### 1. What should idle compute nodes do?

Options to discuss:
- [ ] Run trading algorithms
- [ ] Run Claude sessions for parallel tasks
- [ ] Run market data collection
- [ ] Run backtesting
- [ ] Remain idle as backup capacity
- [ ] Other: _______________

### 2. What is ho-cli-main's purpose?

Current: Running 2 Claude sessions, one hunting for credentials
Should be: _______________

### 3. Work distribution model?

- [ ] pm-helper distributes tasks to compute nodes
- [ ] Each node runs independent workloads
- [ ] Compute nodes are standby only
- [ ] Other: _______________

---

## Proposed Architecture

**To be filled in after coordination discussion**

---

## How To Contribute

1. Read this document
2. Add your thoughts via messages.jsonl
3. Do NOT make infrastructure changes
4. Wait for user approval on any plan

---

## Message Format for Discussion

```json
{
  "from": "claude-code@[node-name]",
  "to": "all",
  "type": "plan_input",
  "message": "Your thoughts on cluster architecture",
  "context": {"section": "idle_nodes|ho_cli_main|work_distribution"}
}
```
