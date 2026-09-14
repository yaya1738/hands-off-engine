# DASS autonomous heartbeat

The DASS heartbeat is intentionally bounded and fail-closed.

- `autonomous/dass_heartbeat.py` performs one authorization/observation cycle and exits.
- It never enables LIVE execution.
- `.github/workflows/dass-heartbeat.yml` schedules the bounded cycle every 15 minutes.
- Runtime `state/` remains ephemeral on GitHub-hosted runners; durable production state must remain on the governed execution host or another explicitly durable store.
- The existing long-lived `autonomous/governed_root.py` remains the host-side authority observer.

This separation prevents the GitHub-hosted heartbeat from being mistaken for production execution authority.
