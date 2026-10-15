# Human participant email channel

CommHub now supports an opt-in `email` delivery channel. This is transport
plumbing only: it does not enable automatic messages or register any real
recipient by default.

## Private runtime configuration

Set these in an untracked environment file or secret manager, never in Git:

- `EMAIL_SMTP_HOST`
- `EMAIL_SMTP_PORT` (optional; defaults to 465 for SMTP over TLS)
- `EMAIL_SMTP_USERNAME`
- `EMAIL_SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_ALLOWED_RECIPIENTS` (comma-separated exact recipient addresses)

The participant's private runtime registry entry must include `email`,
`email_consent: true`, and `channels: ["email"]`. Their address must also
appear in `EMAIL_ALLOWED_RECIPIENTS`. Both consent and allowlisting are checked
before the transport is called. No default party is configured for email.

Messages include a reference ID to help correlate replies with the originating
task. The current change does **not** automatically ingest email replies; those
must remain advisory until a separately tested inbound-mail adapter verifies
sender identity and correlates the reference. An email reply must never itself
approve or execute a protected action.

## Test

Run `python -m pytest tests/test_comm_hub_email.py -q`. The tests mock the
transport and make no network requests. A successful SMTP response means only
that the SMTP server accepted the message, not that it was delivered or read.
