"""Bounded local Ollama agent invocation for factory canary edits.

Extracted from .github/workflows/factory-ollama-canary.yml (commit 5226635)
so the same model-invocation pattern used in the validated GitHub Actions
canary can run outside CI, on self-hosted infrastructure.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

from . import validator


@dataclass(frozen=True)
class BoundedTask:
    allowed_path: str
    allowed_contents: frozenset
    write_content: str

    def prompt(self) -> str:
        return (
            "You are a bounded coding agent. Return ONLY one valid JSON "
            "object, with no markdown and no extra text, in exactly this "
            "schema:\n"
            '{"path":"' + self.allowed_path + '","content":"'
            + self.write_content.replace("\n", "\\n") + '"}\n'
            "The requested change is to create that one file with "
            "exactly that content. You are not being asked to execute "
            "shell commands. Do not propose commands. Do not include "
            "any other file or field."
        )


def run_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    """Invoke a local Ollama model and return its raw stdout output."""
    result = subprocess.run(
        ["ollama", "run", model, prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    return result.stdout


def execute_bounded_edit(model: str, task: BoundedTask) -> dict:
    """Run the model, extract the authorized edit, and apply it."""
    raw_output = run_ollama(model, task.prompt())
    data = validator.extract_authorized_edit(
        raw_output,
        allowed_path=task.allowed_path,
        allowed_contents=set(task.allowed_contents),
    )
    if data is None:
        raise SystemExit("No authorized JSON edit found in agent response.")
    validator.apply_edit(data, task.write_content)
    return data


def prove_local_execution(model: str, expected: str = "FACTORY_OLLAMA_READY") -> bool:
    """Mirror the 'Prove local model execution' canary step."""
    result = run_ollama(model, "Reply with exactly: " + expected).strip()
    return result == expected
