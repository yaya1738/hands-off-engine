from ai.factory.state_stream import (
    FactoryStateStream,
)


def test_publish_state():
    stream = FactoryStateStream()

    stream.publish_state(
        {
            "status": "HEALTHY",
        }
    )

    assert stream.latest()["status"] == "HEALTHY"


def test_subscriber_receives_state():
    stream = FactoryStateStream()

    received = []

    stream.subscribe(
        lambda state: received.append(state)
    )

    stream.publish_state(
        {
            "tasks": 5,
        }
    )

    assert received[0]["tasks"] == 5
