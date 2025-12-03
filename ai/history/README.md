# AI History (Raw Logs for Contraction)

This directory contains raw historical logs that feed into Part 2 (Memory Kernels) contraction engine.

## Structure

```
ai/history/
├── chatgpt/           # ChatGPT conversation exports
├── claude_cli/        # Claude CLI session logs
├── github_agent/      # GitHub agent activity
├── user/              # User events (Part 3 input)
├── system/            # System messages (Part 3 output)
└── README.md          # This file
```

## Log Sources

### chatgpt/
Raw exports of ChatGPT conversations. Format: JSONL

Expected fields per message:
```json
{
  "timestamp": "2025-11-25T12:00:00Z",
  "role": "user" | "assistant",
  "content": "message text",
  "conversation_id": "conv_abc123"
}
```

### claude_cli/
Claude CLI session logs. Format: JSONL

Expected fields per message:
```json
{
  "timestamp": "2025-11-25T12:00:00Z",
  "role": "user" | "assistant",
  "content": "message text",
  "session_id": "session_xyz"
}
```

### github_agent/
GitHub Copilot Agent activity (issues, PRs, comments). Format: JSONL

Expected fields per event:
```json
{
  "timestamp": "2025-11-25T12:00:00Z",
  "type": "issue_comment" | "pr_review" | "commit",
  "content": "event details",
  "issue_id": 123
}
```

### user/
User events from Part 3 (UserEvent objects). Format: JSONL

See: `ai_nexus/spark_plug_types.py` (UserEvent)

### system/
System messages to user from Part 3 (SystemToUserMessage objects). Format: JSONL

See: `ai_nexus/spark_plug_types.py` (SystemToUserMessage)

## Contraction Flow

1. **Raw Logs** → This directory (`ai/history/*`)
2. **Normalization** → Structured format per source
3. **Topic Grouping** → Group by risk, alpha, infra, coordination, etc.
4. **Extraction** → Key decisions, failed paths, open questions
5. **Compression** → Tight summaries per topic
6. **Kernel Storage** → `ai/memory/kernels/*.json`

## Future: Auto-Ingestion

The contraction engine (not yet fully implemented) will:
- Monitor `ai/history/` for new logs
- Auto-normalize and ingest
- Update relevant kernels
- Maintain source references

For now, ingestion is manual via `ai_nexus/memory_kernels.py` API.

## See Also

- `docs/SPARK_PLUG_ARCHITECTURE_v0.1.md` - Full architecture
- `ai_nexus/memory_kernels.py` - Contraction API
- `ai_nexus/spark_plug_types.py` - Core types
- `ai/memory/` - Output kernels

---

**Status:** Directory structure ready, auto-contraction not yet implemented
