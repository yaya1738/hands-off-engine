# Human capability boundary

This module defines the public policy boundary for named non-owner human
identities without publishing their contact details.

Current persisted policy:
- David Kaplan: `communicate`
- Carol Kaplan: `communicate`

The runtime may provide private identity/contact records through
`/root/hands-off-engine/security/human_identity_registry.json`.
Those records are deliberately not committed to the public repository.

The capability boundary is deny-by-default for unknown identities. Communication
does not imply access to commands, trading, approvals, credentials, code
execution, or system administration.

The existing owner identity retains its separate master authorization path.
