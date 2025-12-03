# Race Condition Fix - decision_report.json - 2025-11-28

## Summary
`decision_report.json` was corrupted by concurrent writes from multiple scripts. Two partial JSONs were concatenated, making the file unparseable.

## Root Cause
Multiple scripts write to the same file without coordination:
- `ho-decision-infra.py` (timer: every 2 min)
- `ho-market-scanner.py` (timer: every 15 min)
- `decision_enricher.py` (path watcher)

When timers align (e.g., at :00 and :30), concurrent writes cause VFS race:
1. Script A opens file, truncates, starts writing
2. Script B opens file, truncates, starts writing
3. Smaller write doesn't shrink file
4. Result: partial JSON from A + tail of JSON from B = unparseable

## Evidence
The corrupt file (`decision_report.json.corrupt_backup_20251128`) shows concatenation at byte ~9045:
```
}s": [],
    "reason": "DRYRUN mode...
```
The `}s": [],` is where two JSONs merged.

## Fix Applied
Added atomic writes to all three scripts (write to `.tmp`, then `replace()`):

### ho-decision-infra.py (lines 116-119)
```python
tmp = DECISION.with_suffix(".json.tmp")
tmp.write_text(json.dumps(base, indent=2, sort_keys=True))
tmp.replace(DECISION)
```

### ho-market-scanner.py (lines 108-111, 118-120, 203-205, 213-215)
```python
tmp = SCANNER_PATH.with_suffix(".json.tmp")
tmp.write_text(json.dumps(scanner, indent=2), encoding="utf-8")
tmp.replace(SCANNER_PATH)
```

### decision_enricher.py (lines 67-74)
```python
tmp_path = decision_path.with_suffix(".json.tmp")
with tmp_path.open("w", encoding="utf-8") as f:
    json.dump(decision, f, indent=2)
tmp_path.replace(decision_path)
```

## Scripts Location
These scripts are in `/usr/local/bin/` and `/root/`, NOT in the repo. Fixes applied to live system but not version controlled.

## Monitoring Gap
No check existed for JSON validity. Self-healing checks freshness (age) but not parseability.

## Recommendation
1. Copy fixed scripts to repo under `scripts/` or `bin/`
2. Add JSON validity check to self-healing agent
3. Add check that scripts writing shared state use atomic writes

## Timeline
- Nov 22 00:00:01 - Corruption occurred (timer alignment at midnight)
- Nov 22-28 - Scripts failed silently (6 days undetected)
- Nov 28 ~09:xx - Cascade failure investigation led to discovery
- Nov 28 10:57 - Atomic writes added to scripts

## Related
- `docs/claude/CASCADE_FAILURE_2025-11-28.md` - separate issue (healthcheck stacking)
- `docs/DEVELOPMENT_STANDARDS.md` - line 2728 mandates atomic writes
- `docs/SYSTEM_ASSUMPTIONS.md` - documents file coordination assumptions
