import json
import urllib.request
from typing import Any, Dict


class OllamaLocalAgent:
    """Small transport adapter for a locally running Ollama model.

    It only returns the model result. File mutation remains the responsibility
    of the bounded execution layer, keeping transport and authorization
    separate.
    """

    def __init__(self, model: str = "qwen2.5-coder:0.5b", endpoint: str = "http://127.0.0.1:11434/api/generate", timeout: int = 300):
        self.model = model
        self.endpoint = endpoint
        self.timeout = timeout

    def __call__(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        task = envelope["task"]
        allowed_paths = envelope["allowed_paths"]
        prompt = self._prompt(task, allowed_paths)
        body = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode()
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.load(response)

        result = payload.get("response")
        if not isinstance(result, str) or not result.strip():
            raise ValueError("Ollama returned no usable response")

        return {"status": "agent_completed", "response": result.strip(), "model": self.model}

    @staticmethod
    def _prompt(task: Dict[str, Any], allowed_paths) -> str:
        return (
            "You are a bounded autonomous coding agent.\n"
            f"Objective: {task.get('objective') or task.get('goal') or 'complete the assigned task'}\n"
            f"Authorized paths: {', '.join(allowed_paths) or '(none)'}\n"
            "Do not modify or propose changes outside the authorized paths.\n"
            "Return only the structured result requested by the caller."
        )
