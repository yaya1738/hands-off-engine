from ai.factory.live_order_authority import LiveOrderAuthority, OrderIntent, submit_legacy_order


def test_authority_denies_by_default():
    decision = LiveOrderAuthority().submit(
        OrderIntent(token_id="token", price=0.5, size=1, side="BUY", source="test")
    )
    assert decision["executed"] is False
    assert decision["reason"] == "live_order_authority_disabled"


def test_authority_rejects_invalid_order_before_activation():
    authority = LiveOrderAuthority()
    assert authority.authorize(
        OrderIntent(token_id="", price=0.5, size=1, side="BUY")
    )["reason"] == "missing_token_id"
    assert authority.authorize(
        OrderIntent(token_id="token", price=2, size=1, side="BUY")
    )["reason"] == "invalid_price"
    assert authority.authorize(
        OrderIntent(token_id="token", price=0.5, size=0, side="BUY")
    )["reason"] == "invalid_size"
    assert authority.authorize(
        OrderIntent(token_id="token", price=0.5, size=1, side="HOLD")
    )["reason"] == "invalid_side"


def test_enabled_still_fails_closed_without_activation_contract():
    decision = LiveOrderAuthority(enabled=True).submit(
        OrderIntent(token_id="token", price=0.5, size=1, side="BUY")
    )
    assert decision["executed"] is False
    assert decision["reason"] == "activation_contract_not_implemented"


def test_legacy_denial_is_falsey_and_never_looks_executed():
    result = submit_legacy_order(object(), source="regression-test")
    assert not result
    assert result["executed"] is False
    assert result["reason"] == "missing_token_id"
