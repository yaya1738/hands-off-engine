from pathlib import Path

target = Path("ai/factory/runtime.py")

source = target.read_text()

marker = "# checkpoint_metadata_bridge"

if marker in source:
    print({
        "status": "ALREADY_INSTALLED"
    })
    raise SystemExit

method = '''
    # checkpoint_metadata_bridge

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

anchor = "        self._history: List[Dict[str, Any]] = []"

if anchor not in source:
    raise SystemExit("Insertion point not found")

source = source.replace(
    anchor,
    method + anchor,
    1,
)

target.write_text(source)

print({
    "status": "CHECKPOINT_METADATA_BRIDGE_PATCHED",
    "target": str(target),
})
