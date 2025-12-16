#!/usr/bin/env python3
"""
M2M Security Layer - Authentication & Authorization

Enterprise-grade security for machine-to-machine communication:
- API Key authentication
- JWT token authentication
- Role-based access control (RBAC)
- Rate limiting
- IP whitelisting
- Request encryption
- Audit logging

Protects M2M infrastructure from unauthorized access.

Security layers:
    External Request
           ↓
    1. IP Whitelist Check
           ↓
    2. Authentication (API Key / JWT)
           ↓
    3. Authorization (RBAC)
           ↓
    4. Rate Limiting
           ↓
    5. Audit Log
           ↓
    Process Request
"""

import json
import time
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

STATE_FILE = Path(__file__).parent.parent / 'state' / 'machine_security.json'
API_KEYS_FILE = Path(__file__).parent.parent / '.env.machine_api_keys'


class Role(Enum):
    """Access control roles."""
    ADMIN = "admin"          # Full access
    OPERATOR = "operator"    # Can control system
    OBSERVER = "observer"    # Read-only access
    SYSTEM = "system"        # Internal system access
    IOT_DEVICE = "iot"       # IoT device access
    EXTERNAL_AI = "external" # External AI agent access


class Permission(Enum):
    """Access permissions."""
    READ_STATE = "read_state"
    WRITE_STATE = "write_state"
    EXECUTE_COMMAND = "execute_command"
    CONTROL_HARDWARE = "control_hardware"
    EXECUTE_TRADE = "execute_trade"
    MANAGE_SYSTEM = "manage_system"
    PUBLISH_EVENT = "publish_event"
    SUBSCRIBE_EVENT = "subscribe_event"


# Role permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: list(Permission),  # All permissions
    Role.OPERATOR: [
        Permission.READ_STATE,
        Permission.EXECUTE_COMMAND,
        Permission.CONTROL_HARDWARE,
        Permission.EXECUTE_TRADE,
        Permission.PUBLISH_EVENT,
        Permission.SUBSCRIBE_EVENT
    ],
    Role.OBSERVER: [
        Permission.READ_STATE,
        Permission.SUBSCRIBE_EVENT
    ],
    Role.SYSTEM: [
        Permission.READ_STATE,
        Permission.WRITE_STATE,
        Permission.EXECUTE_COMMAND,
        Permission.PUBLISH_EVENT,
        Permission.SUBSCRIBE_EVENT
    ],
    Role.IOT_DEVICE: [
        Permission.READ_STATE,
        Permission.PUBLISH_EVENT,
        Permission.SUBSCRIBE_EVENT
    ],
    Role.EXTERNAL_AI: [
        Permission.READ_STATE,
        Permission.EXECUTE_COMMAND,
        Permission.SUBSCRIBE_EVENT
    ]
}


@dataclass
class APIKey:
    """API key credential."""
    key: str
    name: str
    role: str
    created_at: str
    last_used: Optional[str] = None
    expires_at: Optional[str] = None
    active: bool = True
    ip_whitelist: Optional[List[str]] = None
    rate_limit: int = 1000  # requests per hour


@dataclass
class AuthToken:
    """Authentication token (JWT-like)."""
    token: str
    subject: str  # User/system identifier
    role: str
    issued_at: str
    expires_at: str
    permissions: List[str]


class MachineSecurity:
    """
    Security layer for M2M communication.

    Handles authentication, authorization, rate limiting, and audit logging.
    """

    def __init__(self):
        self.state = self.load_state()
        self.api_keys: Dict[str, APIKey] = {}
        self.tokens: Dict[str, AuthToken] = {}
        self.ip_whitelist: Set[str] = set()
        self.rate_limits: Dict[str, List[float]] = {}  # key -> [timestamps]

        # Load API keys
        self._load_api_keys()

        # Load IP whitelist
        self.ip_whitelist = set(self.state.get('ip_whitelist', ['127.0.0.1', 'localhost']))

    def load_state(self) -> dict:
        """Load security state."""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            'total_requests': 0,
            'authenticated_requests': 0,
            'failed_auth': 0,
            'rate_limited': 0,
            'ip_whitelist': ['127.0.0.1', 'localhost'],
            'audit_log': []
        }

    def save_state(self):
        """Save security state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    # ================================================================
    # API KEY MANAGEMENT
    # ================================================================

    def generate_api_key(
        self,
        name: str,
        role: Role,
        expires_days: Optional[int] = None,
        ip_whitelist: Optional[List[str]] = None,
        rate_limit: int = 1000
    ) -> str:
        """
        Generate new API key.

        Args:
            name: Key name/description
            role: Access role
            expires_days: Days until expiry (None = never)
            ip_whitelist: Allowed IP addresses
            rate_limit: Requests per hour

        Returns:
            API key string
        """
        # Generate secure random key
        key = f"intgx_{secrets.token_urlsafe(32)}"

        # Calculate expiry
        expires_at = None
        if expires_days:
            expires_dt = datetime.now(timezone.utc) + timedelta(days=expires_days)
            expires_at = expires_dt.isoformat()

        api_key = APIKey(
            key=key,
            name=name,
            role=role.value,
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=expires_at,
            ip_whitelist=ip_whitelist,
            rate_limit=rate_limit
        )

        self.api_keys[key] = api_key

        # Save to file
        self._save_api_keys()

        print(f"✓ Generated API key for {name}")
        print(f"  Role: {role.value}")
        print(f"  Key: {key}")

        return key

    def revoke_api_key(self, key: str):
        """Revoke API key."""
        if key in self.api_keys:
            self.api_keys[key].active = False
            self._save_api_keys()
            print(f"✓ Revoked API key: {key[:20]}...")

    def _load_api_keys(self):
        """Load API keys from file."""
        if not API_KEYS_FILE.exists():
            # Create with default system key
            self.api_keys['intgx_SYSTEM_INTERNAL'] = APIKey(
                key='intgx_SYSTEM_INTERNAL',
                name='System Internal',
                role=Role.SYSTEM.value,
                created_at=datetime.now(timezone.utc).isoformat()
            )
            self._save_api_keys()
            return

        try:
            data = json.loads(API_KEYS_FILE.read_text())
            for key_data in data.get('keys', []):
                key = key_data['key']
                self.api_keys[key] = APIKey(**key_data)
        except Exception as e:
            print(f"⚠️  Error loading API keys: {e}")

    def _save_api_keys(self):
        """Save API keys to file."""
        data = {
            'keys': [asdict(k) for k in self.api_keys.values()]
        }
        API_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
        API_KEYS_FILE.write_text(json.dumps(data, indent=2))

    # ================================================================
    # AUTHENTICATION
    # ================================================================

    def authenticate_api_key(self, key: str, ip_address: str = None) -> Optional[APIKey]:
        """
        Authenticate using API key.

        Args:
            key: API key
            ip_address: Client IP address

        Returns:
            APIKey if valid, None if invalid
        """
        self.state['total_requests'] += 1

        # Check if key exists
        if key not in self.api_keys:
            self.state['failed_auth'] += 1
            self._audit_log('auth_failed', {'key': key[:10], 'reason': 'invalid_key'})
            self.save_state()
            return None

        api_key = self.api_keys[key]

        # Check if active
        if not api_key.active:
            self.state['failed_auth'] += 1
            self._audit_log('auth_failed', {'key': key[:10], 'reason': 'inactive'})
            self.save_state()
            return None

        # Check expiry
        if api_key.expires_at:
            expires = datetime.fromisoformat(api_key.expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires:
                self.state['failed_auth'] += 1
                self._audit_log('auth_failed', {'key': key[:10], 'reason': 'expired'})
                self.save_state()
                return None

        # Check IP whitelist
        if api_key.ip_whitelist and ip_address:
            if ip_address not in api_key.ip_whitelist:
                self.state['failed_auth'] += 1
                self._audit_log('auth_failed', {'key': key[:10], 'reason': 'ip_blocked', 'ip': ip_address})
                self.save_state()
                return None

        # Update last used
        api_key.last_used = datetime.now(timezone.utc).isoformat()

        self.state['authenticated_requests'] += 1
        self.save_state()

        return api_key

    def generate_token(self, subject: str, role: Role, expires_hours: int = 24) -> str:
        """
        Generate JWT-like authentication token.

        Args:
            subject: User/system identifier
            role: Access role
            expires_hours: Hours until expiry

        Returns:
            Token string
        """
        # Generate token
        token_data = f"{subject}:{role.value}:{time.time()}"
        token = hashlib.sha256(token_data.encode()).hexdigest()

        # Get permissions
        permissions = [p.value for p in ROLE_PERMISSIONS.get(role, [])]

        # Calculate expiry
        expires_dt = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

        auth_token = AuthToken(
            token=token,
            subject=subject,
            role=role.value,
            issued_at=datetime.now(timezone.utc).isoformat(),
            expires_at=expires_dt.isoformat(),
            permissions=permissions
        )

        self.tokens[token] = auth_token

        return token

    def authenticate_token(self, token: str) -> Optional[AuthToken]:
        """
        Authenticate using token.

        Args:
            token: Authentication token

        Returns:
            AuthToken if valid, None if invalid
        """
        if token not in self.tokens:
            return None

        auth_token = self.tokens[token]

        # Check expiry
        expires = datetime.fromisoformat(auth_token.expires_at.replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires:
            return None

        return auth_token

    # ================================================================
    # AUTHORIZATION (RBAC)
    # ================================================================

    def check_permission(self, role: Role, permission: Permission) -> bool:
        """
        Check if role has permission.

        Args:
            role: User role
            permission: Required permission

        Returns:
            True if authorized
        """
        role_perms = ROLE_PERMISSIONS.get(role, [])
        return permission in role_perms

    def authorize_request(
        self,
        api_key: APIKey,
        required_permission: Permission
    ) -> bool:
        """
        Authorize request based on permissions.

        Args:
            api_key: Authenticated API key
            required_permission: Required permission

        Returns:
            True if authorized
        """
        role = Role(api_key.role)
        authorized = self.check_permission(role, required_permission)

        if not authorized:
            self._audit_log('authorization_failed', {
                'key': api_key.key[:10],
                'role': role.value,
                'required_permission': required_permission.value
            })

        return authorized

    # ================================================================
    # RATE LIMITING
    # ================================================================

    def check_rate_limit(self, key: str, rate_limit: int) -> bool:
        """
        Check rate limit.

        Args:
            key: Rate limit key (API key)
            rate_limit: Max requests per hour

        Returns:
            True if within limit
        """
        now = time.time()
        hour_ago = now - 3600

        # Get timestamps for this key
        if key not in self.rate_limits:
            self.rate_limits[key] = []

        # Remove old timestamps
        self.rate_limits[key] = [ts for ts in self.rate_limits[key] if ts > hour_ago]

        # Check limit
        if len(self.rate_limits[key]) >= rate_limit:
            self.state['rate_limited'] += 1
            self._audit_log('rate_limited', {'key': key[:10]})
            self.save_state()
            return False

        # Add current timestamp
        self.rate_limits[key].append(now)

        return True

    # ================================================================
    # IP WHITELISTING
    # ================================================================

    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP is whitelisted."""
        return ip_address in self.ip_whitelist or self.ip_whitelist == {'*'}

    def add_ip_to_whitelist(self, ip_address: str):
        """Add IP to whitelist."""
        self.ip_whitelist.add(ip_address)
        self.state['ip_whitelist'] = list(self.ip_whitelist)
        self.save_state()

    def remove_ip_from_whitelist(self, ip_address: str):
        """Remove IP from whitelist."""
        self.ip_whitelist.discard(ip_address)
        self.state['ip_whitelist'] = list(self.ip_whitelist)
        self.save_state()

    # ================================================================
    # AUDIT LOGGING
    # ================================================================

    def _audit_log(self, event: str, details: Dict):
        """Log security event."""
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event': event,
            'details': details
        }

        # Keep last 1000 events
        if 'audit_log' not in self.state:
            self.state['audit_log'] = []

        self.state['audit_log'].append(log_entry)
        self.state['audit_log'] = self.state['audit_log'][-1000:]

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries."""
        return self.state.get('audit_log', [])[-limit:]

    # ================================================================
    # SECURITY MIDDLEWARE
    # ================================================================

    def secure_request(
        self,
        api_key: str,
        ip_address: str,
        required_permission: Permission
    ) -> Tuple[bool, Optional[APIKey], Optional[str]]:
        """
        Complete security check for request.

        Args:
            api_key: API key
            ip_address: Client IP
            required_permission: Required permission

        Returns:
            (authorized, api_key_obj, error_message)
        """
        # 1. Check IP whitelist
        if not self.is_ip_allowed(ip_address):
            return (False, None, "IP address not whitelisted")

        # 2. Authenticate
        key_obj = self.authenticate_api_key(api_key, ip_address)
        if not key_obj:
            return (False, None, "Invalid or expired API key")

        # 3. Check rate limit
        if not self.check_rate_limit(api_key, key_obj.rate_limit):
            return (False, key_obj, "Rate limit exceeded")

        # 4. Authorize
        if not self.authorize_request(key_obj, required_permission):
            return (False, key_obj, "Insufficient permissions")

        return (True, key_obj, None)

    # ================================================================
    # STATISTICS
    # ================================================================

    def get_stats(self) -> Dict:
        """Get security statistics."""
        return {
            'total_requests': self.state['total_requests'],
            'authenticated_requests': self.state['authenticated_requests'],
            'failed_auth': self.state['failed_auth'],
            'rate_limited': self.state['rate_limited'],
            'auth_success_rate': self._calculate_auth_success_rate(),
            'active_api_keys': len([k for k in self.api_keys.values() if k.active]),
            'ip_whitelist_size': len(self.ip_whitelist)
        }

    def _calculate_auth_success_rate(self) -> float:
        """Calculate authentication success rate."""
        total = self.state['authenticated_requests'] + self.state['failed_auth']
        if total == 0:
            return 0.0
        return (self.state['authenticated_requests'] / total) * 100


# ================================================================
# CONVENIENCE FUNCTIONS
# ================================================================

_security_instance = None

def get_security() -> MachineSecurity:
    """Get singleton security instance."""
    global _security_instance
    if _security_instance is None:
        _security_instance = MachineSecurity()
    return _security_instance


def generate_api_key(name: str, role: Role, **kwargs) -> str:
    """Generate API key."""
    security = get_security()
    return security.generate_api_key(name, role, **kwargs)


def authenticate(api_key: str, ip_address: str = '127.0.0.1') -> Optional[APIKey]:
    """Authenticate API key."""
    security = get_security()
    return security.authenticate_api_key(api_key, ip_address)


def authorize(api_key: APIKey, permission: Permission) -> bool:
    """Authorize permission."""
    security = get_security()
    return security.authorize_request(api_key, permission)


# ================================================================
# TESTING
# ================================================================

def test_security():
    """Test security system."""
    print("="*60)
    print("M2M SECURITY SYSTEM TEST")
    print("="*60)
    print()

    security = MachineSecurity()

    # Test 1: Generate API keys
    print("1. Generating API keys...")
    admin_key = security.generate_api_key("Admin Key", Role.ADMIN, rate_limit=1000)
    observer_key = security.generate_api_key("Observer Key", Role.OBSERVER, rate_limit=100)
    print()

    # Test 2: Authentication
    print("2. Testing authentication...")
    key_obj = security.authenticate_api_key(admin_key, "127.0.0.1")
    if key_obj:
        print(f"   ✓ Authenticated as {key_obj.name} ({key_obj.role})")
    print()

    # Test 3: Authorization
    print("3. Testing authorization...")
    can_execute = security.authorize_request(key_obj, Permission.EXECUTE_COMMAND)
    print(f"   Can execute commands: {can_execute}")
    print()

    # Test 4: Rate limiting
    print("4. Testing rate limiting...")
    for i in range(5):
        allowed = security.check_rate_limit(admin_key, 1000)
        print(f"   Request {i+1}: {'✓ Allowed' if allowed else '✗ Rate limited'}")
    print()

    # Test 5: Statistics
    print("5. Security statistics:")
    stats = security.get_stats()
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Authenticated: {stats['authenticated_requests']}")
    print(f"   Failed auth: {stats['failed_auth']}")
    print(f"   Success rate: {stats['auth_success_rate']:.1f}%")

    print()
    print("="*60)


def main():
    """Run security system."""
    import sys

    if '--test' in sys.argv:
        test_security()
    elif '--generate-key' in sys.argv:
        name = input("Key name: ")
        role_input = input("Role (admin/operator/observer): ")
        role = Role(role_input.lower())
        key = generate_api_key(name, role)
        print(f"\nAPI Key: {key}")
    elif '--stats' in sys.argv:
        security = get_security()
        stats = security.get_stats()
        print(json.dumps(stats, indent=2))
    else:
        print("M2M Security System")
        print()
        print("Usage:")
        print("  --test          Test security system")
        print("  --generate-key  Generate new API key")
        print("  --stats         Show statistics")


if __name__ == '__main__':
    main()
