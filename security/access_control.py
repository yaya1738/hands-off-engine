#!/usr/bin/env python3
"""
ACCESS CONTROL - Master tool for Yair Siegel
Usage:
    python3 access_control.py status          # Show who has access
    python3 access_control.py pending         # Show pending requests
    python3 access_control.py approve <id>    # Approve a request
    python3 access_control.py revoke <entity> # Revoke access
    python3 access_control.py grant           # Interactive grant
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Import gates
sys.path.insert(0, str(Path(__file__).parent.parent))
from security.identity_gate import (
    is_master, request_access, approve_access, check_access,
    MASTER_IDENTITY, APPROVAL_QUEUE
)
from security.benefit_gate import (
    grant_benefit_access, validate_token, revoke_access as revoke_token,
    list_active_access, BenefitType, SCOPES
)

def show_status():
    """Show current access status"""
    print("=" * 50)
    print("ACCESS CONTROL STATUS")
    print("=" * 50)

    print(f"\nMASTER: {MASTER_IDENTITY['name']}")
    print(f"Email: {MASTER_IDENTITY['email']}")
    print(f"Verified Devices: {len(MASTER_IDENTITY['devices'])}")
    for d in MASTER_IDENTITY['devices']:
        print(f"  - {d}")

    print("\n" + "-" * 50)
    print("ACTIVE EXTERNAL ACCESS:")
    active = list_active_access()
    if not active:
        print("  None - all locked out")
    else:
        for a in active:
            print(f"  Entity: {a['entity']}")
            print(f"    Benefit: {a['benefit']}")
            print(f"    Scope: {a['scope']}")
            print(f"    Expires: {a['expires']}")
            print()

def show_pending():
    """Show pending access requests"""
    print("PENDING ACCESS REQUESTS:")
    if not APPROVAL_QUEUE.exists():
        print("  None")
        return

    queue = json.loads(APPROVAL_QUEUE.read_text())
    pending = [r for r in queue if r['status'] == 'pending']

    if not pending:
        print("  None")
        return

    for r in pending:
        print(f"\n  ID: {r['id']}")
        print(f"  From: {r['requester']}")
        print(f"  Purpose: {r['purpose']}")
        print(f"  Benefit to you: {r['benefit_to_master']}")
        print(f"  Requested: {r['timestamp']}")

def approve(request_id: str, hours: int = 24):
    """Approve a pending request"""
    result = approve_access(request_id, hours)
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Approved: {result['requester']}")
        print(f"Duration: {hours} hours")

def revoke(entity: str):
    """Revoke all access for an entity"""
    result = revoke_token(entity=entity)
    print(f"Revoked {result.get('revoked', 0)} tokens for {entity}")

def interactive_grant():
    """Interactive grant access"""
    print("\nGRANT ACCESS")
    print("-" * 30)

    entity = input("Entity (email/name): ").strip()
    if not entity:
        print("Cancelled")
        return

    print("\nBenefit Types:")
    print("  1) INCOME - They're paying you")
    print("  2) GROWTH - They help scale your systems")
    print("  3) KNOWLEDGE - They provide valuable info")
    print("  4) NETWORK - They connect you to people/resources")

    bt_choice = input("Benefit type [1-4]: ").strip()
    benefit_map = {'1': BenefitType.INCOME, '2': BenefitType.GROWTH,
                   '3': BenefitType.KNOWLEDGE, '4': BenefitType.NETWORK}

    if bt_choice not in benefit_map:
        print("Invalid choice")
        return

    benefit_type = benefit_map[bt_choice]
    benefit_value = input("What benefit are they providing? ").strip()

    print("\nAvailable Scopes:")
    for k, v in SCOPES.items():
        print(f"  {k}: {v}")

    scope_input = input("Scopes (comma-separated): ").strip()
    scopes = [s.strip() for s in scope_input.split(',')]

    hours = int(input("Duration in hours [24]: ").strip() or "24")

    result = grant_benefit_access(entity, benefit_type, benefit_value, scopes, hours)

    print(f"\nAccess granted!")
    print(f"Token: {result['token']}")
    print(f"Expires in: {result['expires_in_hours']} hours")
    print(f"\nGive this token to {entity} for authentication")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "status":
        show_status()
    elif cmd == "pending":
        show_pending()
    elif cmd == "approve" and len(sys.argv) >= 3:
        hours = int(sys.argv[3]) if len(sys.argv) > 3 else 24
        approve(sys.argv[2], hours)
    elif cmd == "revoke" and len(sys.argv) >= 3:
        revoke(sys.argv[2])
    elif cmd == "grant":
        interactive_grant()
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
