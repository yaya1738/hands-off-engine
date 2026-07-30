import json

data=json.load(open("factory_capability_runtime_map.json"))

groups={
    "execution": [],
    "decision": [],
    "learning_memory": [],
    "governance": [],
    "other": []
}

for name,obj in data.items():

    text=(name+" "+obj["type"]+" "+obj["module"]).lower()

    if any(x in text for x in [
        "executor",
        "execution",
        "runner",
        "scheduler",
        "orchestrator",
        "action"
    ]):
        groups["execution"].append((name,obj["type"]))

    elif any(x in text for x in [
        "decision",
        "policy",
        "strategy",
        "planner"
    ]):
        groups["decision"].append((name,obj["type"]))

    elif any(x in text for x in [
        "learning",
        "memory",
        "feedback",
        "knowledge"
    ]):
        groups["learning_memory"].append((name,obj["type"]))

    elif any(x in text for x in [
        "audit",
        "authority",
        "governance",
        "control",
        "supervisor"
    ]):
        groups["governance"].append((name,obj["type"]))

    else:
        groups["other"].append((name,obj["type"]))

for k,v in groups.items():
    print("\n====",k.upper(),"====")
    print("count:",len(v))
    for item in v[:40]:
        print(item)
