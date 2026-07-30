from pathlib import Path

patch = r'''#!/usr/bin/env python3
from pathlib import Path

TARGET = Path("ai/factory/runtime.py")

def main():
    if not TARGET.exists():
        raise SystemExit(f"Missing {TARGET}")

    source = TARGET.read_text()

    marker = "checkpoint_metadata_bridge"

    if marker in source:
        print({
            "status": "ALREADY_INSTALLED",
            "target": str(TARGET),
        })
        return

    addition = r'''

    # checkpoint_metadata_bridge
    #
    # Attach autonomous improvement context before checkpoint execution.
    # This keeps checkpoint history useful for recovery and analysis.

    def build_checkpoint_context(self, improvement=None, result=None):
        return {
            "type": "autonomous_improvement",
            "improvement": improvement or {},
            "execution_result": result or {},
            "audit_context": {
                "component": "FactoryRuntime",
                "source": "autonomous_improvement_loop",
            },
            "validation": {
                "status": "recorded",
            },
            "rollback_context": {
                "available": True,
            },
        }

'''

    # Add helper near end of class before final history initialization
    anchor = "self._history: List[Dict[str, Any]] = []"

    if anchor not in source:
        raise SystemExit("Could not find runtime insertion point")

    source = source.replace(
        anchor,
        addition + "\n" + anchor,
        1,
    )

    TARGET.write_text(source)

    print({
        "status": "CHECKPOINT_METADATA_BRIDGE_PATCHED",
        "target": str(TARGET),
    })


if __name__ == "__main__":
    main()
'''

Path("add_checkpoint_metadata_bridge.py").write_text(patch)

print({
    "status": "CREATED",
    "script": "add_checkpoint_metadata_bridge.py",
})
