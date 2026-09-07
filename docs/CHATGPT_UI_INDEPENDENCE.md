# Consumer ChatGPT UI independence

The regular human-to-ChatGPT consumer interface is not an operational dependency of the autonomous system.

## Required invariant

With the consumer ChatGPT UI unavailable, the system must still be able to:

1. receive authenticated external requests;
2. persist them as durable work;
3. select and execute work through the governed authority gateway;
4. record truthful completion/verification evidence; and
5. communicate results through an independent control surface.

Backend model providers remain optional capabilities. This invariant prohibits only a requirement for a human to open a consumer AI session, copy/paste work, or send a continuation message for the system to progress.

## Implementation

The autonomous supervisor runs independently of consumer AI sessions. The Telegram control surface provides authenticated request ingress and result feedback. The AI Nexus runner loads providers lazily, so constructing the runner does not require ChatGPT or any other provider to be available.
