"""Retired direct high-frequency order executor.

Historical versions could load a credential fallback and submit signed orders
directly to an external trading venue, bypassing the canonical Factory authority
boundary. This module is intentionally fail-closed.
"""

class HFTOrderCannon:
    def __init__(self, *_args, **_kwargs):
        raise RuntimeError(
            "executor.hft_order_cannon is retired: direct trading execution is "
            "not authorized through this legacy module."
        )

def main():
    raise RuntimeError(
        "executor.hft_order_cannon is retired and cannot submit external orders."
    )

if __name__ == "__main__":
    main()
