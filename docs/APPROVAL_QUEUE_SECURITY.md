# Approval Queue Execution Boundary

Approval IDs are not a general-purpose shell or host-file-write capability.

- Arbitrary bash_command proposals are never executed by ApprovalQueue, even after approval.
- edit_file and write_file paths must resolve inside the configured repository root; absolute paths outside the repo, traversal, and symlink escapes are rejected.
- write_file is create-only and refuses to overwrite an existing file.
- edit_file requires a non-empty exact old-content match against an existing regular file.
- Telegram pending-approval views and notifications include description, files affected, action type, and target path, but never expose file contents.
- Risky execution should use the governed executor allowlist rather than a shell string.

This boundary protects both Telegram approval entrypoints and local autonomous_change callers. Approval is still an explicit authorization step; it does not bypass path or action validation.
