from pathlib import Path

runtime = Path("ai/factory/runtime.py")
text = runtime.read_text()

imp = "from ai.factory.operations_intelligence import FactoryOperationsIntelligence\n"

if imp not in text:
    anchor = "from ai.factory.improvement_executor import FactoryImprovementExecutor\n"
    if anchor not in text:
        raise SystemExit("Runtime import anchor not found")
    text = text.replace(anchor, anchor + imp)

init = "        self.operations_intelligence = FactoryOperationsIntelligence(self)\n"

if init not in text:
    anchor = "        self.decision_option_adapter = FactoryDecisionOptionAdapter()\n"
    if anchor not in text:
        raise SystemExit("Runtime init anchor not found")
    text = text.replace(anchor, anchor + init)

method = '''
    def get_operations_report(self):
        return self.operations_intelligence.generate_report()

'''

if "def get_operations_report(self):" not in text:
    anchor = "    def history(self):\n"
    if anchor in text:
        text = text.replace(anchor, method + anchor)
    else:
        raise SystemExit("Runtime method anchor not found")

runtime.write_text(text)

print("OPERATIONS INTELLIGENCE INTEGRATED")
