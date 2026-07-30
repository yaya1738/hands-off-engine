from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

gap = {
    "component": "FactoryDevelopmentPipeline",
    "error": "'list' object has no attribute 'get'",
    "type": "capability_gap"
}

controller = r.gap_repair_controller

analysis = controller.analyze_gap(gap)

print({
    "analysis": analysis,
    "selected": controller.select_repair(gap)
})
