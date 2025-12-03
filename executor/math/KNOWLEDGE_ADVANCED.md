# THEORETICAL MATHEMATICS - ADVANCED MATHEMATICAL INFRASTRUCTURE

## KNOWLEDGE BASE FOR: Comprehensive Mathematical Foundation

**File**: `executor/theoretical_math.py`
**Purpose**: Earth-scale theoretical mathematics for quantitative analysis
**Serving**: Yair Siegel

---

## MATHEMATICAL CONSTANTS

```python
PI = 3.14159265...       # π
E = 2.71828182...        # Euler's number
PHI = 1.61803398...      # Golden ratio
EULER_GAMMA = 0.5772...  # Euler-Mascheroni constant
EPSILON = 1e-10          # Numerical tolerance
```

---

## MODULE 1: PROBABILITY THEORY (`prob`)

Probability distributions, Bayesian inference, and statistical moments.

### Bayesian Inference

```python
from executor.theoretical_math import prob

# Bayes' Theorem: P(H|E) = P(E|H) * P(H) / P(E)
prob.bayes_update(prior=0.5, likelihood=0.8, evidence=0.6)

# Bayes Factor (evidence strength)
prob.bayes_factor(likelihood_h1=0.9, likelihood_h0=0.3)  # BF > 1 supports H1

# Law of Total Probability
prob.total_probability([
    (0.9, 0.3),  # (P(A|B1), P(B1))
    (0.2, 0.7)   # (P(A|B2), P(B2))
])

# Conditional Probability
prob.conditional(p_joint=0.2, p_condition=0.4)  # P(A|B) = 0.5

# Independence Test
prob.independence_test(p_a=0.5, p_b=0.4, p_ab=0.2)  # True if independent
```

### Probability Distributions

```python
# Normal/Gaussian
prob.normal_pdf(x=0, mu=0, sigma=1)      # PDF
prob.normal_cdf(x=1.96, mu=0, sigma=1)   # CDF ≈ 0.975
prob.normal_quantile(p=0.975)            # Inverse CDF ≈ 1.96

# Other distributions
prob.uniform_pdf(x=0.5, a=0, b=1)
prob.exponential_pdf(x=1, rate=0.5)
prob.poisson_pmf(k=3, lam=2.5)
prob.binomial_pmf(k=7, n=10, p=0.6)
prob.beta_pdf(x=0.3, alpha=2, beta=5)
```

### Statistical Moments

```python
# Expected value and variance
prob.expected_value(values=[1, 2, 3], probs=[0.2, 0.5, 0.3])
prob.variance(values, probs)

# Higher moments
prob.skewness(data)   # Asymmetry measure
prob.kurtosis(data)   # Tail heaviness (excess)

# Covariance and correlation
prob.covariance(x, y)
prob.correlation(x, y)
```

---

## MODULE 2: CALCULUS (`calc`)

Differential and integral calculus operations.

### Derivatives

```python
from executor.theoretical_math import calc

# First derivative (central difference)
calc.derivative(f=lambda x: x**2, x=3)  # Returns 6

# Second derivative
calc.second_derivative(f, x)

# Partial derivative
calc.partial_derivative(f=lambda x: x[0]**2 + x[1]**2, x=[1, 2], i=0)

# Gradient vector ∇f
calc.gradient(f, x=[1, 2])

# Hessian matrix (second partial derivatives)
calc.hessian(f, x)
```

### Integration

```python
# Definite integral (Simpson's rule)
calc.integrate(f=lambda x: x**2, a=0, b=1, n=1000)  # Returns 1/3

# Double integral
calc.double_integrate(f=lambda x, y: x*y, ax=0, bx=1, ay=0, by=1)

# Taylor series approximation
calc.taylor_series(f, x0=0, x=0.1, n_terms=5)

# Numerical limit
calc.limit(f, x=0, direction="both")  # "left", "right", "both"
```

---

## MODULE 3: LINEAR ALGEBRA (`linalg`)

Matrix operations and linear algebra utilities.

### Vector Operations

```python
from executor.theoretical_math import linalg

# Dot product
linalg.dot([1, 2, 3], [4, 5, 6])  # 32

# Vector norm
linalg.norm([3, 4], p=2)  # Euclidean = 5
linalg.norm([3, 4], p=float('inf'))  # Max = 4

# Projection
linalg.project(u=[1, 2], v=[1, 0])  # Project u onto v

# Outer product
linalg.outer_product([1, 2], [3, 4])  # 2x2 matrix
```

### Matrix Operations

```python
# Matrix multiplication
linalg.matrix_multiply(A, B)

# Transpose
linalg.transpose(A)

# Identity matrix
linalg.identity(n=3)

# Determinant
linalg.determinant(A)

# Trace
linalg.trace(A)

# 2x2 inverse
linalg.inverse_2x2([[a, b], [c, d]])

# Solve Ax = b (2x2)
linalg.solve_2x2(A, b)

# Eigenvalues (2x2)
linalg.eigenvalues_2x2(A)  # Returns tuple of eigenvalues
```

---

## MODULE 4: STOCHASTIC PROCESSES (`stoch`)

Random processes for financial modeling.

### Brownian Motion

```python
from executor.theoretical_math import stoch

# Standard Brownian motion
path = stoch.brownian_motion(t=1.0, dt=0.01, mu=0, sigma=1)

# Geometric Brownian Motion (stock prices)
# dS = μS dt + σS dW
prices = stoch.geometric_brownian_motion(
    S0=100,      # Initial price
    t=1.0,       # Time horizon
    mu=0.05,     # Drift (5% annual)
    sigma=0.2,   # Volatility (20%)
    dt=0.01
)

# Ornstein-Uhlenbeck (mean-reverting)
# dX = θ(μ - X)dt + σdW
path = stoch.ornstein_uhlenbeck(
    x0=0.5,      # Initial value
    t=1.0,
    theta=5.0,   # Mean reversion speed
    mu=0.5,      # Long-term mean
    sigma=0.1
)
```

### Discrete Processes

```python
# Poisson process arrivals
arrivals = stoch.poisson_process(t=10, rate=2.5)
# Returns: [(time, count), ...]

# Markov chain step
next_state = stoch.markov_chain_step(
    current_state=0,
    transition_matrix=[[0.7, 0.3], [0.4, 0.6]]
)

# Stationary distribution
pi = stoch.stationary_distribution(P, n_iter=1000)
```

---

## MODULE 5: TIME SERIES (`ts`)

Time series analysis and forecasting.

### Autocorrelation

```python
from executor.theoretical_math import ts

# Autocorrelation at lag k
ts.autocorrelation(x=prices, lag=5)

# Partial autocorrelation function
ts.partial_autocorrelation(x, max_lag=10)
```

### Moving Averages

```python
# Simple moving average
ts.moving_average(x, window=20)

# Exponential moving average
ts.exponential_moving_average(x, alpha=0.3)
```

### Stationarity & Forecasting

```python
# Differencing (make stationary)
ts.differencing(x, d=1)  # First difference
ts.differencing(x, d=2)  # Second difference

# Augmented Dickey-Fuller test statistic
ts.adf_statistic(x)  # Test for unit root

# AR(1) forecast
ts.forecast_ar1(x, steps=10)
```

---

## MODULE 6: MONTE CARLO (`mc`)

Simulation and numerical integration.

### Simulation

```python
from executor.theoretical_math import mc

# General Monte Carlo simulation
results = mc.simulate(
    func=lambda: random.gauss(0, 1)**2,
    n_trials=10000
)
# Returns: {"mean": ..., "std": ..., "p5": ..., "p95": ...}

# Bootstrap resampling
mc.bootstrap(
    data=returns,
    statistic=lambda x: sum(x)/len(x),  # Mean
    n_bootstrap=1000
)
# Returns: {"estimate": ..., "std_error": ..., "ci_95": (low, high)}
```

### Monte Carlo Integration

```python
# Integrate over region
mc.integrate_mc(
    f=lambda x: x[0]**2 + x[1]**2,
    bounds=[(0, 1), (0, 1)],
    n_samples=100000
)
# Returns: {"estimate": ..., "std_error": ...}

# Importance sampling
mc.importance_sampling(
    f=target_function,
    p=target_density,
    q=proposal_density,
    q_sampler=proposal_sampler,
    n_samples=10000
)
```

---

## MODULE 7: OPTIMIZATION (`opt`)

Numerical optimization algorithms.

### Gradient-Based Methods

```python
from executor.theoretical_math import opt

# Gradient descent
result = opt.gradient_descent(
    f=objective,
    grad_f=gradient,
    x0=[0, 0],
    lr=0.01,
    max_iter=1000,
    tol=1e-6
)
# Returns: {"x": [...], "f_min": ..., "converged": True/False}

# Newton's method (root finding)
opt.newton_method(f, x0=1.0, max_iter=100)
```

### Other Methods

```python
# Bisection (root finding)
opt.bisection(f, a=0, b=2, tol=1e-8)

# Golden section search (1D minimization)
opt.golden_section(f, a=0, b=2)

# Simulated annealing (global optimization)
opt.simulated_annealing(
    f=objective,
    x0=[0, 0],
    T0=100,          # Initial temperature
    cooling=0.99,    # Cooling rate
    max_iter=10000
)
```

---

## MODULE 8: INFORMATION THEORY (`info`)

Information-theoretic measures.

```python
from executor.theoretical_math import info

# Shannon entropy: H(X) = -Σ p(x) log p(x)
info.entropy(probs=[0.5, 0.5])  # = 1 bit

# Cross entropy
info.cross_entropy(p=[0.5, 0.5], q=[0.6, 0.4])

# KL divergence: D_KL(P||Q)
info.kl_divergence(p, q)

# Mutual information: I(X;Y)
info.mutual_information(joint_distribution)

# Conditional entropy: H(Y|X)
info.conditional_entropy(joint_distribution)

# Bits needed
info.bits_to_represent(n_outcomes=8)  # = 3 bits
```

---

## MODULE 9: GAME THEORY (`game`)

Strategic decision analysis.

```python
from executor.theoretical_math import game

# Nash equilibrium (2x2 game)
result = game.nash_equilibrium_2x2(
    payoff_A=[[3, 0], [5, 1]],
    payoff_B=[[3, 5], [0, 1]]
)
# Returns: {"player_A_mix": [p, 1-p], "player_B_mix": [q, 1-q], ...}

# Minimax (zero-sum game)
game.minimax(payoff)
# Returns: {"maximin": ..., "minimax": ..., "saddle_point": True/False}

# Find dominated strategies
game.dominated_strategies(payoff)
```

---

## MODULE 10: NUMERICAL METHODS (`num`)

General numerical computation.

### Interpolation

```python
from executor.theoretical_math import num

# Linear interpolation
num.interpolate_linear(x=2.5, x_points=[1, 2, 3], y_points=[1, 4, 9])

# Cubic interpolation
num.interpolate_cubic(x, x_points, y_points)
```

### Differential Equations

```python
# Finite difference derivatives
num.finite_difference(f, x, order=1)  # 1st, 2nd, or 3rd

# Runge-Kutta 4 (ODE solver)
trajectory = num.runge_kutta_4(
    f=lambda t, y: -y,  # dy/dt = -y
    y0=1.0,
    t0=0,
    t_end=5,
    dt=0.1
)
# Returns: [(t, y), ...]
```

### Fourier Analysis

```python
# DFT magnitude spectrum
magnitudes = num.fft_magnitude(signal)
```

---

## SPECIALIZED MATH MODULES

Additional libraries in `executor/math/`:

### 1. Number Theory (`number_theory.py`)
- Prime testing and factorization
- Modular arithmetic
- GCD, LCM, extended Euclidean
- Chinese Remainder Theorem

### 2. Abstract Algebra (`abstract_algebra.py`)
- Group operations
- Ring and field structures
- Polynomial operations

### 3. Analysis (`analysis.py`)
- Real analysis fundamentals
- Complex analysis basics
- Measure theory concepts

### 4. Discrete Math (`discrete.py`)
- Combinatorics (permutations, combinations)
- Graph algorithms
- Set operations

### 5. Geometry (`geometry.py`)
- Vector operations
- Transformations
- Distance calculations

### 6. Financial Math (`financial.py`)
- Option pricing (Black-Scholes)
- Bond calculations
- Interest rate models

### 7. Statistics (`statistics.py`)
- Distribution functions
- Hypothesis testing
- Regression analysis

### 8. ML Math (`ml_math.py`)
- Gradient computations
- Loss functions
- Activation functions

---

## USAGE EXAMPLES

### Bayesian Market Probability Update

```python
from executor.theoretical_math import prob

# Prior: 50% chance market resolves YES
prior = 0.5

# New evidence: 80% of similar events resolved YES
likelihood = 0.8

# Background rate: 60% of predictions are confident
evidence = 0.6

posterior = prob.bayes_update(prior, likelihood, evidence)
# posterior ≈ 0.67
```

### Monte Carlo Price Simulation

```python
from executor.theoretical_math import stoch, mc

def simulate_final_price():
    path = stoch.geometric_brownian_motion(
        S0=0.5, t=30, mu=0, sigma=0.02, dt=1
    )
    return path[-1]

results = mc.simulate(simulate_final_price, n_trials=10000)
print(f"Expected final price: {results['mean']:.4f}")
print(f"95% CI: [{results['p5']:.4f}, {results['p95']:.4f}]")
```

### Optimal Entry Finding

```python
from executor.theoretical_math import opt

def cost_function(price):
    # Minimize distance from fair value with risk penalty
    fair_value = 0.55
    return (price - fair_value)**2 + 0.1 * price

result = opt.golden_section(cost_function, a=0.4, b=0.7)
optimal_entry = result['x_min']
```

---

## INTEGRATION WITH TRADING SYSTEM

These theoretical tools integrate with:
- **Kelly sizing**: Bayesian probability updates
- **Risk management**: VaR via Monte Carlo
- **Market making**: Stochastic process modeling
- **Strategy optimization**: Gradient methods
- **Signal detection**: Information theory

---

## SUMMARY

**Theoretical Coverage**:
- Probability: Full Bayesian inference + distributions
- Calculus: Numerical derivatives and integrals
- Linear Algebra: Matrix operations, eigenvalues
- Stochastic: Brownian motion, OU, Markov chains
- Time Series: ARIMA components, forecasting
- Monte Carlo: Simulation, bootstrap, integration
- Optimization: Gradient descent, Newton, annealing
- Information: Entropy, KL divergence, mutual information
- Game Theory: Nash equilibrium, minimax
- Numerics: Interpolation, RK4, FFT

**Design Philosophy**:
- Pure Python implementations
- No external dependencies (numpy/scipy optional)
- Numerical stability with EPSILON tolerance
- Comprehensive coverage of quantitative finance math
