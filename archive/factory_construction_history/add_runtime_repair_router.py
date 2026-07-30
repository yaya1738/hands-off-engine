from pathlib import Path

path = Path("ai/factory/runtime.py")

source = path.read_text()

if "def route_autonomous_failure_repair" in source:
    print({"status": "ALREADY_EXISTS"})
    raise SystemExit

anchor = "    def run_autonomous_improvement(self):\n"

method = '''
    def route_autonomous_failure_repair(self, failure):
        if hasattr(self, "integration_supervisor"):
            return {
                "status": "REPAIR_ROUTED_TO_SUPERVISOR",
                "failure": failure,
                "supervisor": self.integration_supervisor.inspect(),
            }

        return {
            "status": "NO_REPAIR_ROUTER_AVAILABLE",
            "failure": failure,
        }

'''

if anchor not in source:
    print({"status": "ANCHOR_NOT_FOUND"})
    raise SystemExit

source = source.replace(anchor, method + anchor)

path.write_text(source)

print({
    "status": "RUNTIME_REPAIR_ROUTER_ADDED",
    "target": str(path),
})
