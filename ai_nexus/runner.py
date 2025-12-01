#!/usr/bin/env python3
"""
AI Nexus Runner - Multi-provider task dispatcher

This script monitors the tasks directory for new task JSON files,
dispatches them to the appropriate AI provider (ChatGPT, Claude, etc.),
and saves the results to the output directory.

Usage:
    python runner.py [--once] [--tasks-dir DIR] [--output-dir DIR]

Options:
    --once           Process existing tasks once and exit (no monitoring)
    --tasks-dir DIR  Custom tasks directory (default: ./tasks)
    --output-dir DIR Custom output directory (default: ./output)
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_nexus.provider_chatgpt import ChatGPTProvider


class AIRunner:
    """Orchestrates task execution across multiple AI providers."""

    def __init__(self, tasks_dir: str = "./tasks", output_dir: str = "./output"):
        self.tasks_dir = Path(tasks_dir)
        self.output_dir = Path(output_dir)
        self.processed_tasks = set()

        # Ensure directories exist
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            format="%(asctime)s [%(levelname)s] %(message)s",
            level=logging.INFO
        )
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize providers
        self.providers: Dict[str, Any] = {}
        self._init_providers()

    def _init_providers(self):
        """Initialize available AI providers."""
        try:
            self.providers['chatgpt'] = ChatGPTProvider()
            self.logger.info("Registered ChatGPT provider")
        except Exception as e:
            self.logger.warning(f"Failed to initialize ChatGPT provider: {e}")

        if not self.providers:
            self.logger.error("No providers available! Check your configuration.")

    def load_task(self, task_file: Path) -> Optional[Dict[str, Any]]:
        """Load and validate a task JSON file."""
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task = json.load(f)

            # Validate required fields
            if 'provider' not in task:
                self.logger.error(f"Task {task_file.name} missing 'provider' field")
                return None

            if 'prompt' not in task:
                self.logger.error(f"Task {task_file.name} missing 'prompt' field")
                return None

            return task
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {task_file.name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load task {task_file.name}: {e}")
            return None

    def execute_task(self, task_file: Path, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using the specified provider."""
        provider_name = task['provider']

        if provider_name not in self.providers:
            return {
                "success": False,
                "error": f"Unknown provider: {provider_name}",
                "provider": provider_name
            }

        self.logger.info(f"Executing task {task_file.name} with provider {provider_name}")

        try:
            provider = self.providers[provider_name]
            result = provider.run_task(task)

            # Add metadata
            result['task_file'] = task_file.name
            result['timestamp'] = datetime.utcnow().isoformat()

            return result
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider_name,
                "task_file": task_file.name,
                "timestamp": datetime.utcnow().isoformat()
            }

    def save_result(self, task_file: Path, result: Dict[str, Any]):
        """Save task result to output directory."""
        # Generate output filename
        base_name = task_file.stem  # filename without extension
        output_file = self.output_dir / f"{base_name}_result.json"

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Result saved to {output_file}")

            # Also create a human-readable text file if successful
            if result.get('success') and result.get('content'):
                text_file = self.output_dir / f"{base_name}_result.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(f"Task: {task_file.name}\n")
                    f.write(f"Provider: {result.get('provider', 'unknown')}\n")
                    f.write(f"Timestamp: {result.get('timestamp', 'unknown')}\n")
                    f.write(f"\n{'='*70}\n\n")
                    f.write(result['content'])
                    f.write(f"\n\n{'='*70}\n")
                    if 'usage' in result:
                        f.write(f"\nToken Usage: {result['usage']}\n")

                self.logger.info(f"Human-readable output saved to {text_file}")

        except Exception as e:
            self.logger.error(f"Failed to save result for {task_file.name}: {e}")

    def process_tasks(self, once: bool = False):
        """Process tasks from the tasks directory."""
        self.logger.info(f"Monitoring tasks directory: {self.tasks_dir}")

        while True:
            # Find all JSON files in tasks directory
            task_files = list(self.tasks_dir.glob("*.json"))

            for task_file in task_files:
                # Skip if already processed
                if task_file in self.processed_tasks:
                    continue

                self.logger.info(f"Found new task: {task_file.name}")

                # Load task
                task = self.load_task(task_file)
                if task is None:
                    self.processed_tasks.add(task_file)
                    continue

                # Execute task
                result = self.execute_task(task_file, task)

                # Save result
                self.save_result(task_file, result)

                # Mark as processed
                self.processed_tasks.add(task_file)

            if once:
                self.logger.info("One-time processing complete")
                break

            # Wait before checking again
            time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="AI Nexus Task Runner")
    parser.add_argument('--once', action='store_true',
                       help='Process existing tasks once and exit')
    parser.add_argument('--tasks-dir', type=str, default='./tasks',
                       help='Tasks directory (default: ./tasks)')
    parser.add_argument('--output-dir', type=str, default='./output',
                       help='Output directory (default: ./output)')

    args = parser.parse_args()

    # Create and run the runner
    runner = AIRunner(tasks_dir=args.tasks_dir, output_dir=args.output_dir)

    try:
        runner.process_tasks(once=args.once)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")


if __name__ == "__main__":
    main()
