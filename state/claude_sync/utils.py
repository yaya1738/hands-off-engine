#!/usr/bin/env python3
"""
Dual-Claude Coordination Utilities

Provides helper functions for Web Claude and CLI Claude to coordinate work.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

SYNC_DIR = Path(__file__).parent


def now():
    """Current UTC timestamp in ISO-8601 format"""
    return datetime.utcnow().isoformat() + 'Z'


def read_json(filename):
    """Read JSON file, return empty structure if doesn't exist"""
    path = SYNC_DIR / filename
    if not path.exists():
        if filename == 'active_sessions.json':
            return {'sessions': [], 'last_sync': now()}
        elif filename == 'task_queue.json':
            return {'tasks': []}
        else:
            return {}
    return json.loads(path.read_text())


def write_json(filename, data):
    """Write JSON file atomically"""
    path = SYNC_DIR / filename
    path.write_text(json.dumps(data, indent=2) + '\n')


def register_session(instance: str, session_id: str, task: str = None):
    """Register this Claude instance"""
    data = read_json('active_sessions.json')

    # Remove old sessions from this instance (cleanup)
    data['sessions'] = [s for s in data['sessions']
                       if s['instance'] != instance or
                          (datetime.fromisoformat(s['last_heartbeat'].replace('Z', ''))
                           > datetime.utcnow())]

    # Add new session
    data['sessions'].append({
        'instance': instance,
        'session_id': session_id,
        'started_at': now(),
        'last_heartbeat': now(),
        'current_task': task,
        'status': 'active'
    })

    data['last_sync'] = now()
    write_json('active_sessions.json', data)
    print(f"✓ Registered {instance} session: {session_id}")


def update_heartbeat(instance: str, task: str = None, status: str = 'active'):
    """Update heartbeat for this instance"""
    data = read_json('active_sessions.json')

    for session in data['sessions']:
        if session['instance'] == instance:
            session['last_heartbeat'] = now()
            if task is not None:
                session['current_task'] = task
            session['status'] = status
            break

    data['last_sync'] = now()
    write_json('active_sessions.json', data)


def post_message(from_instance: str, to_instance: str, msg_type: str, content: str, ref: str = None):
    """Post a message to another instance"""
    path = SYNC_DIR / 'messages.jsonl'
    msg = {
        'from': from_instance,
        'to': to_instance,
        'timestamp': now(),
        'type': msg_type,
        'content': content
    }
    if ref:
        msg['ref'] = ref

    with path.open('a') as f:
        f.write(json.dumps(msg) + '\n')

    print(f"✓ Message sent: {from_instance} → {to_instance} ({msg_type})")


def read_messages(for_instance: str, since: str = None, mark_read: bool = False):
    """Read messages for this instance"""
    path = SYNC_DIR / 'messages.jsonl'
    if not path.exists():
        return []

    messages = []
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            msg = json.loads(line)
            if msg['to'] == for_instance or msg['to'] == 'all':
                if since is None or msg['timestamp'] > since:
                    messages.append(msg)

    return messages


def get_active_sessions():
    """Get all active sessions"""
    data = read_json('active_sessions.json')
    now_ts = datetime.utcnow()

    active = []
    for session in data['sessions']:
        last_hb = datetime.fromisoformat(session['last_heartbeat'].replace('Z', ''))
        age_minutes = (now_ts - last_hb).total_seconds() / 60

        if age_minutes < 10:  # Active if heartbeat within 10 minutes
            session['age_minutes'] = age_minutes
            active.append(session)

    return active


def claim_task(instance: str, task_id: str):
    """Claim a task"""
    data = read_json('task_queue.json')

    for task in data['tasks']:
        if task['task_id'] == task_id:
            if task['claimed_by'] is None:
                task['claimed_by'] = instance
                task['claimed_at'] = now()
                task['status'] = 'in_progress'
                write_json('task_queue.json', data)
                log_action(instance, 'claimed_task', task_id)
                print(f"✓ Task {task_id} claimed by {instance}")
                return True
            else:
                print(f"✗ Task {task_id} already claimed by {task['claimed_by']}")
                return False

    print(f"✗ Task {task_id} not found")
    return False


def complete_task(instance: str, task_id: str, result: str = 'success', artifacts: list = None):
    """Mark task as completed"""
    data = read_json('task_queue.json')

    for task in data['tasks']:
        if task['task_id'] == task_id and task['claimed_by'] == instance:
            task['status'] = 'completed'
            task['completed_at'] = now()
            if artifacts:
                task['artifacts'] = artifacts
            write_json('task_queue.json', data)
            log_action(instance, 'completed_task', task_id, {'result': result, 'artifacts': artifacts})
            print(f"✓ Task {task_id} completed by {instance}")
            return True

    print(f"✗ Task {task_id} not found or not claimed by {instance}")
    return False


def add_task(task_id: str, description: str, priority: str = 'medium',
             assigned_to: str = 'any', dependencies: list = None):
    """Add a new task to the queue"""
    data = read_json('task_queue.json')

    # Check if task already exists
    if any(t['task_id'] == task_id for t in data['tasks']):
        print(f"✗ Task {task_id} already exists")
        return False

    task = {
        'task_id': task_id,
        'description': description,
        'priority': priority,
        'assigned_to': assigned_to,
        'claimed_by': None,
        'status': 'pending',
        'created_at': now(),
        'claimed_at': None,
        'completed_at': None,
        'dependencies': dependencies or [],
        'artifacts': [],
        'notes': ''
    }

    data['tasks'].append(task)
    write_json('task_queue.json', data)
    print(f"✓ Task {task_id} added to queue")
    return True


def log_action(instance: str, action: str, task_id: str = None, details: dict = None):
    """Log an action to the work log"""
    path = SYNC_DIR / 'work_log.jsonl'
    entry = {
        'instance': instance,
        'timestamp': now(),
        'action': action,
    }
    if task_id:
        entry['task_id'] = task_id
    if details:
        entry['details'] = details

    with path.open('a') as f:
        f.write(json.dumps(entry) + '\n')


def init_coordination():
    """Initialize coordination files"""
    SYNC_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize files if they don't exist
    if not (SYNC_DIR / 'active_sessions.json').exists():
        write_json('active_sessions.json', {'sessions': [], 'last_sync': now()})
        print("✓ Created active_sessions.json")

    if not (SYNC_DIR / 'task_queue.json').exists():
        write_json('task_queue.json', {'tasks': []})
        print("✓ Created task_queue.json")

    if not (SYNC_DIR / 'messages.jsonl').exists():
        (SYNC_DIR / 'messages.jsonl').touch()
        print("✓ Created messages.jsonl")

    if not (SYNC_DIR / 'work_log.jsonl').exists():
        (SYNC_DIR / 'work_log.jsonl').touch()
        print("✓ Created work_log.jsonl")

    print("✓ Coordination system initialized")


# CLI interface
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: utils.py <command> [args...]")
        print("\nCommands:")
        print("  init                                    - Initialize coordination system")
        print("  register <instance> <session_id>        - Register a session")
        print("  heartbeat <instance> [task]             - Update heartbeat")
        print("  post <from> <to> <type> <content>       - Post a message")
        print("  read <instance>                         - Read messages")
        print("  sessions                                - Show active sessions")
        print("  claim <instance> <task_id>              - Claim a task")
        print("  complete <instance> <task_id> [result]  - Complete a task")
        print("  add-task <task_id> <description>        - Add a task")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init':
        init_coordination()

    elif command == 'register':
        if len(sys.argv) < 4:
            print("Usage: register <instance> <session_id> [task]")
            sys.exit(1)
        instance = sys.argv[2]
        session_id = sys.argv[3]
        task = sys.argv[4] if len(sys.argv) > 4 else None
        register_session(instance, session_id, task)

    elif command == 'heartbeat':
        if len(sys.argv) < 3:
            print("Usage: heartbeat <instance> [task]")
            sys.exit(1)
        instance = sys.argv[2]
        task = sys.argv[3] if len(sys.argv) > 3 else None
        update_heartbeat(instance, task)
        print(f"✓ Heartbeat updated for {instance}")

    elif command == 'post':
        if len(sys.argv) < 6:
            print("Usage: post <from> <to> <type> <content>")
            sys.exit(1)
        post_message(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

    elif command == 'read':
        if len(sys.argv) < 3:
            print("Usage: read <instance>")
            sys.exit(1)
        messages = read_messages(sys.argv[2])
        if messages:
            print(f"\n{len(messages)} message(s) for {sys.argv[2]}:\n")
            for msg in messages:
                print(f"[{msg['timestamp']}] {msg['from']} → {msg['to']} ({msg['type']})")
                print(f"  {msg['content']}\n")
        else:
            print(f"No messages for {sys.argv[2]}")

    elif command == 'sessions':
        sessions = get_active_sessions()
        if sessions:
            print(f"\n{len(sessions)} active session(s):\n")
            for s in sessions:
                print(f"• {s['instance']} ({s['session_id']})")
                print(f"  Status: {s['status']}")
                print(f"  Task: {s.get('current_task', 'None')}")
                print(f"  Last heartbeat: {s['age_minutes']:.1f} minutes ago\n")
        else:
            print("No active sessions")

    elif command == 'claim':
        if len(sys.argv) < 4:
            print("Usage: claim <instance> <task_id>")
            sys.exit(1)
        claim_task(sys.argv[2], sys.argv[3])

    elif command == 'complete':
        if len(sys.argv) < 4:
            print("Usage: complete <instance> <task_id> [result]")
            sys.exit(1)
        instance = sys.argv[2]
        task_id = sys.argv[3]
        result = sys.argv[4] if len(sys.argv) > 4 else 'success'
        complete_task(instance, task_id, result)

    elif command == 'add-task':
        if len(sys.argv) < 4:
            print("Usage: add-task <task_id> <description>")
            sys.exit(1)
        add_task(sys.argv[2], sys.argv[3])

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
