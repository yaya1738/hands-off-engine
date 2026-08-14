#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
Oracle provisioning automation has been retired.

Reason: cloud-account/payment verification and provider-specific network setup
must remain outside the repository, while host deployment is provider-neutral.
This script must not collect credentials, generate provider credentials, or
mutate cloud resources with guessed defaults.

Use the cloud provider's official console/API to provision an Ubuntu Linux host,
configure SSH using your own credentials, then run:

  scripts/bootstrap_host.sh <ssh-host> [remote-repo-path]

The bootstrap installs the existing persistent Factory systemd user service and
verifies that live financial execution remains hard-disabled.
EOF
