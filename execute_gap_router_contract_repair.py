from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "GAP_REPAIR_CONTROLLER_CONTRACT_ADAPTER",
    "reason": (
        "FactoryGapRepairController.select_repair expects a hashable "
        "repair identifier but autonomous gap analysis supplies structured "
        "gap dictionaries."
    )
}

print(r.execute(goal))
