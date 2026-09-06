def test_communication_modules_import():
    from telegram.communication_protocol import ConversationProtocol
    from telegram.human_loop import HumanLoop

    assert ConversationProtocol is not None
    assert HumanLoop is not None
