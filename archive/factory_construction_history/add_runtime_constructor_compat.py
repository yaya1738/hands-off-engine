from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

old = """class FactoryRuntime:
    def __init__(self):
        self.registry = FactoryRegistry()
"""

new = """class FactoryRuntime:
    def __init__(
        self,
        bootstrap=None,
        control_plane=None,
        **kwargs,
    ):
        self.bootstrap = bootstrap
        self.control_plane = control_plane
        self._history = []

        self.registry = FactoryRegistry()
"""

if old not in text:
    raise SystemExit("target block not found")

path.write_text(text.replace(old, new))

print({
    "status": "RUNTIME_CONSTRUCTOR_COMPAT_ADDED",
    "target": "ai/factory/runtime.py"
})
