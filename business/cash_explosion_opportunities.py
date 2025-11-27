#!/usr/bin/env python3
"""
Cash Explosion Opportunities System
Track and execute high-impact cash generation opportunities
Integrated with emergency financial response
"""
import json
import pathlib
import datetime
import sys
from typing import Dict, Any, List, Optional
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from business.yair_siegel_business_profile import BusinessProfileManager

REPO_ROOT = pathlib.Path(__file__).parent.parent
OPPORTUNITIES_DB = REPO_ROOT / "business/data/cash_opportunities.jsonl"
OPPORTUNITIES_STATE = REPO_ROOT / "business/data/cash_opportunities_state.json"
EXECUTION_LOG = REPO_ROOT / "business/data/opportunity_execution.jsonl"


class CashOpportunity:
    """Represents a cash generation opportunity"""

    def __init__(self, data: Dict[str, Any]):
        self.id = data.get("id", None)
        self.title = data.get("title", "")
        self.description = data.get("description", "")
        self.category = data.get("category", "general")  # trading, gig, contract, sale, investment
        self.potential_revenue = float(data.get("potential_revenue", 0))
        self.time_to_cash_hours = float(data.get("time_to_cash_hours", 24))
        self.effort_hours = float(data.get("effort_hours", 1))
        self.required_capital = float(data.get("required_capital", 0))
        self.confidence = float(data.get("confidence", 0.5))  # 0-1
        self.risk_level = data.get("risk_level", "medium")  # low, medium, high
        self.status = data.get("status", "identified")  # identified, in_progress, completed, failed
        self.created_at = data.get("created_at", datetime.datetime.utcnow().isoformat() + "Z")
        self.priority = data.get("priority", "medium")  # critical, high, medium, low
        self.action_steps = data.get("action_steps", [])
        self.notes = data.get("notes", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "potential_revenue": self.potential_revenue,
            "time_to_cash_hours": self.time_to_cash_hours,
            "effort_hours": self.effort_hours,
            "required_capital": self.required_capital,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "status": self.status,
            "created_at": self.created_at,
            "priority": self.priority,
            "action_steps": self.action_steps,
            "notes": self.notes,
        }

    def expected_value(self) -> float:
        """Calculate expected value (revenue * confidence)"""
        return self.potential_revenue * self.confidence

    def hourly_rate(self) -> float:
        """Calculate expected hourly rate"""
        if self.effort_hours == 0:
            return 0
        return self.expected_value() / self.effort_hours

    def roi(self) -> float:
        """Calculate ROI if capital required"""
        if self.required_capital == 0:
            return float('inf')
        return (self.expected_value() - self.required_capital) / self.required_capital

    def urgency_score(self) -> float:
        """Calculate urgency score for prioritization"""
        # Higher score = more urgent
        score = 0

        # Priority weight
        priority_weights = {"critical": 100, "high": 50, "medium": 25, "low": 10}
        score += priority_weights.get(self.priority, 25)

        # Time to cash (faster = higher score)
        if self.time_to_cash_hours <= 24:
            score += 50
        elif self.time_to_cash_hours <= 72:
            score += 30
        elif self.time_to_cash_hours <= 168:  # 1 week
            score += 10

        # Expected value
        score += min(self.expected_value() / 10, 50)  # Cap at 50

        # Hourly rate
        hourly = self.hourly_rate()
        if hourly > 100:
            score += 30
        elif hourly > 50:
            score += 20
        elif hourly > 25:
            score += 10

        return score


class CashExplosionManager:
    """Manages cash generation opportunities"""

    def __init__(self):
        self.profile_manager = BusinessProfileManager()
        self.opportunities_db = OPPORTUNITIES_DB
        self.opportunities_state = OPPORTUNITIES_STATE
        self.execution_log = EXECUTION_LOG
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure required directories exist"""
        self.opportunities_db.parent.mkdir(parents=True, exist_ok=True)

    def generate_opportunity_id(self) -> str:
        """Generate unique opportunity ID"""
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"OPP-{timestamp}"

    def add_opportunity(self, opportunity: CashOpportunity) -> str:
        """Add new opportunity to database"""
        if not opportunity.id:
            opportunity.id = self.generate_opportunity_id()

        # Append to database
        with open(self.opportunities_db, "a") as f:
            f.write(json.dumps(opportunity.to_dict()) + "\n")

        # Update state
        self._update_state()

        return opportunity.id

    def load_opportunities(self, status_filter: Optional[str] = None) -> List[CashOpportunity]:
        """Load opportunities from database"""
        if not self.opportunities_db.exists():
            return []

        opportunities = []
        with open(self.opportunities_db, "r") as f:
            for line in f:
                data = json.loads(line)
                opp = CashOpportunity(data)

                if status_filter is None or opp.status == status_filter:
                    opportunities.append(opp)

        return opportunities

    def get_active_opportunities(self) -> List[CashOpportunity]:
        """Get all active (not completed/failed) opportunities"""
        all_opps = self.load_opportunities()
        return [opp for opp in all_opps if opp.status in ["identified", "in_progress"]]

    def prioritize_opportunities(self, opportunities: List[CashOpportunity]) -> List[CashOpportunity]:
        """Sort opportunities by urgency score"""
        return sorted(opportunities, key=lambda x: x.urgency_score(), reverse=True)

    def update_opportunity_status(self, opp_id: str, new_status: str, notes: str = ""):
        """Update opportunity status"""
        event = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "opportunity_id": opp_id,
            "new_status": new_status,
            "notes": notes,
        }

        with open(self.execution_log, "a") as f:
            f.write(json.dumps(event) + "\n")

        self._update_state()

    def _update_state(self):
        """Update state file with current stats"""
        opps = self.load_opportunities()

        total_potential = sum(opp.expected_value() for opp in opps if opp.status in ["identified", "in_progress"])
        completed_revenue = sum(opp.potential_revenue for opp in opps if opp.status == "completed")

        state = {
            "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            "total_opportunities": len(opps),
            "active_opportunities": len([o for o in opps if o.status in ["identified", "in_progress"]]),
            "completed_opportunities": len([o for o in opps if o.status == "completed"]),
            "total_potential_revenue": round(total_potential, 2),
            "completed_revenue": round(completed_revenue, 2),
        }

        self.opportunities_state.write_text(json.dumps(state, indent=2))

    def get_emergency_opportunities(self) -> List[CashOpportunity]:
        """Get opportunities suitable for emergency cash generation"""
        opps = self.get_active_opportunities()

        # Filter for emergency criteria:
        # - Fast (< 48 hours to cash)
        # - High confidence (> 0.6)
        # - Decent revenue (> $100)
        emergency_opps = [
            opp for opp in opps
            if opp.time_to_cash_hours <= 48
            and opp.confidence >= 0.6
            and opp.expected_value() >= 100
        ]

        return self.prioritize_opportunities(emergency_opps)

    def generate_execution_plan(self, opportunity: CashOpportunity) -> Dict[str, Any]:
        """Generate execution plan for an opportunity"""
        plan = {
            "opportunity_id": opportunity.id,
            "title": opportunity.title,
            "expected_revenue": opportunity.expected_value(),
            "time_to_cash": f"{opportunity.time_to_cash_hours} hours",
            "effort_required": f"{opportunity.effort_hours} hours",
            "hourly_rate": f"${opportunity.hourly_rate():.2f}/hr",
            "action_steps": opportunity.action_steps,
            "execution_timeline": self._generate_timeline(opportunity),
            "prerequisites": [],
            "risks": [],
        }

        # Add prerequisites
        if opportunity.required_capital > 0:
            plan["prerequisites"].append(f"Capital required: ${opportunity.required_capital}")

        # Add risks based on risk level
        if opportunity.risk_level == "high":
            plan["risks"].append("High risk - proceed with caution")
        elif opportunity.risk_level == "medium":
            plan["risks"].append("Medium risk - validate before committing")

        return plan

    def _generate_timeline(self, opportunity: CashOpportunity) -> List[Dict[str, str]]:
        """Generate execution timeline"""
        now = datetime.datetime.utcnow()

        timeline = [
            {
                "phase": "Start",
                "time": "0 hours",
                "deadline": now.isoformat() + "Z",
                "action": "Begin execution",
            }
        ]

        # Execution phase
        execution_end = now + datetime.timedelta(hours=opportunity.effort_hours)
        timeline.append({
            "phase": "Execution",
            "time": f"0-{opportunity.effort_hours} hours",
            "deadline": execution_end.isoformat() + "Z",
            "action": "Complete work/action steps",
        })

        # Cash phase
        cash_time = now + datetime.timedelta(hours=opportunity.time_to_cash_hours)
        timeline.append({
            "phase": "Cash Received",
            "time": f"{opportunity.time_to_cash_hours} hours",
            "deadline": cash_time.isoformat() + "Z",
            "action": "Receive payment",
        })

        return timeline

    def display_opportunity_dashboard(self):
        """Display comprehensive opportunity dashboard"""
        print("=" * 80)
        print("💰 CASH EXPLOSION OPPORTUNITIES DASHBOARD 💰")
        print("=" * 80)
        print()

        # Load profile for context
        profile = self.profile_manager.generate_current_profile()

        print("CURRENT FINANCIAL CONTEXT:")
        print(f"  Personal Liquid:     ${profile.personal_accounts.total_personal_liquid:,.2f}")
        print(f"  Emergency Mode:      {'🔴 ACTIVE' if self._is_emergency_mode() else 'Inactive'}")
        print()

        # Get active opportunities
        active_opps = self.get_active_opportunities()
        emergency_opps = self.get_emergency_opportunities()

        print(f"ACTIVE OPPORTUNITIES: {len(active_opps)}")
        print(f"EMERGENCY-READY OPPORTUNITIES: {len(emergency_opps)}")
        print()

        if emergency_opps:
            print("🔥 TOP EMERGENCY OPPORTUNITIES (Fast cash < 48hrs):")
            print()
            for i, opp in enumerate(emergency_opps[:5], 1):
                print(f"{i}. {opp.title}")
                print(f"   Expected Revenue: ${opp.expected_value():.2f}")
                print(f"   Time to Cash: {opp.time_to_cash_hours} hours")
                print(f"   Effort: {opp.effort_hours} hours @ ${opp.hourly_rate():.2f}/hr")
                print(f"   Confidence: {opp.confidence*100:.0f}%")
                print(f"   Status: {opp.status}")
                print()
        else:
            print("⚠️  No emergency-ready opportunities identified")
            print("   Add opportunities with: add_opportunity()")
            print()

        # All active opportunities
        if active_opps:
            print(f"ALL ACTIVE OPPORTUNITIES ({len(active_opps)}):")
            print()

            prioritized = self.prioritize_opportunities(active_opps)
            for i, opp in enumerate(prioritized, 1):
                print(f"{i}. [{opp.priority.upper()}] {opp.title}")
                print(f"   ${opp.expected_value():.2f} in {opp.time_to_cash_hours}hrs | {opp.status}")
            print()

        # Total potential
        total_potential = sum(opp.expected_value() for opp in active_opps)
        print(f"TOTAL POTENTIAL REVENUE: ${total_potential:,.2f}")
        print()

        # Stats
        if self.opportunities_state.exists():
            state = json.loads(self.opportunities_state.read_text())
            print("LIFETIME STATS:")
            print(f"  Total Opportunities: {state.get('total_opportunities', 0)}")
            print(f"  Completed: {state.get('completed_opportunities', 0)}")
            print(f"  Total Revenue: ${state.get('completed_revenue', 0):,.2f}")
            print()

        print("=" * 80)

    def _is_emergency_mode(self) -> bool:
        """Check if emergency mode is active"""
        emergency_mode_file = REPO_ROOT / "business/data/emergency_mode.json"
        if emergency_mode_file.exists():
            config = json.loads(emergency_mode_file.read_text())
            return config.get("enabled", False)
        return False


def create_opportunity_interactive():
    """Interactive opportunity creation"""
    print("=" * 80)
    print("💰 ADD NEW CASH OPPORTUNITY 💰")
    print("=" * 80)
    print()

    print("Enter opportunity details:")
    print()

    title = input("Title: ").strip()
    description = input("Description: ").strip()

    print("\nCategory options: trading, gig, contract, sale, investment, other")
    category = input("Category: ").strip() or "other"

    potential_revenue = float(input("Potential Revenue ($): ").strip() or "0")
    time_to_cash = float(input("Time to Cash (hours): ").strip() or "24")
    effort_hours = float(input("Effort Required (hours): ").strip() or "1")
    required_capital = float(input("Capital Required ($): ").strip() or "0")
    confidence = float(input("Confidence (0.0-1.0): ").strip() or "0.5")

    print("\nRisk Level: low, medium, high")
    risk_level = input("Risk Level: ").strip() or "medium"

    print("\nPriority: critical, high, medium, low")
    priority = input("Priority: ").strip() or "medium"

    print("\nAction Steps (one per line, blank line to finish):")
    action_steps = []
    while True:
        step = input("  - ").strip()
        if not step:
            break
        action_steps.append(step)

    notes = input("\nNotes: ").strip()

    # Create opportunity
    opp = CashOpportunity({
        "title": title,
        "description": description,
        "category": category,
        "potential_revenue": potential_revenue,
        "time_to_cash_hours": time_to_cash,
        "effort_hours": effort_hours,
        "required_capital": required_capital,
        "confidence": confidence,
        "risk_level": risk_level,
        "priority": priority,
        "action_steps": action_steps,
        "notes": notes,
    })

    # Preview
    print("\n" + "=" * 80)
    print("OPPORTUNITY PREVIEW:")
    print("=" * 80)
    print(f"Title: {opp.title}")
    print(f"Expected Revenue: ${opp.expected_value():.2f}")
    print(f"Hourly Rate: ${opp.hourly_rate():.2f}/hr")
    print(f"Time to Cash: {opp.time_to_cash_hours} hours")
    print()

    confirm = input("Add this opportunity? (y/n): ").strip().lower()

    if confirm == 'y':
        manager = CashExplosionManager()
        opp_id = manager.add_opportunity(opp)
        print(f"\n✅ Opportunity added: {opp_id}")
        return opp
    else:
        print("\n❌ Cancelled")
        return None


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Cash Explosion Opportunities Manager")
    parser.add_argument("--add", action="store_true", help="Add new opportunity interactively")
    parser.add_argument("--dashboard", action="store_true", help="Show opportunities dashboard")
    parser.add_argument("--list", action="store_true", help="List all active opportunities")
    parser.add_argument("--emergency", action="store_true", help="Show emergency-ready opportunities")
    args = parser.parse_args()

    manager = CashExplosionManager()

    if args.add:
        create_opportunity_interactive()
    elif args.dashboard:
        manager.display_opportunity_dashboard()
    elif args.list:
        opps = manager.get_active_opportunities()
        prioritized = manager.prioritize_opportunities(opps)
        for i, opp in enumerate(prioritized, 1):
            print(f"{i}. {opp.title} - ${opp.expected_value():.2f}")
    elif args.emergency:
        opps = manager.get_emergency_opportunities()
        print(f"Emergency-Ready Opportunities: {len(opps)}")
        for i, opp in enumerate(opps, 1):
            print(f"{i}. {opp.title} - ${opp.expected_value():.2f} in {opp.time_to_cash_hours}hrs")
    else:
        # Default: show dashboard
        manager.display_opportunity_dashboard()


if __name__ == "__main__":
    main()
