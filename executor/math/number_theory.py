#!/usr/bin/env python3
"""
Number Theory - Foundation of Discrete Mathematics and Cryptography

Covers:
- Prime numbers and primality testing
- Modular arithmetic
- Greatest common divisor and extended Euclidean algorithm
- Chinese Remainder Theorem
- Euler's totient function
- Fermat's little theorem
- Quadratic residues
- Continued fractions
- Diophantine equations
- Cryptographic primitives

USAGE:
    from executor.math.number_theory import nt

    nt.is_prime(17)  # True
    nt.prime_factors(84)  # [2, 2, 3, 7]
    nt.mod_exp(2, 10, 1000)  # 24
    nt.chinese_remainder([2, 3, 2], [3, 5, 7])  # 23
"""

import math as _math
import random
from typing import List, Tuple, Dict, Optional, Generator
from functools import lru_cache


class NumberTheory:
    """Comprehensive number theory operations."""

    # ==================== PRIME NUMBERS ====================

    def is_prime(self, n: int) -> bool:
        """
        Deterministic primality test for small numbers,
        Miller-Rabin probabilistic test for large numbers.
        """
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        if n < 9:
            return True
        if n % 3 == 0:
            return False

        # For small numbers, trial division
        if n < 1000:
            for i in range(5, int(_math.sqrt(n)) + 1, 6):
                if n % i == 0 or n % (i + 2) == 0:
                    return False
            return True

        # Miller-Rabin for larger numbers
        return self._miller_rabin(n, 20)

    def _miller_rabin(self, n: int, k: int = 20) -> bool:
        """Miller-Rabin primality test with k rounds."""
        if n < 2:
            return False
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False

        # Write n-1 as 2^r * d
        r, d = 0, n - 1
        while d % 2 == 0:
            r += 1
            d //= 2

        # Witnesses to test
        def check(a):
            x = pow(a, d, n)
            if x == 1 or x == n - 1:
                return True
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1:
                    return True
            return False

        # Test with random witnesses
        for _ in range(k):
            a = random.randrange(2, n - 1)
            if not check(a):
                return False
        return True

    def next_prime(self, n: int) -> int:
        """Find the next prime >= n."""
        if n <= 2:
            return 2
        if n % 2 == 0:
            n += 1
        while not self.is_prime(n):
            n += 2
        return n

    def prev_prime(self, n: int) -> int:
        """Find the largest prime < n."""
        if n <= 2:
            return None
        if n == 3:
            return 2
        n = n - 1 if n % 2 == 0 else n - 2
        while n > 2 and not self.is_prime(n):
            n -= 2
        return n if n >= 2 else None

    def primes_up_to(self, n: int) -> List[int]:
        """Sieve of Eratosthenes - all primes up to n."""
        if n < 2:
            return []

        sieve = [True] * (n + 1)
        sieve[0] = sieve[1] = False

        for i in range(2, int(_math.sqrt(n)) + 1):
            if sieve[i]:
                for j in range(i*i, n + 1, i):
                    sieve[j] = False

        return [i for i in range(n + 1) if sieve[i]]

    def prime_factors(self, n: int) -> List[int]:
        """Prime factorization of n (with repetition)."""
        if n < 2:
            return []

        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors

    def prime_factorization(self, n: int) -> Dict[int, int]:
        """Prime factorization as {prime: exponent} dict."""
        factors = {}
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors[d] = factors.get(d, 0) + 1
                n //= d
            d += 1
        if n > 1:
            factors[n] = factors.get(n, 0) + 1
        return factors

    def prime_counting(self, n: int) -> int:
        """π(n) - count of primes <= n."""
        return len(self.primes_up_to(n))

    def nth_prime(self, n: int) -> int:
        """Find the nth prime (1-indexed)."""
        if n < 1:
            return None
        if n == 1:
            return 2

        # Upper bound estimation
        if n >= 6:
            upper = int(n * (_math.log(n) + _math.log(_math.log(n))))
        else:
            upper = 15

        primes = self.primes_up_to(upper)
        while len(primes) < n:
            upper *= 2
            primes = self.primes_up_to(upper)

        return primes[n - 1]

    def twin_primes(self, n: int) -> List[Tuple[int, int]]:
        """Find all twin prime pairs up to n."""
        primes = self.primes_up_to(n)
        twins = []
        for i in range(len(primes) - 1):
            if primes[i + 1] - primes[i] == 2:
                twins.append((primes[i], primes[i + 1]))
        return twins

    def mersenne_check(self, p: int) -> bool:
        """Check if 2^p - 1 is a Mersenne prime (Lucas-Lehmer test)."""
        if p == 2:
            return True
        if not self.is_prime(p):
            return False

        m = (1 << p) - 1  # 2^p - 1
        s = 4
        for _ in range(p - 2):
            s = (s * s - 2) % m
        return s == 0

    # ==================== DIVISIBILITY ====================

    def gcd(self, a: int, b: int) -> int:
        """Greatest common divisor (Euclidean algorithm)."""
        while b:
            a, b = b, a % b
        return abs(a)

    def lcm(self, a: int, b: int) -> int:
        """Least common multiple."""
        if a == 0 or b == 0:
            return 0
        return abs(a * b) // self.gcd(a, b)

    def gcd_list(self, nums: List[int]) -> int:
        """GCD of a list of numbers."""
        from functools import reduce
        return reduce(self.gcd, nums)

    def lcm_list(self, nums: List[int]) -> int:
        """LCM of a list of numbers."""
        from functools import reduce
        return reduce(self.lcm, nums)

    def extended_gcd(self, a: int, b: int) -> Tuple[int, int, int]:
        """
        Extended Euclidean Algorithm.
        Returns (gcd, x, y) such that a*x + b*y = gcd(a, b)
        """
        if b == 0:
            return (a, 1, 0)

        g, x, y = self.extended_gcd(b, a % b)
        return (g, y, x - (a // b) * y)

    def coprime(self, a: int, b: int) -> bool:
        """Check if a and b are coprime (relatively prime)."""
        return self.gcd(a, b) == 1

    def divisors(self, n: int) -> List[int]:
        """All divisors of n."""
        if n <= 0:
            return []

        small = []
        large = []

        i = 1
        while i * i <= n:
            if n % i == 0:
                small.append(i)
                if i != n // i:
                    large.append(n // i)
            i += 1

        return small + large[::-1]

    def divisor_count(self, n: int) -> int:
        """Count of divisors (sigma_0)."""
        factors = self.prime_factorization(n)
        count = 1
        for exp in factors.values():
            count *= (exp + 1)
        return count

    def divisor_sum(self, n: int) -> int:
        """Sum of divisors (sigma_1)."""
        factors = self.prime_factorization(n)
        total = 1
        for p, e in factors.items():
            total *= (pow(p, e + 1) - 1) // (p - 1)
        return total

    def is_perfect(self, n: int) -> bool:
        """Check if n is a perfect number (sum of proper divisors = n)."""
        return n > 0 and self.divisor_sum(n) - n == n

    def is_abundant(self, n: int) -> bool:
        """Check if n is abundant (sum of proper divisors > n)."""
        return n > 0 and self.divisor_sum(n) - n > n

    def is_deficient(self, n: int) -> bool:
        """Check if n is deficient (sum of proper divisors < n)."""
        return n > 0 and self.divisor_sum(n) - n < n

    # ==================== MODULAR ARITHMETIC ====================

    def mod_exp(self, base: int, exp: int, mod: int) -> int:
        """Modular exponentiation: base^exp mod m (fast)."""
        if mod == 1:
            return 0
        result = 1
        base = base % mod
        while exp > 0:
            if exp & 1:
                result = (result * base) % mod
            exp >>= 1
            base = (base * base) % mod
        return result

    def mod_inverse(self, a: int, m: int) -> Optional[int]:
        """
        Modular multiplicative inverse of a mod m.
        Returns x such that (a * x) % m == 1, or None if not exists.
        """
        g, x, _ = self.extended_gcd(a, m)
        if g != 1:
            return None
        return x % m

    def mod_sqrt(self, a: int, p: int) -> Optional[int]:
        """
        Modular square root using Tonelli-Shanks algorithm.
        Returns x such that x^2 ≡ a (mod p), or None if not exists.
        """
        if self.legendre_symbol(a, p) != 1:
            return None

        if a == 0:
            return 0
        if p == 2:
            return a
        if p % 4 == 3:
            return pow(a, (p + 1) // 4, p)

        # Tonelli-Shanks
        q, s = p - 1, 0
        while q % 2 == 0:
            q //= 2
            s += 1

        # Find quadratic non-residue
        z = 2
        while self.legendre_symbol(z, p) != -1:
            z += 1

        m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)

        while t != 1:
            # Find least i such that t^(2^i) ≡ 1
            i, temp = 1, pow(t, 2, p)
            while temp != 1:
                temp = pow(temp, 2, p)
                i += 1

            b = pow(c, 1 << (m - i - 1), p)
            m, c, t, r = i, pow(b, 2, p), (t * pow(b, 2, p)) % p, (r * b) % p

        return r

    def chinese_remainder(self, remainders: List[int], moduli: List[int]) -> int:
        """
        Chinese Remainder Theorem.
        Solve: x ≡ r_i (mod m_i) for all i
        """
        if len(remainders) != len(moduli):
            raise ValueError("remainders and moduli must have same length")

        M = 1
        for m in moduli:
            M *= m

        x = 0
        for r, m in zip(remainders, moduli):
            Mi = M // m
            yi = self.mod_inverse(Mi, m)
            x += r * Mi * yi

        return x % M

    # ==================== NUMBER-THEORETIC FUNCTIONS ====================

    def euler_phi(self, n: int) -> int:
        """
        Euler's totient function φ(n).
        Count of integers 1..n coprime to n.
        """
        if n < 1:
            return 0

        result = n
        p = 2
        while p * p <= n:
            if n % p == 0:
                while n % p == 0:
                    n //= p
                result -= result // p
            p += 1
        if n > 1:
            result -= result // n
        return result

    def mobius(self, n: int) -> int:
        """
        Möbius function μ(n).
        μ(n) = 0 if n has squared prime factor
        μ(n) = (-1)^k if n is product of k distinct primes
        """
        if n == 1:
            return 1

        factors = self.prime_factorization(n)
        for exp in factors.values():
            if exp > 1:
                return 0

        return 1 if len(factors) % 2 == 0 else -1

    def legendre_symbol(self, a: int, p: int) -> int:
        """
        Legendre symbol (a/p).
        Returns: 0 if p|a, 1 if a is QR mod p, -1 if a is QNR mod p
        """
        if p == 2:
            return a % 2

        ls = pow(a, (p - 1) // 2, p)
        return -1 if ls == p - 1 else ls

    def jacobi_symbol(self, a: int, n: int) -> int:
        """
        Jacobi symbol (a/n) - generalization of Legendre symbol.
        """
        if n <= 0 or n % 2 == 0:
            raise ValueError("n must be positive odd integer")

        a = a % n
        result = 1

        while a != 0:
            while a % 2 == 0:
                a //= 2
                if n % 8 in [3, 5]:
                    result = -result
            a, n = n, a
            if a % 4 == 3 and n % 4 == 3:
                result = -result
            a = a % n

        return result if n == 1 else 0

    def carmichael_lambda(self, n: int) -> int:
        """
        Carmichael function λ(n).
        Smallest positive m such that a^m ≡ 1 (mod n) for all coprime a.
        """
        if n == 1:
            return 1

        factors = self.prime_factorization(n)
        result = 1

        for p, k in factors.items():
            if p == 2 and k >= 3:
                pk_lambda = pow(p, k - 2)
            else:
                pk_lambda = pow(p, k - 1) * (p - 1)
            result = self.lcm(result, pk_lambda)

        return result

    def order_mod(self, a: int, n: int) -> Optional[int]:
        """
        Multiplicative order of a modulo n.
        Smallest positive k such that a^k ≡ 1 (mod n).
        """
        if self.gcd(a, n) != 1:
            return None

        lambda_n = self.carmichael_lambda(n)
        divisors = self.divisors(lambda_n)

        for d in divisors:
            if pow(a, d, n) == 1:
                return d

        return lambda_n

    def primitive_root(self, n: int) -> Optional[int]:
        """
        Find a primitive root modulo n (generator of multiplicative group).
        """
        phi = self.euler_phi(n)
        factors = list(self.prime_factorization(phi).keys())

        for g in range(2, n):
            if self.gcd(g, n) != 1:
                continue
            is_primitive = True
            for p in factors:
                if pow(g, phi // p, n) == 1:
                    is_primitive = False
                    break
            if is_primitive:
                return g

        return None

    # ==================== SPECIAL SEQUENCES ====================

    @lru_cache(maxsize=1000)
    def fibonacci(self, n: int) -> int:
        """Fibonacci number F_n."""
        if n <= 0:
            return 0
        if n == 1:
            return 1

        # Matrix exponentiation for large n
        if n > 30:
            return self._fib_matrix(n)
        return self.fibonacci(n - 1) + self.fibonacci(n - 2)

    def _fib_matrix(self, n: int) -> int:
        """Fibonacci via matrix exponentiation O(log n)."""
        def mat_mult(A, B, mod=None):
            return [
                [A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
                [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]]
            ]

        def mat_pow(M, p):
            if p == 1:
                return M
            if p % 2 == 0:
                half = mat_pow(M, p // 2)
                return mat_mult(half, half)
            return mat_mult(M, mat_pow(M, p - 1))

        if n == 0:
            return 0
        M = [[1, 1], [1, 0]]
        result = mat_pow(M, n)
        return result[0][1]

    def lucas(self, n: int) -> int:
        """Lucas number L_n."""
        if n == 0:
            return 2
        if n == 1:
            return 1
        return self.fibonacci(n - 1) + self.fibonacci(n + 1)

    def catalan(self, n: int) -> int:
        """Catalan number C_n."""
        if n <= 0:
            return 1
        return self.binomial(2 * n, n) // (n + 1)

    def binomial(self, n: int, k: int) -> int:
        """Binomial coefficient C(n, k)."""
        if k < 0 or k > n:
            return 0
        if k == 0 or k == n:
            return 1
        k = min(k, n - k)
        result = 1
        for i in range(k):
            result = result * (n - i) // (i + 1)
        return result

    def stirling1(self, n: int, k: int) -> int:
        """Stirling number of the first kind s(n, k)."""
        if n == 0 and k == 0:
            return 1
        if n == 0 or k == 0:
            return 0
        return (n - 1) * self.stirling1(n - 1, k) + self.stirling1(n - 1, k - 1)

    def stirling2(self, n: int, k: int) -> int:
        """Stirling number of the second kind S(n, k)."""
        if n == 0 and k == 0:
            return 1
        if n == 0 or k == 0:
            return 0
        return k * self.stirling2(n - 1, k) + self.stirling2(n - 1, k - 1)

    def bell(self, n: int) -> int:
        """Bell number B_n (number of partitions of n-set)."""
        return sum(self.stirling2(n, k) for k in range(n + 1))

    def partition(self, n: int) -> int:
        """Partition number p(n) (ways to write n as sum of positive integers)."""
        if n < 0:
            return 0
        if n == 0:
            return 1

        # Dynamic programming
        dp = [0] * (n + 1)
        dp[0] = 1

        for i in range(1, n + 1):
            for j in range(i, n + 1):
                dp[j] += dp[j - i]

        return dp[n]

    # ==================== CONTINUED FRACTIONS ====================

    def continued_fraction(self, num: int, den: int, max_terms: int = 20) -> List[int]:
        """Continued fraction expansion of num/den."""
        cf = []
        for _ in range(max_terms):
            if den == 0:
                break
            q = num // den
            cf.append(q)
            num, den = den, num - q * den
        return cf

    def convergents(self, cf: List[int]) -> List[Tuple[int, int]]:
        """Convergents of a continued fraction."""
        if not cf:
            return []

        convs = []
        h_prev, h_curr = 1, cf[0]
        k_prev, k_curr = 0, 1
        convs.append((h_curr, k_curr))

        for a in cf[1:]:
            h_prev, h_curr = h_curr, a * h_curr + h_prev
            k_prev, k_curr = k_curr, a * k_curr + k_prev
            convs.append((h_curr, k_curr))

        return convs

    def best_rational_approx(self, x: float, max_den: int) -> Tuple[int, int]:
        """Best rational approximation p/q to x with q <= max_den."""
        cf = []
        num, den = int(x * 10**10), 10**10
        g = self.gcd(num, den)
        num, den = num // g, den // g

        cf = self.continued_fraction(num, den, 50)
        convs = self.convergents(cf)

        for p, q in convs:
            if q > max_den:
                break
            best = (p, q)

        return best

    # ==================== DIOPHANTINE EQUATIONS ====================

    def linear_diophantine(self, a: int, b: int, c: int) -> Optional[Tuple[int, int, int, int]]:
        """
        Solve ax + by = c.
        Returns (x0, y0, dx, dy) where general solution is:
        x = x0 + dx*t, y = y0 + dy*t for integer t
        Returns None if no solution.
        """
        g = self.gcd(a, b)
        if c % g != 0:
            return None

        _, x, y = self.extended_gcd(a, b)
        x0 = x * (c // g)
        y0 = y * (c // g)
        dx = b // g
        dy = -a // g

        return (x0, y0, dx, dy)

    def pell_equation(self, d: int, n: int = 1) -> Optional[Tuple[int, int]]:
        """
        Find fundamental solution to x² - d*y² = n.
        Returns (x, y) or None if no solution.
        """
        if d <= 0 or int(_math.sqrt(d)) ** 2 == d:
            return None

        # Use continued fraction of sqrt(d)
        m, d_val, a = 0, 1, int(_math.sqrt(d))
        sqrt_d = int(_math.sqrt(d))

        cf = [a]
        seen = {}

        for _ in range(100):
            m = d_val * a - m
            d_val = (d - m * m) // d_val
            a = (sqrt_d + m) // d_val

            state = (m, d_val)
            if state in seen:
                break
            seen[state] = len(cf)
            cf.append(a)

        # Try convergents
        convs = self.convergents(cf)
        for p, q in convs:
            if p * p - d * q * q == n:
                return (p, q)

        return None


# Singleton instance
nt = NumberTheory()
