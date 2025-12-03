#!/usr/bin/env python3
"""
Mathematical Analysis - Real, Complex, and Functional Analysis

Covers:
- Real analysis (limits, series, convergence)
- Complex analysis (complex functions, contour integration)
- Functional analysis (norms, operators, Hilbert spaces)
- Fourier analysis (transforms, series)
- Special functions (Gamma, Beta, Bessel)
- Differential equations
- Measure theory basics

USAGE:
    from executor.math.analysis import analysis

    analysis.limit(lambda x: math.sin(x)/x, 0)  # 1.0
    analysis.complex_exp(1 + 2j)
    analysis.fourier_transform(signal, sample_rate)
"""

import math as _math
import cmath as _cmath
from typing import List, Tuple, Callable, Optional, Union
from functools import lru_cache


# Constants
PI = _math.pi
E = _math.e
EULER_GAMMA = 0.5772156649015329  # Euler-Mascheroni constant


class Analysis:
    """Comprehensive mathematical analysis."""

    # ==================== REAL ANALYSIS ====================

    def limit(self, f: Callable, x: float, direction: str = 'both',
              h: float = 1e-8, tolerance: float = 1e-10) -> Optional[float]:
        """
        Numerical limit of f(x) as x approaches given value.
        direction: 'left', 'right', or 'both'
        """
        try:
            if direction == 'left':
                values = [f(x - h * (0.1 ** i)) for i in range(10)]
            elif direction == 'right':
                values = [f(x + h * (0.1 ** i)) for i in range(10)]
            else:
                left = [f(x - h * (0.1 ** i)) for i in range(5)]
                right = [f(x + h * (0.1 ** i)) for i in range(5)]
                if abs(left[-1] - right[-1]) > tolerance:
                    return None  # Limit doesn't exist
                values = left + right

            return values[-1]
        except:
            return None

    def derivative(self, f: Callable, x: float, h: float = 1e-8) -> float:
        """Numerical derivative using central difference."""
        return (f(x + h) - f(x - h)) / (2 * h)

    def nth_derivative(self, f: Callable, x: float, n: int, h: float = 1e-5) -> float:
        """Nth derivative using recursive central difference."""
        if n == 0:
            return f(x)
        if n == 1:
            return self.derivative(f, x, h)

        def f_prime(t):
            return self.derivative(f, t, h)
        return self.nth_derivative(f_prime, x, n - 1, h * 2)

    def partial_derivative(self, f: Callable, x: List[float], var_idx: int, h: float = 1e-8) -> float:
        """Partial derivative with respect to variable at index var_idx."""
        x_plus = x.copy()
        x_minus = x.copy()
        x_plus[var_idx] += h
        x_minus[var_idx] -= h
        return (f(x_plus) - f(x_minus)) / (2 * h)

    def gradient(self, f: Callable, x: List[float], h: float = 1e-8) -> List[float]:
        """Gradient of f at x."""
        return [self.partial_derivative(f, x, i, h) for i in range(len(x))]

    def hessian(self, f: Callable, x: List[float], h: float = 1e-5) -> List[List[float]]:
        """Hessian matrix of f at x."""
        n = len(x)
        H = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i, n):
                def partial_i(y):
                    return self.partial_derivative(f, y, i, h)
                H[i][j] = self.partial_derivative(partial_i, x, j, h)
                H[j][i] = H[i][j]

        return H

    def jacobian(self, f: Callable, x: List[float], h: float = 1e-8) -> List[List[float]]:
        """Jacobian matrix of vector-valued f at x."""
        f_x = f(x)
        m, n = len(f_x), len(x)
        J = [[0.0] * n for _ in range(m)]

        for j in range(n):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[j] += h
            x_minus[j] -= h
            f_plus = f(x_plus)
            f_minus = f(x_minus)
            for i in range(m):
                J[i][j] = (f_plus[i] - f_minus[i]) / (2 * h)

        return J

    def integrate(self, f: Callable, a: float, b: float, n: int = 1000) -> float:
        """Numerical integration using Simpson's rule."""
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

    def double_integrate(self, f: Callable, x_bounds: Tuple[float, float],
                         y_bounds: Callable, n: int = 100) -> float:
        """
        Double integral ∫∫f(x,y)dydx.
        y_bounds is function of x returning (y_min, y_max)
        """
        x_min, x_max = x_bounds
        hx = (x_max - x_min) / n
        result = 0

        for i in range(n + 1):
            x = x_min + i * hx
            y_min, y_max = y_bounds(x)

            def fy(y):
                return f(x, y)

            inner = self.integrate(fy, y_min, y_max, n)
            w = 1 if i == 0 or i == n else (4 if i % 2 == 1 else 2)
            result += w * inner

        return result * hx / 3

    def improper_integral(self, f: Callable, a: float, b: float = float('inf'),
                          n: int = 1000) -> float:
        """Improper integral with infinite bounds."""
        if b == float('inf'):
            # Transform to finite interval using t = 1/(1+x)
            def g(t):
                if t <= 0:
                    return 0
                x = (1 - t) / t + a
                return f(x) / (t ** 2)
            return self.integrate(g, 0, 1, n)
        elif a == float('-inf'):
            def g(t):
                if t >= 1:
                    return 0
                x = t / (1 - t) + b
                return f(x) / ((1 - t) ** 2)
            return self.integrate(g, 0, 1, n)
        else:
            return self.integrate(f, a, b, n)

    # ==================== SERIES ====================

    def taylor_coefficients(self, f: Callable, x0: float, n: int) -> List[float]:
        """Taylor series coefficients of f at x0."""
        coeffs = []
        factorial = 1
        for k in range(n + 1):
            if k > 0:
                factorial *= k
            deriv = self.nth_derivative(f, x0, k)
            coeffs.append(deriv / factorial)
        return coeffs

    def taylor_series(self, f: Callable, x0: float, x: float, n: int = 10) -> float:
        """Evaluate Taylor series of f centered at x0."""
        coeffs = self.taylor_coefficients(f, x0, n)
        result = 0
        power = 1
        for c in coeffs:
            result += c * power
            power *= (x - x0)
        return result

    def power_series_radius(self, coeffs: List[float]) -> float:
        """Radius of convergence using ratio test."""
        ratios = []
        for i in range(1, len(coeffs)):
            if coeffs[i] != 0 and coeffs[i-1] != 0:
                ratios.append(abs(coeffs[i-1] / coeffs[i]))
        if not ratios:
            return float('inf')
        return sum(ratios) / len(ratios)

    def series_sum(self, term_func: Callable, n_terms: int, start: int = 0) -> float:
        """Sum of series: Σ term_func(k) for k from start to start+n_terms-1."""
        return sum(term_func(k) for k in range(start, start + n_terms))

    def convergent_series(self, term_func: Callable, tolerance: float = 1e-12,
                          max_terms: int = 10000) -> Tuple[float, int]:
        """
        Sum convergent series until terms become negligible.
        Returns (sum, number_of_terms).
        """
        total = 0
        for k in range(max_terms):
            term = term_func(k)
            if abs(term) < tolerance:
                return (total, k)
            total += term
        return (total, max_terms)

    # ==================== COMPLEX ANALYSIS ====================

    def complex_exp(self, z: complex) -> complex:
        """Complex exponential e^z = e^x(cos(y) + i*sin(y))."""
        return _cmath.exp(z)

    def complex_log(self, z: complex, branch: int = 0) -> complex:
        """
        Complex logarithm (principal branch + 2πi*branch).
        """
        return _cmath.log(z) + 2j * PI * branch

    def complex_power(self, z: complex, w: complex) -> complex:
        """Complex power z^w = e^(w*log(z))."""
        return _cmath.exp(w * _cmath.log(z))

    def complex_sin(self, z: complex) -> complex:
        """Complex sine."""
        return _cmath.sin(z)

    def complex_cos(self, z: complex) -> complex:
        """Complex cosine."""
        return _cmath.cos(z)

    def complex_sinh(self, z: complex) -> complex:
        """Complex hyperbolic sine."""
        return _cmath.sinh(z)

    def complex_cosh(self, z: complex) -> complex:
        """Complex hyperbolic cosine."""
        return _cmath.cosh(z)

    def residue(self, f: Callable, z0: complex, radius: float = 0.001, n: int = 1000) -> complex:
        """
        Compute residue of f at z0 using contour integration.
        Res(f, z0) = (1/2πi) ∮ f(z) dz
        """
        result = 0j
        for k in range(n):
            theta = 2 * PI * k / n
            z = z0 + radius * _cmath.exp(1j * theta)
            dz = 1j * radius * _cmath.exp(1j * theta) * (2 * PI / n)
            result += f(z) * dz
        return result / (2j * PI)

    def contour_integral(self, f: Callable, path: List[complex], n_per_segment: int = 100) -> complex:
        """
        Numerical contour integral along piecewise linear path.
        """
        result = 0j
        for i in range(len(path) - 1):
            z0, z1 = path[i], path[i + 1]
            for k in range(n_per_segment):
                t = k / n_per_segment
                z = z0 + t * (z1 - z0)
                dz = (z1 - z0) / n_per_segment
                result += f(z) * dz
        return result

    def cauchy_integral(self, f: Callable, z0: complex, radius: float = 1.0, n: int = 1000) -> complex:
        """
        Cauchy integral formula: f(z0) = (1/2πi) ∮ f(z)/(z-z0) dz
        """
        result = 0j
        for k in range(n):
            theta = 2 * PI * k / n
            z = z0 + radius * _cmath.exp(1j * theta)
            dz = 1j * radius * _cmath.exp(1j * theta) * (2 * PI / n)
            result += f(z) / (z - z0) * dz
        return result / (2j * PI)

    def analytic_continuation(self, coeffs: List[complex], z0: complex,
                              target: complex, steps: int = 10) -> complex:
        """
        Analytic continuation of power series from z0 toward target.
        """
        # Simple approach: re-expand series at intermediate points
        current = z0
        current_coeffs = coeffs

        step_size = (target - z0) / steps

        for _ in range(steps):
            # Evaluate at new center
            new_center = current + step_size * 0.5

            # Get function value (crude approximation)
            def f(z):
                result = 0
                power = 1
                for c in current_coeffs:
                    result += c * power
                    power *= (z - current)
                return result

            current = new_center
            # Re-expand (simplified)
            current_coeffs = self.taylor_coefficients(f, current, len(coeffs) - 1)

        # Final evaluation
        result = 0
        power = 1
        for c in current_coeffs:
            result += c * power
            power *= (target - current)
        return result

    # ==================== FOURIER ANALYSIS ====================

    def dft(self, x: List[complex]) -> List[complex]:
        """Discrete Fourier Transform."""
        N = len(x)
        result = []
        for k in range(N):
            Xk = sum(x[n] * _cmath.exp(-2j * PI * k * n / N) for n in range(N))
            result.append(Xk)
        return result

    def idft(self, X: List[complex]) -> List[complex]:
        """Inverse Discrete Fourier Transform."""
        N = len(X)
        result = []
        for n in range(N):
            xn = sum(X[k] * _cmath.exp(2j * PI * k * n / N) for k in range(N)) / N
            result.append(xn)
        return result

    def fft(self, x: List[complex]) -> List[complex]:
        """Fast Fourier Transform (Cooley-Tukey)."""
        N = len(x)
        if N <= 1:
            return x

        # Pad to power of 2
        log_N = (N - 1).bit_length()
        N_padded = 1 << log_N
        if N_padded != N:
            x = list(x) + [0] * (N_padded - N)
            N = N_padded

        if N == 1:
            return x

        # Bit-reversal permutation
        result = list(x)
        j = 0
        for i in range(1, N):
            bit = N >> 1
            while j & bit:
                j ^= bit
                bit >>= 1
            j ^= bit
            if i < j:
                result[i], result[j] = result[j], result[i]

        # Cooley-Tukey
        length = 2
        while length <= N:
            angle = -2 * PI / length
            wlen = _cmath.exp(1j * angle)
            for i in range(0, N, length):
                w = 1
                for k in range(length // 2):
                    u = result[i + k]
                    v = result[i + k + length // 2] * w
                    result[i + k] = u + v
                    result[i + k + length // 2] = u - v
                    w *= wlen
            length *= 2

        return result

    def ifft(self, X: List[complex]) -> List[complex]:
        """Inverse Fast Fourier Transform."""
        N = len(X)
        # Conjugate, FFT, conjugate, scale
        X_conj = [z.conjugate() for z in X]
        result = self.fft(X_conj)
        return [z.conjugate() / N for z in result]

    def fourier_series_coefficients(self, f: Callable, period: float,
                                     n_terms: int, n_samples: int = 1000) -> Tuple[List[float], List[float]]:
        """
        Compute Fourier series coefficients a_n, b_n.
        f(x) ≈ a_0/2 + Σ(a_n cos(nωx) + b_n sin(nωx))
        """
        omega = 2 * PI / period
        a = []
        b = []

        for n in range(n_terms + 1):
            def cos_integrand(x):
                return f(x) * _math.cos(n * omega * x)
            def sin_integrand(x):
                return f(x) * _math.sin(n * omega * x)

            a_n = (2 / period) * self.integrate(cos_integrand, 0, period, n_samples)
            b_n = (2 / period) * self.integrate(sin_integrand, 0, period, n_samples) if n > 0 else 0

            a.append(a_n)
            b.append(b_n)

        return a, b

    def power_spectrum(self, x: List[float]) -> List[float]:
        """Power spectrum |X(f)|² from signal."""
        X = self.fft([complex(xi) for xi in x])
        return [abs(Xi) ** 2 for Xi in X[:len(x)//2 + 1]]

    # ==================== SPECIAL FUNCTIONS ====================

    def gamma(self, z: Union[float, complex]) -> Union[float, complex]:
        """Gamma function Γ(z) using Lanczos approximation."""
        if isinstance(z, complex):
            return self._gamma_complex(z)

        if z <= 0 and z == int(z):
            return float('inf')

        if z < 0.5:
            return PI / (_math.sin(PI * z) * self.gamma(1 - z))

        z -= 1
        g = 7
        c = [
            0.99999999999980993,
            676.5203681218851,
            -1259.1392167224028,
            771.32342877765313,
            -176.61502916214059,
            12.507343278686905,
            -0.13857109526572012,
            9.9843695780195716e-6,
            1.5056327351493116e-7
        ]

        x = c[0]
        for i in range(1, g + 2):
            x += c[i] / (z + i)

        t = z + g + 0.5
        return _math.sqrt(2 * PI) * (t ** (z + 0.5)) * _math.exp(-t) * x

    def _gamma_complex(self, z: complex) -> complex:
        """Complex gamma function."""
        if z.real < 0.5:
            return PI / (_cmath.sin(PI * z) * self._gamma_complex(1 - z))

        z -= 1
        g = 7
        c = [
            0.99999999999980993,
            676.5203681218851,
            -1259.1392167224028,
            771.32342877765313,
            -176.61502916214059,
            12.507343278686905,
            -0.13857109526572012,
            9.9843695780195716e-6,
            1.5056327351493116e-7
        ]

        x = c[0]
        for i in range(1, g + 2):
            x += c[i] / (z + i)

        t = z + g + 0.5
        return _cmath.sqrt(2 * PI) * (t ** (z + 0.5)) * _cmath.exp(-t) * x

    def beta(self, a: float, b: float) -> float:
        """Beta function B(a,b) = Γ(a)Γ(b)/Γ(a+b)."""
        return self.gamma(a) * self.gamma(b) / self.gamma(a + b)

    def digamma(self, x: float, n_terms: int = 100) -> float:
        """Digamma function ψ(x) = Γ'(x)/Γ(x)."""
        if x <= 0:
            return float('nan')

        # Use recurrence for small x
        result = 0
        while x < 10:
            result -= 1 / x
            x += 1

        # Asymptotic expansion
        result += _math.log(x) - 1 / (2 * x)
        x2 = x * x
        result -= 1 / (12 * x2)
        result += 1 / (120 * x2 * x2)
        result -= 1 / (252 * x2 * x2 * x2)

        return result

    def zeta(self, s: float, n_terms: int = 10000) -> float:
        """Riemann zeta function ζ(s) for s > 1."""
        if s <= 1:
            return float('inf')

        # Direct summation with Euler-Maclaurin correction
        result = sum(1 / n ** s for n in range(1, n_terms + 1))
        # Tail correction
        result += 1 / ((s - 1) * n_terms ** (s - 1))
        return result

    def erf(self, x: float) -> float:
        """Error function."""
        return _math.erf(x)

    def erfc(self, x: float) -> float:
        """Complementary error function."""
        return _math.erfc(x)

    def bessel_j(self, n: int, x: float) -> float:
        """Bessel function of first kind J_n(x)."""
        if n < 0:
            return ((-1) ** (-n)) * self.bessel_j(-n, x)

        # Series expansion
        result = 0
        for k in range(50):
            sign = (-1) ** k
            num = (x / 2) ** (2 * k + n)
            denom = _math.factorial(k) * self.gamma(n + k + 1)
            term = sign * num / denom
            if abs(term) < 1e-15:
                break
            result += term
        return result

    # ==================== DIFFERENTIAL EQUATIONS ====================

    def ode_euler(self, f: Callable, y0: float, t_span: Tuple[float, float],
                  dt: float) -> List[Tuple[float, float]]:
        """Euler method for ODE dy/dt = f(t, y)."""
        t, y = t_span[0], y0
        result = [(t, y)]

        while t < t_span[1]:
            y += dt * f(t, y)
            t += dt
            result.append((t, y))

        return result

    def ode_rk4(self, f: Callable, y0: float, t_span: Tuple[float, float],
                dt: float) -> List[Tuple[float, float]]:
        """4th order Runge-Kutta for ODE dy/dt = f(t, y)."""
        t, y = t_span[0], y0
        result = [(t, y)]

        while t < t_span[1]:
            k1 = dt * f(t, y)
            k2 = dt * f(t + dt/2, y + k1/2)
            k3 = dt * f(t + dt/2, y + k2/2)
            k4 = dt * f(t + dt, y + k3)
            y += (k1 + 2*k2 + 2*k3 + k4) / 6
            t += dt
            result.append((t, y))

        return result

    def ode_rk4_system(self, f: Callable, y0: List[float],
                       t_span: Tuple[float, float], dt: float) -> List[Tuple[float, List[float]]]:
        """4th order Runge-Kutta for system of ODEs dy/dt = f(t, y)."""
        t, y = t_span[0], list(y0)
        result = [(t, y.copy())]

        def vec_add(a, b):
            return [ai + bi for ai, bi in zip(a, b)]

        def vec_scale(a, s):
            return [ai * s for ai in a]

        while t < t_span[1]:
            k1 = vec_scale(f(t, y), dt)
            k2 = vec_scale(f(t + dt/2, vec_add(y, vec_scale(k1, 0.5))), dt)
            k3 = vec_scale(f(t + dt/2, vec_add(y, vec_scale(k2, 0.5))), dt)
            k4 = vec_scale(f(t + dt, vec_add(y, k3)), dt)

            for i in range(len(y)):
                y[i] += (k1[i] + 2*k2[i] + 2*k3[i] + k4[i]) / 6
            t += dt
            result.append((t, y.copy()))

        return result


# Singleton instance
analysis = Analysis()
