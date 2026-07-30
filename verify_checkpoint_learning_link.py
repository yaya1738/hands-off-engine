from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()
checkpoint = r.run_checkpoint_cycle()

print({
"status": "PASS" if isinstance(checkpoint, dict) and "action" in checkpoint else "FAIL",
"checkpoint_action": checkpoint.get("action"),
"learning_available": hasattr(r, "learning"),
"feedback_available": hasattr(r, "recommendation_feedback")
})
