#!/usr/bin/env python3
"""Retired unsafe income-activation entry point.

Historical versions embedded notification credentials and performed side effects
outside the governed Factory authority boundary. This compatibility facade is
intentionally fail-closed.
"""

def main():
    raise RuntimeError(
        "scripts.activate_income_now is retired: notification, state mutation, "
        "and any external side effect must use the governed Factory runtime."
    )

if __name__ == "__main__":
    main()
