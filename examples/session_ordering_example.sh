#!/bin/bash
# Example: Using Agent Session Ordering
#
# This demonstrates how to use the session ordering system to ensure
# agent sessions execute in the correct order.

set -e

echo "=================================================="
echo "Agent Session Ordering Example"
echo "=================================================="
echo ""

# Example 1: Simple Sequential Sessions
# Session 2 must wait for Session 1 to complete
echo "Example 1: Sequential Sessions"
echo "--------------------------------"
echo ""

echo "Starting Session 1 (Foundation)..."
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_example_session1 \
    --session-goal "Establish foundation and requirements" \
    --rounds 1 \
    --agents chatgpt,claude_cli \
    --session-order 1

echo ""
echo "Session 1 complete. Now starting Session 2..."
echo ""

echo "Starting Session 2 (Implementation)..."
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_example_session2 \
    --session-goal "Implement based on foundation" \
    --previous-session 20251201_example_session1 \
    --rounds 1 \
    --agents chatgpt,claude_cli \
    --session-order 2

echo ""
echo "Session 2 complete."
echo ""

# Example 2: Parallel Dependencies
# Session C depends on both Session A and Session B
echo "Example 2: Parallel Dependencies"
echo "----------------------------------"
echo ""

echo "Starting Session A and B in parallel..."
echo "(In practice, you'd run these in separate terminals)"
echo ""

# Session A
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_example_sessionA \
    --session-goal "Develop component A" \
    --rounds 1 \
    --agents chatgpt

# Session B  
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_example_sessionB \
    --session-goal "Develop component B" \
    --rounds 1 \
    --agents claude_cli

echo ""
echo "Sessions A and B complete. Now starting integration session..."
echo ""

# Session C depends on both
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251201_example_sessionC \
    --session-goal "Integrate components A and B" \
    --depends-on "20251201_example_sessionA,20251201_example_sessionB" \
    --rounds 1 \
    --agents chatgpt,claude_cli

echo ""
echo "Integration session complete."
echo ""

# Example 3: Task Queue with Ordering
echo "Example 3: Task Queue with Dependencies"
echo "----------------------------------------"
echo ""

cat > /tmp/task_queue_example.py << 'EOF'
from pathlib import Path
from scripts.autonomous_task_queue import AutonomousTaskQueue

# Initialize queue
repo_root = Path(__file__).parent.parent
queue = AutonomousTaskQueue(repo_root)

# Phase 1: Setup
setup_id = queue.add_task(
    title="Setup environment",
    description="Install dependencies and configure",
    priority="high",
    metadata={'task_order': 1}
)
print(f"Added task: Setup (order 1, id={setup_id[:8]}...)")

# Phase 2: Build (depends on setup)
build_id = queue.add_task(
    title="Build application",
    description="Compile and build",
    priority="high",
    metadata={
        'previous_task_id': setup_id,
        'task_order': 2
    }
)
print(f"Added task: Build (order 2, depends on setup, id={build_id[:8]}...)")

# Phase 3: Test (depends on build)
test_id = queue.add_task(
    title="Run tests",
    description="Execute test suite",
    priority="high",
    metadata={
        'previous_task_id': build_id,
        'task_order': 3
    }
)
print(f"Added task: Test (order 3, depends on build, id={test_id[:8]}...)")

print("\n--- Getting Tasks in Order ---")

# Get tasks in order
for i in range(3):
    task = queue.get_next_task()
    if task:
        print(f"\nTask {i+1}: {task['title']}")
        print(f"  Order: {task.get('task_order', 'N/A')}")
        print(f"  Previous: {task.get('previous_task_id', 'None')[:8] if task.get('previous_task_id') else 'None'}...")
        
        # Simulate completion
        queue.complete_task(task['id'], f"Completed {task['title']}")
        print(f"  Status: Completed")

print("\n--- All Tasks Complete ---")
EOF

python /tmp/task_queue_example.py

echo ""
echo "=================================================="
echo "Examples Complete!"
echo "=================================================="
echo ""
echo "Key Takeaways:"
echo "1. Use --previous-session for strict sequential ordering"
echo "2. Use --depends-on for parallel dependencies"
echo "3. Use --session-order for explicit numbered sequences"
echo "4. Sessions with unmet dependencies are blocked automatically"
echo "5. Task queue enforces the same ordering for autonomous tasks"
echo ""
echo "See docs/AGENT_SESSION_ORDERING.md for full documentation"
