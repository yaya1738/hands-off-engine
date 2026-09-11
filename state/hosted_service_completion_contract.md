# Hosted autonomous service and DASS live-state contract

The hosted autonomous service is the canonical GitHub-native DASS runtime. A separate physical/cloud host is not required to establish DASS.

A cycle establishes **runtime liveness** only when the governed supervisor actually completes a cycle and persists a fresh, unexpired `live_attestation` whose mechanism is `governed_autonomous_supervisor_cycle`.

A cycle establishes **DASS live state** only when both conditions hold:

1. the authoritative DASS structural measurement is 100% pure, fully classified, and has no operational-unclassified paths, unmapped active files, or quarantined imports; and
2. the fresh runtime attestation represents either:
   - `operating_state == live_executing` with `execution_observed == true` and `execution_succeeded == true`, or
   - `operating_state == live_steady_state` with `converged == true` and `execution_succeeded == false`.

`converged` means healthy autonomous steady-state operation. It never means dormant, stopped, or merely unchanged code.

A stale committed state file, historical successful run, source-only measurement, failed objective, or green workflow without the persisted runtime attestation cannot establish DASS live state.

External production authority and live financial mutation remain separately governed and fail-closed. This contract does not grant additional mutation authority.
