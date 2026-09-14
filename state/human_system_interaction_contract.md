# Human-to-System Interaction Contract

## Purpose

Define the canonical human control surface for the hands-off Factory. Human interaction is an authority/control input, not an execution path.

## Canonical flow

Human intent -> authenticated control surface -> durable Factory control channel -> governed supervisor -> FactoryAuthorityGateway -> policy/risk/approval gates -> execution -> verification -> durable state/evidence.

## Interaction rules

1. A human may submit objectives, requests for review, approvals where policy permits, and stop/hold requests through an authenticated control surface.
2. Human requests MUST receive a stable idempotency key before entering the durable control channel.
3. The control channel is append-only for commands; execution is never performed by the transport layer.
4. Every accepted command MUST be attributable to its source and authority context.
5. The governed supervisor is the only component allowed to promote control-channel commands into executable Factory work.
6. FactoryAuthorityGateway remains the execution authority and must preserve authorization, policy, risk, cost, audit, and fail-closed gates.
7. No human message may directly bypass those gates.
8. The system MUST publish bounded status sufficient for a human to determine: accepted, queued, executing, succeeded, failed, blocked, or awaiting external recovery.
9. Repeated human "continue" messages are not part of the normal lifecycle. Once accepted, work continues through the autonomous supervisor until completion, safe blocking, or an explicit stop/hold condition.
10. If external infrastructure is unavailable, the system remains fail-closed and records the blocker rather than asking the human to manually drive the internal lifecycle.

## Human responsibilities

The human is responsible only for decisions that genuinely require human authority or unavailable external access. Routine investigation, retries, verification, state synchronization, and continuation belong to the Factory.

## Completion criterion

A human-to-system interaction is complete only when the request has a terminal outcome or a durable blocked state with the next machine-owned recovery action recorded.
