# Cascade Failure Analysis - 2025-11-28

## Summary
System experienced runaway process spawning causing load average to spike to 228+.

## Root Cause
1. `ho-health.timer` runs every 5 minutes
2. `healthcheck.sh` calls `master_orchestrator.py` (line 87)
3. Under high load, healthcheck.sh doesn't complete before next timer fires
4. New instances stack up, each spawning orchestrator
5. Load increases → things take longer → more stacking → cascade

## Evidence
- 340+ healthcheck.sh processes running simultaneously
- 400+ master_orchestrator.py processes (orphaned, parent=1)
- Load average peaked at 228
- Parent of newest orchestrator traced to healthcheck.sh

## The Trigger Chain
```
ho-health.timer (every 5min)
  → ho-health.service
    → healthcheck.sh
      → master_orchestrator.py (line 87)
```

## Why It Cascaded
- No process locking/mutex on healthcheck.sh
- No timeout on orchestrator call
- Timer fires regardless of previous run completion
- High load makes each run slower, compounding the problem

## Fix Options
1. Add flock/mutex to healthcheck.sh to prevent concurrent runs
2. Remove orchestrator call from healthcheck (it's not a health check)
3. Add timeout to orchestrator invocation
4. Use systemd's `RefuseManualStart=` or process limits

## Self-Recovery
System eventually self-corrected as processes completed/died faster than spawning.
Load dropped from 228 → 100 over ~10 minutes.

## Lesson
Health checks should be fast and idempotent. Don't call heavy orchestration from health checks.
