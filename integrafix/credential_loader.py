"""
INTEGRAFIX: Unified credential loader for trading execution.

Searches multiple sources for POLYMARKET_PRIVATE_KEY:
1. Environment variable
2. .env file
3. Wallet registry (primary source for this system)
4. Keyring
5. Secrets file
6. Termux sync
"""
import os
import json
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
def load_polymarket_key() -> str:
    """Load Polymarket private key from available sources."""

    # Source 1: Environment variable
    key = os.environ.get("POLYMARKET_PRIVATE_KEY")
    if key:
        return key

    # Source 2: .env file
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().split("\n"):
            if line.startswith("POLYMARKET_PRIVATE_KEY="):
                return line.split("=", 1)[1].strip()

    # Source 3: Wallet registry (INTEGRAFIX: primary source)
    registry_file = BASE_DIR / "state" / "wallets" / "registry.json"
    if registry_file.exists():
        try:
            with open(registry_file) as f:
                registry = json.load(f)
            wallets = registry.get("wallets", {})
            # Look for primary wallet first
            for addr, wallet in wallets.items():
                if wallet.get("alias") == "primary_yair":
                    pk = wallet.get("private_key")
                    if pk:
                        return pk if pk.startswith("0x") else f"0x{pk}"
            # Fallback to first active wallet
            for addr, wallet in wallets.items():
                if wallet.get("status") == "active":
                    pk = wallet.get("private_key")
                    if pk:
                        return pk if pk.startswith("0x") else f"0x{pk}"
        except:
            pass

    # Source 4: Keyring
    try:
        import keyring
        key = keyring.get_password("polymarket", "private_key")
        if key:
            return key
    except:
        pass

    # Source 5: Secrets file
    secrets_file = BASE_DIR / "secrets" / "polymarket.key"
    if secrets_file.exists():
        return secrets_file.read_text().strip()

    # Source 6: Termux sync
    termux_cred = BASE_DIR / "termux-hands-off" / "config" / "credentials.json"
    if termux_cred.exists():
        try:
            data = json.loads(termux_cred.read_text())
            if data.get("polymarket_private_key"):
                return data["polymarket_private_key"]
        except:
            pass

    return None

def get_wallet_address() -> str:
    """Get wallet address from config or registry."""
    # Try config first
    config_file = BASE_DIR / "config" / "trading_config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = json.load(f)
            if config.get("wallet_address"):
                return config.get("wallet_address")
        except:
            pass

    # Try registry
    registry_file = BASE_DIR / "state" / "wallets" / "registry.json"
    if registry_file.exists():
        try:
            with open(registry_file) as f:
                registry = json.load(f)
            wallets = registry.get("wallets", {})
            for addr, wallet in wallets.items():
                if wallet.get("alias") == "primary_yair":
                    return addr
        except:
            pass

    return None
