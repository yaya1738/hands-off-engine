# Operator Context Policy

This public repository must not contain a real person's private profile.

Personal identity, contact details, location, financial accounts, balances, debts, wallet addresses, device identifiers, SSH fingerprints, authentication answers, and private history belong only in a local private configuration directory. Do not recreate them in source code, documentation, logs, fixtures, or generated state.

## Operating priorities

- Maximize durable user benefit, legitimate income, and capital preservation.
- Prefer high-leverage automation that reduces repeated manual effort.
- Keep autonomous behavior governed, observable, reversible, and inexpensive.
- Treat unknown or stale financial information as unknown; never invent balances, profits, revenue, or execution outcomes.
- Require explicit authorization and fresh source verification for real-money actions.
- Keep public source code and reusable engineering assets public while keeping personal data and credentials private.
- Minimize user involvement; request only the authorization or local action that cannot safely be performed autonomously.

## Private configuration

If user-specific configuration is required, load it from the path supplied by `HANDS_OFF_PRIVATE_DIR` or the local default `~/.config/hands-off-engine`. Missing private configuration must fail closed for identity or financial authorization.
