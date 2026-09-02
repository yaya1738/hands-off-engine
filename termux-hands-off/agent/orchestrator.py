"""Legacy Termux orchestrator compatibility facade.

The former implementation executed fetchers, Telegram/IFTTT pushes and
persisted state directly. Operational scheduling and execution are now owned
by the Factory authority path. This module performs no process execution or
state mutation.
"""


def run(cmd):
    return "[FACTORY-AUTHORITY] legacy command execution is disabled; submit through FactoryAuthorityGateway"


def build_master():
    return {
        "authority": "FactoryAuthorityGateway",
        "disabled": True,
    }


def main():
    return build_master()


if __name__ == "__main__":
    print(main())
