from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("OPTION OUTPUT CONTRACT")
print("=" * 35)

for component_name in [
    "improvement_planner",
    "planning",
    "strategy_manager",
]:
    component = getattr(factory, component_name, None)

    if component:
        print("\nCOMPONENT:", component_name)

        for method in dir(component):
            if not method.startswith("_"):
                if any(x in method.lower() for x in [
                    "plan",
                    "recommend",
                    "option",
                    "strategy",
                    "select",
                ]):
                    print("METHOD:", method)

print("\nDONE")
