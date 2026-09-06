# Autonomous Communication Contract

## Objective

Yair should not be a routine operator. The system should continue work on its
own and communicate only information that changes what a human needs to know
or decide.

## Communication classes

- **Progress:** internal milestones; batch these rather than interrupting.
- **Decision:** a choice where human intent materially changes the outcome.
- **Blocker:** external authority, credential, safety, or ambiguity that the
  system cannot legitimately resolve itself.
- **Request:** authenticated human instruction sent to the autonomous queue.
- **Response/Ack:** correlated receipt or answer to a human message.

## Default behavior

1. Detect and resolve routine problems autonomously.
2. Continue through implementation, testing, verification, and recovery.
3. Batch low-value progress updates.
4. Contact Yair for material decisions or genuine blockers.
5. Persist every inbound/outbound message with a correlation ID.
6. Resume automatically after receiving a response.

## Security boundary

Telegram is a communication transport, not an execution authority. Inbound
messages must come from the configured `TELEGRAM_CHAT_ID`; if it is absent,
the listener fails closed. Human requests enter the autonomous task queue and
still pass through the existing authority, approval, and execution controls.

A message saying "continue" therefore means *continue within the existing
safety and authority boundaries*, not bypass them.
