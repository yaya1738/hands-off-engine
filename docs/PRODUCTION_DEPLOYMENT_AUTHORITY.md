# Production Deployment Authority

The production deployment path is intentionally split into two authorities:

1. **Repository authority** — GitHub Actions, using the protected `production` environment.
2. **Host authority** — the production SSH principal supplied through `PRODUCTION_HOST`, `PRODUCTION_USER`, and `PRODUCTION_SSH_KEY` environment secrets.

The deployment workflow accepts an exact `main` commit SHA and refuses to deploy a revision that is not currently the tip of `main`. It never obtains or prints secret values.

Activation is opt-in per workflow dispatch. When enabled, only the known Factory autonomous and Telegram services are restarted if present; the workflow then requires the autonomous service to report active and verifies the deployed SHA.

## Current limitation

The repository cannot inspect GitHub Actions secret values through the GitHub API. Therefore a successful workflow dispatch is the authoritative test that host credentials are configured. A missing secret causes a fail-closed deployment rather than a guessed credential or direct bypass.

This workflow is designed to remove the need for interactive deployment once the repository's protected production environment has the required host credentials.
