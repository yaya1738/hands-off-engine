"""Fail-closed compatibility facade for the local Ollama canary agent.

Direct model-process execution and file mutation are authority operations. They
must enter through FactoryAuthorityGateway rather than this legacy helper.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import validator


@dataclass(frozen=True)
class BoundedTask:
    allowed_path: str
    allowed_contents: frozenset[str]
    write_content: str

    def prompt(self) -> str:
        return (
            'You are a bounded coding agent. Return ONLY one valid JSON object, '
            'with exactly {"path":"' + self.allowed_path + '","content":"' +
            self.write_content.replace("\n", "\\n") + '"}. Do not execute or propose shell commands.'
        )


def run_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    """Fail closed; model execution is owned by FactoryAuthorityGateway."""
    raise RuntimeError(
        "[FACTORY-AUTHORITY] direct Ollama process execution is disabled; "
        "submit through FactoryAuthorityGateway"
    )


def execute_bounded_edit(model: str, task: BoundedTask) -> dict:
    """Fail closed; model output and file mutation require governed authority."""
    raise RuntimeError(
        "[FACTORY-AUTHORITY] bounded agent execution is disabled; "
        "submit through FactoryAuthorityGateway"
    )


def prove_local_execution(model: str, expected: str = "FACTORY_OLLAMA_READY") -> bool:
    """A legacy compatibility probe cannot establish local execution authority."""
    return False
