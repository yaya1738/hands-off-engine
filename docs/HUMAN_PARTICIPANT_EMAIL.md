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
- `EMAIL_ALLOWED_RECIPIENTS`
- `EMAIL_IMAP_HOST`, `EMAIL_IMAP_USERNAME`, `EMAIL_IMAP_PASSWORD` (optional inbound polling)
- `EMAIL_AUTH_SERV_ID` (exact trusted receiving server authserv-id, required to accept inbound replies) (comma-separated exact recipient addresses)

The participant's private runtime registry entry must include `email`,
`email_consent: true`, and `channels: ["email"]`. Their address must also
appear in `EMAIL_ALLOWED_RECIPIENTS`. Both consent and allowlisting are checked
before the transport is called. No default party is configured for email.

Messages include a reference ID to help correlate replies with the originating
task. Inbound polling is optional and disabled until private IMAP credentials and
`EMAIL_AUTH_SERV_ID` are configured. It accepts only an Authentication-Results
header from that exact receiving authserv-id with SPF or DKIM passing for the
sender's domain, then requires the sender to match one uniquely enabled human
participant and the reference to match a message sent to that participant.
The reply is persisted as advisory input pending review; it cannot itself
approve or execute a protected action. Validate the authserv-id against the
actual receiving provider before enabling polling.

## Test

Run `python -m pytest tests/test_comm_hub_email.py -q`. The tests mock the
transport and make no network requests. A successful SMTP response means only
that the SMTP server accepted the message, not that it was delivered or read.
