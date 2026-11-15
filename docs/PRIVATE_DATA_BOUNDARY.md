# Private local data boundary

Personal identity, financial, health, emergency-contact, and wallet metadata must not be stored in this public repository.

## Local-only files

The following runtime files are intentionally excluded from version control:

- `security/yair_identity_profile.json`
- `security/yair_human_identity.json`
- `security/verification_audit.jsonl`
- `finance/yair_finance_hub.json`
- `state/doctor_meetings.jsonl`
- `termux-hands-off/agents/emergency_info.json`
- `termux-hands-off/agents/external_accounts.json`
- `termux-hands-off/agents/cards.json`
- `termux-hands-off/agent/balances_manual.yaml`
- `termux-hands-off/agent/balances_manual.yaml.bak`
- `termux-hands-off/agent/addresses_eth.yaml`

Keep these files on the device or in an encrypted private backup. Do not paste their contents into chat, commit them, or send them to third-party services.

## Before merging this change

**Back up any existing local copies first.** Merging the deletions will remove the tracked copies from the working tree. Store backups outside the repository with owner-only permissions, preferably encrypted. Do not restore the private files into Git.

Some finance and identity features will be unavailable until the relevant local-only data is restored. The finance refresh script now exits safely when its private hub is absent, and the manual finance aggregator skips a missing local source with a warning.

## Repository history

This change removes the files from the current tree only. Previous commits may still contain their contents. History rewriting and credential revocation are separate operations and must be planned explicitly; deleting a file in a later commit does not erase historical copies.

## Identity allowlists

Identity and infrastructure allowlists are now read from local environment variables, not committed source:

- `HANDS_OFF_MASTER_NAME`
- `HANDS_OFF_MASTER_EMAIL`
- `HANDS_OFF_MASTER_DEVICES` (comma-separated)
- `HANDS_OFF_MASTER_SSH_FINGERPRINTS` (comma-separated)
- `HANDS_OFF_TRUSTED_IPS` (comma-separated)

The allowlists default to empty, so identity checks fail closed until configured locally. Do not commit their values. The public bootstrap kernel retains its structure but has private contact, infrastructure, and financial snapshot fields blanked or marked unavailable.
