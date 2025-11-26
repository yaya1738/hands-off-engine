"""
Position Manager for Hands-Off Engine

Manages individual positions including:
- Adding and removing positions
- Updating position prices
- Tracking position history
- Exporting position data
"""

import json
import sys
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


@dataclass
class Position:
    """Represents a single trading position"""
    position_id: str
    market_id: str
    market_name: str
    side: str  # "YES" or "NO"
    entry_price: float
    current_price: float
    quantity: float  # Number of shares
    entry_amount: float  # Dollar amount invested
    current_value: float  # Current dollar value
    opened_at: str  # ISO 8601 timestamp
    mode: str  # "DRYRUN" or "LIVE"
    status: str = "open"  # "open" or "closed"
    closed_at: Optional[str] = None
    exit_price: Optional[float] = None
    realized_pnl: Optional[float] = None
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L for open positions"""
        if self.status == "closed":
            return 0.0
        return self.current_value - self.entry_amount
    
    @property
    def unrealized_pnl_pct(self) -> float:
        """Calculate unrealized P&L percentage"""
        if self.status == "closed" or self.entry_amount == 0:
            return 0.0
        return (self.unrealized_pnl / self.entry_amount) * 100


class PositionManager:
    """
    Manages all positions (both DRYRUN and LIVE).
    Provides atomic operations with audit logging.
    """
    
    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize position manager.
        
        Args:
            state_dir: Directory for state files (defaults to ./state/portfolio)
        """
        if state_dir is None:
            repo_root = Path(__file__).parent.parent
            state_dir = repo_root / "state" / "portfolio"
        
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.positions_file = self.state_dir / "positions.json"
        self.history_file = self.state_dir / "history.jsonl"
        
        self.audit = get_audit_logger(component="position_manager")
        self._positions: Dict[str, Position] = {}
        
        # Load existing positions
        self._load_positions()
    
    def _load_positions(self):
        """Load positions from state file"""
        if self.positions_file.exists():
            try:
                with open(self.positions_file, 'r') as f:
                    data = json.load(f)
                    for pos_data in data.get('positions', []):
                        pos = Position(**pos_data)
                        self._positions[pos.position_id] = pos
            except Exception as e:
                import sys
                print(f"[PositionManager] Warning: Failed to load positions: {e}", file=sys.stderr)
    
    def _save_positions(self):
        """Atomically save positions to state file"""
        positions_data = {
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'positions': [asdict(pos) for pos in self._positions.values()]
        }
        
        # Atomic write: write to temp file, then rename
        tmp_file = self.positions_file.with_suffix('.json.tmp')
        try:
            with open(tmp_file, 'w') as f:
                json.dump(positions_data, f, indent=2)
            tmp_file.replace(self.positions_file)
        except Exception as e:
            import sys
            print(f"[PositionManager] Error: Failed to save positions: {e}", file=sys.stderr)
            if tmp_file.exists():
                tmp_file.unlink()
            raise
    
    def _log_to_history(self, event_type: str, position: Position, metadata: Optional[Dict[str, Any]] = None):
        """Log position event to history file"""
        event = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event_type': event_type,
            'position_id': position.position_id,
            'market_id': position.market_id,
            'position_data': asdict(position)
        }
        if metadata:
            event['metadata'] = metadata
        
        try:
            with open(self.history_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            import sys
            print(f"[PositionManager] Warning: Failed to log to history: {e}", file=sys.stderr)
    
    def add_position(self, market_id: str, market_name: str, side: str,
                    entry_price: float, quantity: float, mode: str = "DRYRUN") -> Position:
        """
        Add a new position.
        
        Args:
            market_id: Market identifier
            market_name: Human-readable market name
            side: "YES" or "NO"
            entry_price: Entry price per share
            quantity: Number of shares
            mode: "DRYRUN" or "LIVE"
            
        Returns:
            Position object
        """
        position_id = f"{market_id}_{side}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        entry_amount = entry_price * quantity
        
        position = Position(
            position_id=position_id,
            market_id=market_id,
            market_name=market_name,
            side=side,
            entry_price=entry_price,
            current_price=entry_price,  # Initialize with entry price
            quantity=quantity,
            entry_amount=entry_amount,
            current_value=entry_amount,  # Initialize with entry amount
            opened_at=datetime.now(timezone.utc).isoformat(),
            mode=mode,
            status="open"
        )
        
        self._positions[position_id] = position
        self._save_positions()
        self._log_to_history("position_opened", position)
        
        # Audit log
        self.audit.log_action(
            action_type="add_position",
            action_data={
                "position_id": position_id,
                "market_id": market_id,
                "market_name": market_name,
                "side": side,
                "entry_price": entry_price,
                "quantity": quantity,
                "entry_amount": entry_amount,
                "mode": mode
            },
            result="success"
        )
        
        return position
    
    def update_position_price(self, position_id: str, current_price: float) -> Optional[Position]:
        """
        Update the current price of a position.
        
        Args:
            position_id: Position identifier
            current_price: New current price
            
        Returns:
            Updated Position object or None if not found
        """
        if position_id not in self._positions:
            return None
        
        position = self._positions[position_id]
        old_price = position.current_price
        old_value = position.current_value
        
        position.current_price = current_price
        position.current_value = current_price * position.quantity
        
        self._save_positions()
        
        # Audit log
        self.audit.log_action(
            action_type="update_position_price",
            action_data={
                "position_id": position_id,
                "old_price": old_price,
                "new_price": current_price,
                "old_value": old_value,
                "new_value": position.current_value,
                "unrealized_pnl": position.unrealized_pnl
            },
            result="success"
        )
        
        return position
    
    def close_position(self, position_id: str, exit_price: float) -> Optional[Position]:
        """
        Close a position and calculate realized P&L.
        
        Args:
            position_id: Position identifier
            exit_price: Exit price per share
            
        Returns:
            Closed Position object or None if not found
        """
        if position_id not in self._positions:
            return None
        
        position = self._positions[position_id]
        
        if position.status == "closed":
            return position  # Already closed
        
        exit_value = exit_price * position.quantity
        realized_pnl = exit_value - position.entry_amount
        
        position.status = "closed"
        position.closed_at = datetime.now(timezone.utc).isoformat()
        position.exit_price = exit_price
        position.current_price = exit_price
        position.current_value = exit_value
        position.realized_pnl = realized_pnl
        
        self._save_positions()
        self._log_to_history("position_closed", position, {
            "realized_pnl": realized_pnl,
            "realized_pnl_pct": (realized_pnl / position.entry_amount * 100) if position.entry_amount > 0 else 0
        })
        
        # Audit log
        self.audit.log_action(
            action_type="close_position",
            action_data={
                "position_id": position_id,
                "market_id": position.market_id,
                "exit_price": exit_price,
                "realized_pnl": realized_pnl,
                "entry_amount": position.entry_amount,
                "exit_value": exit_value
            },
            result="success"
        )
        
        return position
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """Get a position by ID"""
        return self._positions.get(position_id)
    
    def get_all_positions(self, status: Optional[str] = None, mode: Optional[str] = None) -> List[Position]:
        """
        Get all positions with optional filtering.
        
        Args:
            status: Filter by status ("open" or "closed")
            mode: Filter by mode ("DRYRUN" or "LIVE")
            
        Returns:
            List of Position objects
        """
        positions = list(self._positions.values())
        
        if status:
            positions = [p for p in positions if p.status == status]
        
        if mode:
            positions = [p for p in positions if p.mode == mode]
        
        return positions
    
    def get_positions_by_market(self, market_id: str) -> List[Position]:
        """Get all positions for a specific market"""
        return [p for p in self._positions.values() if p.market_id == market_id]
    
    def export_to_json(self, output_file: Path) -> None:
        """Export all positions to JSON file"""
        data = {
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'positions': [asdict(pos) for pos in self._positions.values()]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_to_csv(self, output_file: Path) -> None:
        """Export all positions to CSV file"""
        import csv
        
        if not self._positions:
            return
        
        # Get all field names from the first position
        fieldnames = list(asdict(next(iter(self._positions.values()))).keys())
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for position in self._positions.values():
                writer.writerow(asdict(position))


# Example usage
if __name__ == "__main__":
    # Create position manager
    pm = PositionManager()
    
    # Add a test position
    pos = pm.add_position(
        market_id="test_market_1",
        market_name="Test Market Question?",
        side="YES",
        entry_price=0.65,
        quantity=100.0,
        mode="DRYRUN"
    )
    
    print(f"Added position: {pos.position_id}")
    print(f"Entry amount: ${pos.entry_amount:.2f}")
    print(f"Unrealized P&L: ${pos.unrealized_pnl:.2f} ({pos.unrealized_pnl_pct:.2f}%)")
    
    # Update price
    pm.update_position_price(pos.position_id, 0.75)
    updated_pos = pm.get_position(pos.position_id)
    print(f"\nAfter price update to $0.75:")
    print(f"Current value: ${updated_pos.current_value:.2f}")
    print(f"Unrealized P&L: ${updated_pos.unrealized_pnl:.2f} ({updated_pos.unrealized_pnl_pct:.2f}%)")
    
    # Close position
    closed_pos = pm.close_position(pos.position_id, 0.80)
    print(f"\nClosed position at $0.80:")
    print(f"Realized P&L: ${closed_pos.realized_pnl:.2f}")
    
    print(f"\nState files saved to: {pm.state_dir}")
