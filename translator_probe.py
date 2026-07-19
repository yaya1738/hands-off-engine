import inspect
from ai.factory.development_translator import FactoryDevelopmentTranslator

obj = FactoryDevelopmentTranslator()

print("METHODS:")
for m in dir(obj):
    if not m.startswith("_"):
        print("-", m)

print("\nSOURCE:")
print(inspect.getsource(FactoryDevelopmentTranslator))
