"""Bounded, evidence-based trend summaries for device-condition observations.

This module is advisory only: it does not dispatch work or infer missing telemetry.
Observation format: {"observed_at": ISO-8601, "snapshot": {...}, "assessment": {...}}.
Manual reports require explicit provenance and timestamp.
"""
from datetime import datetime, timedelta, timezone
from statistics import mean

METRICS = ("battery_percent", "temperature_c", "memory_available_percent", "disk_free_percent", "cpu_load_percent", "cpu_throttling_percent", "network_quality_percent", "battery_capacity_percent", "performance_drift_percent", "io_error_count")


def _timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _numeric(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and abs(number) != float("inf") else None


def summarize_device_condition(observations, now=None, max_age_seconds=900,
                               window_seconds=86400, manual_reports=()):
    """Return freshness, bounded-window metrics, thermal recurrence, and attributed defects."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    if max_age_seconds < 0 or window_seconds < 0:
        raise ValueError("age/window limits must be non-negative")

    parsed = []
    for item in observations if isinstance(observations, (list, tuple)) else ():
        if not isinstance(item, dict) or not isinstance(item.get("snapshot"), dict):
            continue
        observed_at = _timestamp(item.get("observed_at"))
        if observed_at is None or observed_at > now:
            continue
        assessment = item.get("assessment")
        parsed.append((observed_at, item["snapshot"], assessment if isinstance(assessment, dict) else {}))
    parsed.sort(key=lambda row: row[0])
    cutoff = now - timedelta(seconds=window_seconds)
    window = [row for row in parsed if row[0] >= cutoff]
    latest = parsed[-1] if parsed else None
    age = (now - latest[0]).total_seconds() if latest else None
    fresh = age is not None and age <= max_age_seconds

    metrics = {}
    for key in METRICS:
        values = [value for _, snapshot, _ in window
                  if (value := _numeric(snapshot.get(key))) is not None]
        if values:
            metrics[key] = {
                "samples": len(values), "latest": values[-1],
                "minimum": min(values), "maximum": max(values),
                "mean": round(mean(values), 3),
            }

    concern_counts = {}
    warning_counts = {}
    for _, _, assessment in window:
        for field, counts in (("concerns", concern_counts), ("warnings", warning_counts)):
            values = assessment.get(field, [])
            if isinstance(values, (list, tuple)):
                for value in values:
                    if isinstance(value, str) and value:
                        counts[value] = counts.get(value, 0) + 1

    resource_pressure_events = sum(
        count for key, count in concern_counts.items()
        if key in {"low_battery", "memory_pressure", "low_storage", "cpu_pressure", "network_degraded", "io_errors"}
    ) + sum(
        count for key, count in warning_counts.items()
        if key in {"battery_low", "memory_pressure", "storage_low", "cpu_pressure", "network_degraded", "io_errors"}
    )

    thermal_events = sum(
        1 for _, snapshot, assessment in window
        if (_numeric(snapshot.get("temperature_c")) is not None
            and _numeric(snapshot.get("temperature_c")) >= 42)
        or "high_temperature" in (assessment.get("concerns") or [])
        or "elevated_temperature" in (assessment.get("warnings") or [])
    )

    attributed_reports = []
    for report in manual_reports if isinstance(manual_reports, (list, tuple)) else ():
        if not isinstance(report, dict):
            continue
        reported_at = _timestamp(report.get("reported_at"))
        defect, reported_by = report.get("defect"), report.get("reported_by")
        if reported_at and reported_at <= now and isinstance(defect, str) and defect.strip() and isinstance(reported_by, str) and reported_by.strip():
            attributed_reports.append({
                "reported_at": reported_at.isoformat(), "defect": defect.strip(),
                "reported_by": reported_by.strip(),
                "source": report.get("source") if isinstance(report.get("source"), str) else "manual",
            })

    return {
        "status": "unknown" if latest is None else ("fresh" if fresh else "stale"),
        "latest_observed_at": latest[0].isoformat() if latest else None,
        "age_seconds": round(age, 3) if age is not None else None,
        "max_age_seconds": max_age_seconds, "window_seconds": window_seconds,
        "observations_in_window": len(window), "metrics": metrics,
        "thermal_events_in_window": thermal_events,
        "resource_pressure_events_in_window": resource_pressure_events,
        "concern_counts": concern_counts, "warning_counts": warning_counts,
        "manual_defects": attributed_reports,
        "advisory_only": True,
    }
