# Hands-Off Engine — Public Engineering Instructions

## Repository and collaboration

- Preserve the public repository, its history, reusable modules, and public development workflow.
- Never use `git add .`; stage explicit paths.
- Do not force-push, rewrite public history, change repository visibility, or merge a draft/unreviewed PR.
- Keep unrelated work in separate branches and focused pull requests.
- Prefer concise evidence, bounded command output, and reproducible tests.

## Runtime and automation

- Treat the governed supervisor as the runtime owner; avoid duplicate schedulers and unmanaged background processes.
- Do not assume boot hooks, services, or connectors are installed unless verified.
- Prefer provider-agnostic, low-cost implementations. Optional integrations must not become core dependencies.
- Preserve existing working components and extend/reuse them before creating replacements.

## Financial integrity

- Financial facts must come from fresh, authoritative sources and carry verification status and timestamp.
- Missing, stale, malformed, or contradictory financial data must fail closed.
- Never substitute demo balances, defaults, model estimates, or historical snapshots for verified money.
- Never claim an order was placed, a payment settled, or revenue received without authoritative confirmation.
- Shadow research and dry-run operation may continue with clearly labelled model-only values.
- Live trading, payments, withdrawals, transfers, and credential changes require explicit authorization and independent safety checks.
- No automatic resumption of live financial activity after pauses or failures.

## Privacy and security

- Never commit personal profiles, identity records, contact details, financial snapshots, wallet addresses, device IDs, SSH fingerprints, authentication answers, API keys, tokens, or private logs.
- Load user-specific values from local-only configuration under `HANDS_OFF_PRIVATE_DIR`.
- Keep private configuration out of public logs and command output.
- Identity checks must not infer ownership from root access, hostnames, IP addresses, working directories, or SSH-agent presence alone.
- Missing identity configuration means access denied.

## Validation

- Add regression tests for safety-sensitive changes.
- Keep CI results visible and do not describe unrun tests as passing.
- Prefer narrow, deterministic tests before broader suites.
- Document blockers and preserve a clear distinction between verified findings and hypotheses.
