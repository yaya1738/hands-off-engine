"""Low-overhead device-condition telemetry and task suitability for Node 1.

Unknown telemetry stays unknown. This module does not start, stop, or dispatch work.
"""
import json
import shutil
import subprocess
from pathlib import Path


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def assess_condition(snapshot):
    """Assess observed condition without treating missing data as healthy."""
    warnings = []
    concerns = []
    battery = _number(snapshot.get("battery_percent"))
    temperature = _number(snapshot.get("temperature_c"))
    memory = _number(snapshot.get("memory_available_percent"))
    disk = _number(snapshot.get("disk_free_percent"))
    charging = snapshot.get("charging")

    if battery is not None and battery <= 15 and charging is not True:
        concerns.append("low_battery")
    elif battery is not None and battery <= 25 and charging is not True:
        warnings.append("battery_low")
    if temperature is not None:
        if temperature >= 45:
            concerns.append("high_temperature")
        elif temperature >= 42:
            warnings.append("elevated_temperature")
    if memory is not None:
        if memory <= 5:
            concerns.append("memory_pressure")
        elif memory <= 10:
            warnings.append("memory_pressure")
    if disk is not None:
        if disk <= 5:
            concerns.append("low_storage")
        elif disk <= 10:
            warnings.append("storage_low")

    metric_keys = (
        "battery_percent", "charging", "temperature_c",
        "memory_available_percent", "disk_free_percent",
    )
    observed = any(snapshot.get(key) is not None for key in metric_keys)
    status = (
        "degraded" if concerns else
        "caution" if warnings else
        "normal" if observed else
        "unknown"
    )
    return {
        "status": status,
        "warnings": warnings,
        "concerns": concerns,
        "observed_metrics": [key for key in metric_keys if snapshot.get(key) is not None],
    }


def task_suitability(snapshot, task_class="routine"):
    """Conservative policy helper; does not execute or dispatch tasks."""
    condition = assess_condition(snapshot)
    reasons = list(condition["warnings"]) + list(condition["concerns"])
    if task_class not in {"routine", "intensive", "optional_intensive"}:
        return {"decision": "defer", "reasons": ["unknown_task_class"]}
    if condition["status"] == "degraded":
        if task_class == "routine":
            return {"decision": "allow", "reasons": reasons}
        return {"decision": "defer", "reasons": reasons}
    if condition["status"] == "caution" and task_class != "routine":
        return {"decision": "throttle", "reasons": reasons}
    if condition["status"] == "unknown" and task_class != "routine":
        return {"decision": "defer", "reasons": ["condition_unknown"]}
    return {"decision": "allow", "reasons": reasons or ["within_observed_limits"]}


def collect_snapshot():
    """Collect best-effort Android/Termux telemetry without external packages."""
    snapshot = {
        "battery_percent": None, "charging": None, "temperature_c": None,
        "memory_available_percent": None, "disk_free_percent": None,
    }
    try:
        result = subprocess.run(
            ["termux-battery-status"], capture_output=True, text=True, timeout=3, check=True,
        )
        battery = json.loads(result.stdout)
        snapshot["battery_percent"] = _number(battery.get("percentage"))
        status = str(battery.get("status", "")).upper()
        if status:
            snapshot["charging"] = status in {"CHARGING", "FULL"}
        snapshot["temperature_c"] = _number(battery.get("temperature"))
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        pass
    try:
        values = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] in {"MemTotal:", "MemAvailable:"}:
                values[parts[0]] = float(parts[1])
        total, available = values.get("MemTotal:"), values.get("MemAvailable:")
        if total and available is not None:
            snapshot["memory_available_percent"] = round(100 * available / total, 2)
    except (OSError, ValueError):
        pass
    try:
        usage = shutil.disk_usage(Path.home())
        if usage.total:
            snapshot["disk_free_percent"] = round(100 * usage.free / usage.total, 2)
    except OSError:
        pass
    return snapshot
