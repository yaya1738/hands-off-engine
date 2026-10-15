# Human participant routing policy

This policy defines when Factory should involve an opted-in human participant. It is transport-independent: email is a delivery channel, not the decision-maker.

## Core rule

Factory owns relevance detection. Do not contact a participant merely because a status changed or because a channel is available. Contact them only when their known role/context makes their input likely to change the next decision, unblock work, or validate a material assumption.

## Eligible reasons to contact

A request may be proposed when one of these conditions is recorded against a task or decision:

- **Human-context gap:** a decision depends on personal, local, relationship, or preference information that the system cannot reliably infer.
- **Material ambiguity:** two or more safe paths remain and the choice has meaningful downstream consequences.
- **External blocker:** progress depends on a human action or information the system cannot obtain through its existing authorized capabilities.
- **Stakeholder validation:** a concrete result needs the participant's domain feedback before the next irreversible or costly step.
- **Requested update:** the participant explicitly opted into a relevant milestone or digest category.

Do not contact for routine heartbeats, internal retries, transient errors with an automated recovery path, or information already available in trusted project state.

## Producer-side decision contract

The canonical task producer may opt into a contact proposal only by placing a structured `human_contact` object in the task assignment's `context`. The task worker forwards that object through the existing continuation event into the review-only coordination proposal. This is metadata for review, not a send instruction.

The object must explicitly identify the participant and include the eligible `reason_code`, one concrete `question`, `why_it_matters`, and a bounded `summary` (plus the task/correlation identity supplied by the task/event). Use only information the producer has actually established. Do not synthesize a question from health warnings, assessment gaps, pending authority, generic blockers, or status changes. The router rejects missing fields and non-eligible reasons; the proposal remains `send_authorized: false` and must pass the separate participant policy and CommHub transport boundary.

The shared Factory decision context remains evidence only. An `authority_decision`, `factory_assessment`, or `system_health_observation` does not itself imply human relevance, consent, or approval authority. This preserves the canonical coordination bus and avoids a second decision store.

## Required message context

Every outbound request should carry structured fields in its payload:

- task_id and stable correlation_id
- reason_code from the eligible reasons above
- concise context and what Factory has already checked
- one specific question or requested observation
- why the answer changes the next step
- bounded choices where practical, plus an option to say “not sure”
- response deadline only when a real deadline exists
- what Factory will do if no reply arrives

Keep the email body understandable without access to GitHub or the runtime. Include the generated Reference value unchanged so a reply can be correlated. Minimize disclosure: send only the context needed for the question, never credentials, private logs, or unrelated personal data.

## Rate limiting and deduplication

Before sending, check durable contact history by participant and task. Do not send duplicate open questions for the same task/correlation. Prefer updating an existing thread. Apply a configurable cooldown and a daily cap; urgent safety-relevant notices may bypass the cooldown only when the reason is recorded. A failed send must not be recorded as delivered.

## Reply handling and authority

Inbound email is untrusted input even after sender authentication. Require all of the following before recording it as a reply:

1. Trusted receiving-server authentication results with a configured exact authserv-id.
2. Exactly one enabled participant matching the authenticated sender address.
3. A known, participant-bound message reference.
4. A provider message ID not already processed.

Persist accepted replies as human_reply_advisory, linked to the originating task/message. Never parse email text as executable commands. Words such as “approve”, “reject”, or “run this” in an email do not grant authority and must not bypass Factory's normal policy, authorization, simulation, approval, or execution gates. A human review step must explicitly decide whether the advice changes a task.

## Learning and closure

After review, record the decision outcome separately from the raw reply: whether it was useful, what assumption it resolved, and which task/decision it affected. Do not automatically promote arbitrary reply text into durable memory. Keep raw content bounded and access-controlled. Mark the question answered, expired, or superseded so Factory does not ask it again unnecessarily.

## Rollout gates

- Keep real participant addresses and consent records in private runtime configuration only.
- Keep outbound delivery and inbox polling disabled until private configuration is verified.
- Test policy decisions and rate limits with a mocked transport.
- Verify the real mail provider's authentication headers before enabling inbox polling.
- Observe advisory replies without automatic execution before considering any further automation.
