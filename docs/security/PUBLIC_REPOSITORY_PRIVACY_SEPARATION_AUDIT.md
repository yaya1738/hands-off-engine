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

## Remaining tracked data requiring a private-preservation migration

The following paths still contain personal or account-specific information in the branch's current tree:

| Path | Data class | Required treatment |
|---|---|---|
| `finance/dollar_access.json` | Wallet identifier, historical balances and account-channel metadata | Preserve privately; replace public copy with schema-only example or remove after consumers are migrated |
| `finance/yair_finance_hub.json` | Personal account, credit and net-worth snapshot | Preserve privately; public copy must contain no live values |
| `termux-hands-off/agents/external_accounts.json` | External account balances, liabilities, rent, credit and wallet metadata | Preserve privately; migrate every reader/writer before removing public copy |
| `security/yair_identity_profile.json` | Identity, device, infrastructure, behavioral and knowledge-verification profile | Preserve privately; remove from public tree after identity consumer migration |
| `state/optimal_trigger_config.json` | Wallet and obsolete capital-trigger configuration | Preserve audit evidence privately; disable/remove public snapshot |
| `state/filler_actions.jsonl` | Historical wallet-bearing action records | Preserve privately; remove personal event payloads from public tree |
| `security/absolute_identity.py` | Hardcoded personal identity/challenge facts in source | Replace with private-profile-backed verification; no personal facts in source code |

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

The finance hub is read by dashboard and autonomous modules. The identity profile is read by `security/absolute_identity.py`. A file deletion before these consumers are migrated would break or silently degrade functionality.

## Required migration design

1. Add one shared private-state resolver. Default location: `~/.config/hands-off-engine/`, overridable with `HANDS_OFF_PRIVATE_DIR`.
2. Add an idempotent migration utility that copies existing local files into that directory with owner-only permissions, verifies byte counts and SHA-256 hashes, and never deletes the source.
3. Update every finance and identity reader/writer to use the resolver. Missing data must remain unknown; no zero defaults.
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
