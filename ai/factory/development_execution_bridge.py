"""GitHub-side execution request bridge for Factory development tasks.

This module intentionally stops at an auditable request. A separate coding
agent is responsible for repository mutation and must return a branch/PR plus
validation evidence. The Factory remains the merge authority.
"""

from __future__ import annotations

from typing import Any, Dict


class GitHubDevelopmentRequestSink:
    """Protocol-level sink description used by the external integration.

    The concrete GitHub transport is injected by the runtime/host. Keeping the
    transport out of the Factory core prevents credentials and network effects
    from becoming implicit capabilities of development tasks.
    """

    def __init__(self, transport):
        self.transport = transport

    def submit(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return self.transport.submit_development_request(request)
