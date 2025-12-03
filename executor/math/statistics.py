#!/usr/bin/env python3
"""
Statistics - Bayesian, Frequentist, and Multivariate Statistics

Covers:
- Descriptive statistics
- Probability distributions
- Hypothesis testing
- Confidence intervals
- Bayesian inference
- Regression analysis
- Multivariate statistics
- Non-parametric tests
- Time series statistics

USAGE:
    from executor.math.statistics import stats

    stats.mean([1, 2, 3, 4, 5])  # 3.0
    stats.t_test(sample1, sample2)
    stats.bayesian_update(prior, likelihood)
"""

import math as _math
import random
from typing import List, Tuple, Dict, Optional, Callable
from functools import lru_cache


PI = _math.pi


class Statistics:
    """Comprehensive statistical analysis."""

    # ==================== DESCRIPTIVE STATISTICS ====================

    def mean(self, data: List[float]) -> float:
        """Arithmetic mean."""
        if not data:
            return 0
        return sum(data) / len(data)

    def geometric_mean(self, data: List[float]) -> float:
        """Geometric mean (for positive data)."""
        if not data or any(x <= 0 for x in data):
            return 0
        return _math.exp(sum(_math.log(x) for x in data) / len(data))

    def harmonic_mean(self, data: List[float]) -> float:
        """Harmonic mean (for positive data)."""
        if not data or any(x <= 0 for x in data):
            return 0
        return len(data) / sum(1/x for x in data)

    def weighted_mean(self, data: List[float], weights: List[float]) -> float:
        """Weighted arithmetic mean."""
        if not data or not weights:
            return 0
        return sum(d * w for d, w in zip(data, weights)) / sum(weights)

    def median(self, data: List[float]) -> float:
        """Median value."""
        if not data:
            return 0
        sorted_data = sorted(data)
        n = len(sorted_data)
        mid = n // 2
        if n % 2 == 0:
            return (sorted_data[mid-1] + sorted_data[mid]) / 2
        return sorted_data[mid]

    def mode(self, data: List[float]) -> List[float]:
        """Mode(s) - most frequent value(s)."""
        if not data:
            return []
        counts = {}
        for x in data:
            counts[x] = counts.get(x, 0) + 1
        max_count = max(counts.values())
        return [x for x, c in counts.items() if c == max_count]

    def variance(self, data: List[float], sample: bool = True) -> float:
        """Variance (sample or population)."""
        if len(data) < 2:
            return 0
        m = self.mean(data)
        ss = sum((x - m)**2 for x in data)
        return ss / (len(data) - 1) if sample else ss / len(data)

    def std(self, data: List[float], sample: bool = True) -> float:
        """Standard deviation."""
        return _math.sqrt(self.variance(data, sample))

    def sem(self, data: List[float]) -> float:
        """Standard error of the mean."""
        if len(data) < 2:
            return 0
        return self.std(data) / _math.sqrt(len(data))

    def cv(self, data: List[float]) -> float:
        """Coefficient of variation (CV = std/mean)."""
        m = self.mean(data)
        if m == 0:
            return 0
        return self.std(data) / abs(m)

    def percentile(self, data: List[float], p: float) -> float:
        """p-th percentile (0-100)."""
        if not data:
            return 0
        sorted_data = sorted(data)
        k = (p / 100) * (len(data) - 1)
        f = _math.floor(k)
        c = _math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)

    def quartiles(self, data: List[float]) -> Tuple[float, float, float]:
        """Q1, Q2 (median), Q3."""
        return (
            self.percentile(data, 25),
            self.percentile(data, 50),
            self.percentile(data, 75)
        )

    def iqr(self, data: List[float]) -> float:
        """Interquartile range."""
        q1, _, q3 = self.quartiles(data)
        return q3 - q1

    def range_stat(self, data: List[float]) -> float:
        """Range (max - min)."""
        if not data:
            return 0
        return max(data) - min(data)

    def skewness(self, data: List[float]) -> float:
        """Fisher's skewness."""
        n = len(data)
        if n < 3:
            return 0
        m = self.mean(data)
        s = self.std(data, sample=False)
        if s == 0:
            return 0
        return sum(((x - m) / s)**3 for x in data) * n / ((n-1) * (n-2))

    def kurtosis(self, data: List[float]) -> float:
        """Excess kurtosis."""
        n = len(data)
        if n < 4:
            return 0
        m = self.mean(data)
        s = self.std(data, sample=False)
        if s == 0:
            return 0
        m4 = sum(((x - m) / s)**4 for x in data) / n
        return m4 - 3

    def covariance(self, x: List[float], y: List[float], sample: bool = True) -> float:
        """Covariance between x and y."""
        n = len(x)
        if n != len(y) or n < 2:
            return 0
        mx, my = self.mean(x), self.mean(y)
        cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
        return cov / (n - 1) if sample else cov / n

    def correlation(self, x: List[float], y: List[float]) -> float:
        """Pearson correlation coefficient."""
        cov = self.covariance(x, y)
        sx, sy = self.std(x), self.std(y)
        if sx == 0 or sy == 0:
            return 0
        return cov / (sx * sy)

    def spearman_correlation(self, x: List[float], y: List[float]) -> float:
        """Spearman rank correlation."""
        n = len(x)
        if n != len(y):
            return 0

        def rank(data):
            sorted_idx = sorted(range(len(data)), key=lambda i: data[i])
            ranks = [0] * len(data)
            for rank_val, idx in enumerate(sorted_idx, 1):
                ranks[idx] = rank_val
            return ranks

        rx, ry = rank(x), rank(y)
        return self.correlation(rx, ry)

    def kendall_tau(self, x: List[float], y: List[float]) -> float:
        """Kendall's tau correlation."""
        n = len(x)
        if n != len(y) or n < 2:
            return 0

        concordant = 0
        discordant = 0

        for i in range(n):
            for j in range(i + 1, n):
                x_sign = (x[i] - x[j]) > 0
                y_sign = (y[i] - y[j]) > 0
                if x[i] != x[j] and y[i] != y[j]:
                    if x_sign == y_sign:
                        concordant += 1
                    else:
                        discordant += 1

        denom = n * (n - 1) / 2
        return (concordant - discordant) / denom if denom > 0 else 0

    # ==================== DISTRIBUTIONS ====================

    def _norm_pdf(self, x: float, mu: float = 0, sigma: float = 1) -> float:
        """Normal PDF."""
        return _math.exp(-0.5 * ((x - mu) / sigma)**2) / (sigma * _math.sqrt(2 * PI))

    def _norm_cdf(self, x: float, mu: float = 0, sigma: float = 1) -> float:
        """Normal CDF."""
        z = (x - mu) / sigma
        return 0.5 * (1 + _math.erf(z / _math.sqrt(2)))

    def _norm_ppf(self, p: float) -> float:
        """Standard normal quantile (inverse CDF)."""
        if p <= 0:
            return float('-inf')
        if p >= 1:
            return float('inf')

        # Approximation
        a = [0, -3.969683028665376e+01, 2.209460984245205e+02,
             -2.759285104469687e+02, 1.383577518672690e+02,
             -3.066479806614716e+01, 2.506628277459239e+00]
        b = [0, -5.447609879822406e+01, 1.615858368580409e+02,
             -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]

        if p < 0.5:
            q = _math.sqrt(-2 * _math.log(p))
            return (((((a[1]*q+a[2])*q+a[3])*q+a[4])*q+a[5])*q+a[6]) / \
                   ((((b[1]*q+b[2])*q+b[3])*q+b[4])*q+1)
        else:
            q = _math.sqrt(-2 * _math.log(1 - p))
            return -(((((a[1]*q+a[2])*q+a[3])*q+a[4])*q+a[5])*q+a[6]) / \
                   ((((b[1]*q+b[2])*q+b[3])*q+b[4])*q+1)

    def _t_cdf(self, t: float, df: int) -> float:
        """Student's t CDF (approximation)."""
        x = df / (df + t * t)
        return 1 - 0.5 * self._beta_inc(df/2, 0.5, x)

    def _beta_inc(self, a: float, b: float, x: float) -> float:
        """Regularized incomplete beta function."""
        if x == 0:
            return 0
        if x == 1:
            return 1

        # Continued fraction approximation
        max_iter = 100
        tol = 1e-10

        qab = a + b
        qap = a + 1
        qam = a - 1
        c = 1
        d = 1 - qab * x / qap
        if abs(d) < 1e-30:
            d = 1e-30
        d = 1 / d
        h = d

        for m in range(1, max_iter + 1):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1 / d
            h *= d * c

            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30
            c = 1 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1 / d
            delta = d * c
            h *= delta

            if abs(delta - 1) < tol:
                break

        return h * x**a * (1-x)**b / (a * self._beta(a, b))

    def _beta(self, a: float, b: float) -> float:
        """Beta function B(a,b)."""
        return _math.gamma(a) * _math.gamma(b) / _math.gamma(a + b)

    def _chi2_cdf(self, x: float, df: int) -> float:
        """Chi-squared CDF."""
        if x <= 0:
            return 0
        return self._gamma_inc(df/2, x/2) / _math.gamma(df/2)

    def _gamma_inc(self, a: float, x: float) -> float:
        """Lower incomplete gamma function."""
        if x == 0:
            return 0

        # Series expansion
        result = 0
        term = 1 / a
        result += term

        for n in range(1, 100):
            term *= x / (a + n)
            result += term
            if abs(term) < 1e-10:
                break

        return result * _math.exp(-x + a * _math.log(x))

    # ==================== HYPOTHESIS TESTING ====================

    def z_test(self, sample: List[float], mu0: float, sigma: float) -> Dict:
        """One-sample z-test."""
        n = len(sample)
        x_bar = self.mean(sample)
        z = (x_bar - mu0) / (sigma / _math.sqrt(n))
        p_value = 2 * (1 - self._norm_cdf(abs(z)))

        return {
            "z_statistic": z,
            "p_value": p_value,
            "sample_mean": x_bar,
            "reject_h0_05": p_value < 0.05
        }

    def t_test_one_sample(self, sample: List[float], mu0: float) -> Dict:
        """One-sample t-test."""
        n = len(sample)
        x_bar = self.mean(sample)
        s = self.std(sample)
        t = (x_bar - mu0) / (s / _math.sqrt(n))
        df = n - 1

        # Two-tailed p-value
        p_value = 2 * (1 - self._t_cdf(abs(t), df))

        return {
            "t_statistic": t,
            "df": df,
            "p_value": p_value,
            "sample_mean": x_bar,
            "reject_h0_05": p_value < 0.05
        }

    def t_test_two_sample(self, sample1: List[float], sample2: List[float],
                          equal_var: bool = True) -> Dict:
        """Two-sample t-test."""
        n1, n2 = len(sample1), len(sample2)
        x1, x2 = self.mean(sample1), self.mean(sample2)
        s1, s2 = self.std(sample1), self.std(sample2)

        if equal_var:
            # Pooled variance
            sp = _math.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / (n1 + n2 - 2))
            se = sp * _math.sqrt(1/n1 + 1/n2)
            df = n1 + n2 - 2
        else:
            # Welch's t-test
            se = _math.sqrt(s1**2/n1 + s2**2/n2)
            df = (s1**2/n1 + s2**2/n2)**2 / \
                 ((s1**2/n1)**2/(n1-1) + (s2**2/n2)**2/(n2-1))

        t = (x1 - x2) / se if se > 0 else 0
        p_value = 2 * (1 - self._t_cdf(abs(t), int(df)))

        return {
            "t_statistic": t,
            "df": df,
            "p_value": p_value,
            "mean_diff": x1 - x2,
            "reject_h0_05": p_value < 0.05
        }

    def paired_t_test(self, sample1: List[float], sample2: List[float]) -> Dict:
        """Paired t-test."""
        if len(sample1) != len(sample2):
            raise ValueError("Samples must have equal length")

        differences = [x1 - x2 for x1, x2 in zip(sample1, sample2)]
        return self.t_test_one_sample(differences, 0)

    def chi_square_test(self, observed: List[float], expected: List[float] = None) -> Dict:
        """Chi-square goodness of fit test."""
        n = len(observed)
        if expected is None:
            expected = [sum(observed) / n] * n

        chi2 = sum((o - e)**2 / e for o, e in zip(observed, expected) if e > 0)
        df = n - 1
        p_value = 1 - self._chi2_cdf(chi2, df)

        return {
            "chi2_statistic": chi2,
            "df": df,
            "p_value": p_value,
            "reject_h0_05": p_value < 0.05
        }

    def anova_one_way(self, *groups: List[float]) -> Dict:
        """One-way ANOVA."""
        k = len(groups)  # Number of groups
        n = sum(len(g) for g in groups)  # Total observations

        grand_mean = sum(sum(g) for g in groups) / n

        # Between-group sum of squares
        ss_between = sum(len(g) * (self.mean(g) - grand_mean)**2 for g in groups)

        # Within-group sum of squares
        ss_within = sum(sum((x - self.mean(g))**2 for x in g) for g in groups)

        df_between = k - 1
        df_within = n - k

        ms_between = ss_between / df_between
        ms_within = ss_within / df_within

        f_stat = ms_between / ms_within if ms_within > 0 else 0

        # F distribution p-value (approximation)
        p_value = 1 - self._f_cdf(f_stat, df_between, df_within)

        return {
            "f_statistic": f_stat,
            "df_between": df_between,
            "df_within": df_within,
            "p_value": p_value,
            "reject_h0_05": p_value < 0.05
        }

    def _f_cdf(self, x: float, d1: int, d2: int) -> float:
        """F distribution CDF."""
        if x <= 0:
            return 0
        return self._beta_inc(d1/2, d2/2, d1*x / (d1*x + d2))

    # ==================== CONFIDENCE INTERVALS ====================

    def ci_mean(self, data: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """Confidence interval for mean."""
        n = len(data)
        x_bar = self.mean(data)
        se = self.sem(data)
        z = self._norm_ppf(1 - (1 - confidence) / 2)
        margin = z * se
        return (x_bar - margin, x_bar + margin)

    def ci_proportion(self, successes: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
        """Confidence interval for proportion (Wilson score)."""
        p_hat = successes / n
        z = self._norm_ppf(1 - (1 - confidence) / 2)
        z2 = z * z

        denom = 1 + z2/n
        center = p_hat + z2/(2*n)
        margin = z * _math.sqrt(p_hat*(1-p_hat)/n + z2/(4*n*n))

        return ((center - margin) / denom, (center + margin) / denom)

    def ci_variance(self, data: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """Confidence interval for variance (chi-square)."""
        n = len(data)
        s2 = self.variance(data)
        df = n - 1
        alpha = 1 - confidence

        # Chi-square quantiles (approximation using Wilson-Hilferty)
        def chi2_ppf(p, df):
            z = self._norm_ppf(p)
            return df * (1 - 2/(9*df) + z * _math.sqrt(2/(9*df)))**3

        chi2_lower = chi2_ppf(alpha/2, df)
        chi2_upper = chi2_ppf(1 - alpha/2, df)

        return (df * s2 / chi2_upper, df * s2 / chi2_lower)

    # ==================== BAYESIAN INFERENCE ====================

    def bayesian_update(self, prior: float, likelihood: float, evidence: float) -> float:
        """Bayesian posterior: P(H|E) = P(E|H)P(H)/P(E)."""
        if evidence == 0:
            return 0
        return (likelihood * prior) / evidence

    def bayesian_update_beta(self, alpha: float, beta: float,
                             successes: int, failures: int) -> Tuple[float, float]:
        """Update Beta prior with binomial data."""
        return (alpha + successes, beta + failures)

    def beta_mean(self, alpha: float, beta: float) -> float:
        """Mean of Beta distribution."""
        return alpha / (alpha + beta)

    def beta_variance(self, alpha: float, beta: float) -> float:
        """Variance of Beta distribution."""
        return (alpha * beta) / ((alpha + beta)**2 * (alpha + beta + 1))

    def credible_interval(self, alpha: float, beta: float,
                          probability: float = 0.95) -> Tuple[float, float]:
        """Credible interval for Beta distribution."""
        # Using quantile approximation
        from scipy.stats import beta as beta_dist
        try:
            lower = beta_dist.ppf((1 - probability) / 2, alpha, beta)
            upper = beta_dist.ppf(1 - (1 - probability) / 2, alpha, beta)
            return (lower, upper)
        except:
            # Fallback using normal approximation
            mean = self.beta_mean(alpha, beta)
            std = _math.sqrt(self.beta_variance(alpha, beta))
            z = self._norm_ppf(1 - (1 - probability) / 2)
            return (mean - z * std, mean + z * std)

    def bayes_factor(self, likelihood_h1: float, likelihood_h0: float) -> float:
        """Bayes factor: evidence for H1 vs H0."""
        if likelihood_h0 == 0:
            return float('inf')
        return likelihood_h1 / likelihood_h0

    # ==================== REGRESSION ====================

    def linear_regression(self, x: List[float], y: List[float]) -> Dict:
        """Simple linear regression: y = a + bx."""
        n = len(x)
        if n != len(y) or n < 2:
            return {}

        x_bar, y_bar = self.mean(x), self.mean(y)

        ss_xy = sum((xi - x_bar) * (yi - y_bar) for xi, yi in zip(x, y))
        ss_xx = sum((xi - x_bar)**2 for xi in x)

        if ss_xx == 0:
            return {"error": "No variance in x"}

        b = ss_xy / ss_xx
        a = y_bar - b * x_bar

        # Predictions and residuals
        y_pred = [a + b * xi for xi in x]
        residuals = [yi - ypi for yi, ypi in zip(y, y_pred)]

        # R-squared
        ss_res = sum(r**2 for r in residuals)
        ss_tot = sum((yi - y_bar)**2 for yi in y)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # Standard error of estimate
        se = _math.sqrt(ss_res / (n - 2)) if n > 2 else 0

        return {
            "intercept": a,
            "slope": b,
            "r_squared": r_squared,
            "std_error": se,
            "predictions": y_pred,
            "residuals": residuals
        }

    def multiple_regression(self, X: List[List[float]], y: List[float]) -> Dict:
        """Multiple linear regression: y = Xβ + ε."""
        n = len(y)
        p = len(X[0]) if X else 0

        if n < p + 1:
            return {"error": "Not enough observations"}

        # Add intercept column
        X_aug = [[1.0] + row for row in X]

        # Normal equations: β = (X'X)^(-1) X'y
        XtX = [[sum(X_aug[k][i] * X_aug[k][j] for k in range(n))
                for j in range(p + 1)] for i in range(p + 1)]
        Xty = [sum(X_aug[k][i] * y[k] for k in range(n)) for i in range(p + 1)]

        # Solve using Gaussian elimination
        beta = self._solve_linear_system(XtX, Xty)

        if beta is None:
            return {"error": "Singular matrix"}

        # Predictions and residuals
        y_pred = [sum(X_aug[i][j] * beta[j] for j in range(p + 1)) for i in range(n)]
        residuals = [yi - ypi for yi, ypi in zip(y, y_pred)]

        # R-squared
        y_bar = self.mean(y)
        ss_res = sum(r**2 for r in residuals)
        ss_tot = sum((yi - y_bar)**2 for yi in y)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        return {
            "coefficients": beta,
            "r_squared": r_squared,
            "predictions": y_pred,
            "residuals": residuals
        }

    def _solve_linear_system(self, A: List[List[float]], b: List[float]) -> Optional[List[float]]:
        """Solve Ax = b using Gaussian elimination."""
        n = len(A)
        # Augmented matrix
        M = [row[:] + [bi] for row, bi in zip(A, b)]

        # Forward elimination
        for col in range(n):
            # Pivot
            max_row = max(range(col, n), key=lambda r: abs(M[r][col]))
            M[col], M[max_row] = M[max_row], M[col]

            if abs(M[col][col]) < 1e-10:
                return None

            for row in range(col + 1, n):
                factor = M[row][col] / M[col][col]
                for j in range(col, n + 1):
                    M[row][j] -= factor * M[col][j]

        # Back substitution
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]

        return x


# Singleton instance
stats = Statistics()
