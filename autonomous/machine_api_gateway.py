#!/usr/bin/env python3
"""Retired unauthenticated machine command gateway.

The historical gateway bound command, JSON-RPC, and WebSocket mutation routes to
all network interfaces without authentication or the canonical Factory authority
boundary. It is intentionally fail-closed and must not expose a replacement
execution endpoint.
"""

def start_gateway(*_args, **_kwargs):
    raise RuntimeError(
        "autonomous.machine_api_gateway is retired: use the governed Factory "
        "authority boundary for privileged operations."
    )

def main():
    start_gateway()

if __name__ == "__main__":
    main()
