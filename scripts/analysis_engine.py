#!/usr/bin/env python3
import sys, json, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

class SystemAnalyzer:
    def __init__(self, repo_root=None):
        if repo_root is None:
            repo_root = Path.home() / "hands-off-engine"
        self.repo_root = repo_root
        self.state_dir = repo_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.state_dir / "results.jsonl"
        self.analysis_log = self.state_dir / "analysis.jsonl"
        self.metrics_file = self.state_dir / "system_metrics.json"
        self.queue_file = self.state_dir / "command_queue.jsonl"
    
    def get_recent_results(self, minutes=60):
        if not self.results_file.exists():
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        cutoff_str = cutoff.isoformat()
        results = []
        try:
            with open(self.results_file, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("timestamp", "") >= cutoff_str:
                                results.append(data)
                        except:
                            pass
        except:
            pass
        return results
    
    def analyze(self):
        results = self.get_recent_results(minutes=120)
        if not results:
            return {"status": "no_data"}
        completed = len([r for r in results if r.get("status") == "completed"])
        failed = len([r for r in results if r.get("status") == "failed"])
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total": len(results),
            "completed": completed,
            "failed": failed,
            "success_rate": completed / len(results) if results else 0
        }
    
    def detect_issues(self, analysis):
        issues = []
        if analysis.get("success_rate", 0) < 0.8:
            issues.append({"type": "low_success_rate", "value": analysis.get("success_rate")})
        return issues
    
    def generate_commands(self, issues):
        commands = []
        for issue in issues:
            if issue["type"] == "low_success_rate":
                commands.append({"action": "adjust", "target": "system", "payload": {"parameter": "timeout", "value": 600}, "priority": 8})
        return commands
    
    def submit_commands(self, commands):
        for cmd in commands:
            try:
                with open(self.queue_file, "a") as f:
                    f.write(json.dumps({"id": f"auto_{int(time.time())}", "source": "analyzer", "action": cmd["action"], "target": cmd["target"], "payload": cmd["payload"], "timestamp": datetime.now(timezone.utc).isoformat(), "priority": cmd.get("priority", 0), "status": "pending"}) + "\n")
            except:
                pass
    
    def log_analysis(self, analysis, issues, commands):
        try:
            with open(self.analysis_log, "a") as f:
                f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "analysis": analysis, "issues": len(issues), "commands": len(commands)}) + "\n")
            with open(self.metrics_file, "w") as f:
                json.dump({"timestamp": analysis.get("timestamp"), "success_rate": analysis.get("success_rate", 0), "total": analysis.get("total", 0)}, f)
        except:
            pass
    
    def run_cycle(self):
        analysis = self.analyze()
        if analysis.get("status") == "no_data":
            return
        issues = self.detect_issues(analysis)
        commands = self.generate_commands(issues)
        if commands:
            self.submit_commands(commands)
        self.log_analysis(analysis, issues, commands)
    
    def run(self, interval=300):
        print(f"[Analysis] Starting (interval: {interval}s)")
        while True:
            try:
                self.run_cycle()
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[Analysis] Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    analyzer = SystemAnalyzer()
    analyzer.run()
