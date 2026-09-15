from typing import Any, Dict, Optional


class FactoryDecisionContextObserver:
    """Read-only seam for supplying an already-derived Factory decision context."""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        self._context = context if isinstance(context, dict) else None

    def observe(self) -> Dict[str, Any]:
        """Return a bounded context copy; never read the bus or mutate source state."""
        if not isinstance(self._context, dict):
            return {"available": False}
        return dict(self._context)
