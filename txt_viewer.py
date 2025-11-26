"""
Text Viewer API for Hands-Off Engine

Provides human-readable text endpoints for monitoring system state.

Endpoints:
    /txt/kernels - Spark Plug kernel status and refresh history

Run:
    uvicorn txt_viewer:app --host 0.0.0.0 --port 8765
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(title="Hands-Off Engine Text Viewer")

# Paths
REPO_ROOT = Path(__file__).parent
CONFIG_DIR = REPO_ROOT / "ai" / "config"
RESULTS_DIR = REPO_ROOT / "ai" / "results"
KERNELS_DIR = REPO_ROOT / "ai" / "memory" / "kernels"
SPARKPLUG_CONFIG = CONFIG_DIR / "sparkplug_kernels.json"


def load_sparkplug_config() -> List[Dict]:
    """Load configured kernels from sparkplug_kernels.json"""
    if not SPARKPLUG_CONFIG.exists():
        return []

    try:
        with open(SPARKPLUG_CONFIG) as f:
            config = json.load(f)
        return config.get("kernels", [])
    except Exception:
        return []


def find_latest_result_for_kernel(kernel_id: str) -> Optional[Dict]:
    """
    Find the most recent Spark Plug result containing this kernel

    Returns the per-kernel result dict, or None if not found
    """
    if not RESULTS_DIR.exists():
        return None

    # Find all sparkplug result files, sorted by timestamp (newest first)
    result_files = sorted(
        RESULTS_DIR.glob("sparkplug_autokernel_refresh_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    for result_file in result_files:
        try:
            with open(result_file) as f:
                result = json.load(f)

            # Look for this kernel in the kernels list
            for kernel_entry in result.get("kernels", []):
                if kernel_entry.get("kernel_id") == kernel_id:
                    # Add run_at timestamp from task level
                    kernel_result = kernel_entry.get("result", {})
                    kernel_result["task_run_at"] = result.get("run_at")
                    return kernel_result
        except Exception:
            continue

    return None


def format_timestamp(ts_str: Optional[str]) -> str:
    """Format ISO timestamp to readable string"""
    if not ts_str:
        return "-"

    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts_str


def extract_suggestion_summary(result: Dict) -> str:
    """Extract a short summary of CPU suggestions from result"""
    updates = result.get("updates", {})
    applied = updates.get("applied", [])

    if not applied:
        return "<none>"

    # Get first applied update
    first_update = applied[0]
    update_type = first_update.get("type", "")

    if update_type == "cpu_suggestion":
        summary = first_update.get("summary", "")
        # Shorten if too long
        if len(summary) > 80:
            summary = summary[:77] + "..."
        return summary or "<cpu_suggestion>"

    return f"<{update_type}>"


@app.get("/txt/kernels", response_class=PlainTextResponse)
async def get_kernels_status():
    """
    Display Spark Plug kernel status and refresh history

    Shows:
    - Configured kernels from ai/config/sparkplug_kernels.json
    - Latest refresh status from ai/results/
    - History event counts
    - CPU suggestions (if any)
    """
    output_lines = []
    output_lines.append("SPARK PLUG KERNELS (v0.4)")
    output_lines.append("=" * 70)
    output_lines.append("")

    # Load configured kernels
    configured_kernels = load_sparkplug_config()

    if not configured_kernels:
        output_lines.append("No kernels configured in ai/config/sparkplug_kernels.json")
        return "\n".join(output_lines)

    # Process each kernel
    for kernel_config in configured_kernels:
        kernel_id = kernel_config.get("kernel_id", "unknown")
        enabled = kernel_config.get("enabled", False)
        notes = kernel_config.get("notes", "")

        output_lines.append(f"Kernel: {kernel_id}")
        output_lines.append(f"Enabled: {'yes' if enabled else 'no'}")

        if notes:
            output_lines.append(f"Notes: {notes}")

        # Find latest result
        latest_result = find_latest_result_for_kernel(kernel_id)

        if latest_result is None:
            output_lines.append("Status: never_run")
            output_lines.append("Last refresh: -")
            output_lines.append("History: 0 items")
            output_lines.append("Suggestion: <none>")
        else:
            status = latest_result.get("status", "unknown")
            task_run_at = latest_result.get("task_run_at")
            history = latest_result.get("history", {})

            items_seen = history.get("items_seen", 0)
            items_used = history.get("items_used", 0)
            time_range = history.get("time_range", {})
            time_start = time_range.get("start")
            time_end = time_range.get("end")

            output_lines.append(f"Status: {status}")
            output_lines.append(f"Last refresh: {format_timestamp(task_run_at)}")
            output_lines.append(f"History: {items_seen} items ({items_used} used)")

            if time_start and time_end:
                output_lines.append(
                    f"Time range: {format_timestamp(time_start)} → {format_timestamp(time_end)}"
                )

            suggestion = extract_suggestion_summary(latest_result)
            output_lines.append(f"Suggestion: {suggestion}")

        output_lines.append("")

    # Add summary footer
    total_kernels = len(configured_kernels)
    enabled_kernels = sum(1 for k in configured_kernels if k.get("enabled", False))

    output_lines.append("=" * 70)
    output_lines.append(f"Total kernels: {total_kernels} ({enabled_kernels} enabled)")
    output_lines.append("")

    return "\n".join(output_lines)


@app.get("/health", response_class=PlainTextResponse)
async def health_check():
    """Basic health check endpoint"""
    return "OK"


@app.get("/", response_class=PlainTextResponse)
async def root():
    """Root endpoint with available routes"""
    return """
Hands-Off Engine Text Viewer
=============================

Available endpoints:
  GET /txt/kernels - Spark Plug kernel status
  GET /health      - Health check
  GET /            - This help message
"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
