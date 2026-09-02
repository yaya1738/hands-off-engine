# Remaining Authority Audit — 2026-09-02

## Current status

The Factory Authority boundary now covers the previously identified legacy approval, autonomous proposal, autopilot control-server, AI-runner, and self-repair shell-execution paths.

## Remaining high-risk legacy authority

`infrastructure/selfheal.py` still contains direct mutation/execution paths outside `FactoryAuthorityGateway`:

- `_restart_service()` executes configuration-derived `systemctl` commands with `shell=True`.
- `_cleanup_old_files()` constructs `find` commands from configured glob patterns and deletes discovered files.
- `_restore_from_backup()` directly overwrites state files with `shutil.copy2()`.
- `_clear_locks()` executes `find ... -delete` with `shell=True`.

`autonomous/self_healer.py` also contains direct process/service restart behavior, including process termination and detached process creation.

## Required remediation

These paths should either be migrated to an explicitly authorized Factory capability or fail closed as record-only operations. No direct self-healing mutation should remain as an independent authority.

## Verification requirement

Add regression tests that prove the legacy self-healing entrypoints cannot invoke process/service/file mutation independently of `FactoryAuthorityGateway`.

This document intentionally does not claim the remaining self-healing authority is fixed; it records the verified gap so the next hardening cycle has a precise target.