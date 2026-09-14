"""
Arbitrage Audit Integration
===========================

Integrates arbitrage detection with the hands-off-engine audit system.
Logs all arbitrage-related events for compliance, analysis, and debugging.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit.audit_logger import AuditLogger, get_audit_logger
from .types import ArbitrageOpportunity, MatchedEvent, Platform


class ArbitrageAuditLogger:
    """
    Specialized audit logger for arbitrage detection.

    Logs:
    - Opportunity detection events
    - Cross-platform matches
    - Execution attempts and results
    - Risk assessments
    """

    # Event type constants
    EVENT_ARB_SCAN = "arb_scan"
    EVENT_ARB_OPPORTUNITY = "arb_opportunity"
    EVENT_ARB_MATCH = "arb_match"
    EVENT_ARB_EXECUTION = "arb_execution"
    EVENT_ARB_ALERT = "arb_alert"

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize arbitrage audit logger.

        Args:
            session_id: Optional session ID for grouping related events
        """
        self._logger = AuditLogger(component="arbitrage")
        self.session_id = session_id or self._generate_session_id()

    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"arb_{timestamp}"

    def log_scan_start(
        self,
        platforms: List[Platform],
        scan_type: str = "full",
        min_profit_threshold: float = 0.005,
    ) -> None:
        """Log the start of an arbitrage scan"""
        self._logger.log(
            event_type=self.EVENT_ARB_SCAN,
            event_data={
                "action": "scan_start",
                "scan_type": scan_type,
                "platforms": [p.value for p in platforms],
                "min_profit_threshold": min_profit_threshold,
            },
            session_id=self.session_id,
        )

    def log_scan_complete(
        self,
        opportunities_found: int,
        markets_scanned: int,
        matches_found: int,
        duration_seconds: float,
    ) -> None:
        """Log scan completion with summary stats"""
        self._logger.log(
            event_type=self.EVENT_ARB_SCAN,
            event_data={
                "action": "scan_complete",
                "opportunities_found": opportunities_found,
                "markets_scanned": markets_scanned,
                "matches_found": matches_found,
                "duration_seconds": round(duration_seconds, 2),
            },
            session_id=self.session_id,
        )

    def log_opportunity(
        self,
        opportunity: ArbitrageOpportunity,
        triggered_alert: bool = False,
    ) -> None:
        """Log a detected arbitrage opportunity"""
        event_data = {
            "opportunity_id": opportunity.opportunity_id,
            "arb_type": opportunity.arb_type.value,
            "profit_pct_gross": round(opportunity.profit_pct, 4),
            "profit_pct_net": round(opportunity.profit_pct_net, 4),
            "execution_risk": opportunity.execution_risk,
            "risk_factors": opportunity.risk_factors,
            "max_size_usd": opportunity.max_size_usd,
            "legs": opportunity.legs,
            "triggered_alert": triggered_alert,
        }

        # Add matched event info if available
        if opportunity.matched_event:
            event_data["matched_event"] = {
                "event_id": opportunity.matched_event.event_id,
                "question": opportunity.matched_event.canonical_question[:200],
                "match_confidence": opportunity.matched_event.match_confidence,
                "platforms": [m.platform.value for m in opportunity.matched_event.markets],
            }

        self._logger.log(
            event_type=self.EVENT_ARB_OPPORTUNITY,
            event_data=event_data,
            session_id=self.session_id,
        )

    def log_match(
        self,
        matched_event: MatchedEvent,
    ) -> None:
        """Log a cross-platform event match"""
        self._logger.log(
            event_type=self.EVENT_ARB_MATCH,
            event_data={
                "event_id": matched_event.event_id,
                "question": matched_event.canonical_question[:200],
                "match_confidence": matched_event.match_confidence,
                "match_method": matched_event.match_method,
                "category": matched_event.category,
                "platforms": [m.platform.value for m in matched_event.markets],
                "market_prices": {
                    m.platform.value: {
                        "yes": m.yes_price,
                        "no": m.no_price,
                        "spread": m.spread,
                    }
                    for m in matched_event.markets
                },
            },
            session_id=self.session_id,
        )

    def log_execution_attempt(
        self,
        opportunity: ArbitrageOpportunity,
        size_usd: float,
        dry_run: bool = True,
    ) -> None:
        """Log an execution attempt"""
        self._logger.log(
            event_type=self.EVENT_ARB_EXECUTION,
            event_data={
                "action": "attempt",
                "opportunity_id": opportunity.opportunity_id,
                "arb_type": opportunity.arb_type.value,
                "size_usd": size_usd,
                "dry_run": dry_run,
                "legs": opportunity.legs,
            },
            session_id=self.session_id,
        )

    def log_execution_result(
        self,
        opportunity_id: str,
        success: bool,
        executed_legs: List[Dict[str, Any]],
        actual_profit_usd: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """Log execution result"""
        severity = "info" if success else "error"

        self._logger.log(
            event_type=self.EVENT_ARB_EXECUTION,
            event_data={
                "action": "result",
                "opportunity_id": opportunity_id,
                "success": success,
                "executed_legs": executed_legs,
                "actual_profit_usd": actual_profit_usd,
                "error": error,
            },
            severity=severity,
            session_id=self.session_id,
        )

    def log_alert(
        self,
        opportunity: ArbitrageOpportunity,
        alert_channel: str,  # e.g., "telegram", "console", "webhook"
        message: str,
    ) -> None:
        """Log an alert sent to user"""
        self._logger.log(
            event_type=self.EVENT_ARB_ALERT,
            event_data={
                "opportunity_id": opportunity.opportunity_id,
                "profit_pct_net": round(opportunity.profit_pct_net, 4),
                "alert_channel": alert_channel,
                "message_preview": message[:200],
            },
            session_id=self.session_id,
        )


def create_audit_logger(session_id: Optional[str] = None) -> ArbitrageAuditLogger:
    """Factory function to create arbitrage audit logger"""
    return ArbitrageAuditLogger(session_id=session_id)
