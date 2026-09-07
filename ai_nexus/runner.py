#!/usr/bin/env python3
"""Provider-agnostic durable task dispatcher; providers are lazy and optional."""
import argparse
import importlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

PROVIDER_IMPORTS = {"chatgpt": ("ai_nexus.provider_chatgpt", "ChatGPTProvider"), "claude": ("ai_nexus.provider_claude", "ClaudeProvider"), "copilot": ("ai_nexus.provider_copilot", "CopilotProvider")}

class AIRunner:
    def __init__(self, tasks_dir: str = "./tasks", output_dir: str = "./output"):
        self.tasks_dir, self.output_dir = Path(tasks_dir), Path(output_dir)
        self.processed_tasks, self.providers = set(), {}
        self.tasks_dir.mkdir(parents=True, exist_ok=True); self.output_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _provider(self, name: str) -> Optional[Any]:
        if name in self.providers: return self.providers[name]
        spec = PROVIDER_IMPORTS.get(name)
        if spec is None: return None
        try:
            provider = getattr(importlib.import_module(spec[0]), spec[1])()
            self.providers[name] = provider
            return provider
        except Exception as exc:
            self.logger.warning("Provider %s unavailable: %s", name, exc)
            return None

    def load_task(self, task_file: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(task_file, encoding="utf-8") as f: task = json.load(f)
            return task if "provider" in task and "prompt" in task else None
        except (json.JSONDecodeError, OSError): return None

    def execute_task(self, task_file: Path, task: Dict[str, Any]) -> Dict[str, Any]:
        name, provider = task["provider"], self._provider(task["provider"])
        if provider is None: return {"success": False, "error": f"Provider {name!r} unavailable", "provider": name}
        try:
            result = provider.run_task(task); result["task_file"] = task_file.name; result["timestamp"] = datetime.utcnow().isoformat(); return result
        except Exception as exc:
            return {"success": False, "error": str(exc), "provider": name, "task_file": task_file.name, "timestamp": datetime.utcnow().isoformat()}

    def save_result(self, task_file: Path, result: Dict[str, Any]):
        with open(self.output_dir / f"{task_file.stem}_result.json", "w", encoding="utf-8") as f: json.dump(result, f, indent=2, ensure_ascii=False)

    def process_tasks(self, once=False):
        while True:
            for path in self.tasks_dir.glob("*.json"):
                if path in self.processed_tasks: continue
                task = self.load_task(path)
                if task is not None: self.save_result(path, self.execute_task(path, task))
                self.processed_tasks.add(path)
            if once: return
            time.sleep(5)

def main():
    p = argparse.ArgumentParser(); p.add_argument("--once", action="store_true"); p.add_argument("--tasks-dir", default="./tasks"); p.add_argument("--output-dir", default="./output"); a = p.parse_args(); AIRunner(a.tasks_dir, a.output_dir).process_tasks(a.once)

if __name__ == "__main__": main()
