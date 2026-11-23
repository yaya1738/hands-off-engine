from scripts.device_condition import assess_condition, task_suitability


def test_healthy_observed_device_allows_routine_and_intensive():
    s = {"battery_percent": 80, "charging": False, "temperature_c": 30,
         "memory_available_percent": 40, "disk_free_percent": 40}
    assert assess_condition(s)["status"] == "normal"
    assert task_suitability(s, "routine")["decision"] == "allow"
    assert task_suitability(s, "intensive")["decision"] == "allow"


def test_low_battery_without_charging_defers_intensive():
    s = {"battery_percent": 10, "charging": False, "temperature_c": 30}
    assert assess_condition(s)["status"] == "degraded"
    assert task_suitability(s, "intensive")["decision"] == "defer"
    assert task_suitability(s, "routine")["decision"] == "allow"


def test_charging_device_is_not_penalized_for_low_battery_alone():
    s = {"battery_percent": 10, "charging": True, "temperature_c": 30}
    assert "low_battery" not in assess_condition(s)["concerns"]
    assert task_suitability(s, "intensive")["decision"] == "allow"


def test_high_temperature_defers_intensive_but_keeps_routine():
    s = {"temperature_c": 46}
    assert task_suitability(s, "intensive")["decision"] == "defer"
    assert task_suitability(s, "routine")["decision"] == "allow"


def test_unknown_metrics_do_not_claim_healthy_or_allow_intensive():
    s = {"battery_percent": None, "charging": None, "temperature_c": None,
         "memory_available_percent": None, "disk_free_percent": None}
    assert assess_condition(s)["status"] == "unknown"
    assert task_suitability(s, "routine")["decision"] == "allow"
    assert task_suitability(s, "intensive")["decision"] == "defer"


def test_memory_and_storage_pressure_are_detected():
    s = {"memory_available_percent": 3, "disk_free_percent": 4}
    result = assess_condition(s)
    assert result["status"] == "degraded"
    assert "memory_pressure" in result["concerns"]
    assert "low_storage" in result["concerns"]


def test_unknown_task_class_is_deferred():
    assert task_suitability({}, "anything")["decision"] == "defer"


def test_warning_thresholds_are_caution():
    s = {"battery_percent": 20, "charging": False, "temperature_c": 43,
         "memory_available_percent": 20, "disk_free_percent": 20}
    assert assess_condition(s)["status"] == "caution"
