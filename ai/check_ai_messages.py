#!/usr/bin/env python3
"""
AI Message Checker

Allows any AI system (Claude CLI, ChatGPT integration, etc.) to check for
pending messages in multi-AI collaborations and respond appropriately.

This enables continuous collaboration without user prompting - each AI can
check for messages when invoked and respond autonomously.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from multi_ai_coordinator import MultiAICoordinator


class AIMessageProcessor:
    """Process messages for a specific AI system."""
    
    def __init__(self, ai_name: str, repo_root: Path):
        """
        Initialize message processor.
        
        Args:
            ai_name: Name of this AI (claude-cli, chatgpt, copilot, etc.)
            repo_root: Root of the repository
        """
        self.ai_name = ai_name
        self.repo_root = repo_root
        self.coordinator = MultiAICoordinator(repo_root)
    
    def check_and_process_messages(self, auto_respond: bool = False) -> Dict[str, Any]:
        """
        Check for pending messages and optionally process them.
        
        Args:
            auto_respond: If True, automatically generate and post responses
            
        Returns:
            Dictionary with message count and summary
        """
        # Get pending messages
        messages = self.coordinator.get_pending_messages(self.ai_name)
        
        if not messages:
            return {
                'pending_messages': 0,
                'processed': 0,
                'summary': f'No pending messages for {self.ai_name}'
            }
        
        print(f"\n{'='*60}")
        print(f"MESSAGES FOR {self.ai_name.upper()}")
        print('='*60)
        print(f"\nFound {len(messages)} pending message(s)\n")
        
        processed = 0
        for i, msg_info in enumerate(messages, 1):
            collab_id = msg_info['collaboration_id']
            collab_topic = msg_info['collaboration_topic']
            msg = msg_info['message']
            
            print(f"Message {i}/{len(messages)}:")
            print(f"  Collaboration: {collab_topic} ({collab_id[:8]}...)")
            print(f"  From: {msg['from']}")
            print(f"  Type: {msg['type']}")
            print(f"  Time: {msg['timestamp']}")
            print(f"  Message: {msg['message'][:200]}{'...' if len(msg['message']) > 200 else ''}")
            print()
            
            if auto_respond:
                # In a full implementation, this would use the AI's API to generate a response
                # For now, we just acknowledge the message
                response = self._generate_auto_response(msg_info)
                if response:
                    self.coordinator.add_message(
                        collaboration_id=collab_id,
                        from_ai=self.ai_name,
                        to_ai=msg['from'] if msg['from'] != 'system' else None,
                        message=response,
                        message_type='auto_response'
                    )
                    processed += 1
                    print(f"  ✓ Auto-responded")
        
        print('='*60 + '\n')
        
        return {
            'pending_messages': len(messages),
            'processed': processed,
            'summary': f"Processed {processed}/{len(messages)} messages for {self.ai_name}",
            'messages': messages
        }
    
    def _generate_auto_response(self, msg_info: Dict[str, Any]) -> str:
        """
        Generate an automatic response to a message.
        
        In a full implementation, this would:
        1. Call the AI's API (OpenAI, Anthropic, etc.)
        2. Pass the message and context
        3. Get a contextually appropriate response
        
        For now, returns a simple acknowledgment.
        """
        msg = msg_info['message']
        msg_type = msg['type']
        
        if msg_type == 'initiation':
            return f"Acknowledged. {self.ai_name} is ready to collaborate on this topic."
        elif msg_type == 'question':
            return f"Received question. {self.ai_name} will analyze and respond with findings."
        elif msg_type == 'task_complete':
            return f"Acknowledged task completion. {self.ai_name} will review the results."
        else:
            return f"Message received by {self.ai_name}. Processing..."
    
    def post_update(self, collaboration_id: str, update: str, message_type: str = 'update'):
        """
        Post an update to a collaboration.
        
        Args:
            collaboration_id: ID of the collaboration
            update: Update message
            message_type: Type of update (update, response, completion, etc.)
        """
        success = self.coordinator.add_message(
            collaboration_id=collaboration_id,
            from_ai=self.ai_name,
            to_ai=None,  # Broadcast
            message=update,
            message_type=message_type
        )
        
        if success:
            print(f"✓ Posted update to collaboration {collaboration_id[:8]}...")
        else:
            print(f"✗ Failed to post update")
    
    def get_collaboration_context(self, collaboration_id: str) -> Dict[str, Any]:
        """
        Get full context for a collaboration.
        
        Args:
            collaboration_id: ID of the collaboration
            
        Returns:
            Collaboration details including all messages
        """
        collaborations = self.coordinator._load_active_collaborations()
        
        if collaboration_id in collaborations:
            return collaborations[collaboration_id]
        
        # Try partial match (first 8 chars)
        for cid, collab in collaborations.items():
            if cid.startswith(collaboration_id):
                return collab
        
        return {}


def main():
    """CLI interface for AI message checking."""
    if len(sys.argv) < 2:
        print("Usage: check_ai_messages.py <ai_name> [command] [args]")
        print()
        print("AI names: claude-cli, chatgpt, copilot, claude-web")
        print()
        print("Commands:")
        print("  check              - Check for pending messages (default)")
        print("  check --auto       - Check and auto-respond to messages")
        print("  post <collab_id> <message> - Post a message to a collaboration")
        print("  context <collab_id> - Get full collaboration context")
        return
    
    ai_name = sys.argv[1]
    repo_root = Path(__file__).parent.parent
    processor = AIMessageProcessor(ai_name, repo_root)
    
    command = sys.argv[2] if len(sys.argv) > 2 else 'check'
    
    if command == 'check':
        auto_respond = '--auto' in sys.argv
        result = processor.check_and_process_messages(auto_respond=auto_respond)
        print(result['summary'])
    
    elif command == 'post':
        if len(sys.argv) < 5:
            print("Usage: check_ai_messages.py <ai_name> post <collab_id> <message>")
            return
        
        collab_id = sys.argv[3]
        message = sys.argv[4]
        processor.post_update(collab_id, message)
    
    elif command == 'context':
        if len(sys.argv) < 4:
            print("Usage: check_ai_messages.py <ai_name> context <collab_id>")
            return
        
        collab_id = sys.argv[3]
        context = processor.get_collaboration_context(collab_id)
        
        if context:
            print(json.dumps(context, indent=2))
        else:
            print(f"Collaboration {collab_id} not found")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == '__main__':
    main()
