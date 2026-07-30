from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

source = inspect.getsource(
    r.get_assessment_metrics
)

print({
    "status": "LOADED",
    "contains_learning_metric": (
        "learning_experience_count" in source
    ),
    "source": source
})
