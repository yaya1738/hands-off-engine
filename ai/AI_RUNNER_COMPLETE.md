# AI Runner — execution disabled pending governed migration

> **Security notice:** This legacy runner is not an authorized execution surface.
> Do not set `AI_RUNNER_EXECUTE=1`, copy an older version of this runner into a
> deployment, or use the historical setup instructions below to enable shell
> execution.

The current `ai/ai_runner.py` implementation treats LLM-generated shell
commands as untrusted proposals. Its `execute_command()` function always
returns a blocked result and never calls a shell. The legacy
`AI_RUNNER_EXECUTE` environment variable is retained only for compatibility;
it is not an authorization mechanism.

## Required migration before execution can be reconsidered

1. Convert each proposed operation into a typed, schema-validated command.
2. Bind the command to an authenticated requester and immutable content digest.
3. Obtain a fresh, explicit approval for that exact command.
4. Submit it through the central governed authority and approved executor.
5. Require the authority's affirmative `execution_enabled` decision at the
   final side-effect boundary.
6. Keep LIVE execution disabled unless a separately reviewed policy explicitly
   grants it. Never infer permission from an environment variable, model
   output, task mode, or approval label alone.

## Current supported behavior

- LLM planning and proposal generation may be used.
- Proposed shell commands may be recorded for review.
- No shell command from this runner may be executed.
- The old systemd example and shell setup instructions have been retired
  because they described a root-running arbitrary-command service.

Use the governed command protocol instead of this legacy runner for any future
execution work.
