# Real-Time Coordination Webhook Security

The coordination webhook is a local-only ingress on 127.0.0.1:8888.

- It does not bind to all interfaces.
- Requests must use a loopback Host header for the exact listening port.
- POST requests are disabled unless COORDINATION_WEBHOOK_TOKEN is configured.
- Authorized POST requests must use Authorization: Bearer <token>.
- Sender IDs are allowlisted to known agent identities. The operator, telegram, system, and system_internal identities are always rejected.
- COORDINATION_ALLOWED_SENDERS can narrow the sender allowlist. It cannot add forbidden operator/system identities.
- Request bodies are limited to 64 KiB; message text is limited to 20,000 characters.
- Accepted messages are appended to the local coordination bus only. The webhook never runs Git commands or pushes inbound content to the repository.

To enable a local agent integration, configure a high-entropy COORDINATION_WEBHOOK_TOKEN in the service environment and send it as a Bearer token. Do not expose this unauthenticated legacy service on a public or LAN interface. If remote agent transport is needed later, build a separately authenticated gateway with per-agent credentials and explicit network controls.
