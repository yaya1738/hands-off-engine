def test_audit_checkpoint_is_documentary_only():
    text = open("AUTHORITY_AUDIT_NOTE_20260902.md", encoding="utf-8").read()
    assert "does not grant execution authority" in text
