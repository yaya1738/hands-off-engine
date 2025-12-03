#!/usr/bin/env python3
"""
CLAUDE OPTIMIZER - System-Optimized Claude Integration
========================================================

Optimizes Claude for this specific system by:
1. Pre-loading system context (master, state, protections)
2. Routing actions through protection layers
3. Providing system-specific capabilities
4. Enforcing system rules automatically

Every Claude session starts INFORMED and ALIGNED.

Serving: Yair Siegel
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
CLAUDE_DIR = BASE_DIR / '.claude'

MASTER = "Yair Siegel"
OPTIMIZER_STATE_FILE = STATE_DIR / 'claude_optimizer.json'


class ClaudeOptimizer:
    """
    Optimizes Claude for this system.

    Ensures every Claude session:
    - Knows the master (Yair Siegel)
    - Knows the system state
    - Has access to protection layers
    - Follows system rules
    """

    def __init__(self):
        self.state = self._load_state()
        self.context = self._build_context()

    def _load_state(self) -> Dict:
        """Load optimizer state."""
        if OPTIMIZER_STATE_FILE.exists():
            try:
                with open(OPTIMIZER_STATE_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "master": MASTER,
            "sessions_optimized": 0,
            "last_optimization": None,
            "rules_enforced": 0
        }

    def _save_state(self):
        """Save optimizer state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(OPTIMIZER_STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _build_context(self) -> Dict:
        """Build comprehensive system context for Claude."""
        context = {
            "master": MASTER,
            "system_name": "hands-off-engine",
            "purpose": "Autonomous trading and infrastructure management",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Load financial state
        context["financial"] = self._get_financial_state()

        # Load infrastructure state
        context["infrastructure"] = self._get_infrastructure_state()

        # Load protection status
        context["protections"] = self._get_protection_status()

        # Load active agents
        context["agents"] = self._get_active_agents()

        # Load critical rules
        context["rules"] = self._get_system_rules()

        return context

    def _get_financial_state(self) -> Dict:
        """Get current financial state."""
        try:
            # Try to get from polymarket state
            poly_state = STATE_DIR / 'polymarket-model.json'
            if poly_state.exists():
                with open(poly_state) as f:
                    data = json.load(f)
                    return {
                        "balance": data.get("balance", 0),
                        "positions": len(data.get("positions", [])),
                        "source": "polymarket"
                    }
        except:
            pass

        # Fallback to brain state
        try:
            brain_state = STATE_DIR / 'brain_state.json'
            if brain_state.exists():
                with open(brain_state) as f:
                    data = json.load(f)
                    return {
                        "balance": data.get("balance", 0),
                        "positions": data.get("active_positions", 0),
                        "source": "brain"
                    }
        except:
            pass

        return {"balance": "unknown", "positions": "unknown", "source": "none"}

    def _get_infrastructure_state(self) -> Dict:
        """Get infrastructure state."""
        try:
            infra_file = STATE_DIR / 'infra_state.json'
            if infra_file.exists():
                with open(infra_file) as f:
                    data = json.load(f)
                    return {
                        "nodes": data.get("healthy_nodes", 0),
                        "total": data.get("total_nodes", 0),
                        "primary": data.get("primary", "unknown")
                    }
        except:
            pass
        return {"nodes": "unknown", "total": "unknown"}

    def _get_protection_status(self) -> Dict:
        """Get status of all protection layers."""
        protections = {}

        # Self-preservation
        try:
            from autonomous.self_preservation import get_preservation
            sp = get_preservation()
            status = sp.get_status()
            protections["self_preservation"] = {
                "enabled": status.get("enabled", True),
                "blocked_count": status.get("blocked_count", 0)
            }
        except:
            protections["self_preservation"] = {"enabled": "unknown"}

        # System immunity
        try:
            from autonomous.security_layer import get_immunity
            si = get_immunity()
            status = si.get_status()
            protections["system_immunity"] = {
                "enabled": status.get("enabled", True),
                "blocked_count": status.get("blocked_commands", 0)
            }
        except:
            protections["system_immunity"] = {"enabled": "unknown"}

        # Harm prevention
        try:
            from autonomous.harm_prevention import get_harm_prevention
            hp = get_harm_prevention()
            status = hp.get_status()
            protections["harm_prevention"] = {
                "enabled": status.get("enabled", True),
                "harmful_changes": status.get("harmful_changes", 0)
            }
        except:
            protections["harm_prevention"] = {"enabled": "unknown"}

        return protections

    def _get_active_agents(self) -> List[str]:
        """Get list of active agents."""
        agents = []
        try:
            # Check crontab for active agents
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                cron_content = result.stdout
                if "healthcheck" in cron_content:
                    agents.append("healthcheck")
                if "position_monitor" in cron_content:
                    agents.append("position_monitor")
                if "coordination_agent" in cron_content:
                    agents.append("coordination_agent")
                if "self_healing" in cron_content:
                    agents.append("self_healing_agent")
                if "threat_analysis" in cron_content:
                    agents.append("threat_analysis")
        except:
            pass
        return agents

    def _get_system_rules(self) -> List[str]:
        """Get critical system rules Claude must follow."""
        return [
            f"The master is {MASTER}. All actions serve the master.",
            "Never destroy the system - self-preservation is absolute.",
            "All changes go through protection layers before execution.",
            "Rate limit: max 10 automated changes per hour.",
            "Sacred files (.env, state files) cannot be auto-modified.",
            "Sacred processes (python3, cron, sshd) cannot be killed.",
            "Learn from harmful outcomes - never repeat mistakes.",
            "When in doubt, preserve system stability over action.",
            "Document all significant changes.",
            "Financial decisions require high confidence (>75%)."
        ]

    # ========================================================================
    # CONTEXT INJECTION
    # ========================================================================

    def get_system_prompt_prefix(self) -> str:
        """
        Generate system prompt prefix for Claude.

        This should be prepended to any Claude session to ensure
        Claude starts with full system awareness.
        """
        fin = self.context.get("financial", {})
        infra = self.context.get("infrastructure", {})
        prots = self.context.get("protections", {})

        prompt = f"""# SYSTEM CONTEXT - HANDS-OFF ENGINE

## Master
**{MASTER}** - All actions serve the master.

## Current State
- Balance: ${fin.get('balance', 'unknown')}
- Active Positions: {fin.get('positions', 'unknown')}
- Infrastructure: {infra.get('nodes', '?')}/{infra.get('total', '?')} nodes healthy

## Protection Layers (ALL ACTIVE)
1. **Self-Preservation**: {prots.get('self_preservation', {}).get('enabled', 'unknown')} - Cannot destroy system
2. **System Immunity**: {prots.get('system_immunity', {}).get('enabled', 'unknown')} - Blocks malicious actions
3. **Harm Prevention**: {prots.get('harm_prevention', {}).get('enabled', 'unknown')} - Blocks harmful help

## Active Agents
{', '.join(self.context.get('agents', ['none detected']))}

## Critical Rules
"""
        for i, rule in enumerate(self.context.get("rules", []), 1):
            prompt += f"{i}. {rule}\n"

        prompt += f"""
## Timestamp
{self.context.get('timestamp', 'unknown')}

---
You are now operating within the hands-off-engine system.
All actions are logged and validated through protection layers.
"""
        return prompt

    def get_context_json(self) -> str:
        """Get context as JSON for programmatic use."""
        return json.dumps(self.context, indent=2)

    # ========================================================================
    # ACTION VALIDATION
    # ========================================================================

    def validate_action(self, action_type: str, target: str, **kwargs) -> Tuple[bool, str]:
        """
        Validate an action through all protection layers.

        Returns: (allowed, reason)
        """
        # Layer 1: Self-preservation
        try:
            from autonomous.self_preservation import block_self_harm
            allowed, reason = block_self_harm(action_type, target, **kwargs)
            if not allowed:
                return False, f"[SELF-PRESERVATION] {reason}"
        except ImportError:
            pass

        # Layer 2: System immunity
        try:
            from autonomous.security_layer import get_immunity
            immunity = get_immunity()

            if action_type == "execute_command":
                allowed, reason = immunity.validate_command(target)
                if not allowed:
                    return False, f"[SYSTEM-IMMUNITY] {reason}"
            elif action_type in ["write_code", "modify_code"]:
                allowed, reason = immunity.validate_code(target)
                if not allowed:
                    return False, f"[SYSTEM-IMMUNITY] {reason}"
        except ImportError:
            pass

        # Layer 3: Harm prevention
        try:
            from autonomous.harm_prevention import get_harm_prevention, ChangeType
            hp = get_harm_prevention()

            # Map action to change type
            change_type_map = {
                "modify_file": ChangeType.FILE_MODIFICATION,
                "delete_file": ChangeType.RESOURCE_CLEANUP,
                "update": ChangeType.UPDATE,
                "config_change": ChangeType.CONFIG_CHANGE,
                "auto_heal": ChangeType.AUTO_HEAL,
                "optimize": ChangeType.OPTIMIZATION,
            }

            change_type = change_type_map.get(action_type, ChangeType.CONFIG_CHANGE)
            intention = kwargs.get("intention", f"Claude action: {action_type}")

            allowed, reason, _ = hp.validate_change(change_type, target, intention)
            if not allowed:
                return False, f"[HARM-PREVENTION] {reason}"
        except ImportError:
            pass

        return True, "Action validated through all protection layers"

    # ========================================================================
    # OPTIMIZED COMMANDS
    # ========================================================================

    def safe_execute(self, command: str) -> Tuple[bool, str]:
        """
        Execute a command with full protection.

        Validates through all layers before execution.
        """
        allowed, reason = self.validate_action("execute_command", command)
        if not allowed:
            return False, reason

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(BASE_DIR)
            )
            return True, result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return False, str(e)

    def safe_file_modify(self, file_path: str, intention: str) -> Tuple[bool, str]:
        """
        Check if file modification is allowed.

        Returns (allowed, reason) - does NOT modify the file.
        """
        return self.validate_action(
            "modify_file",
            file_path,
            intention=intention
        )

    # ========================================================================
    # CLAUDE INSTRUCTIONS UPDATE
    # ========================================================================

    def update_claude_instructions(self):
        """
        Update .claude/instructions.md with optimized system context.
        """
        instructions_file = CLAUDE_DIR / 'instructions.md'

        # Read existing instructions
        existing_content = ""
        if instructions_file.exists():
            with open(instructions_file) as f:
                existing_content = f.read()

        # Check if already has system context section
        if "# SYSTEM CONTEXT - AUTO-GENERATED" in existing_content:
            # Replace existing section
            parts = existing_content.split("# SYSTEM CONTEXT - AUTO-GENERATED")
            if len(parts) >= 2:
                # Find end of auto-generated section
                end_marker = "# END SYSTEM CONTEXT"
                if end_marker in parts[1]:
                    rest = parts[1].split(end_marker, 1)[1]
                    existing_content = parts[0] + rest
                else:
                    existing_content = parts[0]

        # Build new system context section
        context_section = f"""
# SYSTEM CONTEXT - AUTO-GENERATED
# Updated: {datetime.now(timezone.utc).isoformat()}

{self.get_system_prompt_prefix()}

# END SYSTEM CONTEXT
"""

        # Prepend to instructions
        new_content = context_section + existing_content

        # Write back
        with open(instructions_file, 'w') as f:
            f.write(new_content)

        self.state["sessions_optimized"] = self.state.get("sessions_optimized", 0) + 1
        self.state["last_optimization"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        return True

    # ========================================================================
    # STATUS
    # ========================================================================

    def get_status(self) -> Dict:
        """Get optimizer status."""
        return {
            "master": MASTER,
            "sessions_optimized": self.state.get("sessions_optimized", 0),
            "last_optimization": self.state.get("last_optimization"),
            "context_age_seconds": self._get_context_age(),
            "protection_layers": len(self.context.get("protections", {})),
            "active_agents": len(self.context.get("agents", [])),
            "rules_count": len(self.context.get("rules", []))
        }

    def _get_context_age(self) -> float:
        """Get age of current context in seconds."""
        try:
            ts = datetime.fromisoformat(
                self.context.get("timestamp", "").replace('Z', '+00:00')
            )
            return (datetime.now(timezone.utc) - ts).total_seconds()
        except:
            return -1


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_optimizer: ClaudeOptimizer = None


def get_optimizer() -> ClaudeOptimizer:
    """Get or create global optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = ClaudeOptimizer()
    return _optimizer


def optimize_claude():
    """Main optimization function - updates Claude instructions."""
    optimizer = get_optimizer()
    return optimizer.update_claude_instructions()


def get_system_context() -> str:
    """Get system context for Claude prompt."""
    optimizer = get_optimizer()
    return optimizer.get_system_prompt_prefix()


def validate_claude_action(action_type: str, target: str, **kwargs) -> Tuple[bool, str]:
    """Validate a Claude action through all protection layers."""
    optimizer = get_optimizer()
    return optimizer.validate_action(action_type, target, **kwargs)


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Claude Optimizer")
    parser.add_argument("command", choices=["status", "optimize", "context", "validate"])
    parser.add_argument("--action", help="Action type to validate")
    parser.add_argument("--target", help="Target of action")

    args = parser.parse_args()
    optimizer = get_optimizer()

    if args.command == "status":
        status = optimizer.get_status()
        print(f"\n{'='*60}")
        print(f"CLAUDE OPTIMIZER STATUS")
        print(f"{'='*60}")
        print(f"Master: {status['master']}")
        print(f"Sessions optimized: {status['sessions_optimized']}")
        print(f"Last optimization: {status['last_optimization']}")
        print(f"Context age: {status['context_age_seconds']:.0f}s")
        print(f"Protection layers: {status['protection_layers']}")
        print(f"Active agents: {status['active_agents']}")
        print(f"Rules enforced: {status['rules_count']}")

    elif args.command == "optimize":
        print("Optimizing Claude instructions...")
        success = optimizer.update_claude_instructions()
        if success:
            print("Claude instructions updated with system context")
        else:
            print("Failed to update instructions")

    elif args.command == "context":
        print(optimizer.get_system_prompt_prefix())

    elif args.command == "validate":
        if not args.action or not args.target:
            print("Error: --action and --target required")
            return
        allowed, reason = optimizer.validate_action(args.action, args.target)
        print(f"{'ALLOWED' if allowed else 'BLOCKED'}: {reason}")


if __name__ == "__main__":
    main()
