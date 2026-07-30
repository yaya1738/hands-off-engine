from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

print(inspect.getsource(r.action_router.route))
print("----IMPROVEMENT----")
print(inspect.getsource(r.action_router.improvement))
