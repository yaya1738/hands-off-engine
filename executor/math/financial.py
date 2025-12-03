#!/usr/bin/env python3
"""
Financial Mathematics - Quantitative Finance and Risk

Covers:
- Option pricing (Black-Scholes, binomial, Monte Carlo)
- Greeks (delta, gamma, theta, vega, rho)
- Interest rate models
- Portfolio theory (Markowitz, CAPM, Sharpe)
- Risk measures (VaR, CVaR, drawdown)
- Stochastic calculus (Ito's lemma, SDE simulation)
- Fixed income (bonds, duration, convexity)
- Derivatives pricing

USAGE:
    from executor.math.financial import fin

    fin.black_scholes_call(S=100, K=100, T=1, r=0.05, sigma=0.2)
    fin.delta(S=100, K=100, T=1, r=0.05, sigma=0.2, option='call')
    fin.var_historical(returns, confidence=0.95)
"""

import math as _math
import random
from typing import List, Tuple, Dict, Optional, Callable
from functools import lru_cache


# Constants
PI = _math.pi
TRADING_DAYS_PER_YEAR = 252


class FinancialMath:
    """Comprehensive financial mathematics."""

    # ==================== OPTION PRICING ====================

    def _norm_cdf(self, x: float) -> float:
        """Standard normal CDF."""
        return 0.5 * (1 + _math.erf(x / _math.sqrt(2)))

    def _norm_pdf(self, x: float) -> float:
        """Standard normal PDF."""
        return _math.exp(-0.5 * x**2) / _math.sqrt(2 * PI)

    def black_scholes_call(self, S: float, K: float, T: float,
                           r: float, sigma: float, q: float = 0) -> float:
        """
        Black-Scholes call option price.

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility
            q: Dividend yield

        Returns:
            Call option price
        """
        if T <= 0:
            return max(0, S - K)

        d1 = (_math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * _math.sqrt(T))
        d2 = d1 - sigma * _math.sqrt(T)

        return S * _math.exp(-q * T) * self._norm_cdf(d1) - K * _math.exp(-r * T) * self._norm_cdf(d2)

    def black_scholes_put(self, S: float, K: float, T: float,
                          r: float, sigma: float, q: float = 0) -> float:
        """Black-Scholes put option price."""
        if T <= 0:
            return max(0, K - S)

        d1 = (_math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * _math.sqrt(T))
        d2 = d1 - sigma * _math.sqrt(T)

        return K * _math.exp(-r * T) * self._norm_cdf(-d2) - S * _math.exp(-q * T) * self._norm_cdf(-d1)

    def binomial_option(self, S: float, K: float, T: float, r: float,
                        sigma: float, n_steps: int = 100,
                        option_type: str = 'call',
                        american: bool = False) -> float:
        """
        Binomial tree option pricing (Cox-Ross-Rubinstein).
        Supports American options.
        """
        dt = T / n_steps
        u = _math.exp(sigma * _math.sqrt(dt))
        d = 1 / u
        p = (_math.exp(r * dt) - d) / (u - d)
        discount = _math.exp(-r * dt)

        # Build tree
        prices = [[0.0] * (i + 1) for i in range(n_steps + 1)]
        for i in range(n_steps + 1):
            for j in range(i + 1):
                prices[i][j] = S * (u ** (i - j)) * (d ** j)

        # Option values at expiration
        values = [[0.0] * (i + 1) for i in range(n_steps + 1)]
        for j in range(n_steps + 1):
            if option_type == 'call':
                values[n_steps][j] = max(0, prices[n_steps][j] - K)
            else:
                values[n_steps][j] = max(0, K - prices[n_steps][j])

        # Backward induction
        for i in range(n_steps - 1, -1, -1):
            for j in range(i + 1):
                hold_value = discount * (p * values[i + 1][j] + (1 - p) * values[i + 1][j + 1])

                if american:
                    if option_type == 'call':
                        exercise_value = max(0, prices[i][j] - K)
                    else:
                        exercise_value = max(0, K - prices[i][j])
                    values[i][j] = max(hold_value, exercise_value)
                else:
                    values[i][j] = hold_value

        return values[0][0]

    def monte_carlo_option(self, S: float, K: float, T: float, r: float,
                           sigma: float, n_paths: int = 10000,
                           n_steps: int = 100, option_type: str = 'call',
                           seed: int = None) -> Dict:
        """
        Monte Carlo option pricing with confidence interval.
        """
        if seed is not None:
            random.seed(seed)

        dt = T / n_steps
        drift = (r - 0.5 * sigma**2) * dt
        vol = sigma * _math.sqrt(dt)

        payoffs = []
        for _ in range(n_paths):
            S_t = S
            for _ in range(n_steps):
                Z = random.gauss(0, 1)
                S_t *= _math.exp(drift + vol * Z)

            if option_type == 'call':
                payoff = max(0, S_t - K)
            else:
                payoff = max(0, K - S_t)
            payoffs.append(payoff)

        discount = _math.exp(-r * T)
        mean_payoff = sum(payoffs) / n_paths
        price = discount * mean_payoff

        # Standard error
        variance = sum((p - mean_payoff)**2 for p in payoffs) / (n_paths - 1)
        std_error = discount * _math.sqrt(variance / n_paths)

        return {
            "price": price,
            "std_error": std_error,
            "ci_95": (price - 1.96 * std_error, price + 1.96 * std_error)
        }

    # ==================== GREEKS ====================

    def delta(self, S: float, K: float, T: float, r: float,
              sigma: float, option_type: str = 'call', q: float = 0) -> float:
        """Option delta: dV/dS."""
        if T <= 0:
            if option_type == 'call':
                return 1.0 if S > K else 0.0
            else:
                return -1.0 if S < K else 0.0

        d1 = (_math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * _math.sqrt(T))

        if option_type == 'call':
            return _math.exp(-q * T) * self._norm_cdf(d1)
        else:
            return _math.exp(-q * T) * (self._norm_cdf(d1) - 1)

    def gamma(self, S: float, K: float, T: float, r: float,
              sigma: float, q: float = 0) -> float:
        """Option gamma: d²V/dS²."""
        if T <= 0:
            return 0

        d1 = (_math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * _math.sqrt(T))
        return _math.exp(-q * T) * self._norm_pdf(d1) / (S * sigma * _math.sqrt(T))

    def theta(self, S: float, K: float, T: float, r: float, sigma: float,
              option_type: str = 'call', q: float = 0) -> float:
        """Option theta: dV/dT (per day)."""
        if T <= 0:
            return 0

        d1 = (_math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * _math.sqrt(T))
        d2 = d1 - sigma * _math.sqrt(T)

        term1 = -S * _math.exp(-q * T) * self._norm_pdf(d1) * sigma / (2 * _math.sqrt(T))

        if option_type == 'call':
            term2 = q * S * _math.exp(-q * T) * self._norm_cdf(d1)
            term3 = -r * K * _math.exp(-r * T) * self._norm_cdf(d2)
        else:
            term2 = -q * S * _math.exp(-q * T) * self._norm_cdf(-d1)
            term3 = r * K * _math.exp(-r * T) * self._norm_cdf(-d2)

        return (term1 + term2 + term3) / 365  # Per day

    def vega(self, S: float, K: float, T: float, r: float,
             sigma: float, q: float = 0) -> float:
        """Option vega: dV/dσ (per 1% change in vol)."""
        if T <= 0:
            return 0

        d1 = (_math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * _math.sqrt(T))
        return S * _math.exp(-q * T) * self._norm_pdf(d1) * _math.sqrt(T) / 100

    def rho(self, S: float, K: float, T: float, r: float, sigma: float,
            option_type: str = 'call', q: float = 0) -> float:
        """Option rho: dV/dr (per 1% change in rate)."""
        if T <= 0:
            return 0

        d1 = (_math.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * _math.sqrt(T))
        d2 = d1 - sigma * _math.sqrt(T)

        if option_type == 'call':
            return K * T * _math.exp(-r * T) * self._norm_cdf(d2) / 100
        else:
            return -K * T * _math.exp(-r * T) * self._norm_cdf(-d2) / 100

    def implied_volatility(self, price: float, S: float, K: float, T: float,
                           r: float, option_type: str = 'call',
                           tol: float = 1e-6, max_iter: int = 100) -> float:
        """
        Implied volatility using Newton-Raphson method.
        """
        sigma = 0.2  # Initial guess

        for _ in range(max_iter):
            if option_type == 'call':
                model_price = self.black_scholes_call(S, K, T, r, sigma)
            else:
                model_price = self.black_scholes_put(S, K, T, r, sigma)

            vega_val = self.vega(S, K, T, r, sigma) * 100  # Undo per-1% scaling

            if vega_val < 1e-10:
                break

            diff = model_price - price
            if abs(diff) < tol:
                return sigma

            sigma -= diff / vega_val
            sigma = max(0.001, min(5.0, sigma))  # Bounds

        return sigma

    # ==================== PORTFOLIO THEORY ====================

    def portfolio_return(self, weights: List[float], returns: List[float]) -> float:
        """Expected portfolio return."""
        return sum(w * r for w, r in zip(weights, returns))

    def portfolio_variance(self, weights: List[float],
                           cov_matrix: List[List[float]]) -> float:
        """Portfolio variance."""
        n = len(weights)
        variance = 0
        for i in range(n):
            for j in range(n):
                variance += weights[i] * weights[j] * cov_matrix[i][j]
        return variance

    def portfolio_volatility(self, weights: List[float],
                             cov_matrix: List[List[float]]) -> float:
        """Portfolio volatility (standard deviation)."""
        return _math.sqrt(self.portfolio_variance(weights, cov_matrix))

    def sharpe_ratio(self, ret: float, rf: float, volatility: float) -> float:
        """Sharpe ratio: (R - Rf) / σ."""
        if volatility == 0:
            return 0
        return (ret - rf) / volatility

    def sortino_ratio(self, ret: float, rf: float, downside_dev: float) -> float:
        """Sortino ratio: (R - Rf) / downside_deviation."""
        if downside_dev == 0:
            return 0
        return (ret - rf) / downside_dev

    def downside_deviation(self, returns: List[float], mar: float = 0) -> float:
        """Downside deviation below minimum acceptable return."""
        below_mar = [(r - mar)**2 for r in returns if r < mar]
        if not below_mar:
            return 0
        return _math.sqrt(sum(below_mar) / len(returns))

    def beta(self, asset_returns: List[float], market_returns: List[float]) -> float:
        """CAPM beta: Cov(Ra, Rm) / Var(Rm)."""
        n = len(asset_returns)
        mean_a = sum(asset_returns) / n
        mean_m = sum(market_returns) / n

        cov = sum((asset_returns[i] - mean_a) * (market_returns[i] - mean_m) for i in range(n)) / n
        var_m = sum((r - mean_m)**2 for r in market_returns) / n

        if var_m == 0:
            return 0
        return cov / var_m

    def alpha(self, asset_return: float, rf: float, beta: float, market_return: float) -> float:
        """Jensen's alpha: Ra - (Rf + β(Rm - Rf))."""
        return asset_return - (rf + beta * (market_return - rf))

    def information_ratio(self, active_returns: List[float]) -> float:
        """Information ratio: mean(active_return) / std(active_return)."""
        mean = sum(active_returns) / len(active_returns)
        var = sum((r - mean)**2 for r in active_returns) / len(active_returns)
        if var == 0:
            return 0
        return mean / _math.sqrt(var)

    def treynor_ratio(self, ret: float, rf: float, beta: float) -> float:
        """Treynor ratio: (R - Rf) / β."""
        if beta == 0:
            return 0
        return (ret - rf) / beta

    # ==================== RISK MEASURES ====================

    def var_historical(self, returns: List[float], confidence: float = 0.95,
                       position_size: float = 1.0) -> float:
        """Historical Value at Risk."""
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return -sorted_returns[index] * position_size

    def var_parametric(self, mean: float, std: float, confidence: float = 0.95,
                       position_size: float = 1.0) -> float:
        """Parametric (normal) Value at Risk."""
        # z-score for confidence level
        from math import erf, sqrt
        def norm_ppf(p):
            # Beasley-Springer-Moro approximation
            a = [0, -3.969683028665376e+01, 2.209460984245205e+02,
                 -2.759285104469687e+02, 1.383577518672690e+02,
                 -3.066479806614716e+01, 2.506628277459239e+00]
            b = [0, -5.447609879822406e+01, 1.615858368580409e+02,
                 -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]

            if p < 0.5:
                q = sqrt(-2 * _math.log(p))
                return (((((a[1]*q+a[2])*q+a[3])*q+a[4])*q+a[5])*q+a[6]) / \
                       ((((b[1]*q+b[2])*q+b[3])*q+b[4])*q+1)
            else:
                q = sqrt(-2 * _math.log(1 - p))
                return -(((((a[1]*q+a[2])*q+a[3])*q+a[4])*q+a[5])*q+a[6]) / \
                       ((((b[1]*q+b[2])*q+b[3])*q+b[4])*q+1)

        z = norm_ppf(1 - confidence)
        return -(mean + z * std) * position_size

    def cvar(self, returns: List[float], confidence: float = 0.95,
             position_size: float = 1.0) -> float:
        """Conditional Value at Risk (Expected Shortfall)."""
        sorted_returns = sorted(returns)
        cutoff_index = int((1 - confidence) * len(sorted_returns))
        tail = sorted_returns[:cutoff_index + 1]
        return -sum(tail) / len(tail) * position_size if tail else 0

    def max_drawdown(self, values: List[float]) -> float:
        """Maximum drawdown from peak."""
        if not values:
            return 0
        peak = values[0]
        max_dd = 0
        for v in values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def calmar_ratio(self, annual_return: float, max_drawdown: float) -> float:
        """Calmar ratio: annual return / max drawdown."""
        if max_drawdown == 0:
            return 0
        return annual_return / max_drawdown

    # ==================== STOCHASTIC CALCULUS ====================

    def geometric_brownian_motion(self, S0: float, mu: float, sigma: float,
                                   T: float, n_steps: int = 100,
                                   n_paths: int = 1) -> List[List[float]]:
        """
        Simulate Geometric Brownian Motion: dS = μS dt + σS dW.
        """
        dt = T / n_steps
        paths = []

        for _ in range(n_paths):
            path = [S0]
            S = S0
            for _ in range(n_steps):
                Z = random.gauss(0, 1)
                S *= _math.exp((mu - 0.5 * sigma**2) * dt + sigma * _math.sqrt(dt) * Z)
                path.append(S)
            paths.append(path)

        return paths if n_paths > 1 else paths[0]

    def heston_model(self, S0: float, v0: float, T: float, r: float,
                     kappa: float, theta: float, sigma_v: float, rho: float,
                     n_steps: int = 100, n_paths: int = 1) -> List[Tuple[List[float], List[float]]]:
        """
        Heston stochastic volatility model.
        dS = rS dt + √v S dW1
        dv = κ(θ-v) dt + σ_v √v dW2
        Corr(dW1, dW2) = ρ
        """
        dt = T / n_steps
        paths = []

        for _ in range(n_paths):
            S_path = [S0]
            v_path = [v0]
            S, v = S0, v0

            for _ in range(n_steps):
                Z1 = random.gauss(0, 1)
                Z2 = rho * Z1 + _math.sqrt(1 - rho**2) * random.gauss(0, 1)

                v_sqrt = _math.sqrt(max(0, v))
                S *= _math.exp((r - 0.5 * v) * dt + v_sqrt * _math.sqrt(dt) * Z1)
                v += kappa * (theta - v) * dt + sigma_v * v_sqrt * _math.sqrt(dt) * Z2
                v = max(0, v)

                S_path.append(S)
                v_path.append(v)

            paths.append((S_path, v_path))

        return paths if n_paths > 1 else paths[0]

    def ornstein_uhlenbeck(self, x0: float, mu: float, theta: float, sigma: float,
                           T: float, n_steps: int = 100) -> List[float]:
        """
        Ornstein-Uhlenbeck mean-reverting process.
        dx = θ(μ - x) dt + σ dW
        """
        dt = T / n_steps
        path = [x0]
        x = x0

        for _ in range(n_steps):
            Z = random.gauss(0, 1)
            x += theta * (mu - x) * dt + sigma * _math.sqrt(dt) * Z
            path.append(x)

        return path

    def vasicek(self, r0: float, a: float, b: float, sigma: float,
                T: float, n_steps: int = 100) -> List[float]:
        """
        Vasicek interest rate model: dr = a(b-r) dt + σ dW.
        """
        return self.ornstein_uhlenbeck(r0, b, a, sigma, T, n_steps)

    def cir(self, r0: float, a: float, b: float, sigma: float,
            T: float, n_steps: int = 100) -> List[float]:
        """
        Cox-Ingersoll-Ross interest rate model: dr = a(b-r) dt + σ√r dW.
        """
        dt = T / n_steps
        path = [r0]
        r = r0

        for _ in range(n_steps):
            Z = random.gauss(0, 1)
            r_sqrt = _math.sqrt(max(0, r))
            r += a * (b - r) * dt + sigma * r_sqrt * _math.sqrt(dt) * Z
            r = max(0, r)
            path.append(r)

        return path

    # ==================== FIXED INCOME ====================

    def bond_price(self, face: float, coupon_rate: float, ytm: float,
                   years: int, freq: int = 2) -> float:
        """Bond price from yield to maturity."""
        c = face * coupon_rate / freq
        n = years * freq
        y = ytm / freq

        pv_coupons = c * (1 - (1 + y)**(-n)) / y if y > 0 else c * n
        pv_face = face / (1 + y)**n

        return pv_coupons + pv_face

    def bond_ytm(self, price: float, face: float, coupon_rate: float,
                 years: int, freq: int = 2, tol: float = 1e-6) -> float:
        """Yield to maturity using Newton-Raphson."""
        ytm = coupon_rate  # Initial guess

        for _ in range(100):
            p = self.bond_price(face, coupon_rate, ytm, years, freq)
            dp = -self.bond_duration(face, coupon_rate, ytm, years, freq) * p

            if abs(dp) < 1e-10:
                break

            ytm -= (p - price) / dp
            ytm = max(0.0001, ytm)

            if abs(p - price) < tol:
                break

        return ytm

    def bond_duration(self, face: float, coupon_rate: float, ytm: float,
                      years: int, freq: int = 2) -> float:
        """Macaulay duration."""
        c = face * coupon_rate / freq
        n = years * freq
        y = ytm / freq

        price = self.bond_price(face, coupon_rate, ytm, years, freq)
        if price == 0:
            return 0

        weighted_cf = 0
        for t in range(1, n + 1):
            cf = c if t < n else c + face
            weighted_cf += t * cf / (1 + y)**t

        return (weighted_cf / price) / freq

    def bond_modified_duration(self, face: float, coupon_rate: float, ytm: float,
                                years: int, freq: int = 2) -> float:
        """Modified duration."""
        mac_dur = self.bond_duration(face, coupon_rate, ytm, years, freq)
        return mac_dur / (1 + ytm / freq)

    def bond_convexity(self, face: float, coupon_rate: float, ytm: float,
                       years: int, freq: int = 2) -> float:
        """Bond convexity."""
        c = face * coupon_rate / freq
        n = years * freq
        y = ytm / freq

        price = self.bond_price(face, coupon_rate, ytm, years, freq)
        if price == 0:
            return 0

        conv = 0
        for t in range(1, n + 1):
            cf = c if t < n else c + face
            conv += t * (t + 1) * cf / (1 + y)**(t + 2)

        return conv / (price * freq**2)


# Singleton instance
fin = FinancialMath()
