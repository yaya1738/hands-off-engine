# Deployment control plane

## Safety contract

Production deployment is deliberately separate from ordinary `main` pushes. A deployment must identify an exact commit that is currently on `main`, verify the deployment credentials supplied through the protected production environment, deploy that exact revision, and verify the resulting revision and service state.

The production workflow therefore remains an explicit governed operation. Repository automation must not bypass the production environment, inject credentials, or mutate the production host through an alternate path.

## Current readiness boundary

At commit `a95ebe250a7f2dc6d7b9413685457087a19fb1a8`, repository-side safety gates have passed, including Secret Scan and the Factory Ollama fail-closed canary. The remaining deployment evidence must come from the production workflow and the target host; repository CI cannot truthfully substitute for that evidence.

## Fail-closed requirements

- Do not claim production is active without host-side verification.
- Do not fall back to historical credentials or repository-embedded secrets.
- Do not add a second SSH/deployment path to bypass the governed workflow.
- If deployment credentials are absent or invalid, deployment must stop.
- If the target revision cannot be verified after checkout, deployment must stop.
- If the autonomous service fails its post-deploy health check, deployment must be considered unsuccessful.
- Trading or other privileged external actions remain disabled until their separate authority and credential requirements are satisfied.

## Operator recovery

When the authorized production connection is available, deploy the exact approved `main` SHA through the governed production workflow and request activation only after the pre-deployment gates are green. Then verify the host revision and service health independently.
