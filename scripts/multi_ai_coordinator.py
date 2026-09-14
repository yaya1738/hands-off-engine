#!/usr/bin/env python3
import sys, json, time, uuid
from pathlib import Path
from datetime import datetime, timezone

class MultiAICoordinator:
    def __init__(self, repo_root=None):
        if repo_root is None:
            repo_root = Path.home() / "hands-off-engine"
        self.repo_root = repo_root
        self.state_dir = repo_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.state_dir / "command_queue.jsonl"
        self.results_file = self.state_dir / "results.jsonl"
        self.coordination_log = self.state_dir / "coordination.jsonl"
        self.systems = ["hands-off-engine", "grok", "chatgpt", "openclaw"]
    
    def submit_command(self, target, action, payload, priority=5):
        cmd_id = str(uuid.uuid4())
        cmd = {
            "id": cmd_id, "source": "multi-ai-coordinator", "target_system": target,
            "action": action, "payload": payload, "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": priority, "status": "pending"
        }
        try:
            with open(self.queue_file, "a") as f:
                f.write(json.dumps(cmd) + "\n")
        except:
            pass
        return cmd_id
    
    def broadcast_query(self, query, systems=None):
        if systems is None:
            systems = self.systems
        results = {}
        for system in systems:
            cmd_id = self.submit_command(system, "query", {"query": query}, priority=8)
            results[system] = cmd_id
        return results
    
    def aggregate_results(self, query_ids, timeout=30):
        results = {}
        start = time.time()
        while time.time() - start < timeout:
            if self.results_file.exists():
                try:
                    with open(self.results_file, "r") as f:
                        for line in f:
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    for system, cmd_id in query_ids.items():
                                        if data.get("id") == cmd_id and system not in results:
                                            results[system] = data.get("result")
                                except:
                                    pass
                except:
                    pass
            if len(results) == len(query_ids):
                break
            time.sleep(1)
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "results": results, "systems_responded": len(results), "systems_total": len(query_ids)}
    
    def optimization_round(self):
        print(f"\n[{datetime.now(timezone.utc).isoformat()}] Multi-AI optimization round")
        analysis_ids = self.broadcast_query("Analyze results: what's working, broken, optimize?", self.systems)
        analysis = self.aggregate_results(analysis_ids, timeout=30)
        
        consensus_ids = self.broadcast_query("Consensus: single top optimization?", self.systems)
        consensus = self.aggregate_results(consensus_ids, timeout=30)
        
        optimizations = []
        if consensus.get("results"):
            for system, suggestion in consensus["results"].items():
                self.submit_command(system, "adjust", {"optimization": suggestion}, priority=9)
                optimizations.append({"system": system, "suggestion": suggestion})
        
        round_log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "systems": self.systems,
            "analysis_responses": analysis.get("systems_responded", 0),
            "consensus_responses": consensus.get("systems_responded", 0),
            "optimizations": len(optimizations)
        }
        
        try:
            with open(self.coordination_log, "a") as f:
                f.write(json.dumps(round_log) + "\n")
        except:
            pass
        
        print(f"  ✅ Round complete: {len(optimizations)} optimizations from {consensus.get('systems_responded', 0)} systems")
        return round_log
    
    def run(self, interval=600):
        print(f"[Multi-AI Coordinator] Starting with systems: {', '.join(self.systems)}")
        while True:
            try:
                self.optimization_round()
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

if __name__ == "__main__":
    coordinator = MultiAICoordinator()
    coordinator.run()
