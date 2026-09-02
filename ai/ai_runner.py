#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# Directories
TASKS_DIR = Path("/root/hands-off/ai/tasks")
RESULTS_DIR = Path("/root/hands-off/ai/results")
PROCESSED_DIR = Path("/root/hands-off/ai/processed")
LOG_DIR = Path("/root/hands-off-out/ai")

# Environment variables
API_URL = os.getenv("AI_RUNNER_API_URL", "")
API_KEY = os.getenv("AI_RUNNER_API_KEY", "")
MODEL = os.getenv("AI_RUNNER_MODEL", "anthropic/claude-3.5-sonnet")
EXECUTE = os.getenv("AI_RUNNER_EXECUTE", "0") == "1"

# Allowed write paths
ALLOWED_PATHS = [
    "/usr/local/bin",
    "/root/hands-off",
    "/root/hands-off-out"
]

# Dangerous patterns retained for compatibility with the legacy planner.
DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "dd if=",
    "mkfs",
    ":(){ :|:& };:",
    "> /dev/sd",
    "curl | sh",
    "wget | sh",
]

# Setup logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "ai-runner.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def validate_command(cmd):
    """Validate a planned command for compatibility/reporting only."""
    cmd_lower = cmd.lower().strip()

    for pattern in DANGEROUS_PATTERNS:
        if pattern in cmd_lower:
            return False, f"Dangerous pattern detected: {pattern}"

    if any(op in cmd_lower for op in ["touch", "mkdir", "cp", "mv", ">"]):
        for part in cmd.split():
            if part.startswith("/") and not any(part.startswith(allowed) for allowed in ALLOWED_PATHS):
                return False, f"Write to disallowed path: {part}"

    return True, "OK"


def read_file_safe(path):
    """Read file contents safely."""
    try:
        p = Path(path)
        if not p.exists():
            return f"[FILE NOT FOUND: {path}]"
        if p.stat().st_size > 1_000_000:
            return f"[FILE TOO LARGE: {path}]"
        return p.read_text()
    except Exception as e:
        return f"[ERROR READING {path}: {e}]"


def call_llm(system_prompt, user_prompt):
    """Call LLM API and return JSON response."""
    if not API_URL or not API_KEY:
        raise ValueError("AI_RUNNER_API_URL and AI_RUNNER_API_KEY must be set")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()

    if "choices" in data:
        content = data["choices"][0]["message"]["content"]
    elif "content" in data:
        if isinstance(data["content"], list):
            content = data["content"][0].get("text", "")
        else:
            content = data["content"]
    else:
        raise ValueError(f"Unexpected API response format: {data}")

    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    return json.loads(content.strip())


def execute_command(cmd):
    """Legacy execution authority is permanently disabled.

    Execution must enter through FactoryAuthorityGateway, where approval,
    journaling, reconciliation, and runtime policy are enforced.
    """
    logger.warning("Blocked legacy AI-runner execution; use FactoryAuthorityGateway")
    return {
        "command": cmd,
        "status": "blocked",
        "stdout": "",
        "stderr": "legacy_ai_runner_execution_disabled",
        "returncode": -1,
        "authority": "FactoryAuthorityGateway",
    }


def process_task(task_file):
    """Process a single task file."""
    task_id = task_file.stem
    logger.info(f"Processing task: {task_id}")

    started_at = datetime.utcnow().isoformat()

    try:
        task = json.loads(task_file.read_text())
        task_id = task.get("id", task_id)
        goal = task.get("goal", "")
        context = task.get("context", {})
        mode = task.get("mode", "plan-and-execute")

        logger.info(f"Task {task_id}: {goal}")

        file_contents = []
        for file_path in context.get("files", []):
            content = read_file_safe(file_path)
            file_contents.append(f"=== {file_path} ===\n{content}\n")

        system_prompt = (
            "You are an infrastructure coding agent. "
            "Respond ONLY with JSON containing a high-level plan and a list of shell commands. "
            "No prose. Format: {\"plan\": \"...\", \"commands\": [\"cmd1\", \"cmd2\", ...]}"
        )

        user_prompt = f"""GOAL: {goal}

MODE: {mode}

CONTEXT FILES:
{''.join(file_contents)}

NOTES: {context.get('notes', 'None')}

Provide a plan and shell commands to accomplish this goal."""

        logger.info(f"Calling LLM with model {MODEL}")
        llm_response = call_llm(system_prompt, user_prompt)

        plan = llm_response.get("plan", "")
        commands = llm_response.get("commands", [])

        logger.info(f"Plan: {plan}")
        logger.info(f"Commands: {len(commands)}")

        command_results = []
        overall_status = "ok"

        for cmd in commands:
            valid, reason = validate_command(cmd)
            if not valid:
                logger.error(f"Command validation failed: {reason}")
                command_results.append({
                    "command": cmd,
                    "status": "validation_failed",
                    "reason": reason,
                    "stdout": "",
                    "stderr": "",
                    "returncode": -1
                })
                overall_status = "failed"
                continue

            if EXECUTE:
                result = execute_command(cmd)
                command_results.append(result)
                if result["status"] != "success":
                    overall_status = "failed"
            else:
                logger.info(f"DRY RUN (AI_RUNNER_EXECUTE not set): {cmd}")
                command_results.append({
                    "command": cmd,
                    "status": "dry_run",
                    "stdout": "",
                    "stderr": "",
                    "returncode": 0
                })

        finished_at = datetime.utcnow().isoformat()

        result = {
            "id": task_id,
            "status": overall_status,
            "plan": plan,
            "commands": commands,
            "command_results": command_results,
            "started_at": started_at,
            "finished_at": finished_at
        }

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        result_file = RESULTS_DIR / f"{task_id}.result.json"
        result_file.write_text(json.dumps(result, indent=2))

        logger.info(f"Task {task_id} completed with status: {overall_status}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        task_file.rename(PROCESSED_DIR / task_file.name)

    except Exception as e:
        logger.error(f"Task {task_id} failed with exception: {e}", exc_info=True)

        finished_at = datetime.utcnow().isoformat()

        result = {
            "id": task_id,
            "status": "failed",
            "error": str(e),
            "started_at": started_at,
            "finished_at": finished_at
        }

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        result_file = RESULTS_DIR / f"{task_id}.result.json"
        result_file.write_text(json.dumps(result, indent=2))

        try:
            PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
            task_file.rename(PROCESSED_DIR / task_file.name)
        except Exception:
            pass


def main():
    """Main loop."""
    logger.info("AI Runner started")
    logger.info(f"API URL: {API_URL}")
    logger.info(f"Model: {MODEL}")
    logger.info(f"Execute mode: {EXECUTE}")

    if not API_URL or not API_KEY:
        logger.warning("AI_RUNNER_API_URL or AI_RUNNER_API_KEY not set - will fail on first task")

    while True:
        try:
            TASKS_DIR.mkdir(parents=True, exist_ok=True)
            task_files = sorted(TASKS_DIR.glob("*.json"))

            if task_files:
                logger.info(f"Found {len(task_files)} task(s)")
                for task_file in task_files:
                    process_task(task_file)

            time.sleep(7)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
            time.sleep(10)


if __name__ == "__main__":
    main()
