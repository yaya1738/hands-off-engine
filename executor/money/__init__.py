"""
Money & Finance Knowledge Base
==============================

Complete Earth money and finance knowledge - breadth and depth.

KNOWLEDGE FILES:
----------------
- KNOWLEDGE.md: Complete money reference (20 sections)
- KNOWLEDGE_ADVANCED.md: Deep technical internals (20 sections)

TOPICS COVERED (KNOWLEDGE.md):
-----------------------------
1. Nature of Money - Functions, types, properties
2. History of Money - Barter to digital currencies
3. Monetary Systems - Commodity, fiat, mixed
4. Central Banking - Functions, major banks, tools
5. Commercial Banking - Functions, risks, regulation
6. Money Supply & Creation - Aggregates, multiplier, QE
7. Interest Rates - Types, yield curve, determinants
8. Inflation & Deflation - Causes, effects, targeting
9. Foreign Exchange - Market, rates, trading
10. Payment Systems - Types, infrastructure
11. Personal Finance - Budgeting, emergency fund
12. Wealth Building - Compound interest, accounts
13. Debt & Credit - Types, management
14. Investing Fundamentals - Asset classes, risk/return
15. Cryptocurrencies - Bitcoin, Ethereum, DeFi
16. Gold & Precious Metals - Investment approaches
17. Real Estate - Investing, financing
18. Taxes - Types, planning, accounts
19. Financial Planning - Life stages, insurance, estate
20. Psychology of Money - Biases, habits

ADVANCED TOPICS (KNOWLEDGE_ADVANCED.md):
---------------------------------------
1. Monetary Theory Deep Dive - Quantity theory, money creation
2. Central Bank Operations - OMO, discount window, reserves
3. Interest Rate Models - Vasicek, CIR, Nelson-Siegel
4. Yield Curve Analysis - Construction, shapes, duration
5. Foreign Exchange Mathematics - PPP, IRP, options
6. Inflation Dynamics - Phillips curve, expectations
7. Banking & Credit Analysis - Basel, credit risk, liquidity
8. Derivatives Pricing - Greeks, exotics, rates
9. Portfolio Mathematics - MPT, factors, risk measures
10. Fixed Income Analytics - Duration, credit, MBS
11. Behavioral Finance Mathematics - Prospect theory, limits to arbitrage
12. Market Microstructure - Bid-ask models, price impact
13. Cryptocurrency Mathematics - Mining, DeFi, token economics
14. Real Estate Finance - Valuation, mortgages, REITs
15. Private Equity Mathematics - LBO, VC, fund economics
16. Insurance Mathematics - Life, P&C, RBC
17. Commodity Markets - Futures, energy, agricultural
18. Financial Econometrics - Time series, volatility, events
19. Financial Regulation - Basel, market rules, systemic risk
20. Quantitative Trading - Backtesting, stat arb, execution

KEY CONCEPTS:
-------------
- NPV: Sum of discounted future cash flows
- IRR: Rate that makes NPV = 0
- Duration: Price sensitivity to yield changes
- VaR: Value at Risk (worst loss at confidence level)
- Sharpe Ratio: Return per unit of risk
- WACC: Weighted average cost of capital
- Black-Scholes: Option pricing formula
- CAPM: Expected return = Rf + β(Rm - Rf)

USAGE:
------
```python
# Read the knowledge
from executor.money import KNOWLEDGE_PATH, KNOWLEDGE_ADVANCED_PATH

# Or import constants
from executor.money import (
    INTEREST_RATE_TYPES,
    INFLATION_TYPES,
    ASSET_CLASSES,
    RISK_METRICS,
)

# Use helper functions
from executor.money import (
    calculate_compound_interest,
    calculate_loan_payment,
    calculate_npv,
    calculate_irr,
)
```
"""

import os
from typing import List, Optional
import math

# Knowledge file paths
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), "KNOWLEDGE.md")
KNOWLEDGE_ADVANCED_PATH = os.path.join(os.path.dirname(__file__), "KNOWLEDGE_ADVANCED.md")

# ===========================================
# MONEY SUPPLY AGGREGATES
# ===========================================

MONEY_SUPPLY = {
    "M0": {
        "description": "Monetary base / High-powered money",
        "components": ["Currency in circulation", "Bank reserves"],
    },
    "M1": {
        "description": "Narrow money",
        "components": ["Currency", "Demand deposits", "Checking accounts", "Traveler's checks"],
    },
    "M2": {
        "description": "Broad money",
        "components": ["M1", "Savings deposits", "Small time deposits", "Money market funds"],
    },
    "M3": {
        "description": "Broadest measure (discontinued in US)",
        "components": ["M2", "Large time deposits", "Institutional money funds", "Repos"],
    },
}

# ===========================================
# INTEREST RATE TYPES
# ===========================================

INTEREST_RATE_TYPES = {
    "nominal": {
        "description": "Stated rate without inflation adjustment",
        "formula": "Rate as quoted",
    },
    "real": {
        "description": "Inflation-adjusted rate",
        "formula": "(1 + nominal) / (1 + inflation) - 1",
        "approximation": "nominal - inflation",
    },
    "effective": {
        "description": "Rate accounting for compounding",
        "formula": "(1 + r/n)^n - 1",
    },
    "risk_free": {
        "description": "Theoretical return with zero risk",
        "proxy": "T-bill rate or government bond yield",
    },
    "prime": {
        "description": "Rate banks charge best customers",
        "typically": "Fed funds rate + 3%",
    },
    "discount": {
        "description": "Rate Fed charges banks for short-term loans",
        "relation": "Usually above Fed funds target",
    },
}

# ===========================================
# INFLATION TYPES
# ===========================================

INFLATION_TYPES = {
    "demand_pull": {
        "cause": "Too much money chasing too few goods",
        "characteristic": "Economic expansion",
    },
    "cost_push": {
        "cause": "Rising production costs",
        "sources": ["Wages", "Raw materials", "Energy"],
    },
    "built_in": {
        "cause": "Wage-price spiral",
        "mechanism": "Expectations become self-fulfilling",
    },
    "hyperinflation": {
        "definition": ">50% monthly inflation",
        "historical": ["Weimar Germany", "Zimbabwe", "Venezuela"],
    },
    "deflation": {
        "definition": "Sustained price decreases",
        "risks": ["Debt burden increases", "Delayed spending", "Economic contraction"],
    },
    "stagflation": {
        "definition": "High inflation + High unemployment",
        "challenge": "Policy dilemma",
    },
}

# ===========================================
# ASSET CLASSES
# ===========================================

ASSET_CLASSES = {
    "equities": {
        "description": "Ownership in companies",
        "subtypes": ["Large cap", "Mid cap", "Small cap", "International", "Emerging"],
        "risk": "High",
        "return_expectation": "8-10% long-term",
    },
    "fixed_income": {
        "description": "Debt instruments",
        "subtypes": ["Government", "Corporate", "Municipal", "High yield"],
        "risk": "Low to medium",
        "return_expectation": "3-6%",
    },
    "cash_equivalents": {
        "description": "Highly liquid, low-risk",
        "subtypes": ["Money market", "T-bills", "CDs"],
        "risk": "Very low",
        "return_expectation": "0-3%",
    },
    "real_estate": {
        "description": "Property investments",
        "subtypes": ["Residential", "Commercial", "REITs"],
        "risk": "Medium",
        "return_expectation": "4-8%",
    },
    "commodities": {
        "description": "Physical goods",
        "subtypes": ["Energy", "Metals", "Agriculture"],
        "risk": "High",
        "return_expectation": "Variable",
    },
    "alternatives": {
        "description": "Non-traditional investments",
        "subtypes": ["Private equity", "Hedge funds", "Venture capital", "Crypto"],
        "risk": "Very high",
        "return_expectation": "Variable, potentially high",
    },
}

# ===========================================
# RISK METRICS
# ===========================================

RISK_METRICS = {
    "standard_deviation": {
        "formula": "sqrt(Σ(x - mean)² / n)",
        "interpretation": "Total volatility measure",
    },
    "beta": {
        "formula": "Cov(Ri, Rm) / Var(Rm)",
        "interpretation": "Systematic risk relative to market",
        "benchmark": "Market beta = 1.0",
    },
    "sharpe_ratio": {
        "formula": "(Return - Risk_free) / Std_dev",
        "interpretation": "Return per unit of total risk",
        "good_range": "> 1.0",
    },
    "sortino_ratio": {
        "formula": "(Return - Target) / Downside_deviation",
        "interpretation": "Return per unit of downside risk",
    },
    "var": {
        "description": "Value at Risk",
        "formula": "μ - z_α × σ",
        "interpretation": "Maximum expected loss at confidence level",
    },
    "max_drawdown": {
        "formula": "(Peak - Trough) / Peak",
        "interpretation": "Largest peak-to-trough decline",
    },
}

# ===========================================
# YIELD CURVE SHAPES
# ===========================================

YIELD_CURVES = {
    "normal": {
        "shape": "Upward sloping",
        "implication": "Economic expansion expected",
        "long_short_spread": "Positive",
    },
    "inverted": {
        "shape": "Downward sloping",
        "implication": "Recession predictor",
        "long_short_spread": "Negative",
        "accuracy": "~80% historically",
    },
    "flat": {
        "shape": "Little slope",
        "implication": "Transition/uncertainty",
        "long_short_spread": "Near zero",
    },
    "humped": {
        "shape": "Rises then falls",
        "implication": "Medium-term rate hikes expected",
    },
}

# ===========================================
# CENTRAL BANKS
# ===========================================

CENTRAL_BANKS = {
    "fed": {
        "name": "Federal Reserve",
        "country": "United States",
        "mandate": "Maximum employment, stable prices",
        "inflation_target": "2%",
        "key_rate": "Federal Funds Rate",
    },
    "ecb": {
        "name": "European Central Bank",
        "country": "Eurozone",
        "mandate": "Price stability",
        "inflation_target": "2%",
        "key_rate": "Main Refinancing Operations Rate",
    },
    "boj": {
        "name": "Bank of Japan",
        "country": "Japan",
        "mandate": "Price stability, financial system stability",
        "inflation_target": "2%",
        "key_rate": "Policy Rate",
    },
    "boe": {
        "name": "Bank of England",
        "country": "United Kingdom",
        "mandate": "Price stability, support government economic policy",
        "inflation_target": "2%",
        "key_rate": "Bank Rate",
    },
    "pboc": {
        "name": "People's Bank of China",
        "country": "China",
        "mandate": "Currency stability, economic growth",
        "key_rate": "Loan Prime Rate",
    },
}

# ===========================================
# CREDIT RATINGS
# ===========================================

CREDIT_RATINGS = {
    "investment_grade": {
        "sp_moody": ["AAA/Aaa", "AA/Aa", "A/A", "BBB/Baa"],
        "description": "Lower default risk",
        "typical_spread": "50-200bp over treasuries",
    },
    "high_yield": {
        "sp_moody": ["BB/Ba", "B/B", "CCC/Caa", "CC/Ca", "C/C", "D"],
        "description": "Higher default risk, higher yield",
        "typical_spread": "300-1000+bp over treasuries",
    },
    "default_rates": {
        "AAA_10yr": "<0.1%",
        "BBB_10yr": "~2%",
        "B_10yr": "~25%",
        "CCC_10yr": "~50%",
    },
}

# ===========================================
# TAX-ADVANTAGED ACCOUNTS
# ===========================================

TAX_ACCOUNTS = {
    "401k": {
        "type": "Employer-sponsored retirement",
        "tax_treatment": "Pre-tax contributions, taxed on withdrawal",
        "contribution_limit_2024": "$23,000 ($30,500 if 50+)",
    },
    "roth_401k": {
        "type": "Employer-sponsored retirement",
        "tax_treatment": "After-tax contributions, tax-free growth",
        "contribution_limit_2024": "$23,000 ($30,500 if 50+)",
    },
    "traditional_ira": {
        "type": "Individual retirement",
        "tax_treatment": "Deductible contributions, taxed on withdrawal",
        "contribution_limit_2024": "$7,000 ($8,000 if 50+)",
    },
    "roth_ira": {
        "type": "Individual retirement",
        "tax_treatment": "After-tax contributions, tax-free growth",
        "contribution_limit_2024": "$7,000 ($8,000 if 50+)",
        "income_limits": "Yes, phase out at high income",
    },
    "hsa": {
        "type": "Health savings account",
        "tax_treatment": "Triple tax advantaged",
        "contribution_limit_2024": "$4,150 individual / $8,300 family",
    },
    "529": {
        "type": "Education savings",
        "tax_treatment": "After-tax contributions, tax-free for education",
        "state_deduction": "Many states offer deduction",
    },
}

# ===========================================
# OPTION GREEKS
# ===========================================

OPTION_GREEKS = {
    "delta": {
        "symbol": "Δ",
        "definition": "Rate of change of option price with respect to underlying",
        "formula": "∂V/∂S",
        "call_range": "[0, 1]",
        "put_range": "[-1, 0]",
    },
    "gamma": {
        "symbol": "Γ",
        "definition": "Rate of change of delta with respect to underlying",
        "formula": "∂²V/∂S²",
        "maximum": "At-the-money options",
    },
    "theta": {
        "symbol": "Θ",
        "definition": "Rate of change of option price with respect to time",
        "formula": "∂V/∂t",
        "sign": "Usually negative (time decay)",
    },
    "vega": {
        "symbol": "ν",
        "definition": "Rate of change of option price with respect to volatility",
        "formula": "∂V/∂σ",
        "sign": "Positive for long options",
    },
    "rho": {
        "symbol": "ρ",
        "definition": "Rate of change of option price with respect to interest rate",
        "formula": "∂V/∂r",
    },
}

# ===========================================
# HELPER FUNCTIONS
# ===========================================

def get_knowledge() -> str:
    """Read the main money knowledge document."""
    with open(KNOWLEDGE_PATH, 'r') as f:
        return f.read()


def get_advanced_knowledge() -> str:
    """Read the advanced money knowledge document."""
    with open(KNOWLEDGE_ADVANCED_PATH, 'r') as f:
        return f.read()


def calculate_compound_interest(
    principal: float,
    rate: float,
    time: float,
    n: int = 12
) -> dict:
    """
    Calculate compound interest.

    Args:
        principal: Initial investment
        rate: Annual interest rate (decimal)
        time: Time in years
        n: Compounding frequency per year

    Returns:
        Dictionary with final amount and interest earned
    """
    amount = principal * (1 + rate / n) ** (n * time)
    interest = amount - principal

    return {
        "principal": principal,
        "final_amount": round(amount, 2),
        "interest_earned": round(interest, 2),
        "effective_rate": round((1 + rate / n) ** n - 1, 6),
    }


def calculate_continuous_compound(
    principal: float,
    rate: float,
    time: float
) -> float:
    """
    Calculate continuous compound interest.

    Args:
        principal: Initial investment
        rate: Annual interest rate (decimal)
        time: Time in years

    Returns:
        Final amount
    """
    return principal * math.exp(rate * time)


def calculate_loan_payment(
    principal: float,
    rate: float,
    periods: int
) -> dict:
    """
    Calculate loan payment (amortizing loan).

    Args:
        principal: Loan amount
        rate: Periodic interest rate (decimal)
        periods: Number of payment periods

    Returns:
        Dictionary with payment details
    """
    if rate == 0:
        payment = principal / periods
    else:
        payment = principal * rate * (1 + rate) ** periods / ((1 + rate) ** periods - 1)

    total_paid = payment * periods
    total_interest = total_paid - principal

    return {
        "payment": round(payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "periods": periods,
    }


def calculate_mortgage_payment(
    principal: float,
    annual_rate: float,
    years: int
) -> dict:
    """
    Calculate monthly mortgage payment.

    Args:
        principal: Loan amount
        annual_rate: Annual interest rate (decimal)
        years: Loan term in years

    Returns:
        Dictionary with mortgage details
    """
    monthly_rate = annual_rate / 12
    periods = years * 12

    result = calculate_loan_payment(principal, monthly_rate, periods)
    result["monthly_payment"] = result.pop("payment")
    result["years"] = years
    result["annual_rate"] = annual_rate

    return result


def calculate_npv(
    cash_flows: List[float],
    discount_rate: float,
    initial_investment: float = 0
) -> float:
    """
    Calculate Net Present Value.

    Args:
        cash_flows: List of future cash flows (starting at period 1)
        discount_rate: Discount rate (decimal)
        initial_investment: Initial investment (positive number)

    Returns:
        NPV
    """
    pv_sum = sum(cf / (1 + discount_rate) ** (t + 1)
                 for t, cf in enumerate(cash_flows))
    return pv_sum - initial_investment


def calculate_irr(
    cash_flows: List[float],
    initial_investment: float,
    tolerance: float = 0.0001,
    max_iterations: int = 100
) -> Optional[float]:
    """
    Calculate Internal Rate of Return using Newton-Raphson method.

    Args:
        cash_flows: List of future cash flows
        initial_investment: Initial investment (positive number)
        tolerance: Convergence tolerance
        max_iterations: Maximum iterations

    Returns:
        IRR as decimal, or None if no convergence
    """
    rate = 0.1  # Initial guess

    for _ in range(max_iterations):
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


def calculate_future_value(
    present_value: float,
    rate: float,
    periods: int
) -> float:
    """
    Calculate future value.

    Args:
        present_value: Current value
        rate: Periodic interest rate (decimal)
        periods: Number of periods

    Returns:
        Future value
    """
    return present_value * (1 + rate) ** periods


def calculate_present_value(
    future_value: float,
    rate: float,
    periods: int
) -> float:
    """
    Calculate present value.

    Args:
        future_value: Future value
        rate: Periodic discount rate (decimal)
        periods: Number of periods

    Returns:
        Present value
    """
    return future_value / (1 + rate) ** periods


def calculate_annuity_pv(
    payment: float,
    rate: float,
    periods: int
) -> float:
    """
    Calculate present value of ordinary annuity.

    Args:
        payment: Periodic payment
        rate: Periodic discount rate (decimal)
        periods: Number of periods

    Returns:
        Present value
    """
    if rate == 0:
        return payment * periods
    return payment * (1 - (1 + rate) ** -periods) / rate


def calculate_annuity_fv(
    payment: float,
    rate: float,
    periods: int
) -> float:
    """
    Calculate future value of ordinary annuity.

    Args:
        payment: Periodic payment
        rate: Periodic interest rate (decimal)
        periods: Number of periods

    Returns:
        Future value
    """
    if rate == 0:
        return payment * periods
    return payment * ((1 + rate) ** periods - 1) / rate


def calculate_perpetuity_pv(
    payment: float,
    rate: float
) -> float:
    """
    Calculate present value of perpetuity.

    Args:
        payment: Periodic payment (forever)
        rate: Discount rate (decimal)

    Returns:
        Present value
    """
    return payment / rate


def calculate_growing_perpetuity_pv(
    payment: float,
    rate: float,
    growth: float
) -> float:
    """
    Calculate present value of growing perpetuity (Gordon Growth Model).

    Args:
        payment: First period payment
        rate: Discount rate (decimal)
        growth: Growth rate (decimal), must be < rate

    Returns:
        Present value
    """
    if growth >= rate:
        raise ValueError("Growth rate must be less than discount rate")
    return payment / (rate - growth)


def calculate_bond_price(
    face_value: float,
    coupon_rate: float,
    ytm: float,
    periods: int,
    frequency: int = 2
) -> float:
    """
    Calculate bond price.

    Args:
        face_value: Par value
        coupon_rate: Annual coupon rate (decimal)
        ytm: Yield to maturity (decimal)
        periods: Years to maturity
        frequency: Coupon payments per year

    Returns:
        Bond price
    """
    coupon = face_value * coupon_rate / frequency
    periodic_ytm = ytm / frequency
    n_periods = periods * frequency

    coupon_pv = calculate_annuity_pv(coupon, periodic_ytm, n_periods)
    face_pv = calculate_present_value(face_value, periodic_ytm, n_periods)

    return coupon_pv + face_pv


def calculate_duration(
    face_value: float,
    coupon_rate: float,
    ytm: float,
    periods: int,
    frequency: int = 2
) -> dict:
    """
    Calculate Macaulay and Modified duration.

    Args:
        face_value: Par value
        coupon_rate: Annual coupon rate (decimal)
        ytm: Yield to maturity (decimal)
        periods: Years to maturity
        frequency: Coupon payments per year

    Returns:
        Dictionary with Macaulay and Modified duration
    """
    coupon = face_value * coupon_rate / frequency
    periodic_ytm = ytm / frequency
    n_periods = periods * frequency

    price = calculate_bond_price(face_value, coupon_rate, ytm, periods, frequency)

    # Macaulay duration
    weighted_sum = 0
    for t in range(1, n_periods + 1):
        if t < n_periods:
            cf = coupon
        else:
            cf = coupon + face_value
        pv = cf / (1 + periodic_ytm) ** t
        weighted_sum += (t / frequency) * pv

    macaulay = weighted_sum / price
    modified = macaulay / (1 + periodic_ytm)

    return {
        "macaulay_duration": round(macaulay, 4),
        "modified_duration": round(modified, 4),
    }


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0
) -> float:
    """
    Calculate Sharpe ratio.

    Args:
        returns: List of periodic returns
        risk_free_rate: Risk-free rate for same period

    Returns:
        Sharpe ratio
    """
    if not returns:
        return 0

    mean_return = sum(returns) / len(returns)
    excess_return = mean_return - risk_free_rate

    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5

    if std_dev == 0:
        return 0

    return excess_return / std_dev


def calculate_beta(
    asset_returns: List[float],
    market_returns: List[float]
) -> float:
    """
    Calculate beta (systematic risk).

    Args:
        asset_returns: List of asset returns
        market_returns: List of market returns

    Returns:
        Beta coefficient
    """
    if len(asset_returns) != len(market_returns):
        raise ValueError("Asset and market returns must have same length")

    n = len(asset_returns)
    if n == 0:
        return 0

    mean_asset = sum(asset_returns) / n
    mean_market = sum(market_returns) / n

    covariance = sum((a - mean_asset) * (m - mean_market)
                     for a, m in zip(asset_returns, market_returns)) / n
    variance_market = sum((m - mean_market) ** 2 for m in market_returns) / n

    if variance_market == 0:
        return 0

    return covariance / variance_market


def calculate_capm_return(
    risk_free_rate: float,
    beta: float,
    market_return: float
) -> float:
    """
    Calculate expected return using CAPM.

    Args:
        risk_free_rate: Risk-free rate (decimal)
        beta: Asset beta
        market_return: Expected market return (decimal)

    Returns:
        Expected return (decimal)
    """
    return risk_free_rate + beta * (market_return - risk_free_rate)


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


def calculate_rule_of_72(rate: float) -> float:
    """
    Calculate approximate years to double investment.

    Args:
        rate: Annual return rate (as percentage, e.g., 8 for 8%)

    Returns:
        Approximate years to double
    """
    return 72 / rate


def calculate_real_return(
    nominal_return: float,
    inflation_rate: float
) -> float:
    """
    Calculate real (inflation-adjusted) return.

    Args:
        nominal_return: Nominal return (decimal)
        inflation_rate: Inflation rate (decimal)

    Returns:
        Real return (decimal)
    """
    return (1 + nominal_return) / (1 + inflation_rate) - 1


def calculate_var(
    returns: List[float],
    confidence: float = 0.95
) -> float:
    """
    Calculate parametric Value at Risk (assuming normal distribution).

    Args:
        returns: List of returns
        confidence: Confidence level (e.g., 0.95 for 95%)

    Returns:
        VaR as positive number (loss)
    """
    if not returns:
        return 0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5

    # Z-scores for common confidence levels
    z_scores = {
        0.90: 1.28,
        0.95: 1.645,
        0.99: 2.33,
    }
    z = z_scores.get(confidence, 1.645)

    var = mean_return - z * std_dev
    return -var if var < 0 else 0


def calculate_kelly_criterion(
    win_probability: float,
    win_loss_ratio: float
) -> float:
    """
    Calculate Kelly Criterion for optimal bet sizing.

    Args:
        win_probability: Probability of winning
        win_loss_ratio: Ratio of win size to loss size

    Returns:
        Optimal fraction of bankroll to bet
    """
    q = 1 - win_probability
    kelly = (win_probability * win_loss_ratio - q) / win_loss_ratio
    return max(0, kelly)  # Don't bet if negative


def calculate_dca_returns(
    prices: List[float],
    investment_per_period: float
) -> dict:
    """
    Calculate dollar-cost averaging returns.

    Args:
        prices: List of asset prices per period
        investment_per_period: Amount invested each period

    Returns:
        Dictionary with DCA results
    """
    total_invested = 0
    total_units = 0

    for price in prices:
        units = investment_per_period / price
        total_units += units
        total_invested += investment_per_period

    final_value = total_units * prices[-1]
    average_cost = total_invested / total_units

    return {
        "total_invested": round(total_invested, 2),
        "total_units": round(total_units, 6),
        "average_cost": round(average_cost, 2),
        "final_value": round(final_value, 2),
        "return_pct": round((final_value / total_invested - 1) * 100, 2),
    }


# ===========================================
# EXPORTS
# ===========================================

__all__ = [
    # Paths
    "KNOWLEDGE_PATH",
    "KNOWLEDGE_ADVANCED_PATH",

    # Constants
    "MONEY_SUPPLY",
    "INTEREST_RATE_TYPES",
    "INFLATION_TYPES",
    "ASSET_CLASSES",
    "RISK_METRICS",
    "YIELD_CURVES",
    "CENTRAL_BANKS",
    "CREDIT_RATINGS",
    "TAX_ACCOUNTS",
    "OPTION_GREEKS",

    # Functions - Knowledge
    "get_knowledge",
    "get_advanced_knowledge",

    # Functions - Time Value of Money
    "calculate_compound_interest",
    "calculate_continuous_compound",
    "calculate_loan_payment",
    "calculate_mortgage_payment",
    "calculate_npv",
    "calculate_irr",
    "calculate_future_value",
    "calculate_present_value",
    "calculate_annuity_pv",
    "calculate_annuity_fv",
    "calculate_perpetuity_pv",
    "calculate_growing_perpetuity_pv",

    # Functions - Fixed Income
    "calculate_bond_price",
    "calculate_duration",

    # Functions - Risk & Return
    "calculate_sharpe_ratio",
    "calculate_beta",
    "calculate_capm_return",
    "calculate_wacc",
    "calculate_var",

    # Functions - Utilities
    "calculate_rule_of_72",
    "calculate_real_return",
    "calculate_kelly_criterion",
    "calculate_dca_returns",
]
