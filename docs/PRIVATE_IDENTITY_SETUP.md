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

Before updating an existing local checkout that contains older identity JSON files, copy the local files to the private directory first. Do not upload them to GitHub or paste their contents into logs or chat. The public templates intentionally contain no real identity data.

## Financial data separation

Wallet addresses, balances, debts, income, risk limits, and financial snapshots are also local/private. Public code may define schemas and validation rules, but financial authorization must use fresh, verified sources and explicit approval.
