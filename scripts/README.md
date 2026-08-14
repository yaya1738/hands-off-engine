# Scripts Directory

Executable helpers for testing, diagnostics, and operating the Hands-Off Engine.

## Persistent runtime

The canonical provider-neutral host path is:

```bash
scripts/bootstrap_host.sh <ssh-host> [remote-repo-path]
```

It installs the repository on an already-provisioned Linux host, creates the
Python environment, installs dependencies, installs the existing Factory
systemd user service, and verifies the live-financial kill switch.

No deployment helper in this directory should collect, print, copy, or embed
secrets. Cloud account creation and payment verification happen outside the
repository through the provider's official interface.

## Safety

Live financial execution is currently hard-disabled. Scripts that historically
started live trading or configured trading credentials are compatibility/deprecation
surfaces and must not be used to bypass the Factory authority or current-rules gate.

## Testing

Prefer the repository's automated tests and the portable-runtime regression workflow
for validation. Manual scripts should remain read-only or fail closed when they
would otherwise cross an authority boundary.
