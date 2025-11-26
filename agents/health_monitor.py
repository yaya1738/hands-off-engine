"""
Health Monitor for Hands-Off Engine

Monitors system health:
- API connectivity
- State file integrity
- Cron jobs running
- System resources
- Process status
"""

import json
import os
import psutil
import requests
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit.audit_logger import AuditLogger
from agents.alerts import get_alert_system, AlertLevel


class HealthStatus:
    """Health check status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthMonitor:
    """Monitors system health and reports anomalies"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize health monitor
        
        Args:
            config_path: Path to health_thresholds.json config file
        """
        repo_root = Path(__file__).parent.parent
        
        # Load configuration
        if config_path is None:
            config_path = repo_root / "config" / "health_thresholds.json"
        
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.state_dir = repo_root / "state"
        self.audit_logger = AuditLogger(component="health_monitor")
        self.alerts = get_alert_system()
        
        # Track consecutive failures
        self.failure_counts: Dict[str, int] = {}
    
    def run_health_check(self) -> Dict[str, Any]:
        """
        Run comprehensive health check
        
        Returns:
            Health check results
        """
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": HealthStatus.HEALTHY,
            "checks": {}
        }
        
        # Run individual checks
        checks = [
            ("api_connectivity", self._check_api_connectivity),
            ("state_file_integrity", self._check_state_file_integrity),
            ("cron_jobs", self._check_cron_jobs),
            ("disk_usage", self._check_disk_usage),
            ("memory_usage", self._check_memory_usage),
            ("process_status", self._check_process_status)
        ]
        
        for check_name, check_func in checks:
            try:
                check_result = check_func()
                results["checks"][check_name] = check_result
                
                # Update overall status
                if check_result["status"] == HealthStatus.CRITICAL:
                    results["overall_status"] = HealthStatus.CRITICAL
                elif check_result["status"] == HealthStatus.WARNING and results["overall_status"] == HealthStatus.HEALTHY:
                    results["overall_status"] = HealthStatus.WARNING
                
                # Alert on failures
                if check_result["status"] in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                    self._handle_check_failure(check_name, check_result)
                else:
                    # Reset failure count on success
                    self.failure_counts[check_name] = 0
                    
            except Exception as e:
                results["checks"][check_name] = {
                    "status": HealthStatus.UNKNOWN,
                    "error": str(e)
                }
                results["overall_status"] = HealthStatus.CRITICAL
        
        # Log health check results
        self.audit_logger.log(
            event_type="health_check",
            event_data=results
        )
        
        return results
    
    def _check_api_connectivity(self) -> Dict[str, Any]:
        """Check connectivity to monitored APIs"""
        result = {
            "status": HealthStatus.HEALTHY,
            "apis": {}
        }
        
        for api_config in self.config.get("monitored_apis", []):
            api_name = api_config["name"]
            url = api_config["health_check_url"]
            max_time = api_config.get("max_response_time_ms", 5000) / 1000
            
            try:
                start_time = datetime.now()
                response = requests.get(
                    url,
                    timeout=self.config.get("api_timeout_seconds", 30)
                )
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                api_result = {
                    "status": HealthStatus.HEALTHY,
                    "response_time_ms": elapsed_ms,
                    "http_status": response.status_code
                }
                
                if response.status_code >= 400:
                    api_result["status"] = HealthStatus.CRITICAL
                    result["status"] = HealthStatus.CRITICAL
                elif elapsed_ms > max_time:
                    api_result["status"] = HealthStatus.WARNING
                    if result["status"] == HealthStatus.HEALTHY:
                        result["status"] = HealthStatus.WARNING
                
                result["apis"][api_name] = api_result
                
            except Exception as e:
                result["apis"][api_name] = {
                    "status": HealthStatus.CRITICAL,
                    "error": str(e)
                }
                result["status"] = HealthStatus.CRITICAL
        
        return result
    
    def _check_state_file_integrity(self) -> Dict[str, Any]:
        """Check integrity of critical state files"""
        result = {
            "status": HealthStatus.HEALTHY,
            "files": {}
        }
        
        warning_hours = self.config.get("state_file_age_warning_hours", 24)
        warning_age = timedelta(hours=warning_hours)
        
        for filename in self.config.get("monitored_state_files", []):
            file_path = self.state_dir / filename
            
            file_result = {
                "exists": file_path.exists(),
                "status": HealthStatus.HEALTHY
            }
            
            if not file_path.exists():
                file_result["status"] = HealthStatus.WARNING
                if result["status"] == HealthStatus.HEALTHY:
                    result["status"] = HealthStatus.WARNING
            else:
                # Check file age
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                age = datetime.now(timezone.utc) - mod_time
                file_result["age_hours"] = age.total_seconds() / 3600
                
                if age > warning_age:
                    file_result["status"] = HealthStatus.WARNING
                    if result["status"] == HealthStatus.HEALTHY:
                        result["status"] = HealthStatus.WARNING
                
                # Check JSON validity
                try:
                    with open(file_path) as f:
                        json.load(f)
                    file_result["valid_json"] = True
                except:
                    file_result["valid_json"] = False
                    file_result["status"] = HealthStatus.CRITICAL
                    result["status"] = HealthStatus.CRITICAL
            
            result["files"][filename] = file_result
        
        return result
    
    def _check_cron_jobs(self) -> Dict[str, Any]:
        """Check if cron daemon is running"""
        result = {
            "status": HealthStatus.HEALTHY,
            "crond_running": False
        }
        
        try:
            # Check if crond process is running
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if 'crond' in proc.info['name'] or (
                        proc.info['cmdline'] and 
                        any('crond' in arg for arg in proc.info['cmdline'])
                    ):
                        result["crond_running"] = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not result["crond_running"]:
                result["status"] = HealthStatus.CRITICAL
                
        except Exception as e:
            result["status"] = HealthStatus.UNKNOWN
            result["error"] = str(e)
        
        return result
    
    def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage"""
        result = {
            "status": HealthStatus.HEALTHY
        }
        
        try:
            disk_usage = psutil.disk_usage('/')
            percent_used = disk_usage.percent
            
            result["percent_used"] = percent_used
            result["free_gb"] = disk_usage.free / (1024**3)
            
            warning_threshold = self.config.get("disk_usage_warning_percent", 80)
            critical_threshold = self.config.get("disk_usage_critical_percent", 90)
            
            if percent_used >= critical_threshold:
                result["status"] = HealthStatus.CRITICAL
            elif percent_used >= warning_threshold:
                result["status"] = HealthStatus.WARNING
                
        except Exception as e:
            result["status"] = HealthStatus.UNKNOWN
            result["error"] = str(e)
        
        return result
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        result = {
            "status": HealthStatus.HEALTHY
        }
        
        try:
            mem = psutil.virtual_memory()
            percent_used = mem.percent
            
            result["percent_used"] = percent_used
            result["available_gb"] = mem.available / (1024**3)
            
            warning_threshold = self.config.get("memory_usage_warning_percent", 80)
            critical_threshold = self.config.get("memory_usage_critical_percent", 90)
            
            if percent_used >= critical_threshold:
                result["status"] = HealthStatus.CRITICAL
            elif percent_used >= warning_threshold:
                result["status"] = HealthStatus.WARNING
                
        except Exception as e:
            result["status"] = HealthStatus.UNKNOWN
            result["error"] = str(e)
        
        return result
    
    def _check_process_status(self) -> Dict[str, Any]:
        """Check status of critical processes"""
        result = {
            "status": HealthStatus.HEALTHY,
            "processes": {}
        }
        
        critical_processes = self.config.get("critical_processes", [])
        
        for process_name in critical_processes:
            found = False
            
            try:
                for proc in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if process_name in proc.info['name'] or (
                            proc.info['cmdline'] and
                            any(process_name in arg for arg in proc.info['cmdline'])
                        ):
                            found = True
                            result["processes"][process_name] = {
                                "status": HealthStatus.HEALTHY,
                                "running": True
                            }
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if not found:
                    result["processes"][process_name] = {
                        "status": HealthStatus.CRITICAL,
                        "running": False
                    }
                    result["status"] = HealthStatus.CRITICAL
                    
            except Exception as e:
                result["processes"][process_name] = {
                    "status": HealthStatus.UNKNOWN,
                    "error": str(e)
                }
        
        return result
    
    def _handle_check_failure(self, check_name: str, check_result: Dict[str, Any]):
        """Handle health check failure"""
        # Increment failure count
        self.failure_counts[check_name] = self.failure_counts.get(check_name, 0) + 1
        
        max_failures = self.config.get("max_consecutive_failures", 3)
        
        # Alert on first failure or after max consecutive failures
        if self.failure_counts[check_name] == 1 or self.failure_counts[check_name] >= max_failures:
            level = AlertLevel.CRITICAL if check_result["status"] == HealthStatus.CRITICAL else AlertLevel.WARNING
            
            self.alerts.alert_health_check_failed(
                check_name,
                {
                    "consecutive_failures": self.failure_counts[check_name],
                    "details": check_result
                }
            )


if __name__ == "__main__":
    # Simple test
    monitor = HealthMonitor()
    results = monitor.run_health_check()
    
    print(json.dumps(results, indent=2))
    print(f"\nOverall status: {results['overall_status']}")
