from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

for name in [
    "run_improvement_cycle",
    "trigger_improvement_pipeline",
    "execute_autonomous_improvements",
    "process_approved_improvement"
]:
    obj = getattr(r, name, None)
    print("\n---", name, "---")
    if obj:
        print(inspect.signature(obj))
        print(inspect.getsource(obj)[:800])
    else:
        print("MISSING")
