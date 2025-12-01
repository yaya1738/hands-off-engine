import os
from pathlib import Path

class SafetyAuditor:
    def __init__(self, config):
        self.allowed_cmds = set(config.get("allowed_commands", []))
        self.blocked_subs = config.get("blocked_substrings", [])
        self.protected_paths = config.get("protected_paths", [])
        self.repo_root = Path(os.getcwd()).resolve()

    def audit_task(self, task) -> (bool, str):
        """Returns (is_safe, reason)"""

        cmd = task.command
        if not cmd:
            return False, "Empty command"

        # 1. Check Base Command
        base_cmd = cmd[0]
        if base_cmd not in self.allowed_cmds:
            return False, f"Command '{base_cmd}' is not whitelisted."

        # 2. Check Blocked Substrings (brute force check on full string)
        full_cmd_str = " ".join(cmd)
        for block in self.blocked_subs:
            if block in full_cmd_str:
                return False, f"Command contains banned pattern: '{block}'"

        # 3. Path Safety & Jailbreak Check
        # Prevent accessing parent directories via '..' if restricted to workspace
        target_dir = (self.repo_root / task.working_dir).resolve()

        # Ensure working dir is inside repo root
        if not str(target_dir).startswith(str(self.repo_root)):
             return False, f"Working directory '{task.working_dir}' escapes repo root."

        return True, "Safe"
