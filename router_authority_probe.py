from pathlib import Path
import inspect

from ai.factory.action_router import ActionRouter

print("ACTION ROUTER")
print("=" * 30)

router = ActionRouter()

print(inspect.getsource(router.execute))

print("\nAUTONOMOUS LOOP")
print("=" * 30)

path = Path("ai/factory/autonomous_loop.py")

if path.exists():
    text = path.read_text(errors="ignore")
    start = text.find("def")
    print(text[start:start+1500])
