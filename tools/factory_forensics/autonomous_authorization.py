from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable

from tools.factory_forensics.autonomous_change_policy import ChangePolicyDecision, evaluate_change


POLICY_VERSION = "dass-preauthorization-v1"
AUTONOMOUS_ACTOR = "github-actions[bot]"
AUTONOMOUS_BRANCH_PREFIX = "autonomous-factory/"
READINESS_CHECK = "Autonomous Readiness Attestation"


@dataclass(frozen=True)
class AuthorizationEnvelope:
    permitted: bool
    actor: str
    branch: str
    policy_version: str
    policy_hash: str
    readiness: str
    financial_approval: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "permitted": self.permitted,
            "actor": self.actor,
            "branch": self.branch,
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "readiness": self.readiness,
            "financial_approval": self.financial_approval,
            "reasons": list(self.reasons),
        }


def _policy_hash() -> str:
    payload = {
        "version": POLICY_VERSION,
        "actor": AUTONOMOUS_ACTOR,
        "branch_prefix": AUTONOMOUS_BRANCH_PREFIX,
        "readiness_check": READINESS_CHECK,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def evaluate_authorization(
    *,
    actor: str,
    branch: str,
    paths: Iterable[str],
    additions: int = 0,
    deletions: int = 0,
    readiness: str = "missing",
    financial_approval: bool = False,
) -> AuthorizationEnvelope:
    reasons: list[str] = []
    if actor != AUTONOMOUS_ACTOR:
        reasons.append("actor is not the autonomous Factory identity")
    if not branch.startswith(AUTONOMOUS_BRANCH_PREFIX):
        reasons.append("branch is outside the autonomous Factory namespace")

    policy: ChangePolicyDecision = evaluate_change(paths, additions, deletions)
    reasons.extend(policy.reasons)
    if readiness != "pass":
        reasons.append(f"readiness attestation is not passing: {readiness}")

    return AuthorizationEnvelope(
        permitted=not reasons,
        actor=actor,
        branch=branch,
        policy_version=POLICY_VERSION,
        policy_hash=_policy_hash(),
        readiness=readiness,
        financial_approval=financial_approval,
        reasons=tuple(dict.fromkeys(reasons)),
    )
