from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

source = inspect.getsource(
    FactoryRuntime.run_checkpoint_cycle
)

print({
    "status": "ANALYZED",
    "has_record_experience": "record_experience" in source,
    "has_learning_reference": "learning" in source,
    "return_count": source.count("return"),
    "safe_stop_present": "SAFE_STOP" in source,
    "checkpoint_executor_present": "checkpoint_executor" in source
})
