#!/usr/bin/env python3
"""
⛽ FUEL SYSTEM - Complete Fuel Management for Power Plant
Serving: Yair Siegel

Like the real world has oil, gas, coal, solar, wind, nuclear...
Our system has multiple fuel sources that can power the plant.

FUEL TYPES:
- USDC: Direct capital (like oil - primary, liquid)
- Crypto Airdrops: Free tokens (like finding oil deposits)
- Bounties/Grants: Earned fuel (like mining operations)
- API Credits: Computational fuel (like natural gas)
- Consulting Income: Service fuel (like hydroelectric)
- Position Resolutions: Extracted fuel (like refining crude)
- Staking Rewards: Passive fuel (like solar/wind)

FUEL OPERATIONS:
- Detection: Find new fuel sources
- Extraction: Get the fuel
- Processing: Convert raw → usable
- Storage: Hold in fuel tank
- Prediction: Forecast future availability
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"
FUEL_STATE = STATE_DIR / "fuel_system.json"
FUEL_LOG = STATE_DIR / "fuel_operations.jsonl"


class FuelType(Enum):
    """Types of fuel available to the system."""
    USDC = "usdc"                    # Direct capital - primary fuel
    AIRDROP = "airdrop"              # Crypto airdrops - free fuel
    BOUNTY = "bounty"                # Bug bounties, grants
    API_CREDITS = "api_credits"      # OpenAI, Anthropic credits
    CONSULTING = "consulting"        # Service income
    POSITION = "position"            # Pending trading positions
    STAKING = "staking"              # Staking rewards
    REFERRAL = "referral"            # Referral bonuses


@dataclass
class FuelSource:
    """A source of fuel."""
    name: str
    fuel_type: FuelType
    status: str  # "active", "pending", "depleted", "detected"

    # Quantity
    raw_amount: float = 0.0          # Unprocessed amount
    refined_amount: float = 0.0      # Ready-to-use amount
    extraction_rate: float = 0.0     # Units per day

    # Timing
    detected_at: Optional[str] = None
    available_at: Optional[str] = None
    depletes_at: Optional[str] = None

    # Metadata
    source_url: Optional[str] = None
    confidence: float = 0.0          # 0-1 confidence in extraction
    notes: str = ""


@dataclass
class FuelDeposit:
    """A detected but not yet extracted fuel deposit."""
    deposit_id: str
    fuel_type: FuelType
    estimated_amount: float
    location: str  # URL, address, or identifier
    extraction_difficulty: str  # "easy", "medium", "hard"
    confidence: float
    detected_at: str
    expires_at: Optional[str] = None


class FuelDetector:
    """
    Detects new fuel sources - like geological surveys for oil.
    Scans for airdrops, bounties, grants, and other opportunities.
    """

    def __init__(self):
        self.detected_deposits: List[FuelDeposit] = []

    def scan_airdrops(self) -> List[FuelDeposit]:
        """Scan for crypto airdrops."""
        deposits = []

        # Known airdrop sources to monitor
        airdrop_sources = [
            {"name": "Layer2 Airdrops", "url": "https://l2beat.com", "likelihood": 0.3},
            {"name": "DeFi Protocol Airdrops", "url": "various", "likelihood": 0.2},
            {"name": "NFT Holder Airdrops", "url": "various", "likelihood": 0.1},
        ]

        # Check wallet for potential eligibility
        # This would query blockchain for eligible addresses

        return deposits

    def scan_bounties(self) -> List[FuelDeposit]:
        """Scan for bug bounties and grants."""
        deposits = []

        bounty_sources = [
            {
                "name": "GitHub Sponsors",
                "type": "recurring",
                "estimated": 50.0,
                "difficulty": "medium",
                "url": "https://github.com/sponsors"
            },
            {
                "name": "Immunefi Bug Bounties",
                "type": "one-time",
                "estimated": 500.0,
                "difficulty": "hard",
                "url": "https://immunefi.com"
            },
            {
                "name": "Gitcoin Grants",
                "type": "one-time",
                "estimated": 100.0,
                "difficulty": "medium",
                "url": "https://gitcoin.co"
            },
            {
                "name": "Protocol Grants",
                "type": "one-time",
                "estimated": 1000.0,
                "difficulty": "hard",
                "url": "various"
            },
        ]

        for source in bounty_sources:
            deposit = FuelDeposit(
                deposit_id=f"bounty_{source['name'].lower().replace(' ', '_')}",
                fuel_type=FuelType.BOUNTY,
                estimated_amount=source["estimated"],
                location=source["url"],
                extraction_difficulty=source["difficulty"],
                confidence=0.3 if source["difficulty"] == "hard" else 0.5,
                detected_at=datetime.now(timezone.utc).isoformat(),
            )
            deposits.append(deposit)

        return deposits

    def scan_consulting(self) -> List[FuelDeposit]:
        """Scan for consulting opportunities."""
        deposits = []

        # Check platforms for opportunities
        platforms = [
            {"name": "Upwork AI Projects", "avg_value": 500, "difficulty": "medium"},
            {"name": "Fiverr Gigs", "avg_value": 100, "difficulty": "easy"},
            {"name": "Direct Outreach", "avg_value": 1000, "difficulty": "hard"},
        ]

        for platform in platforms:
            deposit = FuelDeposit(
                deposit_id=f"consulting_{platform['name'].lower().replace(' ', '_')}",
                fuel_type=FuelType.CONSULTING,
                estimated_amount=platform["avg_value"],
                location=platform["name"],
                extraction_difficulty=platform["difficulty"],
                confidence=0.2,  # Cold outreach has low confidence
                detected_at=datetime.now(timezone.utc).isoformat(),
            )
            deposits.append(deposit)

        return deposits

    def scan_positions(self) -> List[FuelDeposit]:
        """Scan for pending position resolutions."""
        deposits = []

        # Check trading positions
        try:
            fin_file = STATE_DIR / "financial_state.json"
            if fin_file.exists():
                data = json.loads(fin_file.read_text())
                positions = data.get("positions", [])

                for pos in positions:
                    deposit = FuelDeposit(
                        deposit_id=f"position_{pos.get('id', 'unknown')}",
                        fuel_type=FuelType.POSITION,
                        estimated_amount=pos.get("value", 0),
                        location="Polymarket",
                        extraction_difficulty="easy",  # Just wait for resolution
                        confidence=0.8,  # High confidence - just timing unknown
                        detected_at=datetime.now(timezone.utc).isoformat(),
                        expires_at=pos.get("resolution_date"),
                    )
                    deposits.append(deposit)
        except:
            pass

        return deposits

    def full_scan(self) -> List[FuelDeposit]:
        """Run full fuel detection scan."""
        all_deposits = []

        all_deposits.extend(self.scan_bounties())
        all_deposits.extend(self.scan_consulting())
        all_deposits.extend(self.scan_positions())
        # all_deposits.extend(self.scan_airdrops())  # Requires blockchain queries

        self.detected_deposits = all_deposits
        return all_deposits


class FuelExtractor:
    """
    Extracts fuel from detected deposits.
    Different extraction methods for different fuel types.
    """

    def extract(self, deposit: FuelDeposit) -> Dict:
        """Extract fuel from a deposit."""
        result = {
            "deposit_id": deposit.deposit_id,
            "fuel_type": deposit.fuel_type.value,
            "attempted": True,
            "success": False,
            "extracted_amount": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if deposit.fuel_type == FuelType.POSITION:
            # Position extraction = waiting for resolution
            result["method"] = "wait_for_resolution"
            result["message"] = "Position will auto-extract on resolution"
            result["success"] = True
            result["extracted_amount"] = 0  # Pending

        elif deposit.fuel_type == FuelType.BOUNTY:
            # Bounty extraction = apply and complete work
            result["method"] = "apply_and_complete"
            result["message"] = f"Apply at {deposit.location}"
            result["action_required"] = "human_action"

        elif deposit.fuel_type == FuelType.CONSULTING:
            # Consulting extraction = outreach and delivery
            result["method"] = "outreach_and_deliver"
            result["message"] = "Requires client acquisition"
            result["action_required"] = "human_action"

        elif deposit.fuel_type == FuelType.AIRDROP:
            # Airdrop extraction = claim tokens
            result["method"] = "claim_tokens"
            result["message"] = "Check eligibility and claim"

        return result


class FuelRefinery:
    """
    Processes raw fuel into usable form.
    - Converts tokens to USDC
    - Processes payments
    - Settles positions
    """

    def __init__(self):
        self.processing_queue: List[Dict] = []

    def refine(self, raw_fuel: Dict) -> Dict:
        """Refine raw fuel into usable USDC."""
        result = {
            "input": raw_fuel,
            "output_type": "USDC",
            "output_amount": 0.0,
            "efficiency": 1.0,  # Processing fee losses
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        fuel_type = raw_fuel.get("fuel_type")
        amount = raw_fuel.get("amount", 0)

        if fuel_type == FuelType.USDC.value:
            # Already refined
            result["output_amount"] = amount
            result["efficiency"] = 1.0

        elif fuel_type == FuelType.POSITION.value:
            # Position profit - already in USDC
            result["output_amount"] = amount
            result["efficiency"] = 1.0

        elif fuel_type in [FuelType.AIRDROP.value, FuelType.STAKING.value]:
            # Need to swap tokens to USDC
            # Assume 95% efficiency (5% slippage/fees)
            result["output_amount"] = amount * 0.95
            result["efficiency"] = 0.95
            result["method"] = "token_swap"

        elif fuel_type in [FuelType.BOUNTY.value, FuelType.CONSULTING.value]:
            # Direct payment - may have platform fees
            result["output_amount"] = amount * 0.90  # 10% platform fee
            result["efficiency"] = 0.90

        return result


class FuelPredictor:
    """
    Predicts future fuel availability.
    Forecasts when deposits will become extractable.
    """

    def predict_availability(self, deposits: List[FuelDeposit]) -> Dict:
        """Predict when fuel will be available."""
        predictions = {
            "immediate": 0.0,      # Available now
            "within_7_days": 0.0,
            "within_30_days": 0.0,
            "within_90_days": 0.0,
            "uncertain": 0.0,
            "breakdown": [],
        }

        now = datetime.now(timezone.utc)

        for deposit in deposits:
            amount = deposit.estimated_amount * deposit.confidence

            if deposit.expires_at:
                try:
                    exp = datetime.fromisoformat(deposit.expires_at.replace('Z', '+00:00'))
                    days_until = (exp - now).days

                    if days_until <= 0:
                        predictions["immediate"] += amount
                    elif days_until <= 7:
                        predictions["within_7_days"] += amount
                    elif days_until <= 30:
                        predictions["within_30_days"] += amount
                    elif days_until <= 90:
                        predictions["within_90_days"] += amount
                    else:
                        predictions["uncertain"] += amount

                    predictions["breakdown"].append({
                        "deposit": deposit.deposit_id,
                        "amount": amount,
                        "days_until": days_until,
                    })
                except:
                    predictions["uncertain"] += amount
            else:
                # No expiry - uncertain timing
                predictions["uncertain"] += amount

        predictions["total_predicted"] = sum([
            predictions["immediate"],
            predictions["within_7_days"],
            predictions["within_30_days"],
            predictions["within_90_days"],
        ])

        return predictions


class CapitalTracker:
    """
    Complete fuel management system.
    Integrates detection, extraction, processing, and prediction.
    """

    def __init__(self):
        self.detector = FuelDetector()
        self.extractor = FuelExtractor()
        self.refinery = FuelRefinery()
        self.predictor = FuelPredictor()
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if FUEL_STATE.exists():
            try:
                return json.loads(FUEL_STATE.read_text())
            except:
                pass
        return {
            "created": datetime.now(timezone.utc).isoformat(),
            "detected_deposits": [],
            "extracted_fuel": [],
            "refined_fuel": 0.0,
            "total_processed": 0.0,
        }

    def _save_state(self):
        self.state["updated"] = datetime.now(timezone.utc).isoformat()
        FUEL_STATE.write_text(json.dumps(self.state, indent=2, default=str))

    def _log_operation(self, operation: Dict):
        operation["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(FUEL_LOG, "a") as f:
            f.write(json.dumps(operation, default=str) + "\n")

    def survey(self) -> Dict:
        """
        Run full fuel survey - detect all available sources.
        Like a geological survey for oil.
        """
        deposits = self.detector.full_scan()

        # Store detected deposits
        self.state["detected_deposits"] = [asdict(d) for d in deposits]
        self._save_state()

        # Get predictions
        predictions = self.predictor.predict_availability(deposits)

        result = {
            "deposits_found": len(deposits),
            "deposits": [asdict(d) for d in deposits],
            "predictions": predictions,
            "total_estimated": sum(d.estimated_amount for d in deposits),
            "total_confidence_weighted": sum(d.estimated_amount * d.confidence for d in deposits),
        }

        self._log_operation({"type": "survey", "result": result})

        return result

    def get_fuel_status(self) -> Dict:
        """Get current fuel status across all sources."""

        # Current liquid fuel (in tank)
        try:
            fin_file = STATE_DIR / "financial_state.json"
            if fin_file.exists():
                fin = json.loads(fin_file.read_text())
                liquid = fin.get("balance", 0)
                pending = fin.get("positions_value", 0)
            else:
                liquid = 0
                pending = 0
        except:
            liquid = 0
            pending = 0

        # Detected deposits
        deposits = self.state.get("detected_deposits", [])

        status = {
            "liquid_fuel": liquid,  # Available now
            "pending_fuel": pending,  # From positions
            "detected_deposits": len(deposits),
            "total_detected": sum(d.get("estimated_amount", 0) for d in deposits),
            "by_type": {},
        }

        # Group by fuel type
        for d in deposits:
            ft = d.get("fuel_type", "unknown")
            if ft not in status["by_type"]:
                status["by_type"][ft] = {"count": 0, "total": 0}
            status["by_type"][ft]["count"] += 1
            status["by_type"][ft]["total"] += d.get("estimated_amount", 0)

        return status

    def display(self):
        """Display fuel system status."""
        status = self.get_fuel_status()

        print("\n⛽ FUEL SYSTEM STATUS")
        print("=" * 60)

        # Current fuel
        print(f"\n💧 LIQUID FUEL (Ready to Use)")
        print(f"   USDC Balance: ${status['liquid_fuel']:.2f}")

        print(f"\n📦 PENDING FUEL (Extracting)")
        print(f"   Position Resolutions: ${status['pending_fuel']:.2f}")

        # Detected deposits
        print(f"\n🔍 DETECTED DEPOSITS ({status['detected_deposits']} found)")
        for fuel_type, info in status.get("by_type", {}).items():
            print(f"   {fuel_type}: {info['count']} sources, ${info['total']:.2f} estimated")

        print(f"\n📊 TOTALS")
        print(f"   Total Detected: ${status['total_detected']:.2f}")
        print(f"   Total Available: ${status['liquid_fuel'] + status['pending_fuel']:.2f}")

        # Predictions
        deposits = [FuelDeposit(**d) for d in self.state.get("detected_deposits", [])]
        if deposits:
            predictions = self.predictor.predict_availability(deposits)
            print(f"\n🔮 FUEL PREDICTIONS")
            print(f"   Immediate: ${predictions['immediate']:.2f}")
            print(f"   Within 7 days: ${predictions['within_7_days']:.2f}")
            print(f"   Within 30 days: ${predictions['within_30_days']:.2f}")
            print(f"   Uncertain: ${predictions['uncertain']:.2f}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="⛽ Fuel System")
    parser.add_argument("command", choices=["status", "survey", "predict"], nargs="?", default="status")
    args = parser.parse_args()

    system = CapitalTracker()

    if args.command == "status":
        system.display()
    elif args.command == "survey":
        print("🔍 Running fuel survey...")
        result = system.survey()
        print(f"Found {result['deposits_found']} fuel deposits")
        print(f"Total estimated: ${result['total_estimated']:.2f}")
        print(f"Confidence-weighted: ${result['total_confidence_weighted']:.2f}")
        system.display()
    elif args.command == "predict":
        deposits = [FuelDeposit(**d) for d in system.state.get("detected_deposits", [])]
        predictions = system.predictor.predict_availability(deposits)
        print("\n🔮 FUEL PREDICTIONS")
        print(f"   Immediate: ${predictions['immediate']:.2f}")
        print(f"   Within 7 days: ${predictions['within_7_days']:.2f}")
        print(f"   Within 30 days: ${predictions['within_30_days']:.2f}")
        print(f"   Within 90 days: ${predictions['within_90_days']:.2f}")
        print(f"   Total predicted: ${predictions['total_predicted']:.2f}")


if __name__ == "__main__":
    main()
