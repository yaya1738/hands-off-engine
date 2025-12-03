"""
Comprehensive Mathematics Library
=================================

A unified interface to earth's known mathematics, organized into specialized modules:

MODULES:
--------
1. number_theory (nt)   - Primes, modular arithmetic, cryptographic math
2. abstract_algebra     - Groups, rings, fields, quaternions
3. geometry (geo)       - Euclidean, differential, computational geometry
4. analysis             - Real, complex, functional analysis, Fourier, special functions
5. financial (fin)      - Options, Greeks, stochastic calculus, risk measures
6. discrete             - Combinatorics, graph theory, coding theory
7. statistics (stats)   - Descriptive, inferential, Bayesian statistics
8. ml_math (ml)         - Neural networks, kernels, optimization, attention

QUICK USAGE:
------------
```python
from executor.math import nt, geo, fin, stats, ml, analysis, discrete, algebra

# Number theory
nt.is_prime(17)                    # True
nt.miller_rabin(104729)            # True (primality test)
nt.euler_phi(12)                   # 4

# Geometry
geo.distance_2d((0,0), (3,4))      # 5.0
geo.convex_hull(points)            # Convex hull of points
geo.polygon_area(vertices)         # Area of polygon

# Financial math
fin.black_scholes_call(100, 100, 1, 0.05, 0.2)  # Option price
fin.delta(100, 100, 1, 0.05, 0.2)                # Delta Greek
fin.var_historical(returns, 0.95)                # Value at Risk

# Statistics
stats.mean([1,2,3,4,5])            # 3.0
stats.t_test_one_sample(data, 0)  # T-test
stats.linear_regression(X, y)     # Regression

# ML Math
ml.sigmoid(0)                      # 0.5
ml.softmax([1, 2, 3])             # Probability distribution
ml.adam_step(params, grads, m, v, t)  # Adam optimizer

# Analysis
analysis.derivative(f, x)          # Numerical derivative
analysis.fft(signal)               # Fast Fourier Transform
analysis.gamma(5)                  # 24.0 (Gamma function)

# Discrete math
discrete.combinations(5, 2)        # 10
discrete.shortest_path(graph, 0, 4)  # Dijkstra
discrete.hamming_encode_7_4(data)    # Error correction

# Abstract algebra
algebra.gf_mult(3, 5, 7)          # Finite field multiplication
algebra.quat_mult(q1, q2)         # Quaternion product
```

FULL API REFERENCE:
-------------------
See individual module docstrings for complete API documentation.
"""

# Import all singleton instances for easy access
from .number_theory import nt, NumberTheory
from .abstract_algebra import algebra, AbstractAlgebra
from .geometry import geo, Geometry
from .analysis import analysis, Analysis
from .financial import fin, FinancialMath
from .discrete import discrete, DiscreteMath
from .statistics import stats, Statistics
from .ml_math import ml, MLMath

# Unified math interface class
class Math:
    """
    Unified interface to all mathematical modules.

    Access any mathematical function through a single entry point:
        math = Math()
        math.nt.is_prime(17)
        math.geo.distance_2d((0,0), (3,4))
        math.fin.black_scholes_call(100, 100, 1, 0.05, 0.2)
    """

    def __init__(self):
        # Core modules
        self.nt = nt                    # Number theory
        self.number_theory = nt

        self.algebra = algebra          # Abstract algebra
        self.abstract_algebra = algebra

        self.geo = geo                  # Geometry
        self.geometry = geo

        self.analysis = analysis        # Analysis

        self.fin = fin                  # Financial math
        self.financial = fin

        self.discrete = discrete        # Discrete math

        self.stats = stats              # Statistics
        self.statistics = stats

        self.ml = ml                    # ML math
        self.ml_math = ml

    def list_modules(self):
        """List all available math modules"""
        return {
            'nt (number_theory)': 'Primes, modular arithmetic, cryptographic math',
            'algebra (abstract_algebra)': 'Groups, rings, fields, quaternions',
            'geo (geometry)': 'Euclidean, differential, computational geometry',
            'analysis': 'Real, complex, functional analysis',
            'fin (financial)': 'Options, Greeks, stochastic calculus',
            'discrete': 'Combinatorics, graph theory, coding theory',
            'stats (statistics)': 'Descriptive, inferential, Bayesian',
            'ml (ml_math)': 'Neural networks, kernels, optimization'
        }

    def list_functions(self, module_name: str = None):
        """List functions in a specific module or all modules"""
        modules = {
            'nt': self.nt,
            'algebra': self.algebra,
            'geo': self.geo,
            'analysis': self.analysis,
            'fin': self.fin,
            'discrete': self.discrete,
            'stats': self.stats,
            'ml': self.ml
        }

        if module_name:
            if module_name not in modules:
                return f"Unknown module: {module_name}. Available: {list(modules.keys())}"
            mod = modules[module_name]
            return [m for m in dir(mod) if not m.startswith('_') and callable(getattr(mod, m))]

        result = {}
        for name, mod in modules.items():
            result[name] = [m for m in dir(mod) if not m.startswith('_') and callable(getattr(mod, m))]
        return result


# Singleton unified math instance
math = Math()

# Export everything
__all__ = [
    # Singleton instances (primary usage)
    'nt', 'algebra', 'geo', 'analysis', 'fin', 'discrete', 'stats', 'ml',
    # Classes (for custom instantiation)
    'NumberTheory', 'AbstractAlgebra', 'Geometry', 'Analysis',
    'FinancialMath', 'DiscreteMath', 'Statistics', 'MLMath',
    # Unified interface
    'Math', 'math'
]
