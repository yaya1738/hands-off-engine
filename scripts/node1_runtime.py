#!/usr/bin/env python3
"""
Node 1 Runtime — stable compute node on Xiaomi Redmi (Android 15).

This is the unified runtime for the first compute node: this phone.
It runs all core services as a single supervised process:
- Task worker: polls inbox, processes tasks, emits continuation events
- Event router: reads messages.jsonl, routes events between parties
- Factory intake: consumes continuation events, produces next tasks

Design:
- Durable: state persists across restarts (crash-safe)
- Self-contained: no external orchestration needed
- Supervised: watchdog restarts on crash with bounded backoff
- Identity: always identifies as node-1 on the coordination bus
- Fail-closed: never auto-authorizes live execution

Device: Xiaomi Redmi 23117RA68G, Android 15, proot, Codex CLI
"""

import json
import os
import sys
import time
import signal
import fcntl
import hashlib
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = REPO_ROOT / "state"
NODE_STATE = STATE_DIR / "node1_state.json"
NODE_PID = STATE_DIR / "node1.pid"
NODE_LOCK = STATE_DIR / "node1.lock"
NODE_LOG = STATE_DIR / "logs" / "node1.log"
MESSAGES_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"

STATE_DIR.mkdir(parents=True, exist_ok=True)
(STATE_DIR / "logs").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [Node1] %(message)s',
)
log = logging.getLogger("Node1")

# Node identity
NODE_ID = "node-1"
NODE_NAME = "Yair Phone (Xiaomi Redmi)"
NODE_DEVICE = "Xiaomi Redmi 23117RA68G / Android 15 / proot"
NODE_PARTY = "anyclaw"  # maps to the anyclaw party on the coordination bus


class NodeLock:
    """One-instance lock."""

    def __init__(self):
        self.fd = None

    def try_acquire(self) -> bool:
        try:
            self.fd = open(NODE_LOCK, "w")
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            NODE_PID.write_text(str(os.getpid()))
            return True
        except (IOError, OSError):
            if self.fd:
                self.fd.close()
                self.fd = None
            return False

    def release(self):
        if self.fd:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
            except Exception:
                pass
        try:
            NODE_LOCK.unlink(missing_ok=True)
            NODE_PID.unlink(missing_ok=True)
        except Exception:
            pass


class NodeState:
    """Durable node state: counters, health, timestamps."""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> dict:
        if NODE_STATE.exists():
            try:
                return json.loads(NODE_STATE.read_text())
            except Exception:
                pass
        return {
            "node_id": NODE_ID,
            "node_name": NODE_NAME,
            "device": NODE_DEVICE,
            "started_at": None,
            "last_heartbeat": None,
            "tasks_processed": 0,
            "events_routed": 0,
            "intake_decisions": 0,
            "restarts": 0,
            "health": "starting",
        }

    def save(self):
        NODE_STATE.write_text(json.dumps(self.data, indent=2) + "\n")

    def record_heartbeat(self):
        self.data["last_heartbeat"] = datetime.now(timezone.utc).isoformat()
        self.data["health"] = "healthy"
        self.save()

    def record_task(self):
        self.data["tasks_processed"] = self.data.get("tasks_processed", 0) + 1
        self.save()

    def record_event_routed(self):
        self.data["events_routed"] = self.data.get("events_routed", 0) + 1

    def record_intake(self):
        self.data["intake_decisions"] = self.data.get("intake_decisions", 0) + 1


class Node1Runtime:
    """Unified Node 1 runtime — task worker + event router + factory intake."""

    def __init__(self):
        self.lock = NodeLock()
        self.state = NodeState()
        self.running = True
        self.last_heartbeat = 0

    def run(self):
        if not self.lock.try_acquire():
            log.error(f"Node1 already running (pid={NODE_PID.read_text().strip()})")
            return False

        self.state.data["started_at"] = datetime.now(timezone.utc).isoformat()
        self.state.data["restarts"] = self.state.data.get("restarts", 0) + 1
        self.state.save()

        log.info(f"Node 1 started: {NODE_NAME} (pid={os.getpid()})")
        log.info(f"Device: {NODE_DEVICE}")
        log.info(f"Restart #{self.state.data['restarts']}")

        signal.signal(signal.SIGTERM, self._signal)
        signal.signal(signal.SIGINT, self._signal)

        # Lazy imports to avoid circular deps
        try:
            from scripts.task_worker import poll_once
        except ImportError:
            poll_once = None
            log.warning("task_worker not available")

        try:
            from scripts.event_router import EventRouter
            router = EventRouter(repo_root=REPO_ROOT)
        except ImportError:
            router = None
            log.warning("event_router not available")

        try:
            from scripts.factory_intake import FactoryIntake
            intake = FactoryIntake(repo_root=REPO_ROOT)
        except ImportError:
            intake = None
            log.warning("factory_intake not available")

        try:
            from scripts.factory_request_intake import RequestIntake
            req_intake = RequestIntake(repo_root=REPO_ROOT)
        except ImportError:
            req_intake = None
            log.warning("factory_request_intake not available")
        try:
            from scripts.improvement_applier import ImprovementApplier
            applier = ImprovementApplier(repo_root=REPO_ROOT)
        except ImportError:
            applier = None
            log.warning("improvement_applier not available")
        
        try:
            from scripts.self_improvement import generate_improvements, save_improvements
        except ImportError:
            generate_improvements = None
            log.warning("self_improvement not available")

        try:
            from scripts.continuation import ContinuationEmitter
            emitter = ContinuationEmitter()
        except ImportError:
            emitter = None
            log.warning("continuation emitter not available")

        # Main loop: 10s tick
        tick = 0
        while self.running:
            try:
                # 1. Poll task worker (process inbox)
                if poll_once:
                    try:
                        count = poll_once()
                        if count:
                            log.info(f"Task worker: {count} tasks processed")
                            self.state.record_task()
                    except Exception as e:
                        log.error(f"Task worker error: {e}")

                # 2. Event router (read messages, route)
                if router:
                    try:
                        count = router.process_once()
                        if count:
                            log.info(f"Event router: {count} events routed")
                            self.state.data["events_routed"] = (
                                self.state.data.get("events_routed", 0) + count
                            )
                    except Exception as e:
                        log.error(f"Event router error: {e}")

                # 3. Factory intake (consume continuation events, emit next task)
                if intake and tick % 3 == 0:  # every 30s to avoid rapid looping
                    try:
                        decisions = intake.intake_once()
                        if decisions:
                            log.info(f"Factory intake: {len(decisions)} decisions")
                            self.state.data["intake_decisions"] = (
                                self.state.data.get("intake_decisions", 0) + len(decisions)
                            )
                    except Exception as e:
                        log.error(f"Factory intake error: {e}")

                # 3b. Request intake (admission gate for AnyClaw->Factory task_requests)
                if req_intake and tick % 3 == 0:
                    try:
                        req_decisions = req_intake.admit_once()
                        if req_decisions:
                            log.info(f"Request intake: {len(req_decisions)} admitted/rejected")
                            self.state.data["request_intake_count"] = (
                                self.state.data.get("request_intake_count", 0) + len(req_decisions)
                            )
                    except Exception as e:
                        log.error(f"Request intake error: {e}")

                # 3c. Improvement applier (every 5 minutes, tick % 30)
                if applier and tick % 30 == 0:
                    try:
                        # Generate improvement candidates
                        if generate_improvements:
                            candidates = generate_improvements()
                            save_improvements(candidates)
                            # Apply safe ones
                            results = applier.apply_batch(candidates)
                            applied = sum(1 for r in results if r.get("applied"))
                            if applied:
                                log.info(f"Improvement applier: {applied} improvements applied")
                                self.state.data["improvements_applied"] = (
                                    self.state.data.get("improvements_applied", 0) + applied
                                )
                    except Exception as e:
                        log.error(f"Improvement applier error: {e}")

                # 3d. Feedback analysis (every 10 minutes, tick % 60)
                if tick % 60 == 0:
                    try:
                        from scripts.improvement_feedback import analyze_feedback
                        analyze_feedback()
                    except Exception as e:
                        log.error(f"Feedback analysis error: {e}")

                # 4. Heartbeat (every 60s)
                if time.time() - self.last_heartbeat >= 60:
                    self.state.record_heartbeat()
                    self.last_heartbeat = time.time()

                # 5. Emit heartbeat event (every 5 min, non-wake)
                if emitter and tick % 30 == 0:
                    try:
                        emitter.emit_heartbeat(
                            summary=f"Node 1 alive: {self.state.data.get('tasks_processed', 0)} tasks, "
                            f"{self.state.data.get('events_routed', 0)} events routed"
                        )
                    except Exception:
                        pass

                tick += 1
                time.sleep(10)

            except Exception as e:
                log.error(f"Main loop error: {e}")
                self.state.data["health"] = "error"
                self.state.save()
                time.sleep(5)

        self.lock.release()
        self.state.data["health"] = "stopped"
        self.state.save()
        log.info("Node 1 stopped")
        return True

    def _signal(self, signum, frame):
        log.info(f"Signal {signum}, shutting down")
        self.running = False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Node 1 Runtime — Yair's phone compute node")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("run", help="Start Node 1 runtime")
    sub.add_parser("status", help="Show Node 1 status")
    sub.add_parser("stop", help="Stop Node 1")

    args = parser.parse_args()

    if args.cmd == "run":
        node = Node1Runtime()
        node.run()
    elif args.cmd == "status":
        if NODE_STATE.exists():
            print(NODE_STATE.read_text())
        else:
            print("Node 1 has never been started")
    elif args.cmd == "stop":
        if NODE_PID.exists():
            pid = int(NODE_PID.read_text().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Sent SIGTERM to Node 1 (pid={pid})")
            except ProcessLookupError:
                print(f"Node 1 not running (stale pid={pid})")
        else:
            print("Node 1 is not running")
    else:
        parser.print_help()
