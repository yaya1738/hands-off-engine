# Credential Rotation Runbook

Date: 2026-11-22
Status: Prepared only — no provider credentials have been revoked or replaced.

## Why this is required

The public repository contains tracked exchange credentials and a security archive that embeds exchange credentials plus personal financial records. Tracked public environment files also contain values matching Google Apps Script/Sheets, IFTTT, Telegram bot, and autopilot admin credential formats. The private backup/mirror repositories contain an additional exchange-signing configuration and a cloud API token.

Provider-side validity and permissions have not been tested. Treat the exposed values as compromised. Do not paste secret values into chat, issues, commits, logs, or shell command history.

## Priority 0 — revoke public credentials

Complete these directly in the provider dashboards:

1. **OKX** — revoke every API key represented in the public vault/archive. Review recent API activity. If continued access is needed, create a new read-only key with only required account-read permissions, IP restrictions where available, and withdrawals disabled.
2. **Kraken** — revoke the exposed API key/secret pair. Review recent API activity. If needed, create a new read-only key; disable trading and withdrawals unless separately justified.
3. **Google Apps Script / Sheets** — rotate the deployed webhook or token consumed by the finance push script. Restrict the deployment audience and authorization.
4. **IFTTT** — rotate the webhook key and update the private local environment file.
5. **Telegram** — revoke the exposed bot token through BotFather, issue a replacement, and update the private runtime bot environment. Verify the bot's chat access and remove any unknown sessions/integrations.
6. **Autopilot admin control** — revoke the exposed admin token. Keep remote admin disabled until a new token is stored privately and the authorization boundary is tested.

## Priority 1 — private backup credentials

7. **DigitalOcean** — the private backup/mirror configuration contains a populated API token. Revoke it if the private repositories or archive were accessible to anyone outside the trusted owner. Create a new least-privilege token only if required; inspect account activity and existing resources.
8. **Polymarket signing key** — the private backup/mirror configuration contains a signing key. It was not found in the public main vault or the inspected public security archive. Treat it as compromised if either private backup repository was shared beyond the owner or its contents were copied to an untrusted device. If the key is to be retired, create a new wallet securely and migrate assets only after independently checking balances and destinations. Do not sign, trade, or transfer using the exposed key.

## Safe replacement procedure

- Run the copy-only private-state migration before replacing local files.
- Store new credentials only under `~/.config/hands-off-engine/secrets/` (or the configured `HANDS_OFF_PRIVATE_DIR`).
- Use owner-only directory/file permissions.
- Never place credentials in repository source, tracked environment files, dashboard snapshots, CI artifacts, or logs.
- Prefer read-only API permissions, IP allowlists, and no withdrawal permission.
- Update consumers to use private configuration paths only.
- Verify old credentials are revoked in the provider dashboard; deleting a local file is not revocation.
- Re-run repository and history scans after the public file cleanup.

## Completion checklist

- [ ] Private-state preservation completed and manifest verified
- [ ] OKX credentials revoked and activity reviewed
- [ ] Kraken credentials revoked and activity reviewed
- [ ] Google Apps Script/Sheets credential rotated
- [ ] IFTTT webhook rotated
- [ ] Telegram bot token revoked/replaced
- [ ] Autopilot admin token revoked/replaced
- [ ] DigitalOcean token reviewed and rotated if exposure scope requires it
- [ ] Polymarket key exposure scope assessed; replacement/migration decision made
- [ ] New credentials stored only in private config
- [ ] Public tracked secret files removed after preservation
- [ ] Public Git history scrubbed in a coordinated operation
- [ ] Final scans and CI passed

No rotation, account login, wallet action, trading action, or transfer is performed by this runbook.
