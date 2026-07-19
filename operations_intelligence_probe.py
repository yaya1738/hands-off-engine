from ai.factory.runtime import FactoryRuntime
from ai.factory.operations_intelligence import (
    FactoryOperationsIntelligence,
)

factory = FactoryRuntime()

intel = FactoryOperationsIntelligence(factory)

print(intel.generate_report())
