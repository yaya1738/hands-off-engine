# Public Repository Privacy Separation Audit

Date: 2026-11-22
Scope: `yaya1738/hands-off-engine`, financial-integrity review branch

## Objective

Keep the repository public and preserve its reusable code, collaboration, issue, CI, and funding capabilities while ensuring personal identity, financial balances, wallet identifiers, credentials, and runtime history live only in private local state.

This is a data-separation audit, not a recommendation to make the repository private.

## Work completed in this review branch

- Added ignore rules for private identity and financial runtime records. These rules prevent future accidental additions but do not untrack files already committed.
- Removed stale personal balance, position, rent, and historical P&L figures from the static Termux dashboard. It now displays unknown/private placeholders.
- Removed personal name and stale runway/debt figures from `.claude/instructions.md`.
- Replaced the obsolete status instructions that sourced a credential file and queried a hardcoded public server with local health and evidence-backed financial-truth guidance.
- Existing financial-integrity changes also removed the wallet literal from the payment monitor and require its configured address to be supplied through local environment configuration.

## Additional historical exposure found by full tree enumeration

The current tree contains 808 timestamped finance snapshots (about 167 KB total), a historical net-worth CSV, finance state and P&L files (including a multi-megabyte ledger), tracked environment/configuration records, and a 60 KB `termux-hands-off/security_snapshot.tar` archive. The public main branch contains non-empty credential-shaped values in tracked `auto_sources.env`, `ifttt.env`, Telegram bot configuration, and the autopilot admin environment. The Google Apps Script webhook, IFTTT webhook, Telegram token, and admin token values match their respective credential formats; provider-side validity was not tested. Treat them as exposed and rotate/revoke through the providers. Some adjacent environment values are placeholders. The security archive has not been extracted or inspected; treat it as potentially containing further secrets.

The migration utility now recursively preserves `termux-hands-off/state/`, `termux-hands-off/logs/`, `termux-hands-off/data/finances/`, and the security archive, plus corresponding `~/hands-off` runtime directories. It also preserves `security/identity_checks.jsonl`. This prevents the cleanup plan from losing historical finance evidence.

## Remaining tracked data requiring a private-preservation migration

The following paths still contain personal or account-specific information in the branch's current tree:

| Path | Data class | Required treatment |
|---|---|---|
| `finance/dollar_access.json` | Wallet identifier, historical balances and account-channel metadata | Preserve privately; replace public copy with schema-only example or remove after consumers are migrated |
| `termux-hands-off/agents/external_accounts.json` | External account balances, liabilities, rent, credit and wallet metadata | Preserve privately; migrate every reader/writer before removing public copy |
| `security/yair_identity_profile.json` | Identity, device, infrastructure, behavioral and knowledge-verification profile | Preserve privately; remove from public tree after identity consumer migration |
| `state/optimal_trigger_config.json` | Wallet and obsolete capital-trigger configuration | Preserve audit evidence privately; disable/remove public snapshot |
| `state/filler_actions.jsonl` | Historical wallet-bearing action records | Preserve privately; remove personal event payloads from public tree |

The tracked `finance/yair_finance_hub.json` has already been replaced in this branch with a null/unknown, non-authoritative placeholder. The migration utility still preserves a pre-update local copy before the branch is pulled, in case the device checkout contains the former live snapshot. The identity verifier source has also been refactored to use a private profile and fail closed when it is absent.

The public funding metadata also associates the project with a wallet address. It is not a private key, but it is a public identity link. Keep the GitHub Sponsors entry; decide separately whether the wallet donation route is an intentional public business decision before changing it.

## Consumer compatibility discovered

The external-account JSON is read or written by multiple legacy agents, including:

- `balances_fill.py`
- `external_accounts_fill.py`
- `weekly_summary.py`
- `finance_watcher.py`
- `polymarket_positions.py`
- `credit_guardrail.py`
- `dashboard_builder.py`
- `rotate_today.py`

These consumers now use the shared `termux-hands-off/agents/private_state.py` resolver, which prefers the migrated `legacy_runtime` copy, then the migrated repository-source copy, and never falls back to plaintext files in the public checkout or old `~/hands-off` paths. The security mirror now archives the migrated private records. The migration utility also preserves the card, emergency-info, and finance-rules files needed by these agents.

The finance hub is read by dashboard and autonomous modules; its tracked current-tree file is now an unknown placeholder. The identity profile is read from the private `security/` path by `security/absolute_identity.py`. Public tracked copies must still remain until the device has run the preservation command and the updated checkout is deployed. Deploying these code changes before migration would intentionally leave the agents without those local inputs.



The two private backup repositories `hands-off-engine-backup` and `hands-off-engine-mirror` contain the same `.env.polymarket` blob. Its Polymarket private-key field is a valid 32-byte hex key, the funder field is a populated wallet address, and the DigitalOcean token field is non-empty; `LIVE_TRADING_ENABLED` is set to `1`. Treat the key and token as compromised even though the repositories are private. Do not use the key to sign or trade. No values are reproduced here and no credential rotation was performed.

## Required migration design

1. Use the shared private-state resolvers. Default location: `~/.config/hands-off-engine/`, overridable with `HANDS_OFF_PRIVATE_DIR`.
2. Add an idempotent migration utility that copies existing local files into that directory with owner-only permissions, verifies byte counts and SHA-256 hashes, and never deletes the source.
3. Complete any remaining finance and identity reader/writer migrations to the resolver. Missing data must remain unknown; no zero defaults.
4. Add tests for missing private state, permissions, malformed data, migration repeatability, and read/write isolation.
5. Replace tracked live-data files with schema-only examples or remove them only after consumer tests pass.
6. Scan all tracked files and reachable history for personal values, wallet identifiers, secrets, server endpoints, and historical finance/P&L data.
7. Coordinate a reviewed history rewrite only after a verified private backup exists and all local clones are accounted for. Preserve the public repository and its public code history where possible; remove only sensitive blobs and references.

## Preservation command

From the repository checkout on the device, the copy-only migration can be run as:

```bash
python scripts/migrate_private_state.py \
  --source-root "$HOME/hands-off-engine" \
  --legacy-runtime-root "$HOME/hands-off" \
  --destination "$HOME/.config/hands-off-engine"
```

It records the repo and legacy runtime sources separately under the private destination. Review the summary and manifest; resolve any destination conflicts before proceeding. The command does not delete or modify originals.

## Important boundary

A `.gitignore` entry does not remove a file already tracked by Git. Removing a file from the current tree does not remove its earlier versions from public Git history. Gitleaks passing does not establish that personal financial information or identity data is absent.

No private data was copied, deleted, or overwritten in this review step. No repository visibility change, history rewrite, merge, deployment, wallet action, credential rotation, or trading action was performed.
