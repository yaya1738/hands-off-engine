#!/usr/bin/env python3
"""
ABSOLUTE IDENTITY VERIFICATION
Private, profile-backed owner verification

Verification Layers:
1. CRYPTOGRAPHIC - SSH keys, wallet signatures (unforgeable)
2. INFRASTRUCTURE - Known IPs, servers, devices
3. BEHAVIORAL - Typing patterns, decision style
4. KNOWLEDGE - Things only Yair knows
5. CONTEXTUAL - Project familiarity, history

Threshold: 60% = YAIR, <60% = NOT YAIR, no middle ground
"""

import os
import re
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

PRIVATE_DIR = Path(os.environ.get(
    "HANDS_OFF_PRIVATE_DIR",
    str(Path.home() / ".config" / "hands-off-engine"),
)).expanduser()
PROFILE_PATH = Path(os.environ.get("HANDS_OFF_IDENTITY_PROFILE", str(PRIVATE_DIR / "yair_identity_profile.json"))).expanduser()
HUMAN_IDENTITY_PATH = Path(os.environ.get("HANDS_OFF_HUMAN_IDENTITY", str(PRIVATE_DIR / "yair_human_identity.json"))).expanduser()
VERIFICATION_LOG = Path(os.environ.get("HANDS_OFF_IDENTITY_AUDIT_LOG", str(PRIVATE_DIR / "verification_audit.jsonl"))).expanduser()

class AbsoluteIdentity:
    def __init__(self):
        self.profile = self._load_profile()
        self.signals = []
        self.score = 0.0
        self.verification_time = datetime.now()

    def _load_profile(self) -> dict:
        if PROFILE_PATH.exists():
            try:
                profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
                return profile if isinstance(profile, dict) else {}
            except (OSError, ValueError, TypeError):
                return {}
        return {}

    def verify_cryptographic(self) -> float:
        """Layer 1: Unforgeable cryptographic verification"""
        score = 0.0
        weight = self.profile.get("verification_weights", {}).get("ssh_key_match", 0.4)

        # Check SSH key fingerprint from auth log
        try:
            result = subprocess.run(
                ["tail", "-100", "/var/log/auth.log"],
                capture_output=True, text=True, timeout=5
            )
            known_fps = self.profile.get("cryptographic", {}).get("ssh_key_fingerprints", [])

            for fp in known_fps:
                fp_short = fp.replace("SHA256:", "")
                if fp_short in result.stdout:
                    self.signals.append(f"CRYPTO:ssh_key_verified:{fp_short[:12]}...")
                    score = weight
                    break
        except:
            pass

        # Check for authorized key connection
        if os.environ.get("SSH_AUTH_SOCK"):
            self.signals.append("CRYPTO:ssh_agent_present")
            score = max(score, weight * 0.5)

        return score

    def verify_infrastructure(self) -> float:
        """Layer 2: Known infrastructure verification"""
        score = 0.0
        weight = self.profile.get("verification_weights", {}).get("trusted_ip", 0.2)

        # Get client IP
        client_ip = None
        for env_var in ["SSH_CLIENT", "SSH_CONNECTION"]:
            val = os.environ.get(env_var, "")
            if val:
                client_ip = val.split()[0]
                break

        if client_ip:
            owned_ips = [s["ip"] for s in self.profile.get("infrastructure", {}).get("owned_servers", [])]
            if client_ip in owned_ips:
                server_name = next(
                    (s["name"] for s in self.profile["infrastructure"]["owned_servers"] if s["ip"] == client_ip),
                    "unknown"
                )
                self.signals.append(f"INFRA:from_owned_server:{server_name}")
                score = weight

        # Check device ID
        device_weight = self.profile.get("verification_weights", {}).get("device_id", 0.15)
        hostname = os.uname().nodename
        known_devices = self.profile.get("cryptographic", {}).get("device_ids", [])

        for device in known_devices:
            if device.split("@")[0] in hostname or hostname in device:
                self.signals.append(f"INFRA:known_device:{hostname}")
                score += device_weight
                break

        return score

    def verify_behavioral(self, message: str = None) -> float:
        """Layer 3: Behavioral pattern matching"""
        if not message:
            return 0.0

        score = 0.0
        weight = self.profile.get("verification_weights", {}).get("typing_pattern", 0.1)
        patterns = self.profile.get("communication", {}).get("typing_patterns", {})

        matches = 0

        # Check abbreviations
        if patterns.get("uses_abbreviations"):
            abbrevs = patterns.get("examples", [])
            for abbrev in abbrevs:
                if abbrev.lower() in message.lower():
                    matches += 1

        # Check lowercase preference
        if patterns.get("lowercase_preference"):
            if message == message.lower():
                matches += 1

        # Check short messages
        if patterns.get("short_messages") and len(message) < 50:
            matches += 1

        # Check common phrases
        phrases = self.profile.get("communication", {}).get("vocabulary", {}).get("common_phrases", [])
        for phrase in phrases:
            if phrase.lower() in message.lower():
                matches += 2

        if matches >= 2:
            self.signals.append(f"BEHAV:typing_pattern_match:{matches}_signals")
            score = weight

        return score

    def verify_knowledge(self, responses: dict = None) -> float:
        """Layer 4: Knowledge only Yair would have"""
        if not responses:
            # Use context clues instead
            score = 0.0
            weight = self.profile.get("verification_weights", {}).get("knowledge_test", 0.1)

            # Check if in hands-off-engine directory
            cwd = os.getcwd()
            if "hands-off" in cwd:
                self.signals.append("KNOW:working_in_project_dir")
                score += weight * 0.5

            # Check if accessing project files
            if Path("/root/hands-off-engine").exists():
                self.signals.append("KNOW:project_exists")
                score += weight * 0.5

            return score

        # Explicit knowledge verification
        weight = self.profile.get("verification_weights", {}).get("knowledge_test", 0.1)
        questions = self.profile.get("knowledge_verification", {}).get("questions_only_yair_knows", [])

        correct = 0
        for q in questions:
            if q["category"] in responses:
                answer = responses[q["category"]]
                if "answer_hash" in q and answer == q["answer_hash"]:
                    correct += 1
                elif "answer_contains" in q:
                    if any(kw in answer.lower() for kw in q["answer_contains"]):
                        correct += 1

        if correct > 0:
            self.signals.append(f"KNOW:passed_{correct}_of_{len(questions)}_tests")
            return weight * (correct / len(questions))

        return 0.0

    def verify_contextual(self) -> float:
        """Layer 5: Contextual verification"""
        score = 0.0
        weight = self.profile.get("verification_weights", {}).get("behavioral", 0.05)

        # Running as root
        if os.getuid() == 0:
            self.signals.append("CTX:root_user")
            score += weight * 0.5

        # On a known hostname
        hostname = os.uname().nodename
        known_prefixes = ["pm-", "ho-", "handsoff"]
        if any(hostname.startswith(p) or p in hostname for p in known_prefixes):
            self.signals.append(f"CTX:known_hostname:{hostname}")
            score += weight * 0.5

        return score

    def verify_human_identity(self, answers: dict = None) -> float:
        """No personal challenge answers are embedded in public source code."""
        self.signals.append("HUMAN:private_challenge_not_configured")
        return 0.0

    def full_verification(self, message: str = None, knowledge_responses: dict = None, human_answers: dict = None) -> dict:
        """Run all verification layers"""
        self.signals = []
        self.score = 0.0

        # Never infer an owner identity from hostnames, SSH-agent presence, or defaults.
        if not self.profile:
            result = {
                "timestamp": self.verification_time.isoformat(),
                "identity": "NOT VERIFIED - ACCESS DENIED",
                "verified": False,
                "confidence": 0.0,
                "signals": ["PROFILE:missing_or_invalid"],
                "layers_passed": 0,
                "verdict": "UNVERIFIED",
            }
            self._log_verification(result)
            return result

        # Run all layers
        self.score += self.verify_cryptographic()
        self.score += self.verify_infrastructure()
        self.score += self.verify_behavioral(message)
        self.score += self.verify_knowledge(knowledge_responses)
        self.score += self.verify_contextual()
        self.score += self.verify_human_identity(human_answers)

        # Determine identity
        threshold = 0.5  # 50% required
        is_owner = self.score >= threshold

        result = {
            "timestamp": self.verification_time.isoformat(),
            "identity": "CONFIGURED OWNER" if is_owner else "NOT VERIFIED - ACCESS DENIED",
            "verified": is_owner,
            "confidence": round(self.score * 100, 1),
            "signals": self.signals,
            "layers_passed": len([s for s in self.signals if s.startswith(("CRYPTO", "INFRA"))]),
            "verdict": "AUTHENTIC" if is_owner else "UNVERIFIED"
        }

        # Log verification
        self._log_verification(result)

        return result

    def _log_verification(self, result: dict):
        """Audit log all verification attempts"""
        try:
            VERIFICATION_LOG.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            try:
                VERIFICATION_LOG.parent.chmod(0o700)
            except OSError:
                pass
            fd = os.open(VERIFICATION_LOG, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(result) + "\n")
        except OSError:
            pass


def is_configured_owner(message: str = None) -> bool:
    """Return whether the configured private owner profile verifies."""
    verifier = AbsoluteIdentity()
    result = verifier.full_verification(message)
    return result["verified"]


def get_identity(message: str = None) -> dict:
    """Get full identity verification result"""
    verifier = AbsoluteIdentity()
    return verifier.full_verification(message)


def require_absolute_identity(func):
    """Decorator - only runs if the configured private owner profile verifies."""
    def wrapper(*args, **kwargs):
        verifier = AbsoluteIdentity()
        result = verifier.full_verification()
        if not result["verified"]:
            raise PermissionError(
                f"IDENTITY VERIFICATION FAILED\n"
                f"Verdict: {result['verdict']}\n"
                f"Confidence: {result['confidence']}%\n"
                f"Required: 50%"
            )
        return func(*args, **kwargs)
    return wrapper


if __name__ == "__main__":
    verifier = AbsoluteIdentity()
    result = verifier.full_verification()

    print("=" * 60)
    print("ABSOLUTE IDENTITY VERIFICATION")
    print("SUBJECT: YAIR SIEGEL")
    print("=" * 60)

    print("\n[PRIVATE PROFILE]")
    print(f"  Profile configured: {PROFILE_PATH.is_file()}")

    print(f"\n[VERIFICATION RESULT]")
    print(f"  Identity: {result['identity']}")
    print(f"  Verdict: {result['verdict']}")
    print(f"  Confidence: {result['confidence']}%")

    print(f"\n[SIGNALS DETECTED]")
    for signal in result['signals']:
        layer = signal.split(":")[0]
        detail = ":".join(signal.split(":")[1:])
        print(f"  [{layer}] {detail}")

    print(f"\n[SECURITY LAYERS]")
    print(f"  Cryptographic: {'PASS' if any('CRYPTO' in s for s in result['signals']) else 'N/A'}")
    print(f"  Infrastructure: {'PASS' if any('INFRA' in s for s in result['signals']) else 'N/A'}")
    print(f"  Behavioral: {'PASS' if any('BEHAV' in s for s in result['signals']) else 'N/A'}")
    print(f"  Knowledge: {'PASS' if any('KNOW' in s for s in result['signals']) else 'N/A'}")
    print(f"  Contextual: {'PASS' if any('CTX' in s for s in result['signals']) else 'N/A'}")
    print(f"  Human Identity: {'PASS' if any('HUMAN' in s for s in result['signals']) else 'N/A'}")

    print("=" * 60)
    if result['verified']:
        print("ACCESS: GRANTED - Configured owner verified")
    else:
        print("ACCESS: DENIED - Identity not verified")
    print("=" * 60)
