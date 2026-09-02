"""Read-only identity compatibility facade.

Identity assertions must not derive authority from shell inspection, process
inspection, network identity, or mutable audit state. Callers requiring an
identity-backed privileged action must use the central Factory authority path.
"""
from functools import wraps

MASTER_IDENTITY = {
    "name": "Yair Siegel",
    "email": "siegel.yaz@gmail.com",
}


def is_yair():
    return {
        "is_master": False,
        "confidence": 0.0,
        "signals": [],
        "identity": "Unknown",
        "authority_required": "FactoryAuthorityGateway",
        "disabled": True,
    }


def am_i_yair():
    return False


def whoami():
    return "Unknown (identity authority unavailable)"


def require_yair(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        raise PermissionError(
            "[FACTORY-AUTHORITY] identity authorization is disabled; "
            "submit the privileged request through FactoryAuthorityGateway"
        )
    return wrapper


if __name__ == "__main__":
    print(is_yair())
