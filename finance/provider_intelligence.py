#!/usr/bin/env python3
"""
PROVIDER INTELLIGENCE - Complete Provider Knowledge Base
=========================================================

This module contains EVERYTHING we know about each provider:
- Full terms & conditions
- All pricing structures
- Every possible action
- Rate limits & quotas
- Billing cycles
- Hidden costs
- Atomic action components

PRINCIPLE: The system knows EVERYTHING before acting.

Every action is decomposed into atomic components:
  complex_action = atom1 + atom2 + atom3 + ...
  cost(complex_action) = cost(atom1) + cost(atom2) + cost(atom3) + ...

Serving: Yair Siegel
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent.parent
FINANCE_DIR = BASE_DIR / 'finance'

MASTER = "Yair Siegel"


# =============================================================================
# ATOMIC COMPONENTS - Smallest billable units
# =============================================================================

@dataclass
class AtomicComponent:
    """Smallest possible billable unit."""
    atom_id: str
    name: str
    provider: str
    cost_per_unit: float
    unit: str
    billing_trigger: str  # What triggers this cost
    minimum_charge: float = 0.0
    maximum_charge: Optional[float] = None
    free_tier_limit: Optional[float] = None
    rate_limit: Optional[str] = None
    notes: str = ""


# Complete atomic component registry
ATOMIC_COMPONENTS: Dict[str, AtomicComponent] = {

    # =========================================================================
    # DIGITALOCEAN ATOMS
    # =========================================================================

    "do_vcpu_hour": AtomicComponent(
        atom_id="do_vcpu_hour",
        name="vCPU Hour",
        provider="digitalocean",
        cost_per_unit=0.00744,  # Base rate per vCPU hour
        unit="vcpu_hour",
        billing_trigger="Droplet exists (running or stopped)",
        notes="Base compute unit - scales with droplet size"
    ),

    "do_ram_gb_hour": AtomicComponent(
        atom_id="do_ram_gb_hour",
        name="RAM GB Hour",
        provider="digitalocean",
        cost_per_unit=0.00744,  # Bundled with vCPU
        unit="gb_hour",
        billing_trigger="Droplet exists",
        notes="Bundled with vCPU pricing"
    ),

    "do_disk_gb_hour": AtomicComponent(
        atom_id="do_disk_gb_hour",
        name="Disk GB Hour",
        provider="digitalocean",
        cost_per_unit=0.0001,  # ~$0.10/GB/month
        unit="gb_hour",
        billing_trigger="Droplet exists",
        notes="SSD storage included in droplet"
    ),

    "do_bandwidth_gb": AtomicComponent(
        atom_id="do_bandwidth_gb",
        name="Bandwidth GB",
        provider="digitalocean",
        cost_per_unit=0.01,
        unit="gb",
        billing_trigger="Transfer exceeds free allowance",
        free_tier_limit=1000,  # 1TB free per droplet
        notes="$0.01/GB after free tier"
    ),

    "do_snapshot_gb_month": AtomicComponent(
        atom_id="do_snapshot_gb_month",
        name="Snapshot Storage",
        provider="digitalocean",
        cost_per_unit=0.05,
        unit="gb_month",
        billing_trigger="Snapshot exists",
        notes="$0.05/GB/month for snapshots"
    ),

    "do_floating_ip_hour": AtomicComponent(
        atom_id="do_floating_ip_hour",
        name="Floating IP",
        provider="digitalocean",
        cost_per_unit=0.00595,
        unit="hour",
        billing_trigger="Floating IP not attached to droplet",
        notes="FREE when attached, charged when floating"
    ),

    "do_volume_gb_month": AtomicComponent(
        atom_id="do_volume_gb_month",
        name="Block Storage Volume",
        provider="digitalocean",
        cost_per_unit=0.10,
        unit="gb_month",
        billing_trigger="Volume exists",
        notes="$0.10/GB/month for block storage"
    ),

    "do_api_call": AtomicComponent(
        atom_id="do_api_call",
        name="API Call",
        provider="digitalocean",
        cost_per_unit=0.0,
        unit="call",
        billing_trigger="Never (free)",
        rate_limit="5000 requests/hour",
        notes="FREE but rate limited"
    ),

    # =========================================================================
    # OPENAI ATOMS
    # =========================================================================

    "openai_gpt4_turbo_input_token": AtomicComponent(
        atom_id="openai_gpt4_turbo_input_token",
        name="GPT-4 Turbo Input Token",
        provider="openai",
        cost_per_unit=0.00001,  # $0.01/1K
        unit="token",
        billing_trigger="API call with input",
        notes="Input tokens for GPT-4 Turbo"
    ),

    "openai_gpt4_turbo_output_token": AtomicComponent(
        atom_id="openai_gpt4_turbo_output_token",
        name="GPT-4 Turbo Output Token",
        provider="openai",
        cost_per_unit=0.00003,  # $0.03/1K
        unit="token",
        billing_trigger="API call generates output",
        notes="Output tokens cost 3x input"
    ),

    "openai_gpt4o_input_token": AtomicComponent(
        atom_id="openai_gpt4o_input_token",
        name="GPT-4o Input Token",
        provider="openai",
        cost_per_unit=0.000005,  # $0.005/1K
        unit="token",
        billing_trigger="API call with input",
        notes="Cheaper than GPT-4 Turbo"
    ),

    "openai_gpt4o_output_token": AtomicComponent(
        atom_id="openai_gpt4o_output_token",
        name="GPT-4o Output Token",
        provider="openai",
        cost_per_unit=0.000015,  # $0.015/1K
        unit="token",
        billing_trigger="API call generates output",
        notes="Output tokens cost 3x input"
    ),

    "openai_gpt35_input_token": AtomicComponent(
        atom_id="openai_gpt35_input_token",
        name="GPT-3.5 Input Token",
        provider="openai",
        cost_per_unit=0.0000005,  # $0.0005/1K
        unit="token",
        billing_trigger="API call with input",
        notes="Cheapest OpenAI model"
    ),

    "openai_gpt35_output_token": AtomicComponent(
        atom_id="openai_gpt35_output_token",
        name="GPT-3.5 Output Token",
        provider="openai",
        cost_per_unit=0.0000015,  # $0.0015/1K
        unit="token",
        billing_trigger="API call generates output",
        notes="Output tokens cost 3x input"
    ),

    "openai_embedding_token": AtomicComponent(
        atom_id="openai_embedding_token",
        name="Embedding Token",
        provider="openai",
        cost_per_unit=0.00000013,  # $0.00013/1K
        unit="token",
        billing_trigger="Embedding API call",
        notes="text-embedding-3-small"
    ),

    # =========================================================================
    # ANTHROPIC ATOMS
    # =========================================================================

    "anthropic_opus_input_token": AtomicComponent(
        atom_id="anthropic_opus_input_token",
        name="Claude Opus Input Token",
        provider="anthropic",
        cost_per_unit=0.000015,  # $0.015/1K
        unit="token",
        billing_trigger="API call with input",
        notes="Highest quality model"
    ),

    "anthropic_opus_output_token": AtomicComponent(
        atom_id="anthropic_opus_output_token",
        name="Claude Opus Output Token",
        provider="anthropic",
        cost_per_unit=0.000075,  # $0.075/1K
        unit="token",
        billing_trigger="API call generates output",
        notes="Output costs 5x input"
    ),

    "anthropic_sonnet_input_token": AtomicComponent(
        atom_id="anthropic_sonnet_input_token",
        name="Claude Sonnet Input Token",
        provider="anthropic",
        cost_per_unit=0.000003,  # $0.003/1K
        unit="token",
        billing_trigger="API call with input",
        notes="Balanced quality/cost"
    ),

    "anthropic_sonnet_output_token": AtomicComponent(
        atom_id="anthropic_sonnet_output_token",
        name="Claude Sonnet Output Token",
        provider="anthropic",
        cost_per_unit=0.000015,  # $0.015/1K
        unit="token",
        billing_trigger="API call generates output",
        notes="Output costs 5x input"
    ),

    "anthropic_haiku_input_token": AtomicComponent(
        atom_id="anthropic_haiku_input_token",
        name="Claude Haiku Input Token",
        provider="anthropic",
        cost_per_unit=0.00000025,  # $0.00025/1K
        unit="token",
        billing_trigger="API call with input",
        notes="Cheapest Anthropic model"
    ),

    "anthropic_haiku_output_token": AtomicComponent(
        atom_id="anthropic_haiku_output_token",
        name="Claude Haiku Output Token",
        provider="anthropic",
        cost_per_unit=0.00000125,  # $0.00125/1K
        unit="token",
        billing_trigger="API call generates output",
        notes="Output costs 5x input"
    ),

    "anthropic_claude_code_month": AtomicComponent(
        atom_id="anthropic_claude_code_month",
        name="Claude Code Pro Monthly",
        provider="anthropic",
        cost_per_unit=100.0,
        unit="month",
        billing_trigger="Subscription active",
        notes="Flat monthly fee"
    ),

    # =========================================================================
    # FREE PROVIDER ATOMS (Rate Limited)
    # =========================================================================

    "groq_request": AtomicComponent(
        atom_id="groq_request",
        name="Groq API Request",
        provider="groq",
        cost_per_unit=0.0,
        unit="request",
        billing_trigger="Never (free tier)",
        rate_limit="30 RPM, 14400 RPD",
        free_tier_limit=14400,  # requests per day
        notes="FREE - Use first!"
    ),

    "groq_token": AtomicComponent(
        atom_id="groq_token",
        name="Groq Token",
        provider="groq",
        cost_per_unit=0.0,
        unit="token",
        billing_trigger="Never (free tier)",
        free_tier_limit=500000,  # per day
        notes="FREE - 500K tokens/day"
    ),

    "google_gemini_request": AtomicComponent(
        atom_id="google_gemini_request",
        name="Gemini API Request",
        provider="google_ai",
        cost_per_unit=0.0,
        unit="request",
        billing_trigger="Never (free tier)",
        rate_limit="60 RPM",
        notes="FREE - Use second!"
    ),

    "google_gemini_token": AtomicComponent(
        atom_id="google_gemini_token",
        name="Gemini Token",
        provider="google_ai",
        cost_per_unit=0.0,
        unit="token",
        billing_trigger="Never (free tier)",
        free_tier_limit=1000000,  # per day
        notes="FREE - 1M tokens/day"
    ),

    # =========================================================================
    # DATA PROVIDER ATOMS (All Free)
    # =========================================================================

    "coingecko_request": AtomicComponent(
        atom_id="coingecko_request",
        name="CoinGecko API Request",
        provider="coingecko",
        cost_per_unit=0.0,
        unit="request",
        billing_trigger="Never (free tier)",
        rate_limit="10-30 calls/minute",
        notes="FREE - Crypto prices"
    ),

    "cryptocompare_request": AtomicComponent(
        atom_id="cryptocompare_request",
        name="CryptoCompare API Request",
        provider="cryptocompare",
        cost_per_unit=0.0,
        unit="request",
        billing_trigger="Never (free tier)",
        rate_limit="100K calls/month",
        free_tier_limit=100000,
        notes="FREE - News data"
    ),

    "alternative_me_request": AtomicComponent(
        atom_id="alternative_me_request",
        name="Alternative.me API Request",
        provider="alternative_me",
        cost_per_unit=0.0,
        unit="request",
        billing_trigger="Never (free tier)",
        notes="FREE - Fear & Greed"
    ),

    # =========================================================================
    # POLYMARKET ATOMS
    # =========================================================================

    "polymarket_gas": AtomicComponent(
        atom_id="polymarket_gas",
        name="Polygon Gas Fee",
        provider="polymarket",
        cost_per_unit=0.001,  # ~$0.001 average
        unit="transaction",
        billing_trigger="Any on-chain transaction",
        notes="Variable - usually ~$0.001"
    ),

    "polymarket_usdc_lock": AtomicComponent(
        atom_id="polymarket_usdc_lock",
        name="USDC Position Lock",
        provider="polymarket",
        cost_per_unit=0.0,  # Opportunity cost only
        unit="usdc",
        billing_trigger="Position opened",
        notes="Capital locked until resolution - OPPORTUNITY COST"
    ),

    # =========================================================================
    # GITHUB ATOMS
    # =========================================================================

    "github_actions_minute": AtomicComponent(
        atom_id="github_actions_minute",
        name="GitHub Actions Minute",
        provider="github",
        cost_per_unit=0.0,
        unit="minute",
        billing_trigger="After free tier (2000 min/month)",
        free_tier_limit=2000,
        notes="FREE tier covers us"
    ),

    "github_storage_gb": AtomicComponent(
        atom_id="github_storage_gb",
        name="GitHub Storage",
        provider="github",
        cost_per_unit=0.0,
        unit="gb",
        billing_trigger="Never for our usage",
        notes="FREE for public repos"
    ),
}


# =============================================================================
# ACTION DECOMPOSITION - Break actions into atoms
# =============================================================================

@dataclass
class ActionDecomposition:
    """Breaks an action into atomic components."""
    action_id: str
    name: str
    description: str
    atoms: List[Dict[str, Any]]  # [{atom_id, quantity_formula, notes}]
    prerequisites: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)


# Action decomposition registry
ACTION_DECOMPOSITIONS: Dict[str, ActionDecomposition] = {

    # =========================================================================
    # DIGITALOCEAN ACTIONS
    # =========================================================================

    "create_droplet_1vcpu_1gb": ActionDecomposition(
        action_id="create_droplet_1vcpu_1gb",
        name="Create 1vCPU/1GB Droplet",
        description="Create smallest droplet - $5/month",
        atoms=[
            {"atom_id": "do_vcpu_hour", "quantity": "1 * hours", "notes": "1 vCPU"},
            {"atom_id": "do_ram_gb_hour", "quantity": "1 * hours", "notes": "1 GB RAM"},
            {"atom_id": "do_disk_gb_hour", "quantity": "25 * hours", "notes": "25 GB disk"},
            {"atom_id": "do_api_call", "quantity": "1", "notes": "Create API call"},
        ]
    ),

    "create_droplet_4vcpu_8gb": ActionDecomposition(
        action_id="create_droplet_4vcpu_8gb",
        name="Create 4vCPU/8GB Droplet (pm-helper size)",
        description="Create medium droplet - $40/month",
        atoms=[
            {"atom_id": "do_vcpu_hour", "quantity": "4 * hours", "notes": "4 vCPUs"},
            {"atom_id": "do_ram_gb_hour", "quantity": "8 * hours", "notes": "8 GB RAM"},
            {"atom_id": "do_disk_gb_hour", "quantity": "160 * hours", "notes": "160 GB disk"},
            {"atom_id": "do_api_call", "quantity": "1", "notes": "Create API call"},
        ]
    ),

    "create_droplet_8vcpu_16gb_amd": ActionDecomposition(
        action_id="create_droplet_8vcpu_16gb_amd",
        name="Create 8vCPU/16GB AMD Droplet",
        description="Create large droplet - $96/month - SCALING ENGINE DEFAULT",
        atoms=[
            {"atom_id": "do_vcpu_hour", "quantity": "8 * hours * 1.2", "notes": "8 AMD vCPUs (1.2x premium)"},
            {"atom_id": "do_ram_gb_hour", "quantity": "16 * hours", "notes": "16 GB RAM"},
            {"atom_id": "do_disk_gb_hour", "quantity": "320 * hours", "notes": "320 GB disk"},
            {"atom_id": "do_api_call", "quantity": "1", "notes": "Create API call"},
        ],
        side_effects=["potential_bandwidth_overage"]
    ),

    "destroy_droplet": ActionDecomposition(
        action_id="destroy_droplet",
        name="Destroy Droplet",
        description="ONLY way to stop droplet billing!",
        atoms=[
            {"atom_id": "do_api_call", "quantity": "1", "notes": "Destroy API call - FREE"},
        ]
    ),

    "create_snapshot": ActionDecomposition(
        action_id="create_snapshot",
        name="Create Droplet Snapshot",
        description="Backup droplet - costs $0.05/GB/month ongoing",
        atoms=[
            {"atom_id": "do_snapshot_gb_month", "quantity": "disk_size_gb * months", "notes": "Ongoing storage cost"},
            {"atom_id": "do_api_call", "quantity": "1", "notes": "Snapshot API call"},
        ]
    ),

    # =========================================================================
    # AI INFERENCE ACTIONS
    # =========================================================================

    "openai_gpt4_turbo_call": ActionDecomposition(
        action_id="openai_gpt4_turbo_call",
        name="GPT-4 Turbo API Call",
        description="High quality inference - EXPENSIVE",
        atoms=[
            {"atom_id": "openai_gpt4_turbo_input_token", "quantity": "input_tokens", "notes": "Input cost"},
            {"atom_id": "openai_gpt4_turbo_output_token", "quantity": "output_tokens", "notes": "Output cost (3x input)"},
        ],
        prerequisites=["openai_credits_available"]
    ),

    "openai_gpt4o_call": ActionDecomposition(
        action_id="openai_gpt4o_call",
        name="GPT-4o API Call",
        description="Balanced quality/cost",
        atoms=[
            {"atom_id": "openai_gpt4o_input_token", "quantity": "input_tokens", "notes": "Input cost"},
            {"atom_id": "openai_gpt4o_output_token", "quantity": "output_tokens", "notes": "Output cost (3x input)"},
        ],
        prerequisites=["openai_credits_available"]
    ),

    "anthropic_claude_sonnet_call": ActionDecomposition(
        action_id="anthropic_claude_sonnet_call",
        name="Claude Sonnet API Call",
        description="Balanced Anthropic model",
        atoms=[
            {"atom_id": "anthropic_sonnet_input_token", "quantity": "input_tokens", "notes": "Input cost"},
            {"atom_id": "anthropic_sonnet_output_token", "quantity": "output_tokens", "notes": "Output cost (5x input)"},
        ]
    ),

    "groq_llama_call": ActionDecomposition(
        action_id="groq_llama_call",
        name="Groq Llama 70B Call",
        description="FREE AI inference - USE FIRST",
        atoms=[
            {"atom_id": "groq_request", "quantity": "1", "notes": "FREE request"},
            {"atom_id": "groq_token", "quantity": "total_tokens", "notes": "FREE tokens"},
        ]
    ),

    "google_gemini_call": ActionDecomposition(
        action_id="google_gemini_call",
        name="Gemini Flash Call",
        description="FREE AI inference - USE SECOND",
        atoms=[
            {"atom_id": "google_gemini_request", "quantity": "1", "notes": "FREE request"},
            {"atom_id": "google_gemini_token", "quantity": "total_tokens", "notes": "FREE tokens"},
        ]
    ),

    # =========================================================================
    # DATA FETCH ACTIONS (All Free)
    # =========================================================================

    "fetch_crypto_prices": ActionDecomposition(
        action_id="fetch_crypto_prices",
        name="Fetch Crypto Prices",
        description="Get BTC/ETH prices from CoinGecko - FREE",
        atoms=[
            {"atom_id": "coingecko_request", "quantity": "1", "notes": "FREE"},
        ]
    ),

    "fetch_fear_greed": ActionDecomposition(
        action_id="fetch_fear_greed",
        name="Fetch Fear & Greed Index",
        description="Get market sentiment - FREE",
        atoms=[
            {"atom_id": "alternative_me_request", "quantity": "1", "notes": "FREE"},
        ]
    ),

    "fetch_crypto_news": ActionDecomposition(
        action_id="fetch_crypto_news",
        name="Fetch Crypto News",
        description="Get news headlines - FREE",
        atoms=[
            {"atom_id": "cryptocompare_request", "quantity": "1", "notes": "FREE"},
        ]
    ),

    # =========================================================================
    # TRADING ACTIONS
    # =========================================================================

    "polymarket_buy": ActionDecomposition(
        action_id="polymarket_buy",
        name="Polymarket Buy Order",
        description="Buy shares on Polymarket",
        atoms=[
            {"atom_id": "polymarket_gas", "quantity": "1", "notes": "Transaction gas ~$0.001"},
            {"atom_id": "polymarket_usdc_lock", "quantity": "trade_amount", "notes": "USDC locked in position"},
        ],
        prerequisites=["usdc_balance >= trade_amount"]
    ),

    "polymarket_sell": ActionDecomposition(
        action_id="polymarket_sell",
        name="Polymarket Sell Order",
        description="Sell shares on Polymarket",
        atoms=[
            {"atom_id": "polymarket_gas", "quantity": "1", "notes": "Transaction gas ~$0.001"},
        ],
        prerequisites=["position_exists"]
    ),

    # =========================================================================
    # COMPOUND ACTIONS
    # =========================================================================

    "web_agent_full_refresh": ActionDecomposition(
        action_id="web_agent_full_refresh",
        name="Web Agent Full Refresh",
        description="Fetch all market data - FREE",
        atoms=[
            {"atom_id": "coingecko_request", "quantity": "1", "notes": "Prices"},
            {"atom_id": "alternative_me_request", "quantity": "1", "notes": "Fear & Greed"},
            {"atom_id": "cryptocompare_request", "quantity": "1", "notes": "News"},
        ]
    ),

    "dense_ai_analysis": ActionDecomposition(
        action_id="dense_ai_analysis",
        name="Dense AI Full Analysis",
        description="Multi-source analysis with AI fallback",
        atoms=[
            # Data fetching (free)
            {"atom_id": "coingecko_request", "quantity": "1", "notes": "Market data"},
            {"atom_id": "alternative_me_request", "quantity": "1", "notes": "Sentiment"},
            # AI inference (tries free first)
            {"atom_id": "groq_request", "quantity": "1", "notes": "Try Groq first (FREE)"},
            {"atom_id": "groq_token", "quantity": "estimated_tokens", "notes": "FREE tokens"},
            # Fallback costs (only if free fails)
            # {"atom_id": "openai_gpt4_turbo_input_token", "quantity": "fallback_input", "notes": "Fallback"},
        ]
    ),

    "scale_cluster_add_node": ActionDecomposition(
        action_id="scale_cluster_add_node",
        name="Scale Cluster - Add Node",
        description="Add compute node to cluster - $96/month ongoing!",
        atoms=[
            {"atom_id": "do_vcpu_hour", "quantity": "8 * hours * 1.2", "notes": "8 AMD vCPUs ongoing"},
            {"atom_id": "do_ram_gb_hour", "quantity": "16 * hours", "notes": "16 GB RAM ongoing"},
            {"atom_id": "do_disk_gb_hour", "quantity": "320 * hours", "notes": "320 GB disk ongoing"},
            {"atom_id": "do_api_call", "quantity": "1", "notes": "Create call"},
        ],
        side_effects=["ongoing_hourly_cost_$0.14"]
    ),
}


# =============================================================================
# COST FORMULA ENGINE
# =============================================================================

class CostFormulaEngine:
    """
    Calculate exact costs by decomposing actions into atoms.

    Usage:
        engine = CostFormulaEngine()

        # Simple estimate
        cost = engine.calculate("create_droplet_8vcpu_16gb_amd", hours=24)

        # Detailed breakdown
        breakdown = engine.get_breakdown("dense_ai_analysis", tokens=5000)
    """

    def __init__(self):
        self.atoms = ATOMIC_COMPONENTS
        self.decompositions = ACTION_DECOMPOSITIONS

    def get_atom_cost(self, atom_id: str, quantity: float = 1) -> float:
        """Get cost for atomic component."""
        atom = self.atoms.get(atom_id)
        if not atom:
            return 0.0
        return atom.cost_per_unit * quantity

    def calculate(
        self,
        action_id: str,
        **kwargs
    ) -> float:
        """
        Calculate total cost for an action.

        Args:
            action_id: Action to calculate
            **kwargs: Variables for formula (hours, tokens, etc.)

        Returns:
            Total cost in USD
        """
        decomp = self.decompositions.get(action_id)
        if not decomp:
            return 0.0

        total = 0.0
        hours = kwargs.get('hours', 1)
        tokens = kwargs.get('tokens', 1000)
        input_tokens = kwargs.get('input_tokens', tokens * 0.3)
        output_tokens = kwargs.get('output_tokens', tokens * 0.7)

        for atom_spec in decomp.atoms:
            atom_id = atom_spec['atom_id']
            quantity_formula = atom_spec['quantity']

            # Parse quantity formula
            if isinstance(quantity_formula, str):
                # Evaluate formula with context
                try:
                    quantity = eval(quantity_formula, {
                        'hours': hours,
                        'tokens': tokens,
                        'total_tokens': tokens,
                        'input_tokens': input_tokens,
                        'output_tokens': output_tokens,
                        'estimated_tokens': tokens,
                        'disk_size_gb': kwargs.get('disk_size_gb', 160),
                        'months': kwargs.get('months', 1),
                        'trade_amount': kwargs.get('trade_amount', 10),
                    })
                except:
                    quantity = 1
            else:
                quantity = float(quantity_formula)

            atom_cost = self.get_atom_cost(atom_id, quantity)
            total += atom_cost

        return round(total, 6)

    def get_breakdown(
        self,
        action_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get detailed cost breakdown for an action.

        Returns breakdown by atom with quantities and costs.
        """
        decomp = self.decompositions.get(action_id)
        if not decomp:
            return {"error": f"Unknown action: {action_id}"}

        hours = kwargs.get('hours', 1)
        tokens = kwargs.get('tokens', 1000)
        input_tokens = kwargs.get('input_tokens', tokens * 0.3)
        output_tokens = kwargs.get('output_tokens', tokens * 0.7)

        breakdown = {
            "action_id": action_id,
            "name": decomp.name,
            "description": decomp.description,
            "parameters": kwargs,
            "atoms": [],
            "total_cost": 0.0,
            "prerequisites": decomp.prerequisites,
            "side_effects": decomp.side_effects,
        }

        for atom_spec in decomp.atoms:
            atom_id = atom_spec['atom_id']
            atom = self.atoms.get(atom_id)
            quantity_formula = atom_spec['quantity']

            # Parse quantity
            if isinstance(quantity_formula, str):
                try:
                    quantity = eval(quantity_formula, {
                        'hours': hours,
                        'tokens': tokens,
                        'total_tokens': tokens,
                        'input_tokens': input_tokens,
                        'output_tokens': output_tokens,
                        'estimated_tokens': tokens,
                        'disk_size_gb': kwargs.get('disk_size_gb', 160),
                        'months': kwargs.get('months', 1),
                        'trade_amount': kwargs.get('trade_amount', 10),
                    })
                except:
                    quantity = 1
            else:
                quantity = float(quantity_formula)

            atom_cost = self.get_atom_cost(atom_id, quantity)

            breakdown["atoms"].append({
                "atom_id": atom_id,
                "name": atom.name if atom else atom_id,
                "quantity": round(quantity, 2),
                "unit": atom.unit if atom else "unit",
                "cost_per_unit": atom.cost_per_unit if atom else 0,
                "total_cost": round(atom_cost, 6),
                "notes": atom_spec.get('notes', ''),
                "is_free": atom.cost_per_unit == 0 if atom else False,
            })

            breakdown["total_cost"] += atom_cost

        breakdown["total_cost"] = round(breakdown["total_cost"], 6)
        return breakdown

    def compare_options(self, actions: List[str], **kwargs) -> List[Dict]:
        """Compare costs of multiple action options."""
        results = []
        for action_id in actions:
            breakdown = self.get_breakdown(action_id, **kwargs)
            results.append({
                "action": action_id,
                "cost": breakdown.get("total_cost", 0),
                "is_free": breakdown.get("total_cost", 0) == 0
            })
        return sorted(results, key=lambda x: x["cost"])

    def get_cheapest_ai_option(self, tokens: int = 1000) -> str:
        """Find cheapest AI option for given token count."""
        ai_actions = [
            "groq_llama_call",       # Free
            "google_gemini_call",    # Free
            "anthropic_claude_sonnet_call",
            "openai_gpt4o_call",
            "openai_gpt4_turbo_call",
        ]
        comparison = self.compare_options(ai_actions, tokens=tokens)
        return comparison[0]["action"]

    def print_breakdown(self, action_id: str, **kwargs):
        """Print formatted cost breakdown."""
        breakdown = self.get_breakdown(action_id, **kwargs)

        if "error" in breakdown:
            print(f"Error: {breakdown['error']}")
            return

        print(f"\n{'='*60}")
        print(f"COST BREAKDOWN: {breakdown['name']}")
        print(f"{'='*60}")
        print(f"Description: {breakdown['description']}")
        print(f"Parameters: {breakdown['parameters']}")
        print(f"\nATOMIC COMPONENTS:")
        print("-" * 60)

        for atom in breakdown["atoms"]:
            status = "FREE" if atom["is_free"] else f"${atom['total_cost']:.6f}"
            print(f"  {atom['name']}")
            print(f"    Quantity: {atom['quantity']} {atom['unit']}")
            print(f"    Cost: {status}")
            if atom['notes']:
                print(f"    Notes: {atom['notes']}")

        print("-" * 60)
        print(f"TOTAL COST: ${breakdown['total_cost']:.6f}")

        if breakdown["prerequisites"]:
            print(f"\nPREREQUISITES: {breakdown['prerequisites']}")
        if breakdown["side_effects"]:
            print(f"SIDE EFFECTS: {breakdown['side_effects']}")

        print(f"{'='*60}")


# Global instance
_engine: Optional[CostFormulaEngine] = None


def get_engine() -> CostFormulaEngine:
    """Get global engine instance."""
    global _engine
    if _engine is None:
        _engine = CostFormulaEngine()
    return _engine


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Provider Intelligence & Cost Formula Engine")
    parser.add_argument("command", choices=["atoms", "actions", "breakdown", "compare", "cheapest-ai"])
    parser.add_argument("--action", help="Action ID")
    parser.add_argument("--hours", type=float, default=1, help="Duration in hours")
    parser.add_argument("--tokens", type=int, default=1000, help="Token count for AI")
    parser.add_argument("--provider", help="Filter by provider")

    args = parser.parse_args()
    engine = get_engine()

    if args.command == "atoms":
        print(f"\n{'='*60}")
        print(f"ATOMIC COMPONENTS ({len(ATOMIC_COMPONENTS)} total)")
        print(f"{'='*60}")

        by_provider = {}
        for atom_id, atom in ATOMIC_COMPONENTS.items():
            if args.provider and atom.provider != args.provider:
                continue
            if atom.provider not in by_provider:
                by_provider[atom.provider] = []
            by_provider[atom.provider].append(atom)

        for provider, atoms in sorted(by_provider.items()):
            print(f"\n{provider.upper()}")
            print("-" * 40)
            for atom in atoms:
                cost_str = f"${atom.cost_per_unit:.6f}/{atom.unit}"
                if atom.cost_per_unit == 0:
                    cost_str = f"FREE (limit: {atom.free_tier_limit or 'unlimited'})"
                print(f"  {atom.atom_id}: {cost_str}")

    elif args.command == "actions":
        print(f"\n{'='*60}")
        print(f"ACTION DECOMPOSITIONS ({len(ACTION_DECOMPOSITIONS)} total)")
        print(f"{'='*60}")

        for action_id, decomp in ACTION_DECOMPOSITIONS.items():
            print(f"\n{action_id}")
            print(f"  {decomp.description}")
            print(f"  Atoms: {len(decomp.atoms)}")

    elif args.command == "breakdown":
        if args.action:
            engine.print_breakdown(args.action, hours=args.hours, tokens=args.tokens)
        else:
            print("--action required")

    elif args.command == "compare":
        ai_actions = [
            "groq_llama_call",
            "google_gemini_call",
            "anthropic_claude_sonnet_call",
            "openai_gpt4o_call",
        ]
        print(f"\nAI Cost Comparison ({args.tokens} tokens):")
        comparison = engine.compare_options(ai_actions, tokens=args.tokens)
        for item in comparison:
            status = "FREE" if item["is_free"] else f"${item['cost']:.6f}"
            print(f"  {item['action']}: {status}")

    elif args.command == "cheapest-ai":
        cheapest = engine.get_cheapest_ai_option(args.tokens)
        print(f"Cheapest AI for {args.tokens} tokens: {cheapest}")


if __name__ == "__main__":
    main()
