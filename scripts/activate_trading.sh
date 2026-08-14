#!/usr/bin/env bash
set -euo pipefail

# Fail-closed compatibility shim for the historical balance-threshold launcher.
# A balance threshold is never an authority to enable financial execution.

echo "DENIED: legacy trading activation is quarantined."
echo "Financial execution remains disabled and must not be enabled by this script."
exit 1
