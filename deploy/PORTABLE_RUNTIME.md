# Portable Factory Runtime

The Factory runtime does not require DigitalOcean. A Linux machine with Python 3 and systemd user services can run the autonomous daemon directly from a checked-out repository.

## Install

From the repository root:

```bash
bash deploy/install-user-runtime.sh
```

The installer creates a user-level systemd service, enables it for the user, and starts it immediately. systemd restarts the daemon after unexpected exits.

## Verify

```bash
systemctl --user status hands-off-engine-factory.service
journalctl --user -u hands-off-engine-factory.service -n 100 --no-pager
```

The daemon persists its own task state and the Factory scheduler persists queued autonomous objectives. Restarting the service therefore resumes from durable state rather than requiring ChatGPT to drive the next step.

## Safety

This runtime installation does **not** enable live financial execution. The daemon's live-trading capability remains hard-disabled in code until the explicit safety/unban process changes it.

DigitalOcean is therefore an optional deployment provider, not a runtime prerequisite.
