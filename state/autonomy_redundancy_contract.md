# Factory autonomy redundancy contract

The Factory must not depend on a single transport, runner, state publication
path, or human notification mechanism. Redundancy means multiple routes to the
same governed authority, not multiple execution authorities.

## Authority invariant

All autonomous execution remains governed by `FactoryAuthorityGateway`. A
fallback may replace an execution route, but it may not bypass policy, risk,
authorization, approval, audit, idempotency, or verification gates.

## Control ingress

Supported control surfaces may include GitHub autonomous issue ingress, the
Factory mailbox/control channel, authenticated Telegram/local-node transports,
and other explicitly authorized adapters. Ingress transports append durable,
idempotent commands; they never execute objectives directly.

If one ingress is unavailable, another authorized ingress may continue to
accept work. No unauthenticated transport is promoted to an authority merely
because it is available.

## Execution

The integrated autonomous supervisor is the preferred route. The canonical
liveness supervisor is a governed fallback. Additional authorized runners or
local nodes may use the same redundant entrypoint. Backend selection is
recorded so evidence distinguishes the route actually used.

Concurrent routes must rely on stable idempotency and the governed authority;
redundancy must not become duplicate execution.

## State publication

Execution results are persisted locally and published through the durable
Factory control-state snapshot. External bridges may independently relay that
bounded state to GitHub, Telegram, or other authorized observers. Failure of a
notification transport must not invalidate or alter the execution authority.

Stale state never proves liveness. Fresh governed execution and verification
are required before the system claims `live`.

## Human notification

GitHub issue state and authenticated Telegram-capable channels are independent
notification surfaces where configured. Notifications are observational and
must not become a hidden execution bypass.

## Recovery

Recovery is layered: the Factory's own supervisor/control loop, scheduled
hosted execution, redundant hosted recovery, and authorized local execution
may each detect and recover from a failed route. External infrastructure
failures remain explicitly degraded/fail-closed until a route is directly
verified healthy.

## Human involvement

Normal operation does not require repeated `continue` messages. Human input is
reserved for objectives, genuinely human authority, unavailable external
credentials/access, or explicit stop/hold decisions. The machine-owned recovery
loop is responsible for continuing bounded autonomous work between human
interactions.
