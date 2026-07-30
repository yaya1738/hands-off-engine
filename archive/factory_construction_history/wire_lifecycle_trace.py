from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

if "from ai.factory.lifecycle_trace import FactoryLifecycleTrace" not in text:
    text = text.replace(
        "from ai.factory.development_pipeline import FactoryDevelopmentPipeline",
        "from ai.factory.development_pipeline import FactoryDevelopmentPipeline\nfrom ai.factory.lifecycle_trace import FactoryLifecycleTrace",
    )

if "self.lifecycle_trace = FactoryLifecycleTrace(self)" not in text:
    text = text.replace(
        "self.development_pipeline = FactoryDevelopmentPipeline(",
        "self.lifecycle_trace = None\n\n        self.development_pipeline = FactoryDevelopmentPipeline(",
    )

    text = text.replace(
        "self.improvement_executor = FactoryImprovementExecutor()",
        "self.lifecycle_trace = FactoryLifecycleTrace(self)\n\n        self.improvement_executor = FactoryImprovementExecutor()",
    )

p.write_text(text)

print("UPDATED")
