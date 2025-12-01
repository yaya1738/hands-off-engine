# Batch 23 Implementation Transcript - Part 3: Learning Engine (Part 1/2)

## File: ai/ho_learning_engine.py (Lines 1-250)

```python
#!/usr/bin/env python3
"""
Hands-Off Learning Engine (Batch 23)
=====================================

Long-term learning and self-improvement layer for the Hands-Off Engine.
Consumes consensus output from Batch 22 and maintains persistent learning state.

SAFETY:
- DRYRUN-only (no network, no external actions)
- Deterministic (no randomness)
- File operations restricted to state/ directory
- Pure analysis and state tracking

Architecture:
1. Read brain_consensus.json (Batch 22 output)
2. Read/update brain_learning.json (persistent learning state)
3. Track issue recurrence via stable hashing
4. Maintain agent performance metrics
5. Compute learning weights based on historical accuracy
6. Detect trends over time
7. Generate recommendations
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class LearningEngine:
    """Core learning engine for the Hands-Off system."""

    def __init__(self, state_dir: str = "state", verbose: bool = False):
        """
        Initialize the learning engine.

        Args:
            state_dir: Directory containing state files
            verbose: Enable verbose logging
        """
        self.state_dir = Path(state_dir)
        self.verbose = verbose
        self.consensus_path = self.state_dir / "brain_consensus.json"
        self.learning_path = self.state_dir / "brain_learning.json"

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[LEARNING] {message}")

    def generate_issue_hash(self, severity: str, message: str) -> str:
        """
        Generate a stable hash for an issue.

        Args:
            severity: Issue severity level
            message: Issue message

        Returns:
            Hexadecimal hash string
        """
        content = f"{severity}:{message}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def load_consensus(self) -> Dict[str, Any]:
        """
        Load the consensus state from Batch 22.

        Returns:
            Consensus data dictionary

        Raises:
            FileNotFoundError: If consensus file doesn't exist
            json.JSONDecodeError: If consensus file is malformed
        """
        self.log(f"Loading consensus from {self.consensus_path}")

        if not self.consensus_path.exists():
            raise FileNotFoundError(
                f"Consensus file not found: {self.consensus_path}"
            )

        with open(self.consensus_path, 'r') as f:
            data = json.load(f)

        self.log(f"Loaded consensus with {len(data.get('issues', []))} issues")
        return data

    def load_learning_state(self) -> Optional[Dict[str, Any]]:
        """
        Load existing learning state if available.

        Returns:
            Learning state dictionary or None if file doesn't exist
        """
        if not self.learning_path.exists():
            self.log("No existing learning state found")
            return None

        self.log(f"Loading learning state from {self.learning_path}")

        try:
            with open(self.learning_path, 'r') as f:
                data = json.load(f)
            self.log(f"Loaded learning state (run {data.get('run_count', 0)})")
            return data
        except json.JSONDecodeError as e:
            self.log(f"Warning: Malformed learning state file: {e}")
            return None

    def initialize_learning_state(self) -> Dict[str, Any]:
        """
        Create a new learning state structure.

        Returns:
            New learning state dictionary
        """
        self.log("Initializing new learning state")

        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": str(self.consensus_path),
            "run_count": 0,
            "issue_history": [],
            "agent_performance": {},
            "trend_metrics": {
                "error_rate_mean": 0.0,
                "error_rate_std": 0.0,
                "consensus_mean": 0.0,
                "consensus_trend": "flat"
            },
            "learning_weights": {},
            "recommendations": []
        }

    def update_issue_history(
        self,
        learning_state: Dict[str, Any],
        consensus: Dict[str, Any]
    ) -> None:
        """
        Update issue history with new consensus issues.

        Args:
            learning_state: Current learning state
            consensus: Consensus data from Batch 22
        """
        self.log("Updating issue history")

        issues = consensus.get('issues', [])
        current_time = datetime.utcnow().isoformat() + "Z"

        # Build hash index for existing issues
        issue_index = {
            issue['hash']: issue
            for issue in learning_state['issue_history']
        }

        for issue in issues:
            severity = issue.get('severity', 'unknown')
            message = issue.get('message', '')
            confidence = issue.get('confidence', 0.0)

            issue_hash = self.generate_issue_hash(severity, message)

            if issue_hash in issue_index:
                # Update existing issue
                existing = issue_index[issue_hash]
                existing['occurrences'] += 1
                existing['last_seen'] = current_time
                existing['confidence'] = confidence
                self.log(f"  Updated issue {issue_hash[:8]} (occurrences: {existing['occurrences']})")
            else:
                # Add new issue
                new_issue = {
                    "hash": issue_hash,
                    "first_seen": current_time,
                    "last_seen": current_time,
                    "occurrences": 1,
                    "severity": severity,
                    "confidence": confidence,
                    "message": message
                }
                learning_state['issue_history'].append(new_issue)
                issue_index[issue_hash] = new_issue
                self.log(f"  Added new issue {issue_hash[:8]}")
```

*Continued in Part 4...*
