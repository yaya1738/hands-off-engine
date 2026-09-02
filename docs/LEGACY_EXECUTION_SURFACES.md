# Legacy execution surfaces

The legacy `autonomous/state_sync.py` implementation was removed because it could perform direct remote `scp`/`ssh` operations, including invoking a remote Python command, outside the canonical Factory authority gateway.

The repository's canonical privileged execution boundary is the Factory authority layer. Legacy compatibility code must not retain an independent remote mutation path.

A regression test asserts that the removed module does not return to the tree, and the Factory authority regression workflow executes that test when autonomous surfaces change.
