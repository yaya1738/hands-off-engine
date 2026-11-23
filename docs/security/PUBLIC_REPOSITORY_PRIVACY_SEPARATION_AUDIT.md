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

The current tree contains 808 timestamped finance snapshots (about 167 KB total), a historical net-worth CSV, finance state and P&L files (including a multi-megabyte ledger), 220 root `state/` files (about 4 MB) containing financial/trading histories, system telemetry, transcripts and approval records, tracked environment/configuration records, and a 60 KB `termux-hands-off/security_snapshot.tar` archive. The public main branch also contains non-empty values matching Google Apps Script, IFTTT, Telegram bot, and autopilot admin credential formats; provider-side validity was not tested, so treat them as exposed and rotate/revoke through their providers. The tracked `termux-hands-off/agent/vault.json` contains non-placeholder exchange credential fields. The public security archive was inspected structurally and contains a vault with exchange API credentials, external-account records, cards, emergency information, and finance logs. Treat credential material in both the vault and archive as compromised; no values are reproduced here.

The migration utility now recursively preserves the complete root `state/` and `logs/` trees, `termux-hands-off/state/`, `termux-hands-off/logs/`, `termux-hands-off/data/finances/`, `termux-hands-off/autopilot/`, and the security archive, plus corresponding `~/hands-off` runtime directories. It also preserves tracked vault JSON files, `security/identity_checks.jsonl`, any local `.env.polymarket`, and the live `~/.config/hands-off/vault.json` into a private `secrets/` subdirectory. This prevents the cleanup plan from losing historical finance evidence or local credentials.

## Remaining tracked data requiring a private-preservation migration

The following paths still contain personal or account-specific information in the branch's current tree:

| Path | Data class | Required treatment |
|---|---|---|
| `finance/dollar_access.json` | Wallet identifier, historical balances and account-channel metadata | Preserve privately; replace public copy with schema-only example or remove after consumers are migrated |
| `termux-hands-off/agents/external_accounts.json` | External account balances, liabilities, rent, credit and wallet metadata | Preserve privately; migrate every reader/writer before removing public copy |
| `security/yair_identity_profile.json` | Identity, device, infrastructure, behavioral and knowledge-verification profile | Preserve privately; remove from public tree after identity consumer migration |
| `state/optimal_trigger_config.json` | Wallet and obsolete capital-trigger configuration | Preserve audit evidence privately; disable/remove public snapshot |
| `state/filler_actions.jsonl` | Historical wallet-bearing action records | Preserve privately; remove personal event payloads from public tree |
| `termux-hands-off/agent/vault.json` and backup | OKX/Kraken API credentials | Preserve privately; rotate exposed credentials; replace public files with examples |
| `termux-hands-off/agent/balances_manual.yaml.bak` | Historical manual asset/liability snapshot | Preserve privately; remove from public tree after migration |
| `termux-hands-off/security_snapshot.tar` | Embedded vault credentials, external accounts, cards, emergency data and finance logs | Preserve archive privately; remove public copy and scrub history |
| `termux-hands-off/state/` | Telegram, IFTTT and other integration environment values plus runtime state | Preserve privately; rotate confirmed exposed credentials; remove tracked runtime state |
| `termux-hands-off/autopilot/admin.env` | Admin/control-plane token | Preserve privately; rotate/revoke; replace with example |
| `termux-hands-off/data/finances/` and `termux-hands-off/logs/` | Historical snapshots, net-worth/P&L CSVs and finance logs | Preserve recursively; remove personal history from public tree after verification |

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

From Termux, run this single command. It verifies the launcher against its Git blob hash; the launcher separately verifies the migration script before executing it:

```bash
cd "$HOME/hands-off-engine" || exit 1; T="${TMPDIR:-$HOME/.cache}/prepare_private_state_migration.sh"; mkdir -p "$(dirname "$T")" && curl -fsSL https://raw.githubusercontent.com/yaya1738/hands-off-engine/894509e1ab1fdedbf1d05568fe602bbf8b6a04ed/scripts/prepare_private_state_migration.sh -o "$T" && test "$(git hash-object "$T")" = "416bab0aaa8caa51bf0dfc36e5d5a4552fee7551" && sh "$T"
```

It writes owner-only copies and a SHA-256 manifest under `~/.config/hands-off-engine` (or `HANDS_OFF_PRIVATE_DIR`). It prints only aggregate counts and any conflicts. It never deletes or modifies source files. Do not proceed to public-file removal until the manifest reports zero conflicts and the copied files are verified.

A provider-by-provider rotation checklist is maintained in `docs/security/CREDENTIAL_ROTATION_RUNBOOK.md`. It is a manual runbook only; no credentials have been revoked, replaced, or used.

## Important boundary

A `.gitignore` entry does not remove a file already tracked by Git. Removing a file from the current tree does not remove its earlier versions from public Git history. Gitleaks passing does not establish that personal financial information or identity data is absent.

No private data was copied, deleted, or overwritten in this review step. No repository visibility change, history rewrite, merge, deployment, wallet action, credential rotation, or trading action was performed.


## Verified preservation and review-branch cleanup status (2026-11-23)

The owner executed the pinned Termux preservation launcher. It reported 2,760 copied files, 2 already preserved, zero conflicts, and 426,493,620 bytes. The local SHA-256 verification then checked all 2,762 manifest entries: 2,762 hashes matched, zero files were missing, zero mismatched, and zero files had group/other permission bits. The manifest is stored at `~/.config/hands-off-engine/migration_manifest.json`. Source files were not deleted or modified by the migration.

The current review branch `fix/financial-integrity-concurrency-20261122` removes 1,084 tracked paths relative to its P0 base: 213 root `state/` records, 39 Termux `state/` records, all 810 historical finance snapshot files, 3 Termux finance/log records, and 19 other sensitive/private records. The remaining state paths are limited to `.gitkeep`, source code, and the non-personal `state/script_registry.json` required by legacy execution-safety regression tests. Public-safe `.example` environment templates remain. Personal finance decision history and account metadata were also removed. The current branch tree no longer contains the tracked security archive, legacy vaults, external-account records, identity profile, or historical finance snapshots.

The first CI attempt after removal exposed one test dependency on `state/script_registry.json`; that non-personal safety registry was restored from its original Git blob and the regression is being rerun. The workflow now checks out full Git history (`fetch-depth: 0`) before Gitleaks scans. Previous scans ran against a shallow checkout (one commit) and therefore did not establish that the full reachable history was clean. The full-history scan is pending; any findings must be treated as historical exposure, not suppressed as a clean result.

This remains a draft, stacked review PR targeting `fix/p0-financial-integrity-20261122`, not `main`. The public `main` branch remains unchanged and still contains the previously inventoried sensitive files until the reviewed PR stack reaches and is merged into `main`. The repository remains public. No provider credentials have been rotated or revoked, no wallet or cloud account actions have been taken, no Git history has been rewritten, and no PR has been merged. The migration and cleanup do not revoke credentials already exposed in reachable history.

The current cleanup retains the three public-safe integration examples: `termux-hands-off/state/auto_sources.env.example`, `termux-hands-off/state/ifttt.env.example`, and `termux-hands-off/state/tg/bots/handsoff.env.example`. The public wallet funding route remains a separate explicit privacy/business decision; it is not an authentication credential.
