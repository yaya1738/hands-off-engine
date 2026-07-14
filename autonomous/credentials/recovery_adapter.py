"""
Hands-Off Credential Recovery Adapter Contract
"""

from abc import ABC, abstractmethod


class RecoveryAdapter(ABC):
    """
    Interface for provider-specific credential recovery.
    """

    @abstractmethod
    def recover(self, identity):
        """
        Attempt external credential recovery.

        Returns recovery result only.
        Lifecycle decides state changes.
        """
        pass
