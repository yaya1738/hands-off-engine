#!/usr/bin/env python3
"""AI Nexus task runner with optional, lazy AI-provider loading.

The autonomous system does not depend on the regular human-to-ChatGPT UI.
Providers are loaded only when a task explicitly selects one; an unavailable
provider therefore cannot prevent the runner/control plane from starting.
"""

import importlib
import json
import logging
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class AIRunner:
    """Orchestrates explicitly requested AI providers without eager loading."""

    def __init__(self, tasks_dir: str = "./tasks", output_dir: str = "./output"):
        self.tasks_dir = Path(tasks_dir)
        self.output_dir = Path(output_dir)
        self.processed_tasks = set()
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.providers: Dict[str, Any] = {}

    def _load_provider(self, provider_name: str):
        """Load a provider only when a task explicitly requests it."""
        if provider_name in self.providers:
            return self.providers[provider_name]
        provider_modules = {
            "chatgpt": ("ai_nexus.provider_chatgpt", "ChatGPTProvider"),
            "claude": ("ai_nexus.provider_claude", "ClaudeProvider"),
        }
        spec = provider_modules.get(provider_name)
        if spec is None:
            return None
        module_name, class_name = spec
        try:
            module = importlib.import_module(module_name)
            provider = getattr(module, class_name)()
            self.providers[provider_name] = provider
            return provider
        except Exception as exc:
            self.logger.warning("Failed to initialize provider %s: %s", provider_name, exc)
            return None

    def load_task(self, task_file: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                task = json.load(f)
            if "provider" not in task or "prompt" not in task:
                self.logger.error("Task %s missing required fields", task_file.name)
                return None
            return task
        except (json.JSONDecodeError, OSError) as exc:
            self.logger.error("Failed to load %s: %s", task_file.name, exc)
            return None

    def execute_task(self, task_file: Path, task: Dict[str, Any]) -> Dict[str, Any]:
        provider_name = task["provider"]
        provider = self._load_provider(provider_name)
        if provider is None:
            return {"success": False, "error": f"Provider unavailable: {provider_name}", "provider": provider_name}
        try:
            result = provider.run_task(task)
            result["task_file"] = task_file.name
            result["timestamp"] = datetime.utcnow().isoformat()
            return result
        except Exception as exc:
            self.logger.error("Task execution failed: %s", exc)
            return {"success": False, "error": str(exc), "provider": provider_name,
                    "task_file": task_file.name, "timestamp": datetime.utcnow().isoformat()}

    def save_result(self, task_file: Path, result: Dict[str, Any]):
        output_file = self.output_dir / f"{task_file.stem}_result.json"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except OSError as exc:
            self.logger.error("Failed to save result for %s: %s", task_file.name, exc)

    def process_tasks(self, once: bool = False):
        while True:
            for task_file in self.tasks_dir.glob("*.json"):
                if task_file in self.processed_tasks:
                    continue
                task = self.load_task(task_file)
                if task is None:
                    self.processed_tasks.add(task_file)
                    continue
                result = self.execute_task(task_file, task)
                self.save_result(task_file, result)
                self.processed_tasks.add(task_file)
            if once:
                return
            time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="AI Nexus Task Runner")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--tasks-dir", default="./tasks")
    parser.add_argument("--output-dir", default="./output")
    args = parser.parse_args()
    AIRunner(args.tasks_dir, args.output_dir).process_tasks(once=args.once)


if __name__ == "__main__":
    main()
