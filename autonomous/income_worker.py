from integrafix.income_engine import IncomeEngine
from datetime import datetime


def run_income_worker():

    engine = IncomeEngine()

    action = engine.get_next_action()

    if action["action"] != "complete_work":
        return {
            "status": "nothing_to_complete",
            "action": action["action"]
        }

    work = action["details"]
    work_id = work["id"]

    content = f"""
# Completed Work Report

Work ID:
{work_id}

Completed:
{datetime.now().isoformat()}

Summary:
Generated autonomous deliverable.

Status:
Ready for submission.
"""

    deliverable = engine.create_deliverable(
        work_id=work_id,
        deliverable_type="report",
        content=content,
        filename="delivery_report.md"
    )

    completion = engine.complete_work(
        work_id,
        notes="Autonomous deliverable generated"
    )

    return {
        "status": "completed",
        "work_id": work_id,
        "deliverable": deliverable,
        "completion": completion
    }


if __name__ == "__main__":
    print(run_income_worker())
