#!/usr/bin/env python3
"""
AI Runner - Autonomous task processor for Hands-Off Engine
Monitors tasks/ directory and processes JSON task definitions
"""
import json
import time
import logging
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Directories
BASE_DIR = Path("/root/hands-off-out/ai")
TASKS_DIR = BASE_DIR / "tasks"
RESULTS_DIR = BASE_DIR / "results"
PROCESSED_DIR = BASE_DIR / "processed"
LOG_FILE = BASE_DIR / "ai_runner.log"

# Ensure directories exist
for d in [BASE_DIR, TASKS_DIR, RESULTS_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_runner")


def process_task(task_file: Path) -> Dict[str, Any]:
    """Process a single task JSON file"""
    try:
        with open(task_file, 'r') as f:
            task = json.load(f)

        task_id = task.get("task_id", task_file.stem)
        task_type = task.get("type", "unknown")
        command = task.get("command")

        logger.info(f"Processing task {task_id} (type: {task_type})")

        result = {
            "task_id": task_id,
            "task_type": task_type,
            "start_time": datetime.utcnow().isoformat() + "Z",
            "status": "unknown",
            "output": "",
            "error": ""
        }

        if not command:
            result["status"] = "error"
            result["error"] = "No command specified in task"
            return result

        # Execute command
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(BASE_DIR)
            )

            result["status"] = "success" if proc.returncode == 0 else "failed"
            result["exit_code"] = proc.returncode
            result["output"] = proc.stdout
            result["error"] = proc.stderr

            logger.info(f"Task {task_id} completed with exit code {proc.returncode}")

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = "Command execution timeout (5 minutes)"
            logger.warning(f"Task {task_id} timed out")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Task {task_id} failed: {e}")

        result["end_time"] = datetime.utcnow().isoformat() + "Z"
        return result

    except Exception as e:
        logger.error(f"Failed to process task file {task_file}: {e}")
        return {
            "task_id": task_file.stem,
            "status": "error",
            "error": f"Failed to parse task file: {str(e)}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


def save_result(task_file: Path, result: Dict[str, Any]):
    """Save task result and move task to processed"""
    task_id = result.get("task_id", task_file.stem)

    # Save result
    result_file = RESULTS_DIR / f"{task_id}_result.json"
    with open(result_file, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Result saved to {result_file}")

    # Move task to processed
    processed_file = PROCESSED_DIR / f"{task_file.name}.{int(time.time())}"
    task_file.rename(processed_file)
    logger.info(f"Task moved to {processed_file}")


def scan_and_process():
    """Scan tasks directory and process new tasks"""
    task_files = sorted(TASKS_DIR.glob("*.json"))

    for task_file in task_files:
        try:
            logger.info(f"Found task: {task_file.name}")
            result = process_task(task_file)
            save_result(task_file, result)
        except Exception as e:
            logger.error(f"Unexpected error processing {task_file}: {e}")


def main():
    """Main loop"""
    logger.info("AI Runner starting...")
    logger.info(f"Monitoring: {TASKS_DIR}")
    logger.info(f"Results: {RESULTS_DIR}")
    logger.info(f"Processed: {PROCESSED_DIR}")

    poll_interval = int(os.environ.get("AI_RUNNER_POLL_INTERVAL", "10"))

    while True:
        try:
            scan_and_process()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
