#!/usr/bin/env python3
"""
Theoretical Mathematics Engine - Advanced Mathematical Infrastructure

Comprehensive mathematical foundation for quantitative trading:

MODULES:
- probability: Distributions, Bayes, entropy
- calculus: Derivatives, integrals, optimization
- linalg: Matrix operations, decompositions
- stochastic: Random processes, Brownian motion
- timeseries: ARIMA, autocorrelation, forecasting
- montecarlo: Simulation, importance sampling
- optimization: Gradient descent, Newton, convex
- information: Entropy, KL divergence, mutual info
- gametheory: Nash equilibrium, minimax
- numerics: Root finding, interpolation, integration

USAGE:
    from executor.theoretical_math import (
        prob, calc, linalg, stoch, ts, mc, opt, info, game, num
    )

    # Bayesian update
    posterior = prob.bayes_update(prior=0.5, likelihood=0.8, evidence=0.6)

    # Monte Carlo simulation
    results = mc.simulate(func, trials=10000)

    # Optimization
    minimum = opt.gradient_descent(f, grad_f, x0, lr=0.01)

Serving: Yair Siegel
"""

import math as _math
import random
from typing import List, Dict, Tuple, Optional, Callable, Union, Any
from dataclasses import dataclass
from functools import lru_cache
import itertools


# ==================== CONSTANTS ====================

PI = _math.pi
E = _math.e
PHI = (1 + _math.sqrt(5)) / 2  # Golden ratio
EULER_GAMMA = 0.5772156649  # Euler-Mascheroni constant
INF = float('inf')
NEG_INF = float('-inf')
EPSILON = 1e-10


# ==================== PROBABILITY THEORY ====================

class ProbabilityTheory:
    """
    Probability distributions, Bayesian inference, and related calculations.
    """

    # --- Basic Probability ---

    def bayes_update(self, prior: float, likelihood: float,
                     evidence: float) -> float:
        """
        Bayesian posterior probability.
        P(H|E) = P(E|H) * P(H) / P(E)

        Args:
            prior: P(H) - prior probability of hypothesis
            likelihood: P(E|H) - probability of evidence given hypothesis
            evidence: P(E) - probability of evidence

        Returns:
            Posterior probability P(H|E)
        """
        if evidence == 0:
            return 0
        return (likelihood * prior) / evidence

    def bayes_factor(self, likelihood_h1: float, likelihood_h0: float) -> float:
        """
        Bayes factor: evidence strength for H1 vs H0.
        BF > 1 supports H1, BF < 1 supports H0.
        """
        if likelihood_h0 == 0:
            return INF
        return likelihood_h1 / likelihood_h0

    def total_probability(self, conditionals: List[Tuple[float, float]]) -> float:
        """
        Law of total probability.
        P(A) = Σ P(A|Bi) * P(Bi)

        Args:
            conditionals: List of (P(A|Bi), P(Bi)) tuples
        """
        return sum(p_a_given_b * p_b for p_a_given_b, p_b in conditionals)

    def conditional(self, p_joint: float, p_condition: float) -> float:
        """P(A|B) = P(A∩B) / P(B)"""
        if p_condition == 0:
            return 0
        return p_joint / p_condition

    def independence_test(self, p_a: float, p_b: float, p_ab: float,
                          tolerance: float = 0.01) -> bool:
        """Test if A and B are independent: P(A∩B) ≈ P(A)*P(B)"""
        return abs(p_ab - p_a * p_b) < tolerance

    # --- Distributions ---

    def normal_pdf(self, x: float, mu: float = 0, sigma: float = 1) -> float:
        """Normal/Gaussian probability density function."""
        coef = 1 / (sigma * _math.sqrt(2 * PI))
        exp_term = _math.exp(-0.5 * ((x - mu) / sigma) ** 2)
        return coef * exp_term

    def normal_cdf(self, x: float, mu: float = 0, sigma: float = 1) -> float:
        """Normal cumulative distribution function (approximation)."""
        z = (x - mu) / sigma
        return 0.5 * (1 + _math.erf(z / _math.sqrt(2)))

    def normal_quantile(self, p: float, mu: float = 0, sigma: float = 1) -> float:
        """Inverse normal CDF (quantile function) - Beasley-Springer-Moro algorithm."""
        if p <= 0:
            return NEG_INF
        if p >= 1:
            return INF

        # Rational approximation
        a = [0, -3.969683028665376e+01, 2.209460984245205e+02,
             -2.759285104469687e+02, 1.383577518672690e+02,
             -3.066479806614716e+01, 2.506628277459239e+00]
        b = [0, -5.447609879822406e+01, 1.615858368580409e+02,
             -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
        c = [0, -7.784894002430293e-03, -3.223964580411365e-01,
             -2.400758277161838e+00, -2.549732539343734e+00,
             4.374664141464968e+00, 2.938163982698783e+00]
        d = [0, 7.784695709041462e-03, 3.224671290700398e-01,
             2.445134137142996e+00, 3.754408661907416e+00]

        p_low = 0.02425
        p_high = 1 - p_low

        if p < p_low:
            q = _math.sqrt(-2 * _math.log(p))
            z = (((((c[1]*q + c[2])*q + c[3])*q + c[4])*q + c[5])*q + c[6]) / \
                ((((d[1]*q + d[2])*q + d[3])*q + d[4])*q + 1)
        elif p <= p_high:
            q = p - 0.5
            r = q * q
            z = (((((a[1]*r + a[2])*r + a[3])*r + a[4])*r + a[5])*r + a[6])*q / \
                (((((b[1]*r + b[2])*r + b[3])*r + b[4])*r + b[5])*r + 1)
        else:
            q = _math.sqrt(-2 * _math.log(1 - p))
            z = -(((((c[1]*q + c[2])*q + c[3])*q + c[4])*q + c[5])*q + c[6]) / \
                 ((((d[1]*q + d[2])*q + d[3])*q + d[4])*q + 1)

        return mu + sigma * z

    def uniform_pdf(self, x: float, a: float = 0, b: float = 1) -> float:
        """Uniform distribution PDF."""
        if a <= x <= b:
            return 1 / (b - a)
        return 0

    def exponential_pdf(self, x: float, rate: float = 1) -> float:
        """Exponential distribution PDF."""
        if x < 0:
            return 0
        return rate * _math.exp(-rate * x)

    def poisson_pmf(self, k: int, lam: float) -> float:
        """Poisson probability mass function."""
        if k < 0:
            return 0
        return (lam ** k) * _math.exp(-lam) / _math.factorial(k)

    def binomial_pmf(self, k: int, n: int, p: float) -> float:
        """Binomial probability mass function."""
        if k < 0 or k > n:
            return 0
        coef = _math.comb(n, k)
        return coef * (p ** k) * ((1 - p) ** (n - k))

    def beta_pdf(self, x: float, alpha: float, beta: float) -> float:
        """Beta distribution PDF."""
        if x <= 0 or x >= 1:
            return 0
        b_func = _math.gamma(alpha) * _math.gamma(beta) / _math.gamma(alpha + beta)
        return (x ** (alpha - 1)) * ((1 - x) ** (beta - 1)) / b_func

    # --- Moments and Statistics ---

    def expected_value(self, values: List[float], probs: List[float]) -> float:
        """E[X] = Σ xi * P(xi)"""
        return sum(v * p for v, p in zip(values, probs))

    def variance(self, values: List[float], probs: List[float]) -> float:
        """Var(X) = E[X²] - E[X]²"""
        ex = self.expected_value(values, probs)
        ex2 = self.expected_value([v**2 for v in values], probs)
        return ex2 - ex**2

    def skewness(self, values: List[float]) -> float:
        """Sample skewness (Fisher)."""
        n = len(values)
        if n < 3:
            return 0
        mean = sum(values) / n
        m2 = sum((x - mean) ** 2 for x in values) / n
        m3 = sum((x - mean) ** 3 for x in values) / n
        if m2 == 0:
            return 0
        return m3 / (m2 ** 1.5)

    def kurtosis(self, values: List[float]) -> float:
        """Sample excess kurtosis."""
        n = len(values)
        if n < 4:
            return 0
        mean = sum(values) / n
        m2 = sum((x - mean) ** 2 for x in values) / n
        m4 = sum((x - mean) ** 4 for x in values) / n
        if m2 == 0:
            return 0
        return (m4 / (m2 ** 2)) - 3

    def covariance(self, x: List[float], y: List[float]) -> float:
        """Cov(X,Y) = E[(X-μx)(Y-μy)]"""
        n = len(x)
        if n != len(y) or n == 0:
            return 0
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        return sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n

    def correlation(self, x: List[float], y: List[float]) -> float:
        """Pearson correlation coefficient."""
        cov = self.covariance(x, y)
        var_x = self.covariance(x, x)
        var_y = self.covariance(y, y)
        if var_x == 0 or var_y == 0:
            return 0
        return cov / _math.sqrt(var_x * var_y)


# ==================== CALCULUS ====================

class Calculus:
    """
    Differential and integral calculus operations.
    """

    def derivative(self, f: Callable, x: float, h: float = 1e-8) -> float:
        """
        Numerical derivative using central difference.
        f'(x) ≈ [f(x+h) - f(x-h)] / (2h)
        """
        return (f(x + h) - f(x - h)) / (2 * h)

    def second_derivative(self, f: Callable, x: float, h: float = 1e-5) -> float:
        """
        Second derivative using central difference.
        f''(x) ≈ [f(x+h) - 2f(x) + f(x-h)] / h²
        """
        return (f(x + h) - 2 * f(x) + f(x - h)) / (h ** 2)

    def partial_derivative(self, f: Callable, x: List[float],
                           i: int, h: float = 1e-8) -> float:
        """Partial derivative ∂f/∂xi"""
        x_plus = x.copy()
        x_minus = x.copy()
        x_plus[i] += h
        x_minus[i] -= h
        return (f(x_plus) - f(x_minus)) / (2 * h)

    def gradient(self, f: Callable, x: List[float], h: float = 1e-8) -> List[float]:
        """Gradient vector ∇f"""
        return [self.partial_derivative(f, x, i, h) for i in range(len(x))]

    def hessian(self, f: Callable, x: List[float], h: float = 1e-5) -> List[List[float]]:
        """Hessian matrix of second partial derivatives."""
        n = len(x)
        H = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i == j:
                    # Diagonal: ∂²f/∂xi²
                    x_plus = x.copy()
                    x_minus = x.copy()
                    x_plus[i] += h
                    x_minus[i] -= h
                    H[i][j] = (f(x_plus) - 2*f(x) + f(x_minus)) / (h**2)
                else:
                    # Off-diagonal: ∂²f/∂xi∂xj
                    x_pp = x.copy()
                    x_pm = x.copy()
                    x_mp = x.copy()
                    x_mm = x.copy()
                    x_pp[i] += h; x_pp[j] += h
                    x_pm[i] += h; x_pm[j] -= h
                    x_mp[i] -= h; x_mp[j] += h
                    x_mm[i] -= h; x_mm[j] -= h
                    H[i][j] = (f(x_pp) - f(x_pm) - f(x_mp) + f(x_mm)) / (4*h**2)
        return H

    def integrate(self, f: Callable, a: float, b: float,
                  n: int = 1000) -> float:
        """
        Numerical integration using Simpson's rule.
        ∫[a,b] f(x)dx
        """
        if n % 2 == 1:
            n += 1
        h = (b - a) / n

        result = f(a) + f(b)
        for i in range(1, n):
            x = a + i * h
            if i % 2 == 0:
                result += 2 * f(x)
            else:
                result += 4 * f(x)

        return result * h / 3

    def double_integrate(self, f: Callable, ax: float, bx: float,
                         ay: float, by: float, nx: int = 100,
                         ny: int = 100) -> float:
        """Double integral ∫∫ f(x,y) dx dy"""
        hx = (bx - ax) / nx
        hy = (by - ay) / ny

        result = 0
        for i in range(nx):
            for j in range(ny):
                x = ax + (i + 0.5) * hx
                y = ay + (j + 0.5) * hy
                result += f(x, y)

        return result * hx * hy

    def taylor_series(self, f: Callable, x0: float, x: float,
                      n_terms: int = 5) -> float:
        """
        Taylor series approximation.
        f(x) ≈ Σ f^(n)(x0) * (x-x0)^n / n!
        """
        result = f(x0)
        h = 1e-5
        delta = x - x0

        for n in range(1, n_terms):
            # Approximate n-th derivative
            deriv = f
            for _ in range(n):
                deriv_val = self.derivative(deriv, x0, h)
                deriv = lambda t, d=deriv_val: d  # Constant function

            result += deriv(x0) * (delta ** n) / _math.factorial(n)

        return result

    def limit(self, f: Callable, x: float, direction: str = "both",
              h: float = 1e-10) -> float:
        """
        Numerical limit approximation.
        direction: "left", "right", or "both"
        """
        if direction == "left":
            return f(x - h)
        elif direction == "right":
            return f(x + h)
        else:
            left = f(x - h)
            right = f(x + h)
            if abs(left - right) < 1e-6:
                return (left + right) / 2
            return float('nan')  # Limit doesn't exist


# ==================== LINEAR ALGEBRA ====================

class LinearAlgebra:
    """
    Matrix operations and linear algebra utilities.
    """

    def dot(self, a: List[float], b: List[float]) -> float:
        """Dot product of two vectors."""
        return sum(ai * bi for ai, bi in zip(a, b))

    def norm(self, v: List[float], p: int = 2) -> float:
        """Vector p-norm (default: Euclidean)."""
        if p == float('inf'):
            return max(abs(x) for x in v)
        return sum(abs(x) ** p for x in v) ** (1/p)

    def matrix_multiply(self, A: List[List[float]],
                        B: List[List[float]]) -> List[List[float]]:
        """Matrix multiplication A @ B."""
        m, n = len(A), len(A[0])
        n2, p = len(B), len(B[0])

        if n != n2:
            raise ValueError("Incompatible dimensions")

        C = [[0.0] * p for _ in range(m)]
        for i in range(m):
            for j in range(p):
                C[i][j] = sum(A[i][k] * B[k][j] for k in range(n))
        return C

    def transpose(self, A: List[List[float]]) -> List[List[float]]:
        """Matrix transpose."""
        return [[A[j][i] for j in range(len(A))] for i in range(len(A[0]))]

    def identity(self, n: int) -> List[List[float]]:
        """n×n identity matrix."""
        return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    def determinant(self, A: List[List[float]]) -> float:
        """Matrix determinant (recursive expansion)."""
        n = len(A)
        if n == 1:
            return A[0][0]
        if n == 2:
            return A[0][0] * A[1][1] - A[0][1] * A[1][0]

        det = 0
        for j in range(n):
            minor = [[A[i][k] for k in range(n) if k != j]
                     for i in range(1, n)]
            det += ((-1) ** j) * A[0][j] * self.determinant(minor)
        return det

    def trace(self, A: List[List[float]]) -> float:
        """Matrix trace (sum of diagonal)."""
        return sum(A[i][i] for i in range(min(len(A), len(A[0]))))

    def inverse_2x2(self, A: List[List[float]]) -> Optional[List[List[float]]]:
        """Inverse of 2x2 matrix."""
        det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
        if abs(det) < EPSILON:
            return None
        return [[A[1][1]/det, -A[0][1]/det],
                [-A[1][0]/det, A[0][0]/det]]

    def solve_2x2(self, A: List[List[float]], b: List[float]) -> Optional[List[float]]:
        """Solve Ax = b for 2x2 system using Cramer's rule."""
        det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
        if abs(det) < EPSILON:
            return None

        det_x = b[0] * A[1][1] - A[0][1] * b[1]
        det_y = A[0][0] * b[1] - b[0] * A[1][0]

        return [det_x / det, det_y / det]

    def eigenvalues_2x2(self, A: List[List[float]]) -> Tuple[complex, complex]:
        """Eigenvalues of 2x2 matrix."""
        tr = A[0][0] + A[1][1]
        det = A[0][0] * A[1][1] - A[0][1] * A[1][0]

        discriminant = tr**2 - 4*det
        if discriminant >= 0:
            sqrt_d = _math.sqrt(discriminant)
            return ((tr + sqrt_d) / 2, (tr - sqrt_d) / 2)
        else:
            sqrt_d = _math.sqrt(-discriminant)
            return (complex(tr/2, sqrt_d/2), complex(tr/2, -sqrt_d/2))

    def outer_product(self, u: List[float], v: List[float]) -> List[List[float]]:
        """Outer product u ⊗ v."""
        return [[ui * vj for vj in v] for ui in u]

    def project(self, u: List[float], v: List[float]) -> List[float]:
        """Project u onto v."""
        scale = self.dot(u, v) / self.dot(v, v)
        return [scale * vi for vi in v]


# ==================== STOCHASTIC PROCESSES ====================

class StochasticProcesses:
    """
    Random processes and stochastic calculus basics.
    """

    def brownian_motion(self, t: float, dt: float = 0.01,
                        mu: float = 0, sigma: float = 1) -> List[float]:
        """
        Generate Brownian motion path.
        dW = μdt + σ√dt * Z
        """
        n_steps = int(t / dt)
        path = [0.0]

        for _ in range(n_steps):
            dw = mu * dt + sigma * _math.sqrt(dt) * random.gauss(0, 1)
            path.append(path[-1] + dw)

        return path

    def geometric_brownian_motion(self, S0: float, t: float,
                                   mu: float, sigma: float,
                                   dt: float = 0.01) -> List[float]:
        """
        Geometric Brownian Motion (stock price model).
        dS = μS dt + σS dW
        """
        n_steps = int(t / dt)
        path = [S0]

        for _ in range(n_steps):
            S = path[-1]
            dS = S * (mu * dt + sigma * _math.sqrt(dt) * random.gauss(0, 1))
            path.append(S + dS)

        return path

    def ornstein_uhlenbeck(self, x0: float, t: float, theta: float,
                           mu: float, sigma: float,
                           dt: float = 0.01) -> List[float]:
        """
        Ornstein-Uhlenbeck process (mean-reverting).
        dX = θ(μ - X)dt + σdW
        """
        n_steps = int(t / dt)
        path = [x0]

        for _ in range(n_steps):
            x = path[-1]
            dx = theta * (mu - x) * dt + sigma * _math.sqrt(dt) * random.gauss(0, 1)
            path.append(x + dx)

        return path

    def poisson_process(self, t: float, rate: float) -> List[Tuple[float, int]]:
        """
        Generate Poisson process arrivals.
        Returns list of (time, count) tuples.
        """
        arrivals = []
        current_time = 0
        count = 0

        while current_time < t:
            # Inter-arrival time is exponential
            inter_arrival = random.expovariate(rate)
            current_time += inter_arrival
            if current_time < t:
                count += 1
                arrivals.append((current_time, count))

        return arrivals

    def markov_chain_step(self, current_state: int,
                          transition_matrix: List[List[float]]) -> int:
        """Single step in discrete Markov chain."""
        probs = transition_matrix[current_state]
        r = random.random()
        cumsum = 0
        for i, p in enumerate(probs):
            cumsum += p
            if r < cumsum:
                return i
        return len(probs) - 1

    def stationary_distribution(self, P: List[List[float]],
                                n_iter: int = 1000) -> List[float]:
        """Find stationary distribution of Markov chain via iteration."""
        n = len(P)
        pi = [1/n] * n  # Start uniform

        for _ in range(n_iter):
            new_pi = [0.0] * n
            for j in range(n):
                for i in range(n):
                    new_pi[j] += pi[i] * P[i][j]
            pi = new_pi

        return pi


# ==================== TIME SERIES ====================

class TimeSeries:
    """
    Time series analysis and forecasting.
    """

    def autocorrelation(self, x: List[float], lag: int) -> float:
        """Autocorrelation at given lag."""
        n = len(x)
        if lag >= n:
            return 0

        mean = sum(x) / n
        var = sum((xi - mean) ** 2 for xi in x) / n

        if var == 0:
            return 0

        cov = sum((x[i] - mean) * (x[i + lag] - mean)
                  for i in range(n - lag)) / (n - lag)
        return cov / var

    def partial_autocorrelation(self, x: List[float], max_lag: int) -> List[float]:
        """Partial autocorrelation function."""
        pacf = [1.0]  # lag 0 is always 1

        for k in range(1, max_lag + 1):
            # Durbin-Levinson recursion
            acf = [self.autocorrelation(x, i) for i in range(k + 1)]

            if k == 1:
                pacf.append(acf[1])
            else:
                # Solve Yule-Walker equations
                # Simplified approximation
                pacf.append(acf[k])

        return pacf

    def moving_average(self, x: List[float], window: int) -> List[float]:
        """Simple moving average."""
        if window > len(x):
            return []
        return [sum(x[i:i+window]) / window
                for i in range(len(x) - window + 1)]

    def exponential_moving_average(self, x: List[float],
                                    alpha: float = 0.3) -> List[float]:
        """Exponential moving average (EMA)."""
        if not x:
            return []

        ema = [x[0]]
        for i in range(1, len(x)):
            ema.append(alpha * x[i] + (1 - alpha) * ema[-1])
        return ema

    def differencing(self, x: List[float], d: int = 1) -> List[float]:
        """Difference series d times."""
        result = x.copy()
        for _ in range(d):
            result = [result[i] - result[i-1] for i in range(1, len(result))]
        return result

    def adf_statistic(self, x: List[float]) -> float:
        """
        Augmented Dickey-Fuller test statistic (simplified).
        Tests for unit root / stationarity.
        """
        dx = self.differencing(x, 1)
        x_lag = x[:-1]

        # Simple OLS: dx = α + β*x_{t-1} + ε
        n = len(dx)
        mean_dx = sum(dx) / n
        mean_x = sum(x_lag) / n

        # Beta estimate
        num = sum((x_lag[i] - mean_x) * (dx[i] - mean_dx) for i in range(n))
        denom = sum((x_lag[i] - mean_x) ** 2 for i in range(n))

        if denom == 0:
            return 0

        beta = num / denom

        # Standard error (simplified)
        residuals = [dx[i] - mean_dx - beta * (x_lag[i] - mean_x) for i in range(n)]
        sse = sum(r ** 2 for r in residuals)
        se_beta = _math.sqrt(sse / (n - 2) / denom)

        if se_beta == 0:
            return 0

        return beta / se_beta

    def forecast_ar1(self, x: List[float], steps: int) -> List[float]:
        """Simple AR(1) forecast."""
        if len(x) < 2:
            return []

        # Estimate AR(1) coefficient
        x_lag = x[:-1]
        x_cur = x[1:]

        mean_lag = sum(x_lag) / len(x_lag)
        mean_cur = sum(x_cur) / len(x_cur)

        num = sum((x_lag[i] - mean_lag) * (x_cur[i] - mean_cur)
                  for i in range(len(x_lag)))
        denom = sum((x_lag[i] - mean_lag) ** 2 for i in range(len(x_lag)))

        if denom == 0:
            return [x[-1]] * steps

        phi = num / denom
        c = mean_cur - phi * mean_lag

        # Forecast
        forecast = []
        last = x[-1]
        for _ in range(steps):
            next_val = c + phi * last
            forecast.append(next_val)
            last = next_val

        return forecast


# ==================== MONTE CARLO ====================

class MonteCarlo:
    """
    Monte Carlo simulation methods.
    """

    def simulate(self, func: Callable, n_trials: int = 10000) -> Dict:
        """
        Run Monte Carlo simulation.

        Args:
            func: Function that returns a single trial result
            n_trials: Number of trials

        Returns:
            Statistics of results
        """
        results = [func() for _ in range(n_trials)]

        mean = sum(results) / n_trials
        variance = sum((r - mean) ** 2 for r in results) / n_trials

        sorted_results = sorted(results)

        return {
            "mean": mean,
            "std": _math.sqrt(variance),
            "min": min(results),
            "max": max(results),
            "median": sorted_results[n_trials // 2],
            "p5": sorted_results[int(0.05 * n_trials)],
            "p95": sorted_results[int(0.95 * n_trials)],
            "n_trials": n_trials
        }

    def integrate_mc(self, f: Callable, bounds: List[Tuple[float, float]],
                     n_samples: int = 100000) -> Dict:
        """
        Monte Carlo integration.

        Args:
            f: Function to integrate
            bounds: List of (min, max) for each dimension
            n_samples: Number of samples

        Returns:
            {"estimate": float, "std_error": float}
        """
        dim = len(bounds)
        volume = 1
        for a, b in bounds:
            volume *= (b - a)

        samples = []
        for _ in range(n_samples):
            point = [random.uniform(a, b) for a, b in bounds]
            samples.append(f(point) if dim > 1 else f(point[0]))

        mean = sum(samples) / n_samples
        variance = sum((s - mean) ** 2 for s in samples) / n_samples

        estimate = volume * mean
        std_error = volume * _math.sqrt(variance / n_samples)

        return {
            "estimate": estimate,
            "std_error": std_error,
            "volume": volume,
            "n_samples": n_samples
        }

    def importance_sampling(self, f: Callable, p: Callable, q: Callable,
                            q_sampler: Callable, n_samples: int = 10000) -> float:
        """
        Importance sampling for E_p[f(X)].

        Args:
            f: Function to evaluate
            p: Target density (up to normalization)
            q: Proposal density
            q_sampler: Function to sample from q
            n_samples: Number of samples
        """
        weights = []
        values = []

        for _ in range(n_samples):
            x = q_sampler()
            w = p(x) / q(x) if q(x) > 0 else 0
            weights.append(w)
            values.append(f(x) * w)

        total_weight = sum(weights)
        if total_weight == 0:
            return 0

        return sum(values) / total_weight

    def bootstrap(self, data: List[float], statistic: Callable,
                  n_bootstrap: int = 1000) -> Dict:
        """
        Bootstrap resampling for confidence intervals.

        Args:
            data: Original data
            statistic: Function to compute statistic (e.g., mean)
            n_bootstrap: Number of bootstrap samples
        """
        n = len(data)
        bootstrap_stats = []

        for _ in range(n_bootstrap):
            sample = [random.choice(data) for _ in range(n)]
            bootstrap_stats.append(statistic(sample))

        sorted_stats = sorted(bootstrap_stats)

        return {
            "estimate": statistic(data),
            "std_error": _math.sqrt(sum((s - sum(bootstrap_stats)/n_bootstrap)**2
                                         for s in bootstrap_stats) / n_bootstrap),
            "ci_95": (sorted_stats[int(0.025 * n_bootstrap)],
                      sorted_stats[int(0.975 * n_bootstrap)])
        }


# ==================== OPTIMIZATION ====================

class Optimization:
    """
    Numerical optimization algorithms.
    """

    def gradient_descent(self, f: Callable, grad_f: Callable,
                         x0: List[float], lr: float = 0.01,
                         max_iter: int = 1000, tol: float = 1e-6) -> Dict:
        """
        Gradient descent optimization.

        Args:
            f: Objective function
            grad_f: Gradient function
            x0: Initial point
            lr: Learning rate
            max_iter: Maximum iterations
            tol: Convergence tolerance
        """
        x = x0.copy()
        history = [f(x)]

        for i in range(max_iter):
            grad = grad_f(x)
            x = [xi - lr * gi for xi, gi in zip(x, grad)]

            new_val = f(x)
            history.append(new_val)

            if abs(history[-1] - history[-2]) < tol:
                break

        return {
            "x": x,
            "f_min": f(x),
            "iterations": i + 1,
            "converged": abs(history[-1] - history[-2]) < tol
        }

    def newton_method(self, f: Callable, x0: float,
                      max_iter: int = 100, tol: float = 1e-8) -> Dict:
        """
        Newton's method for root finding.
        x_{n+1} = x_n - f(x_n)/f'(x_n)
        """
        x = x0
        calc = Calculus()

        for i in range(max_iter):
            fx = f(x)
            if abs(fx) < tol:
                return {"root": x, "iterations": i + 1, "converged": True}

            fpx = calc.derivative(f, x)
            if abs(fpx) < EPSILON:
                break

            x = x - fx / fpx

        return {"root": x, "iterations": max_iter, "converged": False}

    def bisection(self, f: Callable, a: float, b: float,
                  tol: float = 1e-8, max_iter: int = 100) -> Dict:
        """Bisection method for root finding."""
        if f(a) * f(b) > 0:
            return {"error": "f(a) and f(b) must have opposite signs"}

        for i in range(max_iter):
            c = (a + b) / 2
            fc = f(c)

            if abs(fc) < tol or (b - a) / 2 < tol:
                return {"root": c, "iterations": i + 1, "converged": True}

            if f(a) * fc < 0:
                b = c
            else:
                a = c

        return {"root": (a + b) / 2, "iterations": max_iter, "converged": False}

    def golden_section(self, f: Callable, a: float, b: float,
                       tol: float = 1e-6, max_iter: int = 100) -> Dict:
        """Golden section search for 1D minimization."""
        phi = (1 + _math.sqrt(5)) / 2
        resphi = 2 - phi

        x1 = a + resphi * (b - a)
        x2 = b - resphi * (b - a)
        f1 = f(x1)
        f2 = f(x2)

        for i in range(max_iter):
            if b - a < tol:
                break

            if f1 < f2:
                b = x2
                x2 = x1
                f2 = f1
                x1 = a + resphi * (b - a)
                f1 = f(x1)
            else:
                a = x1
                x1 = x2
                f1 = f2
                x2 = b - resphi * (b - a)
                f2 = f(x2)

        x_min = (a + b) / 2
        return {"x_min": x_min, "f_min": f(x_min), "iterations": i + 1}

    def simulated_annealing(self, f: Callable, x0: List[float],
                            T0: float = 100, cooling: float = 0.99,
                            max_iter: int = 10000) -> Dict:
        """Simulated annealing global optimization."""
        x = x0.copy()
        f_x = f(x)
        best_x = x.copy()
        best_f = f_x
        T = T0

        for i in range(max_iter):
            # Random neighbor
            x_new = [xi + random.gauss(0, T) for xi in x]
            f_new = f(x_new)

            # Accept or reject
            delta = f_new - f_x
            if delta < 0 or random.random() < _math.exp(-delta / T):
                x = x_new
                f_x = f_new

                if f_x < best_f:
                    best_x = x.copy()
                    best_f = f_x

            T *= cooling

        return {"x": best_x, "f_min": best_f, "iterations": max_iter}


# ==================== INFORMATION THEORY ====================

class InformationTheory:
    """
    Information-theoretic measures.
    """

    def entropy(self, probs: List[float]) -> float:
        """Shannon entropy H(X) = -Σ p(x) log p(x)"""
        return -sum(p * _math.log2(p) if p > 0 else 0 for p in probs)

    def cross_entropy(self, p: List[float], q: List[float]) -> float:
        """Cross entropy H(p,q) = -Σ p(x) log q(x)"""
        return -sum(pi * _math.log2(qi) if pi > 0 and qi > 0 else 0
                    for pi, qi in zip(p, q))

    def kl_divergence(self, p: List[float], q: List[float]) -> float:
        """KL divergence D_KL(P||Q) = Σ p(x) log(p(x)/q(x))"""
        return sum(pi * _math.log2(pi / qi) if pi > 0 and qi > 0 else 0
                   for pi, qi in zip(p, q))

    def mutual_information(self, joint: List[List[float]]) -> float:
        """
        Mutual information I(X;Y) from joint distribution.
        I(X;Y) = H(X) + H(Y) - H(X,Y)
        """
        # Marginals
        p_x = [sum(row) for row in joint]
        p_y = [sum(joint[i][j] for i in range(len(joint)))
               for j in range(len(joint[0]))]

        h_x = self.entropy(p_x)
        h_y = self.entropy(p_y)
        h_xy = self.entropy([p for row in joint for p in row])

        return h_x + h_y - h_xy

    def conditional_entropy(self, joint: List[List[float]]) -> float:
        """Conditional entropy H(Y|X) = H(X,Y) - H(X)"""
        p_x = [sum(row) for row in joint]
        h_x = self.entropy(p_x)
        h_xy = self.entropy([p for row in joint for p in row])
        return h_xy - h_x

    def bits_to_represent(self, n_outcomes: int) -> float:
        """Minimum bits needed to represent n outcomes."""
        if n_outcomes <= 1:
            return 0
        return _math.log2(n_outcomes)


# ==================== GAME THEORY ====================

class GameTheory:
    """
    Basic game theory calculations.
    """

    def nash_equilibrium_2x2(self, payoff_A: List[List[float]],
                             payoff_B: List[List[float]]) -> Dict:
        """
        Find mixed strategy Nash equilibrium for 2x2 game.

        Args:
            payoff_A: 2x2 payoff matrix for player A
            payoff_B: 2x2 payoff matrix for player B
        """
        # Player B's mixing probability (makes A indifferent)
        # A plays row 0: payoff_A[0][0]*q + payoff_A[0][1]*(1-q)
        # A plays row 1: payoff_A[1][0]*q + payoff_A[1][1]*(1-q)
        # Set equal and solve for q

        a = payoff_A[0][0] - payoff_A[0][1] - payoff_A[1][0] + payoff_A[1][1]
        if abs(a) < EPSILON:
            q = 0.5  # Degenerate case
        else:
            q = (payoff_A[1][1] - payoff_A[0][1]) / a
            q = max(0, min(1, q))

        # Player A's mixing probability (makes B indifferent)
        b = payoff_B[0][0] - payoff_B[1][0] - payoff_B[0][1] + payoff_B[1][1]
        if abs(b) < EPSILON:
            p = 0.5
        else:
            p = (payoff_B[1][1] - payoff_B[1][0]) / b
            p = max(0, min(1, p))

        # Expected payoffs at equilibrium
        exp_A = p * (q * payoff_A[0][0] + (1-q) * payoff_A[0][1]) + \
                (1-p) * (q * payoff_A[1][0] + (1-q) * payoff_A[1][1])
        exp_B = p * (q * payoff_B[0][0] + (1-q) * payoff_B[0][1]) + \
                (1-p) * (q * payoff_B[1][0] + (1-q) * payoff_B[1][1])

        return {
            "player_A_mix": [p, 1-p],
            "player_B_mix": [q, 1-q],
            "expected_payoff_A": exp_A,
            "expected_payoff_B": exp_B
        }

    def minimax(self, payoff: List[List[float]]) -> Dict:
        """
        Minimax values for zero-sum game.
        """
        # Row player's maximin
        row_mins = [min(row) for row in payoff]
        maximin = max(row_mins)
        maximin_row = row_mins.index(maximin)

        # Column player's minimax
        n_cols = len(payoff[0])
        col_maxs = [max(payoff[i][j] for i in range(len(payoff)))
                    for j in range(n_cols)]
        minimax = min(col_maxs)
        minimax_col = col_maxs.index(minimax)

        return {
            "maximin": maximin,
            "minimax": minimax,
            "saddle_point": maximin == minimax,
            "maximin_strategy": maximin_row,
            "minimax_strategy": minimax_col
        }

    def dominated_strategies(self, payoff: List[List[float]]) -> Dict:
        """Find strictly dominated strategies."""
        n_rows = len(payoff)
        n_cols = len(payoff[0])

        dominated_rows = []
        for i in range(n_rows):
            for j in range(n_rows):
                if i != j:
                    if all(payoff[j][k] > payoff[i][k] for k in range(n_cols)):
                        dominated_rows.append(i)
                        break

        dominated_cols = []
        for i in range(n_cols):
            for j in range(n_cols):
                if i != j:
                    if all(payoff[k][j] < payoff[k][i] for k in range(n_rows)):
                        dominated_cols.append(i)
                        break

        return {
            "dominated_rows": dominated_rows,
            "dominated_cols": dominated_cols
        }


# ==================== NUMERICAL METHODS ====================

class NumericalMethods:
    """
    General numerical computation utilities.
    """

    def interpolate_linear(self, x: float, x_points: List[float],
                           y_points: List[float]) -> float:
        """Linear interpolation."""
        if x <= x_points[0]:
            return y_points[0]
        if x >= x_points[-1]:
            return y_points[-1]

        for i in range(len(x_points) - 1):
            if x_points[i] <= x <= x_points[i + 1]:
                t = (x - x_points[i]) / (x_points[i + 1] - x_points[i])
                return y_points[i] + t * (y_points[i + 1] - y_points[i])

        return y_points[-1]

    def interpolate_cubic(self, x: float, x_points: List[float],
                          y_points: List[float]) -> float:
        """Cubic spline interpolation (simplified)."""
        n = len(x_points)
        if n < 4:
            return self.interpolate_linear(x, x_points, y_points)

        # Find interval
        idx = 0
        for i in range(n - 1):
            if x_points[i] <= x <= x_points[i + 1]:
                idx = i
                break

        # Lagrange 4-point interpolation
        start = max(0, idx - 1)
        end = min(n, start + 4)

        result = 0
        for i in range(start, end):
            term = y_points[i]
            for j in range(start, end):
                if i != j:
                    term *= (x - x_points[j]) / (x_points[i] - x_points[j])
            result += term

        return result

    def finite_difference(self, f: Callable, x: float,
                          order: int = 1, h: float = 1e-5) -> float:
        """Finite difference derivative approximation."""
        if order == 1:
            return (f(x + h) - f(x - h)) / (2 * h)
        elif order == 2:
            return (f(x + h) - 2*f(x) + f(x - h)) / (h**2)
        elif order == 3:
            return (f(x + 2*h) - 2*f(x + h) + 2*f(x - h) - f(x - 2*h)) / (2*h**3)
        else:
            raise ValueError("Order must be 1, 2, or 3")

    def runge_kutta_4(self, f: Callable, y0: float, t0: float,
                      t_end: float, dt: float) -> List[Tuple[float, float]]:
        """
        4th order Runge-Kutta for ODE: dy/dt = f(t, y).
        """
        t = t0
        y = y0
        trajectory = [(t, y)]

        while t < t_end:
            k1 = dt * f(t, y)
            k2 = dt * f(t + dt/2, y + k1/2)
            k3 = dt * f(t + dt/2, y + k2/2)
            k4 = dt * f(t + dt, y + k3)

            y = y + (k1 + 2*k2 + 2*k3 + k4) / 6
            t = t + dt
            trajectory.append((t, y))

        return trajectory

    def fft_magnitude(self, signal: List[float]) -> List[float]:
        """
        Simple DFT magnitude (not optimized FFT).
        """
        n = len(signal)
        magnitudes = []

        for k in range(n // 2):
            real = sum(signal[j] * _math.cos(2 * PI * k * j / n) for j in range(n))
            imag = -sum(signal[j] * _math.sin(2 * PI * k * j / n) for j in range(n))
            magnitudes.append(_math.sqrt(real**2 + imag**2) / n)

        return magnitudes


# ==================== SINGLETON INSTANCES ====================

prob = ProbabilityTheory()
calc = Calculus()
linalg = LinearAlgebra()
stoch = StochasticProcesses()
ts = TimeSeries()
mc = MonteCarlo()
opt = Optimization()
info = InformationTheory()
game = GameTheory()
num = NumericalMethods()


# ==================== CLI ====================

def main():
    import sys
    import json

    print("""
Theoretical Mathematics Engine
==============================

Available modules:
  prob    - Probability theory (Bayes, distributions)
  calc    - Calculus (derivatives, integrals)
  linalg  - Linear algebra (matrices, eigenvalues)
  stoch   - Stochastic processes (Brownian motion, Markov)
  ts      - Time series (ARIMA, forecasting)
  mc      - Monte Carlo (simulation, integration)
  opt     - Optimization (gradient descent, Newton)
  info    - Information theory (entropy, KL divergence)
  game    - Game theory (Nash equilibrium, minimax)
  num     - Numerical methods (interpolation, RK4)

Example:
  from executor.theoretical_math import prob, mc, opt

  # Bayesian update
  prob.bayes_update(prior=0.5, likelihood=0.9, evidence=0.7)

  # Monte Carlo
  mc.simulate(lambda: random.gauss(0, 1), n_trials=10000)

  # Optimization
  opt.gradient_descent(f, grad_f, x0=[0, 0], lr=0.01)
""")


if __name__ == "__main__":
    main()
