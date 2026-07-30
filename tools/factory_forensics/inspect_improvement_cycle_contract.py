from ai.factory.runtime import FactoryRuntime
import inspect

source = inspect.getsource(
    FactoryRuntime.run_improvement_cycle
)

print({
    "status": "ANALYZED",
    "source": source,
    "next_action": "BUILD_CONTRACT_TEST"
})
