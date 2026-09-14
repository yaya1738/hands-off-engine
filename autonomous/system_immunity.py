#!/usr/bin/env python3
"""
SYSTEM IMMUNITY - Protection Against Malicious Actors
======================================================

The system must be IMMUNE to intentional destruction or damage.

PROTECTION LAYERS:
1. INPUT VALIDATION - Sanitize all inputs before execution
2. COMMAND FILTERING - Block dangerous patterns
3. RATE LIMITING - Prevent abuse
4. INTEGRITY CHECKING - Detect tampering
5. ISOLATION - Contain damage
6. AUDIT TRAIL - Track all actions for forensics

THREAT MODEL:
- External attackers trying to compromise the system
- Malicious code injection via inputs
- Credential theft attempts
- Data exfiltration
- System sabotage commands
- Resource exhaustion attacks

Serving: Yair Siegel
"""

import re
import os
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from functools import wraps
import threading

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / 'state'
STATE_DIR.mkdir(parents=True, exist_ok=True)

MASTER = "Yair Siegel"
SECURITY_LOG = STATE_DIR / 'security_events.jsonl'
INTEGRITY_FILE = STATE_DIR / 'integrity_hashes.json'
RATE_LIMIT_FILE = STATE_DIR / 'rate_limits.json'

# Thread-safe lock for rate limiting
_rate_lock = threading.Lock()


# ============================================================================
# DANGEROUS PATTERNS - Commands/inputs that should NEVER execute
# ============================================================================

DANGEROUS_COMMANDS = [
    # System destruction
    r'rm\s+-rf\s+/',
    r'rm\s+-rf\s+\*',
    r'rm\s+-rf\s+~',
    r'rm\s+--no-preserve-root',
    r'mkfs\.',
    r'dd\s+if=/dev/zero',
    r'dd\s+if=/dev/random',
    r'>\s*/dev/sd[a-z]',
    r'chmod\s+-R\s+777\s+/',
    r'chown\s+-R.*\s+/',

    # Process killing
    r'kill\s+-9\s+-1',
    r'killall\s+-9',
    r'pkill\s+-9\s+\.',

    # System control
    r'shutdown',
    r'poweroff',
    r'halt',
    r'init\s+0',
    r'telinit\s+0',

    # Fork bombs
    r':\(\)\{.*\}',
    r'fork\s*while',

    # Network attacks
    r'iptables\s+-F',  # Flush all firewall rules
    r'ufw\s+disable',

    # Credential theft
    r'cat\s+.*\.env',  # Trying to read credentials
    r'cat\s+.*/etc/shadow',
    r'cat\s+.*/etc/passwd',

    # Crypto mining
    r'xmrig',
    r'minerd',
    r'cryptonight',

    # Reverse shells
    r'nc\s+-e',
    r'bash\s+-i\s+>&',
    r'/dev/tcp/',
    r'python.*socket.*connect',
    r'perl.*socket.*',
]

DANGEROUS_CODE_PATTERNS = [
    # Code injection
    r'eval\s*\(',
    r'exec\s*\(',
    r'__import__\s*\(',
    r'subprocess\.call.*shell\s*=\s*True',
    r'os\.system\s*\(',
    r'os\.popen\s*\(',

    # SQL injection
    r"'\s*OR\s+'1'\s*=\s*'1",
    r';\s*DROP\s+TABLE',
    r';\s*DELETE\s+FROM',
    r'UNION\s+SELECT',

    # Path traversal
    r'\.\./\.\.',
    r'%2e%2e%2f',

    # XSS patterns
    r'<script[^>]*>',
    r'javascript:',
    r'on\w+\s*=',
]

ALLOWED_DOMAINS = [
    'polymarket.com',
    'digitalocean.com',
    'github.com',
    'anthropic.com',
    'groq.com',
    'google.com',
    'api.openai.com',
]


@dataclass
class SecurityEvent:
    """A security event to log."""
    timestamp: str
    event_type: str  # blocked, warning, intrusion, audit
    severity: str    # critical, high, medium, low
    source: str      # What triggered this
    details: str
    action_taken: str
    blocked: bool


class SystemImmunity:
    """
    System Immunity Layer.

    Makes the system resistant to malicious attacks.
    """

    def __init__(self):
        self.rate_limits: Dict[str, List[float]] = {}
        self.integrity_hashes = self._load_integrity()
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self.dangerous_cmd_patterns = [
            re.compile(p, re.IGNORECASE) for p in DANGEROUS_COMMANDS
        ]
        self.dangerous_code_patterns = [
            re.compile(p, re.IGNORECASE) for p in DANGEROUS_CODE_PATTERNS
        ]

    def _load_integrity(self) -> Dict:
        """Load integrity hashes."""
        if INTEGRITY_FILE.exists():
            try:
                with open(INTEGRITY_FILE) as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_integrity(self):
        """Save integrity hashes."""
        with open(INTEGRITY_FILE, 'w') as f:
            json.dump(self.integrity_hashes, f, indent=2)

    def _log_event(self, event: SecurityEvent):
        """Log security event."""
        with open(SECURITY_LOG, 'a') as f:
            f.write(json.dumps(asdict(event)) + '\n')

        # Print critical/high events
        if event.severity in ['critical', 'high']:
            print(f"[SECURITY {event.severity.upper()}] {event.event_type}: {event.details}")

    # ========================================================================
    # COMMAND VALIDATION
    # ========================================================================

    def validate_command(self, command: str, source: str = "unknown") -> Tuple[bool, str]:
        """
        Validate a command before execution.

        Returns: (safe, reason)
        """
        if not command:
            return True, "Empty command"

        # Check against dangerous patterns
        for pattern in self.dangerous_cmd_patterns:
            if pattern.search(command):
                self._log_event(SecurityEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="blocked_command",
                    severity="critical",
                    source=source,
                    details=f"Dangerous command blocked: {command[:100]}",
                    action_taken="Command rejected",
                    blocked=True
                ))
                return False, f"BLOCKED: Dangerous command pattern detected"

        # Check for suspicious character sequences
        suspicious = [';', '&&', '||', '`', '$(',  '$()', '|']
        sus_count = sum(1 for s in suspicious if s in command)
        if sus_count > 3:
            self._log_event(SecurityEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="suspicious_command",
                severity="high",
                source=source,
                details=f"Too many shell operators: {command[:100]}",
                action_taken="Command flagged for review",
                blocked=True
            ))
            return False, "BLOCKED: Too many shell operators"

        return True, "OK"

    def validate_code(self, code: str, source: str = "unknown") -> Tuple[bool, str]:
        """
        Validate code before execution.

        Returns: (safe, reason)
        """
        if not code:
            return True, "Empty code"

        for pattern in self.dangerous_code_patterns:
            if pattern.search(code):
                self._log_event(SecurityEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="blocked_code",
                    severity="critical",
                    source=source,
                    details=f"Dangerous code pattern: {pattern.pattern}",
                    action_taken="Code rejected",
                    blocked=True
                ))
                return False, f"BLOCKED: Dangerous code pattern"

        return True, "OK"

    def validate_input(self, input_str: str, source: str = "unknown") -> Tuple[bool, str]:
        """
        Validate user input before processing.

        Returns: (safe, sanitized_input)
        """
        if not input_str:
            return True, ""

        # Check length
        if len(input_str) > 10000:
            self._log_event(SecurityEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="oversized_input",
                severity="medium",
                source=source,
                details=f"Input too large: {len(input_str)} chars",
                action_taken="Truncated",
                blocked=False
            ))
            input_str = input_str[:10000]

        # Check for injection attempts
        for pattern in self.dangerous_code_patterns:
            if pattern.search(input_str):
                self._log_event(SecurityEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="injection_attempt",
                    severity="high",
                    source=source,
                    details=f"Injection pattern detected",
                    action_taken="Input rejected",
                    blocked=True
                ))
                return False, "BLOCKED: Injection attempt detected"

        return True, input_str

    # ========================================================================
    # RATE LIMITING
    # ========================================================================

    def check_rate_limit(self, action: str, limit: int = 100,
                         window_seconds: int = 60) -> Tuple[bool, str]:
        """
        Check if action is within rate limits.

        Returns: (allowed, reason)
        """
        now = datetime.now(timezone.utc).timestamp()

        with _rate_lock:
            if action not in self.rate_limits:
                self.rate_limits[action] = []

            # Clean old entries
            cutoff = now - window_seconds
            self.rate_limits[action] = [
                t for t in self.rate_limits[action] if t > cutoff
            ]

            # Check limit
            if len(self.rate_limits[action]) >= limit:
                self._log_event(SecurityEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="rate_limit_exceeded",
                    severity="medium",
                    source=action,
                    details=f"{len(self.rate_limits[action])} requests in {window_seconds}s",
                    action_taken="Request blocked",
                    blocked=True
                ))
                return False, f"Rate limit exceeded: {limit}/{window_seconds}s"

            # Add this request
            self.rate_limits[action].append(now)

        return True, "OK"

    # ========================================================================
    # INTEGRITY CHECKING
    # ========================================================================

    def compute_file_hash(self, filepath: str) -> str:
        """Compute SHA256 hash of a file."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""

    def register_integrity(self, filepath: str):
        """Register a file for integrity monitoring."""
        file_hash = self.compute_file_hash(filepath)
        if file_hash:
            self.integrity_hashes[filepath] = {
                "hash": file_hash,
                "registered_at": datetime.now(timezone.utc).isoformat()
            }
            self._save_integrity()

    def check_integrity(self, filepath: str) -> Tuple[bool, str]:
        """
        Check if a file has been tampered with.

        Returns: (intact, reason)
        """
        if filepath not in self.integrity_hashes:
            return True, "Not monitored"

        current_hash = self.compute_file_hash(filepath)
        stored_hash = self.integrity_hashes[filepath]["hash"]

        if current_hash != stored_hash:
            self._log_event(SecurityEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="integrity_violation",
                severity="critical",
                source=filepath,
                details=f"File hash changed from {stored_hash[:16]}... to {current_hash[:16]}...",
                action_taken="Alert raised",
                blocked=False
            ))
            return False, "TAMPERED: File hash mismatch"

        return True, "Intact"

    def check_all_integrity(self) -> List[Tuple[str, bool, str]]:
        """Check integrity of all monitored files."""
        results = []
        for filepath in self.integrity_hashes.keys():
            intact, reason = self.check_integrity(filepath)
            results.append((filepath, intact, reason))
        return results

    # ========================================================================
    # URL VALIDATION
    # ========================================================================

    def validate_url(self, url: str, source: str = "unknown") -> Tuple[bool, str]:
        """
        Validate a URL before fetching.

        Returns: (safe, reason)
        """
        if not url:
            return False, "Empty URL"

        # Check for allowed domains
        url_lower = url.lower()

        # Block internal network access
        internal_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
            r'192\.168\.',
            r'10\.',
            r'172\.(1[6-9]|2[0-9]|3[0-1])\.',
            r'::1',
            r'0\.0\.0\.0',
        ]

        for pattern in internal_patterns:
            if re.search(pattern, url_lower):
                self._log_event(SecurityEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type="ssrf_attempt",
                    severity="high",
                    source=source,
                    details=f"Internal network access blocked: {url[:100]}",
                    action_taken="URL rejected",
                    blocked=True
                ))
                return False, "BLOCKED: Internal network access not allowed"

        # Check for file:// protocol
        if url_lower.startswith('file://'):
            return False, "BLOCKED: file:// protocol not allowed"

        return True, "OK"

    # ========================================================================
    # CREDENTIAL PROTECTION
    # ========================================================================

    def protect_credentials(self, text: str) -> str:
        """
        Redact any credentials found in text.

        Returns sanitized text.
        """
        patterns = [
            (r'(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', r'\1=***REDACTED***'),
            (r'(secret|token|password|pwd)\s*[=:]\s*["\']?([^\s"\']+)["\']?', r'\1=***REDACTED***'),
            (r'(sk-[a-zA-Z0-9]{20,})', '***REDACTED_KEY***'),
            (r'(ghp_[a-zA-Z0-9]{20,})', '***REDACTED_GH***'),
            (r'(0x[a-fA-F0-9]{40})', '***REDACTED_ADDR***'),
        ]

        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    # ========================================================================
    # SAFE EXECUTION WRAPPER
    # ========================================================================

    def safe_execute(self, func, *args, source: str = "unknown", **kwargs) -> Any:
        """
        Safely execute a function with security checks.

        Returns function result or raises SecurityError.
        """
        # Rate limit
        allowed, reason = self.check_rate_limit(f"exec:{source}")
        if not allowed:
            raise SecurityError(reason)

        # Log execution
        self._log_event(SecurityEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="audit",
            severity="low",
            source=source,
            details=f"Executing: {func.__name__}",
            action_taken="Allowed",
            blocked=False
        ))

        try:
            return func(*args, **kwargs)
        except Exception as e:
            self._log_event(SecurityEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type="execution_error",
                severity="medium",
                source=source,
                details=f"Error in {func.__name__}: {str(e)[:200]}",
                action_taken="Logged",
                blocked=False
            ))
            raise

    # ========================================================================
    # STATUS
    # ========================================================================

    def get_status(self) -> Dict:
        """Get security status."""
        # Count recent events
        events_24h = 0
        blocked_24h = 0
        critical_24h = 0

        cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

        if SECURITY_LOG.exists():
            with open(SECURITY_LOG) as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get('timestamp', '') > cutoff:
                            events_24h += 1
                            if event.get('blocked'):
                                blocked_24h += 1
                            if event.get('severity') == 'critical':
                                critical_24h += 1
                    except:
                        pass

        return {
            "master": MASTER,
            "status": "ACTIVE",
            "events_24h": events_24h,
            "blocked_24h": blocked_24h,
            "critical_24h": critical_24h,
            "monitored_files": len(self.integrity_hashes),
            "active_rate_limits": len(self.rate_limits),
            "protection_layers": [
                "Command validation",
                "Code injection prevention",
                "Input sanitization",
                "Rate limiting",
                "Integrity monitoring",
                "URL validation",
                "Credential protection"
            ]
        }


class SecurityError(Exception):
    """Security violation exception."""
    pass


# Global instance
_immunity: Optional[SystemImmunity] = None


def get_immunity() -> SystemImmunity:
    """Get or create global immunity instance."""
    global _immunity
    if _immunity is None:
        _immunity = SystemImmunity()
    return _immunity


# ============================================================================
# DECORATOR FOR SAFE FUNCTIONS
# ============================================================================

def secure(rate_limit: int = 100, window: int = 60):
    """
    Decorator to make functions secure.

    Usage:
        @secure(rate_limit=10, window=60)
        def my_function(x):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            immunity = get_immunity()

            # Rate limit check
            allowed, reason = immunity.check_rate_limit(
                f"func:{func.__name__}", rate_limit, window
            )
            if not allowed:
                raise SecurityError(reason)

            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_command_input(command: str) -> Tuple[bool, str]:
    """Convenience function to validate command."""
    return get_immunity().validate_command(command)


def validate_code_input(code: str) -> Tuple[bool, str]:
    """Convenience function to validate code."""
    return get_immunity().validate_code(code)


# CLI
def main():
    import argparse

    parser = argparse.ArgumentParser(description="System Immunity")
    parser.add_argument("command", choices=["status", "check-cmd", "check-code", "integrity", "events"])
    parser.add_argument("--input", help="Input to check")
    parser.add_argument("--file", help="File for integrity")

    args = parser.parse_args()
    immunity = get_immunity()

    if args.command == "status":
        status = immunity.get_status()
        print(f"\n{'='*60}")
        print("SYSTEM IMMUNITY STATUS")
        print(f"{'='*60}")
        print(f"Master: {status['master']}")
        print(f"Status: {status['status']}")
        print(f"\nLast 24 hours:")
        print(f"  Events: {status['events_24h']}")
        print(f"  Blocked: {status['blocked_24h']}")
        print(f"  Critical: {status['critical_24h']}")
        print(f"\nProtection layers:")
        for layer in status['protection_layers']:
            print(f"  - {layer}")
        print(f"\nMonitored files: {status['monitored_files']}")

    elif args.command == "check-cmd":
        if not args.input:
            print("Error: --input required")
            return
        safe, reason = immunity.validate_command(args.input)
        print(f"Command: {args.input[:50]}...")
        print(f"Safe: {safe}")
        print(f"Reason: {reason}")

    elif args.command == "check-code":
        if not args.input:
            print("Error: --input required")
            return
        safe, reason = immunity.validate_code(args.input)
        print(f"Code check result: {reason}")

    elif args.command == "integrity":
        if args.file:
            # Register file
            immunity.register_integrity(args.file)
            print(f"Registered: {args.file}")
        else:
            # Check all
            results = immunity.check_all_integrity()
            print(f"\n{'='*60}")
            print("INTEGRITY CHECK")
            print(f"{'='*60}")
            for filepath, intact, reason in results:
                status = "OK" if intact else "TAMPERED"
                print(f"  [{status}] {filepath}")

    elif args.command == "events":
        print(f"\n{'='*60}")
        print("RECENT SECURITY EVENTS")
        print(f"{'='*60}")
        if SECURITY_LOG.exists():
            with open(SECURITY_LOG) as f:
                lines = f.readlines()
                for line in lines[-20:]:
                    try:
                        event = json.loads(line)
                        status = "BLOCKED" if event.get('blocked') else "LOGGED"
                        print(f"  [{event['severity'].upper()}] [{status}] {event['event_type']}")
                        print(f"      {event['details'][:60]}")
                    except:
                        pass


if __name__ == "__main__":
    main()
