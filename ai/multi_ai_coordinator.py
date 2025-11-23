#!/usr/bin/env python3
"""
Multi-AI Coordinator for Hands-Off Engine

Enables continuous collaboration between Claude Web, ChatGPT, and Claude CLI
without requiring continual user prompting. Coordinates tasks, shares context,
and maintains conversation continuity across different AI systems.

Part of CLM/Nexus/System serving user Yair Siegel.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid


class MultiAICoordinator:
    """
    Manages multi-AI collaboration and continuous interaction.
    
    Enables:
    - Claude web chatbot to continue conversations autonomously
    - ChatGPT to collaborate on tasks
    - Claude CLI to execute and report back
    - All AIs to work together without user prompting each interaction
    """

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.state_dir = repo_root / 'state'
        self.ai_nexus_dir = self.state_dir / 'ai_nexus_logs'
        self.conversation_log = self.ai_nexus_dir / 'conversation_log.jsonl'
        self.active_collaborations = self.ai_nexus_dir / 'active_collaborations.json'
        self.ai_context_cache = self.ai_nexus_dir / 'ai_context_cache.json'
        
        # Ensure directories exist
        self.ai_nexus_dir.mkdir(parents=True, exist_ok=True)

    def start_collaboration(
        self,
        topic: str,
        initiating_ai: str,
        participants: List[str],
        context: Dict[str, Any],
        priority: str = 'normal'
    ) -> str:
        """
        Start a new multi-AI collaboration session.
        
        Args:
            topic: What the AIs are collaborating on
            initiating_ai: Which AI started this (claude-web, chatgpt, claude-cli, copilot)
            participants: List of AI systems that should participate
            context: Shared context for this collaboration
            priority: Priority level (critical, high, normal, low)
            
        Returns:
            collaboration_id
        """
        collab_id = str(uuid.uuid4())
        
        collaboration = {
            'id': collab_id,
            'topic': topic,
            'initiating_ai': initiating_ai,
            'participants': participants,
            'context': context,
            'priority': priority,
            'status': 'active',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'messages': []
        }
        
        # Load and update active collaborations
        collaborations = self._load_active_collaborations()
        collaborations[collab_id] = collaboration
        self._save_active_collaborations(collaborations)
        
        # Log the initiation
        self._log_event({
            'type': 'collaboration_started',
            'collaboration_id': collab_id,
            'topic': topic,
            'initiating_ai': initiating_ai,
            'participants': participants,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        print(f"✓ Started collaboration: {topic}")
        print(f"  ID: {collab_id}")
        print(f"  Participants: {', '.join(participants)}")
        
        return collab_id

    def add_message(
        self,
        collaboration_id: str,
        from_ai: str,
        to_ai: Optional[str],
        message: str,
        message_type: str = 'message',
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add a message to an ongoing collaboration.
        
        Args:
            collaboration_id: ID of the collaboration
            from_ai: Which AI is sending the message
            to_ai: Target AI (None = broadcast to all)
            message: The message content
            message_type: Type of message (message, question, response, task_complete, etc.)
            metadata: Additional message metadata
            
        Returns:
            True if message added successfully
        """
        collaborations = self._load_active_collaborations()
        
        if collaboration_id not in collaborations:
            print(f"Error: Collaboration {collaboration_id} not found")
            return False
        
        collaboration = collaborations[collaboration_id]
        
        msg = {
            'from': from_ai,
            'to': to_ai,
            'message': message,
            'type': message_type,
            'metadata': metadata or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        collaboration['messages'].append(msg)
        collaboration['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Save updated collaboration
        collaborations[collaboration_id] = collaboration
        self._save_active_collaborations(collaborations)
        
        # Log the message
        self._log_event({
            'type': 'message',
            'collaboration_id': collaboration_id,
            'from': from_ai,
            'to': to_ai,
            'message_type': message_type,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return True

    def get_pending_messages(self, for_ai: str) -> List[Dict[str, Any]]:
        """
        Get all pending messages for a specific AI system.
        
        This allows each AI to check for messages when it's invoked,
        enabling async communication without constant polling.
        
        Args:
            for_ai: Which AI to get messages for (claude-web, chatgpt, claude-cli, copilot)
            
        Returns:
            List of pending messages with collaboration context
        """
        collaborations = self._load_active_collaborations()
        pending_messages = []
        
        for collab_id, collab in collaborations.items():
            if collab['status'] != 'active':
                continue
                
            # Check if this AI is a participant
            if for_ai not in collab['participants']:
                continue
            
            # Get unread messages for this AI
            for msg in collab['messages']:
                # Message is for this AI if:
                # 1. Explicitly addressed to this AI, OR
                # 2. Broadcast (to is None) and not from this AI
                if msg['to'] == for_ai or (msg['to'] is None and msg['from'] != for_ai):
                    pending_messages.append({
                        'collaboration_id': collab_id,
                        'collaboration_topic': collab['topic'],
                        'message': msg,
                        'context': collab['context']
                    })
        
        return pending_messages

    def complete_collaboration(
        self,
        collaboration_id: str,
        completing_ai: str,
        result: str,
        success: bool = True
    ) -> bool:
        """
        Mark a collaboration as complete.
        
        Args:
            collaboration_id: ID of the collaboration
            completing_ai: Which AI is completing this
            result: Summary of the collaboration result
            success: Whether the collaboration succeeded
            
        Returns:
            True if marked complete successfully
        """
        collaborations = self._load_active_collaborations()
        
        if collaboration_id not in collaborations:
            print(f"Error: Collaboration {collaboration_id} not found")
            return False
        
        collaboration = collaborations[collaboration_id]
        collaboration['status'] = 'completed' if success else 'failed'
        collaboration['completed_by'] = completing_ai
        collaboration['result'] = result
        collaboration['completed_at'] = datetime.now(timezone.utc).isoformat()
        
        # Save updated collaboration
        collaborations[collaboration_id] = collaboration
        self._save_active_collaborations(collaborations)
        
        # Log completion
        self._log_event({
            'type': 'collaboration_completed',
            'collaboration_id': collaboration_id,
            'completing_ai': completing_ai,
            'success': success,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        print(f"✓ Completed collaboration: {collaboration['topic']}")
        print(f"  Result: {result}")
        
        return True

    def get_active_collaborations(self, for_ai: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all active collaborations, optionally filtered by AI participant.
        
        Args:
            for_ai: Filter to collaborations involving this AI (None = all)
            
        Returns:
            List of active collaboration details
        """
        collaborations = self._load_active_collaborations()
        active = []
        
        for collab_id, collab in collaborations.items():
            if collab['status'] != 'active':
                continue
                
            if for_ai is None or for_ai in collab['participants']:
                active.append({
                    'id': collab_id,
                    'topic': collab['topic'],
                    'participants': collab['participants'],
                    'message_count': len(collab['messages']),
                    'created_at': collab['created_at'],
                    'priority': collab['priority']
                })
        
        return active

    def share_context(self, ai_name: str, context_key: str, context_data: Any) -> bool:
        """
        Share context data that all AIs can access.
        
        This creates a shared knowledge base that survives across AI sessions.
        
        Args:
            ai_name: Which AI is sharing this context
            context_key: Key to store context under
            context_data: The context data to share
            
        Returns:
            True if context shared successfully
        """
        cache = self._load_context_cache()
        
        cache[context_key] = {
            'data': context_data,
            'shared_by': ai_name,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self._save_context_cache(cache)
        
        self._log_event({
            'type': 'context_shared',
            'ai': ai_name,
            'context_key': context_key,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        return True

    def get_shared_context(self, context_key: str) -> Optional[Any]:
        """
        Get shared context data.
        
        Args:
            context_key: Key of the context to retrieve
            
        Returns:
            Context data or None if not found
        """
        cache = self._load_context_cache()
        
        if context_key in cache:
            return cache[context_key]['data']
        
        return None

    def _load_active_collaborations(self) -> Dict[str, Dict]:
        """Load active collaborations from disk."""
        if not self.active_collaborations.exists():
            return {}
        
        with open(self.active_collaborations, 'r') as f:
            return json.load(f)

    def _save_active_collaborations(self, collaborations: Dict[str, Dict]):
        """Save active collaborations to disk."""
        with open(self.active_collaborations, 'w') as f:
            json.dump(collaborations, f, indent=2)

    def _load_context_cache(self) -> Dict[str, Any]:
        """Load shared context cache from disk."""
        if not self.ai_context_cache.exists():
            return {}
        
        with open(self.ai_context_cache, 'r') as f:
            return json.load(f)

    def _save_context_cache(self, cache: Dict[str, Any]):
        """Save shared context cache to disk."""
        with open(self.ai_context_cache, 'w') as f:
            json.dump(cache, f, indent=2)

    def _log_event(self, event: Dict[str, Any]):
        """Log an event to the conversation log."""
        with open(self.conversation_log, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def display_status(self):
        """Display current multi-AI coordination status."""
        print("\n" + "="*60)
        print("MULTI-AI COORDINATION STATUS")
        print("="*60)
        
        # Show active collaborations
        collaborations = self._load_active_collaborations()
        active = [c for c in collaborations.values() if c['status'] == 'active']
        
        print(f"\nActive Collaborations: {len(active)}")
        for collab in active:
            print(f"\n  [{collab['id'][:8]}...] {collab['topic']}")
            print(f"  Participants: {', '.join(collab['participants'])}")
            print(f"  Messages: {len(collab['messages'])}")
            print(f"  Priority: {collab['priority']}")
        
        # Show shared context
        cache = self._load_context_cache()
        print(f"\nShared Context Items: {len(cache)}")
        for key in list(cache.keys())[:5]:
            print(f"  - {key} (by {cache[key]['shared_by']})")
        
        print("\n" + "="*60 + "\n")


def main():
    """CLI interface for multi-AI coordination."""
    import sys
    
    repo_root = Path(__file__).parent.parent
    coordinator = MultiAICoordinator(repo_root)
    
    if len(sys.argv) < 2:
        coordinator.display_status()
        return
    
    command = sys.argv[1]
    
    if command == 'status':
        coordinator.display_status()
    
    elif command == 'start':
        if len(sys.argv) < 5:
            print("Usage: multi_ai_coordinator.py start <topic> <initiating_ai> <participant1,participant2,...>")
            return
        
        topic = sys.argv[2]
        initiating_ai = sys.argv[3]
        participants = sys.argv[4].split(',')
        
        collab_id = coordinator.start_collaboration(
            topic=topic,
            initiating_ai=initiating_ai,
            participants=participants,
            context={}
        )
        print(f"Collaboration ID: {collab_id}")
    
    elif command == 'messages':
        if len(sys.argv) < 3:
            print("Usage: multi_ai_coordinator.py messages <ai_name>")
            return
        
        ai_name = sys.argv[2]
        messages = coordinator.get_pending_messages(ai_name)
        
        print(f"\nPending messages for {ai_name}: {len(messages)}\n")
        for msg_info in messages:
            msg = msg_info['message']
            print(f"[{msg_info['collaboration_topic']}]")
            print(f"From: {msg['from']}")
            print(f"Type: {msg['type']}")
            print(f"Message: {msg['message'][:100]}...")
            print()
    
    elif command == 'add-message':
        if len(sys.argv) < 5:
            print("Usage: multi_ai_coordinator.py add-message <collab_id> <from_ai> <message>")
            return
        
        collab_id = sys.argv[2]
        from_ai = sys.argv[3]
        message = sys.argv[4]
        
        success = coordinator.add_message(
            collaboration_id=collab_id,
            from_ai=from_ai,
            to_ai=None,  # Broadcast
            message=message
        )
        
        if success:
            print("✓ Message added")
    
    elif command == 'list':
        collaborations = coordinator.get_active_collaborations()
        print(f"\nActive collaborations: {len(collaborations)}\n")
        for collab in collaborations:
            print(f"[{collab['id'][:8]}...] {collab['topic']}")
            print(f"  Participants: {', '.join(collab['participants'])}")
            print(f"  Messages: {collab['message_count']}")
            print()
    
    else:
        print(f"Unknown command: {command}")
        print("Commands: status, start, messages, add-message, list")


if __name__ == '__main__':
    main()
