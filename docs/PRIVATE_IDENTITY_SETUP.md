# Private Identity Configuration

Identity and access-control records are local-only. They must never be committed to this public repository.

## Private directory

The default private directory is:

```text
~/.config/hands-off-engine
```

Set `HANDS_OFF_PRIVATE_DIR` to use another local path. Directory permissions should be `0700`; private files should be `0600`.

## Optional environment configuration

- `HANDS_OFF_OWNER_NAME`: display label only; not proof of identity.
- `HANDS_OFF_OWNER_EMAIL`: optional contact label.
- `HANDS_OFF_OWNER_SSH_KEY_FINGERPRINTS`: comma-separated SHA256 SSH fingerprints used for identity matching.
- `HANDS_OFF_OWNER_DEVICE_IDS`: optional secondary device allowlist.
- `HANDS_OFF_OWNER_TRUSTED_IPS`: diagnostic allowlist only; IP matching is not identity proof.
- `HANDS_OFF_IDENTITY_PROFILE`: optional path to the private absolute-identity profile.
- `HANDS_OFF_HUMAN_IDENTITY`: optional path to a private human-verification profile.

Missing fingerprints or private profile data must fail closed. Root access, hostnames, working directories, local connections, environment defaults, and SSH-agent presence are not identity proof.

## Migration note

Before switching an existing local checkout to this privacy branch, preserve local-only data:

1. Fetch the privacy branch without checking it out.
2. Export the migration helper from the branch and run it against the current checkout:
   ```bash
   git fetch origin privacy/private-identity-separation-20261123
   git show origin/privacy/private-identity-separation-20261123:scripts/migrate_private_env.sh > "$TMPDIR/migrate_private_env.sh"
   HANDS_OFF_REPO_ROOT="$HOME/hands-off-engine" bash "$TMPDIR/migrate_private_env.sh"
   ```
3. Verify that the private copies exist before switching branches or pulling the privacy changes.

The helper copies existing profile, identity, environment, and legacy state files into the private directory with restrictive permissions. It does not print their values or delete the originals. Do not upload them to GitHub or paste their contents into logs or chat. The public templates intentionally contain no real identity data.

## Credential rotation

Any Telegram bot token or Sheets/webhook credential previously committed to the public repository must be treated as compromised. Rotate the Telegram token through BotFather and replace the Sheets/webhook credential at its issuing provider. Update only the private local configuration after rotation; never put replacement values in a template or commit.

## Financial data separation

Wallet addresses, balances, debts, income, risk limits, and financial snapshots are also local/private. Public code may define schemas and validation rules, but financial authorization must use fresh, verified sources and explicit approval.
