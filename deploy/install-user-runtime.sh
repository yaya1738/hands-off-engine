#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${HOME}/.config/systemd/user"
SERVICE_PATH="${SERVICE_DIR}/hands-off-engine-factory.service"

mkdir -p "${SERVICE_DIR}"

sed "s#%h/hands-off-engine#${REPO_ROOT}#g" "${REPO_ROOT}/deploy/factory-runtime.service" > "${SERVICE_PATH}"

systemctl --user daemon-reload
systemctl --user enable --now hands-off-engine-factory.service

systemctl --user --no-pager --full status hands-off-engine-factory.service
