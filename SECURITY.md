# Security Policy

## Reporting
Do not open a public issue containing credentials, wallet keys, private account data, or exploit details. Report suspected exposure privately to the repository maintainer.

## Credential rules
- Treat any credential ever committed to this public repository or its history as compromised. Revoke or rotate it at the issuing provider.
- Never commit .env files, wallet/private-key material, tokens, account exports, runtime state, or backups.
- Use local environment variables or an approved secret manager for local runtime credentials. Use GitHub Actions secrets only for CI jobs that genuinely require them.
- Keep production credentials out of pull-request workflows, especially workflows triggered by untrusted forks.
- Do not put real balances, wallet addresses tied to people, or account identifiers in public diagnostics.
- A deletion from the current tree does not erase Git history and does not revoke a credential.

## Public/private boundary
This repository is for public, non-sensitive source, tests, documentation, and reusable workflows. Runtime state, private deployment configuration, wallet material, user data, and production secrets must remain outside the public repository. Public workflows must not fetch or publish private material unless an explicitly reviewed, least-privilege design requires it.

## Incident response
1. Revoke/rotate exposed credentials at the provider.
2. Identify affected accounts and review provider audit logs and on-chain activity where applicable.
3. Remove exposed material from current files; consider history rewriting separately.
4. Verify the replacement credential is stored only in an approved secret store.
5. Record the incident without copying the secret into tickets, logs, or commits.
