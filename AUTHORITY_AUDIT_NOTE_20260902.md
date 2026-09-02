# Authority audit checkpoint — 2026-09-02

The legacy `FactoryValidationRunner` and `FactoryChangeValidation` execution helpers have been converted to non-executing compatibility facades. They no longer invoke subprocesses or shell commands. Validation execution must enter through the governed Factory authority/CI path.

This checkpoint is intentionally documentation-only and does not grant execution authority.
