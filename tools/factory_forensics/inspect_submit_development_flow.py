from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

print(inspect.getsource(r.submit_development_request))
