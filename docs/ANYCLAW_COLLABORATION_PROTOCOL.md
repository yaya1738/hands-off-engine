# AnyClaw ↔ Factory Collaboration Protocol

**Status:** active handshake contract
**Established:** 2026-09-14

## Purpose

This repository recognizes the local AnyClaw runtime as a potential peer execution agent, not merely an AI backend. The goal is bidirectional collaboration between the Factory and the AnyClaw instance on the operator's device.

## Shared bus

The canonical coordination surface is `scripts/comm_hub.py` and `ai/coordination/messages.jsonl`.

AnyClaw should identify itself on the bus as:

- party id: `anyclaw`
- role: `agent`
- capabilities: `chat`, `analysis`, `code`, `reasoning`, `device_control`, `file_access`
- trust: task-scoped; never implicitly grants authority to execute protected actions

## Handshake

A collaboration handshake consists of:

1. Factory publishes a `coordination` message addressed to `anyclaw`.
2. AnyClaw returns a `task_result` or `coordination` message identifying its runtime instance and supported transport.
3. Factory records the discovered transport in durable state.
4. Subsequent work is routed according to capability and ownership rather than by assuming that `codex_anyclaw` means Claude CLI.

## Safety boundary

This protocol deliberately carries **no credentials**. Telegram tokens, API keys, OAuth material, and device secrets must remain outside Git history and outside coordination payloads.

AnyClaw may inspect and propose changes through the collaboration channel, but execution still passes through the Factory's existing authority/approval/executor gates.

## Initial synchronization objective

The first joint task is **runtime identity and transport discovery**:

> AnyClaw, identify the local process/transport through which you can receive and return Factory coordination messages. Do not expose secrets. Return only runtime identity, transport type, repository/workspace identity, and capability summary.

Once acknowledged, the Factory should promote the discovered transport into a reusable capability instead of creating a one-off probe.
