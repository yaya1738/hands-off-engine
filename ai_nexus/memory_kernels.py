"""
Memory Kernels API v0.1 (Part 2: Historical Contraction)

Provides API for loading and updating memory kernels:
    - load_kernel(kernel_id) -> MemoryKernel
    - append_kernel_update(kernel_id, update) -> None
    - list_kernels() -> List[str]

Kernels are stored in: ai/memory/kernels/{kernel_id}.json

Future: Contraction engine will ingest from ai/history/* and build/update kernels.

See: docs/SPARK_PLUG_ARCHITECTURE_v0.1.md (Part 2)
"""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ai_nexus.spark_plug_types import (
    MemoryKernel,
    KernelUpdate,
    Decision,
    FailedPath
)

# Paths
REPO_ROOT = Path(__file__).parent.parent
KERNELS_DIR = REPO_ROOT / "ai" / "memory" / "kernels"


# =============================================================================
# Core API
# =============================================================================

def load_kernel(kernel_id: str) -> Optional[MemoryKernel]:
    """
    Load a memory kernel by ID

    Args:
        kernel_id: Kernel identifier (e.g., "risk_model_v2")

    Returns:
        MemoryKernel if exists, None otherwise
    """
    kernel_path = KERNELS_DIR / f"{kernel_id}.json"

    if not kernel_path.exists():
        return None

    with open(kernel_path) as f:
        data = json.load(f)

    return MemoryKernel.from_dict(data)


def save_kernel(kernel: MemoryKernel) -> None:
    """
    Save a memory kernel to disk

    Args:
        kernel: MemoryKernel to save
    """
    KERNELS_DIR.mkdir(parents=True, exist_ok=True)

    kernel_path = KERNELS_DIR / f"{kernel.kernel_id}.json"

    with open(kernel_path, 'w') as f:
        f.write(kernel.to_json())


def append_kernel_update(kernel_id: str, update: KernelUpdate) -> None:
    """
    Append an update to a memory kernel

    Merges the update into the kernel structure based on update_type:
        - decision: Add to key_decisions[]
        - failed_path: Add to failed_paths[]
        - question: Add to open_questions[]
        - summary_edit: Update summary

    Args:
        kernel_id: Kernel identifier
        update: KernelUpdate to apply

    Raises:
        ValueError: If kernel doesn't exist
    """
    kernel = load_kernel(kernel_id)
    if kernel is None:
        raise ValueError(f"Kernel '{kernel_id}' not found. Create it first with create_kernel().")

    # Apply update based on type
    if update.update_type == "decision":
        decision = Decision(
            decision=update.content.get("decision", ""),
            rationale=update.content.get("rationale", ""),
            source=update.source,
            date=update.date,
            status=update.content.get("status", "approved")
        )
        kernel.key_decisions.append(decision)

    elif update.update_type == "failed_path":
        failed_path = FailedPath(
            attempt=update.content.get("attempt", ""),
            failure=update.content.get("failure", ""),
            lesson=update.content.get("lesson", ""),
            date=update.date
        )
        kernel.failed_paths.append(failed_path)

    elif update.update_type == "question":
        question = update.content.get("question", "")
        if question and question not in kernel.open_questions:
            kernel.open_questions.append(question)

    elif update.update_type == "summary_edit":
        new_summary = update.content.get("summary", "")
        if new_summary:
            kernel.summary = new_summary

    # Update timestamp
    kernel.last_updated = datetime.utcnow().isoformat() + "Z"

    # Add raw ref if provided
    raw_ref = update.content.get("raw_ref")
    if raw_ref and raw_ref not in kernel.raw_refs:
        kernel.raw_refs.append(raw_ref)

    # Save updated kernel
    save_kernel(kernel)


def list_kernels() -> List[str]:
    """
    List all available kernel IDs

    Returns:
        List of kernel IDs (e.g., ["risk_model_v2", "infra_architecture"])
    """
    if not KERNELS_DIR.exists():
        return []

    return [
        p.stem  # filename without .json extension
        for p in KERNELS_DIR.glob("*.json")
    ]


def create_kernel(
    kernel_id: str,
    topic: str,
    summary: str = "",
    source_weights: Optional[dict] = None
) -> MemoryKernel:
    """
    Create a new memory kernel

    Args:
        kernel_id: Unique kernel identifier
        topic: Human-readable topic name
        summary: Initial summary (optional)
        source_weights: Custom source weights (optional)

    Returns:
        Created MemoryKernel

    Raises:
        ValueError: If kernel already exists
    """
    if load_kernel(kernel_id) is not None:
        raise ValueError(f"Kernel '{kernel_id}' already exists")

    kernel = MemoryKernel(
        kernel_id=kernel_id,
        topic=topic,
        summary=summary,
        source_weights=source_weights or {
            "chatgpt": 1.0,
            "claude_cli": 0.8,
            "github_copilot_agent": 0.6
        }
    )

    save_kernel(kernel)
    return kernel


# =============================================================================
# Contraction Engine (Future Implementation - Stubs)
# =============================================================================

def ingest_from_history(history_dir: Path) -> None:
    """
    Ingest raw historical logs and build/update kernels

    Expected inputs in ai/history/:
        - chatgpt/*.jsonl - ChatGPT conversation exports
        - claude_cli/*.jsonl - Claude CLI session logs
        - github_agent/*.jsonl - GitHub agent activity
        - system/*.jsonl - System decisions and actions

    Process:
        1. Read raw logs
        2. Normalize format
        3. Group by topic (risk, alpha, infra, coordination)
        4. Extract key decisions, failed paths, open questions
        5. Compress into kernel summaries
        6. Save/update kernels

    TODO: Implement full contraction engine
    """
    raise NotImplementedError(
        "Contraction engine not yet implemented. "
        "For now, kernels must be created/updated manually using create_kernel() and append_kernel_update()."
    )


def normalize_raw_log(log_file: Path, source: str) -> List[dict]:
    """
    Normalize a raw log file into structured format

    Args:
        log_file: Path to raw log (JSONL)
        source: Source identifier (chatgpt, claude_cli, github_agent, system)

    Returns:
        List of normalized message dicts

    TODO: Implement normalization logic per source
    """
    raise NotImplementedError("Log normalization not yet implemented")


def extract_decisions(messages: List[dict]) -> List[Decision]:
    """
    Extract key decisions from normalized messages

    TODO: Implement decision extraction (ML/heuristic)
    """
    raise NotImplementedError("Decision extraction not yet implemented")


def extract_failed_paths(messages: List[dict]) -> List[FailedPath]:
    """
    Extract failed attempts from normalized messages

    TODO: Implement failed path extraction
    """
    raise NotImplementedError("Failed path extraction not yet implemented")


def compress_to_summary(messages: List[dict], topic: str) -> str:
    """
    Compress messages into tight summary for a topic

    TODO: Implement compression (LLM-based or extractive)
    """
    raise NotImplementedError("Summary compression not yet implemented")


# =============================================================================
# Utility Functions
# =============================================================================

def get_kernel_summary(kernel_id: str) -> Optional[str]:
    """Quick access to kernel summary without loading full kernel"""
    kernel = load_kernel(kernel_id)
    return kernel.summary if kernel else None


def search_kernels(query: str) -> List[str]:
    """
    Search kernels by topic or content

    Args:
        query: Search query

    Returns:
        List of matching kernel IDs

    TODO: Implement full-text search
    """
    # Simple stub: case-insensitive substring match on kernel_id and topic
    results = []
    for kernel_id in list_kernels():
        kernel = load_kernel(kernel_id)
        if kernel and (
            query.lower() in kernel_id.lower() or
            query.lower() in kernel.topic.lower() or
            query.lower() in kernel.summary.lower()
        ):
            results.append(kernel_id)
    return results


# =============================================================================
# Example Usage (for testing)
# =============================================================================

if __name__ == "__main__":
    import sys

    # Example: Create a test kernel
    print("Creating example kernel...")

    try:
        kernel = create_kernel(
            kernel_id="example_test_kernel",
            topic="Example Test Topic",
            summary="This is an example kernel created for testing."
        )
        print(f"✓ Created kernel: {kernel.kernel_id}")
    except ValueError as e:
        print(f"⚠ Kernel already exists, loading...")
        kernel = load_kernel("example_test_kernel")

    # Example: Append a decision
    from ai_nexus.spark_plug_types import create_kernel_update_decision

    update = create_kernel_update_decision(
        decision="Use Kelly fraction 0.15 for week 1",
        rationale="Conservative staged rollout",
        source="cpu_risk_20251125_01",
        agent="chatgpt"
    )

    print("Appending decision update...")
    append_kernel_update("example_test_kernel", update)
    print("✓ Update appended")

    # Reload and display
    kernel = load_kernel("example_test_kernel")
    print(f"\nKernel state:")
    print(f"  Topic: {kernel.topic}")
    print(f"  Summary: {kernel.summary}")
    print(f"  Key Decisions: {len(kernel.key_decisions)}")
    if kernel.key_decisions:
        print(f"    - {kernel.key_decisions[-1].decision}")

    print("\nAvailable kernels:")
    for kid in list_kernels():
        print(f"  - {kid}")
