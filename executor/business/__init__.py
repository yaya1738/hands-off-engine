"""
Business Knowledge Base
=======================

Complete Earth business knowledge - breadth and depth.

KNOWLEDGE FILES:
----------------
- KNOWLEDGE.md: Complete business reference (20 sections)
- KNOWLEDGE_ADVANCED.md: Deep technical internals (20 sections)

TOPICS COVERED (KNOWLEDGE.md):
-----------------------------
1. Nature of Business - Structures, functions, value chain
2. Economics Fundamentals - Micro/macro, supply/demand
3. Accounting & Financial Reporting - Statements, ratios
4. Corporate Finance - TVM, capital structure, WACC
5. Marketing - 4Ps, segmentation, digital marketing
6. Sales - Process, metrics, CRM
7. Operations Management - Quality, inventory, lean
8. Human Resources - Recruitment, compensation, performance
9. Strategy - PESTEL, Five Forces, competitive strategy
10. Entrepreneurship - Lean startup, funding, metrics
11. Legal & Compliance - Contracts, IP, regulations
12. Leadership & Management - Styles, theories, functions
13. Organizational Behavior - Culture, change, teams
14. Supply Chain Management - Logistics, procurement
15. Business Analytics - BI, statistics, big data
16. Digital Business & E-Commerce - Models, platforms
17. International Business - Entry modes, trade, FX
18. Investment & Valuation - DCF, comparables, portfolio
19. Risk Management - Types, ERM, insurance
20. Business Ethics & Sustainability - CSR, ESG, governance

ADVANCED TOPICS (KNOWLEDGE_ADVANCED.md):
---------------------------------------
1. Microeconomics Deep Dive - Utility, production, markets
2. Macroeconomics Internals - IS-LM, AD-AS, growth
3. Financial Statement Analysis - DuPont, Z-score
4. Valuation Mathematics - DCF, multiples, SOTP
5. Options & Derivatives - Black-Scholes, Greeks
6. Portfolio Theory - MPT, CAPM, factor models
7. Behavioral Economics - Biases, prospect theory
8. Game Theory in Business - Nash, signaling
9. Market Microstructure - Orders, spreads, HFT
10. Corporate Governance Internals - Agency, boards
11. M&A Mechanics - Process, structure, synergies
12. Private Equity & Venture Capital - Fund structure, LBO
13. Tax Strategy - Corporate, international, M&A
14. Negotiation Science - BATNA, tactics, psychology
15. Organizational Design - Structures, span, networks
16. Innovation Management - Types, processes, open
17. Business Model Mechanics - Canvas, patterns
18. Network Effects & Platform Economics - Direct, indirect
19. Pricing Science - Value-based, dynamic, behavioral
20. Decision Theory - Expected utility, Bayesian

KEY CONCEPTS:
-------------
- NPV: Sum of discounted future cash flows
- WACC: Weighted average cost of capital
- ROE: Return on equity (Net Income / Equity)
- EBITDA: Earnings before interest, taxes, depreciation, amortization
- CAC: Customer acquisition cost
- LTV: Customer lifetime value
- Beta: Measure of systematic risk
- Nash Equilibrium: No player can improve unilaterally

USAGE:
------
```python
# Read the knowledge
from executor.business import KNOWLEDGE_PATH, KNOWLEDGE_ADVANCED_PATH

# Or import constants
from executor.business import (
    FINANCIAL_RATIOS,
    VALUATION_METHODS,
    PRICING_STRATEGIES,
)
```
"""

import os

# Knowledge file paths
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), "KNOWLEDGE.md")
KNOWLEDGE_ADVANCED_PATH = os.path.join(os.path.dirname(__file__), "KNOWLEDGE_ADVANCED.md")

# ===========================================
# FINANCIAL RATIOS
# ===========================================

FINANCIAL_RATIOS = {
    "profitability": {
        "gross_margin": "Gross Profit / Revenue",
        "operating_margin": "Operating Income / Revenue",
        "net_margin": "Net Income / Revenue",
        "roe": "Net Income / Shareholders' Equity",
        "roa": "Net Income / Total Assets",
        "roic": "NOPAT / Invested Capital",
    },
    "liquidity": {
        "current_ratio": "Current Assets / Current Liabilities",
        "quick_ratio": "(Current Assets - Inventory) / Current Liabilities",
        "cash_ratio": "Cash / Current Liabilities",
    },
    "leverage": {
        "debt_to_equity": "Total Debt / Shareholders' Equity",
        "debt_to_assets": "Total Debt / Total Assets",
        "interest_coverage": "EBIT / Interest Expense",
    },
    "efficiency": {
        "asset_turnover": "Revenue / Average Total Assets",
        "inventory_turnover": "COGS / Average Inventory",
        "receivables_turnover": "Revenue / Average Accounts Receivable",
        "dso": "(Accounts Receivable / Revenue) × 365",
        "dio": "(Inventory / COGS) × 365",
        "dpo": "(Accounts Payable / COGS) × 365",
    },
}

# ===========================================
# VALUATION METHODS
# ===========================================

VALUATION_METHODS = {
    "dcf": {
        "description": "Discounted Cash Flow",
        "formula": "PV = Σ FCF_t / (1 + WACC)^t + TV / (1 + WACC)^n",
        "best_for": "Companies with predictable cash flows",
    },
    "comparable_companies": {
        "description": "Trading multiples of similar public companies",
        "multiples": ["EV/Revenue", "EV/EBITDA", "P/E", "P/B"],
        "best_for": "Companies with good public comparables",
    },
    "precedent_transactions": {
        "description": "Multiples from similar M&A transactions",
        "note": "Includes control premium",
        "best_for": "M&A valuation",
    },
    "lbo": {
        "description": "Leveraged Buyout analysis",
        "formula": "IRR based on debt-financed acquisition",
        "best_for": "PE acquisition targets",
    },
}

# ===========================================
# PRICING STRATEGIES
# ===========================================

PRICING_STRATEGIES = {
    "cost_plus": {
        "formula": "Price = Cost × (1 + Markup%)",
        "pros": "Simple, covers costs",
        "cons": "Ignores demand and competition",
    },
    "value_based": {
        "formula": "Price = Reference Value + Differentiation Value",
        "pros": "Captures value created",
        "cons": "Requires understanding customer value",
    },
    "competitive": {
        "description": "Price based on competitor prices",
        "pros": "Market-based",
        "cons": "May ignore costs and value",
    },
    "dynamic": {
        "description": "Adjust prices based on demand",
        "applications": ["Airlines", "Hotels", "Ride-sharing"],
        "pros": "Maximize revenue",
    },
    "penetration": {
        "description": "Low price to gain market share",
        "when": "New market entry, network effects",
    },
    "skimming": {
        "description": "High price, lower over time",
        "when": "Innovation, limited competition",
    },
}

# ===========================================
# MARKETING MIX
# ===========================================

MARKETING_MIX = {
    "4ps": {
        "product": "Features, quality, design, brand, packaging",
        "price": "List price, discounts, payment terms",
        "place": "Channels, coverage, locations, inventory",
        "promotion": "Advertising, PR, sales promotion, personal selling",
    },
    "7ps": {
        "people": "Employees, training, customer service",
        "process": "Service delivery, customer journey",
        "physical_evidence": "Environment, tangible cues",
    },
}

# ===========================================
# BUSINESS STRUCTURES
# ===========================================

BUSINESS_STRUCTURES = {
    "sole_proprietorship": {
        "liability": "Unlimited personal",
        "taxation": "Pass-through",
        "formation": "Minimal",
    },
    "partnership": {
        "types": ["General (GP)", "Limited (LP)", "LLP"],
        "liability": "Varies by type",
        "taxation": "Pass-through",
    },
    "c_corporation": {
        "liability": "Limited",
        "taxation": "Double (corporate + dividend)",
        "can_issue_stock": True,
    },
    "s_corporation": {
        "liability": "Limited",
        "taxation": "Pass-through",
        "shareholder_limit": 100,
    },
    "llc": {
        "liability": "Limited",
        "taxation": "Flexible (pass-through default)",
        "management": "Flexible",
    },
}

# ===========================================
# STARTUP METRICS
# ===========================================

STARTUP_METRICS = {
    "cac": {
        "formula": "Total Sales & Marketing / New Customers",
        "good_range": "Depends on LTV ratio",
    },
    "ltv": {
        "formula": "ARPU × Customer Lifespan",
        "alternative": "ARPU / Churn Rate",
    },
    "ltv_cac_ratio": {
        "formula": "LTV / CAC",
        "target": ">= 3:1",
    },
    "mrr": {
        "description": "Monthly Recurring Revenue",
        "formula": "Sum of all monthly subscription revenue",
    },
    "arr": {
        "description": "Annual Recurring Revenue",
        "formula": "MRR × 12",
    },
    "churn_rate": {
        "formula": "Customers Lost / Total Customers",
        "good_range": "< 5% monthly for B2B",
    },
    "nrr": {
        "formula": "(Starting MRR - Churn + Expansion) / Starting MRR",
        "target": "> 100%",
    },
    "burn_rate": {
        "description": "Monthly cash consumption",
    },
    "runway": {
        "formula": "Cash / Burn Rate",
        "result": "Months until out of cash",
    },
}

# ===========================================
# PORTER'S FRAMEWORKS
# ===========================================

PORTER_FIVE_FORCES = {
    "threat_of_new_entrants": {
        "factors": ["Barriers to entry", "Capital requirements", "Switching costs"],
    },
    "bargaining_power_suppliers": {
        "factors": ["Supplier concentration", "Uniqueness", "Switching costs"],
    },
    "bargaining_power_buyers": {
        "factors": ["Buyer concentration", "Price sensitivity", "Alternatives"],
    },
    "threat_of_substitutes": {
        "factors": ["Price-performance", "Switching costs", "Buyer propensity"],
    },
    "industry_rivalry": {
        "factors": ["Number of competitors", "Growth rate", "Exit barriers"],
    },
}

GENERIC_STRATEGIES = {
    "cost_leadership": "Lowest cost producer in industry",
    "differentiation": "Unique offering, premium pricing",
    "focus_cost": "Cost leadership in narrow segment",
    "focus_differentiation": "Differentiation in narrow segment",
}

# ===========================================
# HELPER FUNCTIONS
# ===========================================

def get_knowledge() -> str:
    """Read the main business knowledge document."""
    with open(KNOWLEDGE_PATH, 'r') as f:
        return f.read()


def get_advanced_knowledge() -> str:
    """Read the advanced business knowledge document."""
    with open(KNOWLEDGE_ADVANCED_PATH, 'r') as f:
        return f.read()


def calculate_wacc(
    equity_value: float,
    debt_value: float,
    cost_of_equity: float,
    cost_of_debt: float,
    tax_rate: float
) -> float:
    """
    Calculate Weighted Average Cost of Capital.

    Args:
        equity_value: Market value of equity
        debt_value: Market value of debt
        cost_of_equity: Cost of equity (decimal)
        cost_of_debt: Cost of debt (decimal)
        tax_rate: Corporate tax rate (decimal)

    Returns:
        WACC as decimal
    """
    total_value = equity_value + debt_value
    equity_weight = equity_value / total_value
    debt_weight = debt_value / total_value

    wacc = (equity_weight * cost_of_equity +
            debt_weight * cost_of_debt * (1 - tax_rate))
    return wacc


def calculate_npv(
    cash_flows: list,
    discount_rate: float,
    initial_investment: float = 0
) -> float:
    """
    Calculate Net Present Value.

    Args:
        cash_flows: List of future cash flows
        discount_rate: Discount rate (decimal)
        initial_investment: Initial investment (positive number)

    Returns:
        NPV
    """
    pv_sum = sum(cf / (1 + discount_rate) ** (t + 1)
                 for t, cf in enumerate(cash_flows))
    return pv_sum - initial_investment


def calculate_irr(
    cash_flows: list,
    initial_investment: float,
    tolerance: float = 0.0001
) -> float:
    """
    Calculate Internal Rate of Return using Newton-Raphson method.

    Args:
        cash_flows: List of future cash flows
        initial_investment: Initial investment (positive number)
        tolerance: Convergence tolerance

    Returns:
        IRR as decimal
    """
    rate = 0.1  # Initial guess

    for _ in range(100):  # Max iterations
        npv = -initial_investment + sum(
            cf / (1 + rate) ** (t + 1)
            for t, cf in enumerate(cash_flows)
        )
        dnpv = sum(
            -cf * (t + 1) / (1 + rate) ** (t + 2)
            for t, cf in enumerate(cash_flows)
        )

        if abs(dnpv) < 1e-10:
            break

        new_rate = rate - npv / dnpv

        if abs(new_rate - rate) < tolerance:
            return new_rate

        rate = new_rate

    return rate


def calculate_capm(
    risk_free_rate: float,
    beta: float,
    market_return: float
) -> float:
    """
    Calculate expected return using CAPM.

    Args:
        risk_free_rate: Risk-free rate (decimal)
        beta: Beta of the asset
        market_return: Expected market return (decimal)

    Returns:
        Expected return (decimal)
    """
    return risk_free_rate + beta * (market_return - risk_free_rate)


def calculate_dupont_roe(
    net_income: float,
    revenue: float,
    total_assets: float,
    shareholders_equity: float
) -> dict:
    """
    Calculate ROE using DuPont analysis.

    Args:
        net_income: Net income
        revenue: Total revenue
        total_assets: Total assets
        shareholders_equity: Total shareholders' equity

    Returns:
        Dictionary with components and ROE
    """
    net_margin = net_income / revenue
    asset_turnover = revenue / total_assets
    equity_multiplier = total_assets / shareholders_equity

    roe = net_margin * asset_turnover * equity_multiplier

    return {
        "net_margin": net_margin,
        "asset_turnover": asset_turnover,
        "equity_multiplier": equity_multiplier,
        "roe": roe,
    }


def calculate_ltv_cac_ratio(
    average_revenue_per_user: float,
    customer_lifespan_months: float,
    acquisition_cost: float
) -> dict:
    """
    Calculate LTV:CAC ratio.

    Args:
        average_revenue_per_user: Monthly ARPU
        customer_lifespan_months: Average customer lifespan in months
        acquisition_cost: Cost to acquire one customer

    Returns:
        Dictionary with LTV, CAC, and ratio
    """
    ltv = average_revenue_per_user * customer_lifespan_months
    ratio = ltv / acquisition_cost if acquisition_cost > 0 else float('inf')

    return {
        "ltv": ltv,
        "cac": acquisition_cost,
        "ratio": ratio,
        "healthy": ratio >= 3,
    }


def calculate_runway(
    cash_balance: float,
    monthly_burn: float
) -> dict:
    """
    Calculate startup runway.

    Args:
        cash_balance: Current cash balance
        monthly_burn: Monthly cash burn rate

    Returns:
        Dictionary with runway in months and status
    """
    if monthly_burn <= 0:
        return {"months": float('inf'), "status": "profitable"}

    months = cash_balance / monthly_burn

    if months >= 18:
        status = "healthy"
    elif months >= 12:
        status = "adequate"
    elif months >= 6:
        status = "caution"
    else:
        status = "critical"

    return {
        "months": months,
        "status": status,
    }


# ===========================================
# EXPORTS
# ===========================================

__all__ = [
    # Paths
    "KNOWLEDGE_PATH",
    "KNOWLEDGE_ADVANCED_PATH",

    # Constants
    "FINANCIAL_RATIOS",
    "VALUATION_METHODS",
    "PRICING_STRATEGIES",
    "MARKETING_MIX",
    "BUSINESS_STRUCTURES",
    "STARTUP_METRICS",
    "PORTER_FIVE_FORCES",
    "GENERIC_STRATEGIES",

    # Functions
    "get_knowledge",
    "get_advanced_knowledge",
    "calculate_wacc",
    "calculate_npv",
    "calculate_irr",
    "calculate_capm",
    "calculate_dupont_roe",
    "calculate_ltv_cac_ratio",
    "calculate_runway",
]
