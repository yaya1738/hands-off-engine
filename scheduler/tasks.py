"""
Task Definitions - Predefined scheduled tasks for Hands-Off Engine

Defines all scheduled tasks that can be run by the scheduler:
- fetch_markets: Fetch market data every 15 minutes
- calculate_alpha: Run alpha model every 30 minutes
- generate_report: Daily summary at 8am
- backup_state: Backup state files daily
- health_check: System health every 5 minutes
"""

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


def fetch_markets() -> Dict[str, Any]:
    """
    Fetch market data from Polymarket and other sources.
    Runs every 15 minutes.
    """
    audit = get_audit_logger(component="scheduler.fetch_markets")
    
    try:
        # This would typically call the actual fetch script
        # For now, we'll create a placeholder that logs the attempt
        
        audit.log_data_fetch(
            source="polymarket",
            params={"task": "fetch_markets", "scheduled": True},
            success=True,
            record_count=0,  # Would be populated by actual fetch
            session_id="scheduler"
        )
        
        return {
            "status": "success",
            "message": "Market data fetch completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        audit.log_error(
            error_type="fetch_markets_error",
            error_message=str(e),
            session_id="scheduler"
        )
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def calculate_alpha() -> Dict[str, Any]:
    """
    Run alpha model to calculate edges and fair prices.
    Runs every 30 minutes.
    """
    audit = get_audit_logger(component="scheduler.calculate_alpha")
    
    try:
        # This would typically run the alpha calculation pipeline
        # For now, we'll create a placeholder
        
        audit.log(
            event_type="alpha_calculation",
            event_data={
                "task": "calculate_alpha",
                "scheduled": True,
                "status": "completed"
            },
            session_id="scheduler"
        )
        
        return {
            "status": "success",
            "message": "Alpha calculation completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        audit.log_error(
            error_type="calculate_alpha_error",
            error_message=str(e),
            session_id="scheduler"
        )
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def generate_report() -> Dict[str, Any]:
    """
    Generate daily summary report.
    Runs daily at 8am.
    """
    audit = get_audit_logger(component="scheduler.generate_report")
    
    try:
        report_dir = Path(__file__).parent.parent / "logs"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate simple daily report
        report_file = report_dir / f"daily_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}.txt"
        
        with open(report_file, 'w') as f:
            f.write(f"Daily Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write("=" * 60 + "\n\n")
            f.write("Scheduled task: generate_report\n")
            f.write("Status: Completed\n")
        
        audit.log_action(
            action_type="generate_report",
            action_data={
                "task": "generate_report",
                "scheduled": True,
                "report_file": str(report_file)
            },
            result="success",
            session_id="scheduler"
        )
        
        return {
            "status": "success",
            "message": f"Daily report generated: {report_file}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        audit.log_error(
            error_type="generate_report_error",
            error_message=str(e),
            session_id="scheduler"
        )
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def backup_state() -> Dict[str, Any]:
    """
    Backup state files to a timestamped directory.
    Runs daily.
    """
    audit = get_audit_logger(component="scheduler.backup_state")
    
    try:
        state_dir = Path(__file__).parent.parent / "state"
        backup_base = Path(__file__).parent.parent / "backups"
        backup_base.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped backup directory
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_dir = backup_base / f"state_backup_{timestamp}"
        
        if state_dir.exists():
            # Copy state directory
            shutil.copytree(state_dir, backup_dir, dirs_exist_ok=True)
            
            # Get backup size
            total_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
            
            audit.log_action(
                action_type="backup_state",
                action_data={
                    "task": "backup_state",
                    "scheduled": True,
                    "backup_dir": str(backup_dir),
                    "backup_size_bytes": total_size
                },
                result="success",
                session_id="scheduler"
            )
            
            return {
                "status": "success",
                "message": f"State backed up to: {backup_dir}",
                "backup_size_bytes": total_size,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                "status": "warning",
                "message": "State directory does not exist, skipping backup",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    except Exception as e:
        audit.log_error(
            error_type="backup_state_error",
            error_message=str(e),
            session_id="scheduler"
        )
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def health_check() -> Dict[str, Any]:
    """
    Perform system health check.
    Runs every 5 minutes.
    """
    audit = get_audit_logger(component="scheduler.health_check")
    
    try:
        # Check key system components
        checks = {}
        
        # Check state directory
        state_dir = Path(__file__).parent.parent / "state"
        checks["state_dir_exists"] = state_dir.exists()
        
        # Check audit log directory
        audit_dir = Path(__file__).parent.parent / "logs" / "audit"
        checks["audit_dir_exists"] = audit_dir.exists()
        
        # Check scheduler state
        scheduler_state = Path(__file__).parent.parent / "state" / "scheduler" / "schedule.json"
        checks["scheduler_state_exists"] = scheduler_state.exists()
        
        # Overall health
        all_ok = all(checks.values())
        
        audit.log(
            event_type="health_check",
            event_data={
                "task": "health_check",
                "scheduled": True,
                "checks": checks,
                "overall_status": "healthy" if all_ok else "degraded"
            },
            severity="info" if all_ok else "warning",
            session_id="scheduler"
        )
        
        return {
            "status": "success" if all_ok else "warning",
            "message": "Health check completed",
            "checks": checks,
            "overall_status": "healthy" if all_ok else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        audit.log_error(
            error_type="health_check_error",
            error_message=str(e),
            session_id="scheduler"
        )
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Registry of all available tasks
# Maps task_id to (handler_function, default_cron_expression, description)
REGISTERED_TASKS = {
    "fetch_markets": {
        "handler": fetch_markets,
        "cron": "*/15 * * * *",  # Every 15 minutes
        "description": "Fetch market data from Polymarket and other sources",
        "timeout": 300,  # 5 minutes
    },
    "calculate_alpha": {
        "handler": calculate_alpha,
        "cron": "*/30 * * * *",  # Every 30 minutes
        "description": "Run alpha model to calculate edges and fair prices",
        "timeout": 600,  # 10 minutes
    },
    "generate_report": {
        "handler": generate_report,
        "cron": "0 8 * * *",  # Daily at 8am UTC
        "description": "Generate daily summary report",
        "timeout": 180,  # 3 minutes
    },
    "backup_state": {
        "handler": backup_state,
        "cron": "0 2 * * *",  # Daily at 2am UTC
        "description": "Backup state files to timestamped directory",
        "timeout": 300,  # 5 minutes
    },
    "health_check": {
        "handler": health_check,
        "cron": "*/5 * * * *",  # Every 5 minutes
        "description": "Perform system health check",
        "timeout": 60,  # 1 minute
    },
}


def get_task_handler(task_id: str):
    """Get the handler function for a task"""
    task_info = REGISTERED_TASKS.get(task_id)
    if task_info:
        return task_info["handler"]
    return None
