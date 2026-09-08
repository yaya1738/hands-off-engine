from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


# A machine-pre-authorized change is deliberately narrower than the full
# autonomous development surface. It is a policy decision, not an authority
# grant: GitHub permissions and the existing authority gateway remain binding.
ALLOWED_PREFIXES = ("ai/", "tools/", "scripts/", "tests/")
PROTECTED_PREFIXES = (
    ".github/",
    "state/",
    "config/",
    "infra/",
    "autonomous/",
    "secrets/",
    "credentials/",
)
PROTECTED_TERMS = (
    "finance",
    "financial",
    "trading",
    "polymarket",
    "live_trading",
    "executor",
    "wallet",
    "credential",
    "secret",
)
MAX_FILES = 8
MAX_ADDITIONS = 600
MAX_DELETIONS = 250


@dataclass(frozen=True)
class ChangePolicyDecision:
    permitted: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {"permitted": self.permitted, "reasons": list(self.reasons)}


def evaluate_change(
    paths: Iterable[str],
    additions: int = 0,
    deletions: int = 0,
) -> ChangePolicyDecision:
    normalized = tuple(sorted({str(path).strip().lstrip("./") for path in paths if str(path).strip()}))
    reasons: list[str] = []

    if not normalized:
        reasons.append("no changed files")
    if len(normalized) > MAX_FILES:
        reasons.append(f"changed file count exceeds {MAX_FILES}")
    if additions > MAX_ADDITIONS:
        reasons.append(f"additions exceed {MAX_ADDITIONS}")
    if deletions > MAX_DELETIONS:
        reasons.append(f"deletions exceed {MAX_DELETIONS}")

    for path in normalized:
        lower = path.casefold()
        if not lower.startswith(ALLOWED_PREFIXES):
            reasons.append(f"path outside autonomous development surface: {path}")
        if lower.startswith(PROTECTED_PREFIXES):
            reasons.append(f"protected path: {path}")
        if any(term in lower for term in PROTECTED_TERMS):
            reasons.append(f"protected semantic path: {path}")

    return ChangePolicyDecision(not reasons, tuple(dict.fromkeys(reasons)))
