"""
Benefit Gate - Others only access when it benefits Yair Siegel

Access Types:
1. INCOME - They pay you or bring revenue
2. GROWTH - They help grow your systems  
3. KNOWLEDGE - They provide valuable information
4. NETWORK - They connect you to valuable people/resources

If no benefit = NO ACCESS
"""

import json
from datetime import datetime
from pathlib import Path
from enum import Enum

class BenefitType(Enum):
    INCOME = "income"          # Pays money
    GROWTH = "growth"          # Helps scale
    KNOWLEDGE = "knowledge"    # Provides intel
    NETWORK = "network"        # Connections

BENEFIT_LOG = Path("/root/hands-off-engine/security/benefits_received.jsonl")
ACCESS_TOKENS = Path("/root/hands-off-engine/security/access_tokens.json")

def grant_benefit_access(
    entity: str, 
    benefit_type: BenefitType,
    benefit_value: str,
    access_scope: list,
    duration_hours: int = 24
) -> dict:
    """
    Grant access based on benefit provided
    
    Example:
        grant_benefit_access(
            entity="client@example.com",
            benefit_type=BenefitType.INCOME,
            benefit_value="$500 consulting payment",
            access_scope=["read_reports", "api_limited"],
            duration_hours=720  # 30 days
        )
    """
    import secrets
    
    token = {
        "token": secrets.token_urlsafe(32),
        "entity": entity,
        "benefit_type": benefit_type.value,
        "benefit_value": benefit_value,
        "scope": access_scope,
        "created": datetime.now().isoformat(),
        "expires": datetime.now().timestamp() + (duration_hours * 3600),
        "revoked": False
    }
    
    tokens = []
    if ACCESS_TOKENS.exists():
        tokens = json.loads(ACCESS_TOKENS.read_text())
    tokens.append(token)
    ACCESS_TOKENS.write_text(json.dumps(tokens, indent=2))
    
    # Log the benefit
    log_benefit(entity, benefit_type, benefit_value)
    
    return {"token": token["token"], "expires_in_hours": duration_hours}

def log_benefit(entity: str, benefit_type: BenefitType, value: str):
    """Track all benefits received"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "from": entity,
        "type": benefit_type.value,
        "value": value
    }
    with open(BENEFIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def validate_token(token: str) -> dict:
    """Check if token is valid and what access it grants"""
    if not ACCESS_TOKENS.exists():
        return {"valid": False, "reason": "No tokens exist"}
    
    tokens = json.loads(ACCESS_TOKENS.read_text())
    for t in tokens:
        if t["token"] == token:
            if t["revoked"]:
                return {"valid": False, "reason": "Token revoked"}
            if datetime.now().timestamp() > t["expires"]:
                return {"valid": False, "reason": "Token expired"}
            return {
                "valid": True,
                "entity": t["entity"],
                "scope": t["scope"],
                "benefit_provided": t["benefit_value"]
            }
    
    return {"valid": False, "reason": "Token not found"}

def revoke_access(entity: str = None, token: str = None):
    """Revoke access if benefit stops or entity misbehaves"""
    if not ACCESS_TOKENS.exists():
        return {"error": "No tokens"}
    
    tokens = json.loads(ACCESS_TOKENS.read_text())
    revoked = 0
    for t in tokens:
        if (entity and t["entity"] == entity) or (token and t["token"] == token):
            t["revoked"] = True
            revoked += 1
    
    ACCESS_TOKENS.write_text(json.dumps(tokens, indent=2))
    return {"revoked": revoked}

def list_active_access():
    """Show who has access and why"""
    if not ACCESS_TOKENS.exists():
        return []
    
    tokens = json.loads(ACCESS_TOKENS.read_text())
    active = []
    for t in tokens:
        if not t["revoked"] and datetime.now().timestamp() < t["expires"]:
            active.append({
                "entity": t["entity"],
                "benefit": t["benefit_value"],
                "scope": t["scope"],
                "expires": datetime.fromtimestamp(t["expires"]).isoformat()
            })
    return active

# Access scopes available
SCOPES = {
    "read_reports": "Can view trading reports",
    "api_limited": "Limited API access (100 req/day)",
    "api_full": "Full API access",
    "ssh_readonly": "SSH with read-only commands",
    "collaborate": "Can submit code/suggestions for review"
}

if __name__ == "__main__":
    print("Benefit Gate Active")
    print("Access requires providing value to Yair Siegel")
    print(f"Available scopes: {list(SCOPES.keys())}")
