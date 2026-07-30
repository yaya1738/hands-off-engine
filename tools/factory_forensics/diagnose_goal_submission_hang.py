from ai.factory.runtime import FactoryRuntime
import signal

class Timeout(Exception):
    pass

def handler(signum, frame):
    raise Timeout()

signal.signal(signal.SIGALRM, handler)
signal.alarm(15)

try:
    r = FactoryRuntime()

    goal = {
        "type": "capability_gap",
        "target": "IMPROVEMENT_CHANGE_APPLICATION_LAYER",
        "reason": (
            "Factory identifies and executes improvement goals, "
            "but verified capability changes are not being applied"
        )
    }

    result = r.submit_goal(goal)

    signal.alarm(0)

    print({
        "status": "COMPLETED",
        "result": result
    })

except Timeout:
    print({
        "status": "HUNG",
        "next_action": "CREATE_GOAL_PIPELINE_DIAGNOSTIC"
    })

except Exception as e:
    print({
        "status": "ERROR",
        "error": str(e)
    })
