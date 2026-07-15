from integrafix.income_engine import IncomeEngine
from autonomous.communication_router import CommunicationRouter
from datetime import datetime, timedelta


def run_payment_chaser():

    engine = IncomeEngine()

    action = engine.get_next_action()

    if action["action"] != "chase_payment":
        return {
            "status": "nothing_to_chase",
            "action": action["action"]
        }

    payment = action["details"]

    now = datetime.now()
    last_followup = payment.get("last_followup_at")
    followups_sent = payment.get("followups_sent", 0)

    if last_followup:
        try:
            last = datetime.fromisoformat(last_followup)
            if now - last < timedelta(days=3):
                return {
                    "status": "cooldown",
                    "work_id": payment["work_id"],
                    "followups_sent": followups_sent
                }
        except Exception:
            pass

    work_id = payment["work_id"]
    amount = payment.get("expected_amount",
                         payment.get("amount_usd", 0))

    body = f"""
Hello,

The completed work associated with {work_id} has been delivered.

Outstanding amount: ${amount}

Please confirm payment status when convenient.

Thank you.
"""

    result = {
        "status": "payment_followup_created",
        "work_id": work_id,
        "amount": amount,
        "created_at": now.isoformat(),
        "message": body
    }

    payment["last_followup_at"] = now.isoformat()
    payment["followups_sent"] = followups_sent + 1
    engine._save_state()

    # Optional email sending
    if payment.get("email"):
        router = CommunicationRouter()

        sent = router.send_email_response(
            to_email=payment["email"],
            subject="Payment follow-up",
            body=body
        )

        result["email_sent"] = sent

    return result


if __name__ == "__main__":
    print(run_payment_chaser())
