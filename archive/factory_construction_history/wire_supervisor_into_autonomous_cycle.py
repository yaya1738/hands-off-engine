from pathlib import Path

target = Path("ai/factory/runtime.py")

lines = target.read_text().splitlines()

if any("integration_supervisor_gate" in line for line in lines):
    print({"status": "ALREADY_INSTALLED"})
    raise SystemExit

anchor_index = None

for i, line in enumerate(lines):
    if line.strip() == "def run_autonomous_improvement(self):":
        anchor_index = i
        break

if anchor_index is None:
    raise SystemExit("run_autonomous_improvement not found")

insert = [
    "",
    "        # integration_supervisor_gate",
    "        if hasattr(self, \"integration_supervisor\"):",
    "            integration_report = self.integration_supervisor.inspect()",
    "",
    "            if not integration_report.get(\"healthy\", False):",
    "                return {",
    "                    \"status\": \"INTEGRATION_UNHEALTHY\",",
    "                    \"integration_report\": integration_report,",
    "                }",
    "",
]

lines[anchor_index + 1:anchor_index + 1] = insert

target.write_text("\n".join(lines) + "\n")

print({
    "status": "SUPERVISOR_GATE_INSTALLED",
    "target": str(target),
})
