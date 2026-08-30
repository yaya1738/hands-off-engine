"""Bounded local Ollama agent invocation for factory canary edits."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

from . import validator


@dataclass(frozen=True)
class BoundedTask:
    allowed_path: str
    allowed_contents: frozenset[str]
    write_content: str

    def prompt(self) -> str:
        return ('You are a bounded coding agent. Return ONLY one valid JSON object, '
                'with exactly {"path":"' + self.allowed_path + '","content":"' +
                self.write_content.replace("\n", "\\n") + '"}. Do not execute or propose shell commands.')


def run_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    result = subprocess.run(["ollama", "run", model, prompt], capture_output=True, text=True, timeout=timeout, check=True)
    return result.stdout


def execute_bounded_edit(model: str, task: BoundedTask) -> dict:
    data = validator.extract_authorized_edit(run_ollama(model, task.prompt()), task.allowed_path, set(task.allowed_contents))
    if data is None:
        raise SystemExit("No authorized JSON edit found in agent response.")
    validator.apply_edit(data, task.write_content, allowed_path=task.allowed_path, allowed_contents=set(task.allowed_contents))
    return data


def prove_local_execution(model: str, expected: str = "FACTORY_OLLAMA_READY") -> bool:
    for _ in range(3):
        try:
            if run_ollama(model, "Reply with exactly: " + expected).strip() == expected:
                return True
        except subprocess.CalledProcessError:
            pass
    return False
