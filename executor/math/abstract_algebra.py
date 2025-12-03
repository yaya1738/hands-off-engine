#!/usr/bin/env python3
"""
Abstract Algebra - Groups, Rings, Fields, and Algebraic Structures

Covers:
- Group theory (cyclic, symmetric, permutation groups)
- Ring theory (polynomial rings, ideals)
- Field theory (finite fields, field extensions)
- Vector spaces
- Galois theory basics
- Homomorphisms and isomorphisms

USAGE:
    from executor.math.abstract_algebra import algebra

    # Permutation groups
    algebra.permutation_compose([1,2,0], [2,0,1])
    algebra.permutation_order([1,2,0])

    # Polynomial operations
    algebra.poly_mult([1,2,1], [1,1])  # (1+2x+x²)(1+x)

    # Finite fields
    algebra.gf_add(5, 7, 11)
    algebra.gf_mult(5, 7, 11)
"""

import math as _math
from typing import List, Tuple, Dict, Optional, Set, Callable
from functools import reduce
from itertools import permutations, combinations


class AbstractAlgebra:
    """Comprehensive abstract algebra operations."""

    # ==================== GROUP THEORY ====================

    def permutation_compose(self, p1: List[int], p2: List[int]) -> List[int]:
        """
        Compose two permutations: p1 ∘ p2 (apply p2 first, then p1).
        Permutation is represented as [p(0), p(1), ..., p(n-1)]
        """
        n = len(p1)
        return [p1[p2[i]] for i in range(n)]

    def permutation_inverse(self, p: List[int]) -> List[int]:
        """Inverse of a permutation."""
        n = len(p)
        inv = [0] * n
        for i, v in enumerate(p):
            inv[v] = i
        return inv

    def permutation_order(self, p: List[int]) -> int:
        """Order of a permutation (smallest k where p^k = identity)."""
        n = len(p)
        identity = list(range(n))
        current = p.copy()
        order = 1

        while current != identity:
            current = self.permutation_compose(p, current)
            order += 1
            if order > _math.factorial(n):
                break

        return order

    def permutation_to_cycles(self, p: List[int]) -> List[List[int]]:
        """Convert permutation to cycle notation."""
        n = len(p)
        visited = [False] * n
        cycles = []

        for i in range(n):
            if visited[i]:
                continue
            cycle = []
            j = i
            while not visited[j]:
                visited[j] = True
                cycle.append(j)
                j = p[j]
            if len(cycle) > 1:
                cycles.append(cycle)

        return cycles

    def cycles_to_permutation(self, cycles: List[List[int]], n: int) -> List[int]:
        """Convert cycle notation to permutation."""
        p = list(range(n))
        for cycle in cycles:
            for i in range(len(cycle)):
                p[cycle[i]] = cycle[(i + 1) % len(cycle)]
        return p

    def permutation_sign(self, p: List[int]) -> int:
        """Sign (parity) of permutation: +1 for even, -1 for odd."""
        cycles = self.permutation_to_cycles(p)
        inversions = sum(len(c) - 1 for c in cycles)
        return 1 if inversions % 2 == 0 else -1

    def is_permutation(self, p: List[int]) -> bool:
        """Check if list represents a valid permutation."""
        n = len(p)
        return sorted(p) == list(range(n))

    def symmetric_group(self, n: int) -> List[List[int]]:
        """Generate all permutations in S_n."""
        return [list(p) for p in permutations(range(n))]

    def alternating_group(self, n: int) -> List[List[int]]:
        """Generate all even permutations in A_n."""
        return [p for p in self.symmetric_group(n) if self.permutation_sign(p) == 1]

    def cyclic_group(self, n: int) -> List[int]:
        """Elements of cyclic group Z_n as {0, 1, ..., n-1}."""
        return list(range(n))

    def group_cayley_table(self, elements: List, op: Callable) -> List[List]:
        """Generate Cayley table for a group."""
        n = len(elements)
        table = [[None] * n for _ in range(n)]
        for i, a in enumerate(elements):
            for j, b in enumerate(elements):
                table[i][j] = op(a, b)
        return table

    def is_group(self, elements: List, op: Callable, identity) -> Dict:
        """
        Check if (elements, op) forms a group.
        Returns dict with closure, identity, inverses, associativity checks.
        """
        result = {
            "closure": True,
            "identity": True,
            "inverses": True,
            "associative": True
        }

        elem_set = set(map(tuple, elements)) if isinstance(elements[0], list) else set(elements)

        # Closure
        for a in elements:
            for b in elements:
                r = op(a, b)
                r_key = tuple(r) if isinstance(r, list) else r
                if r_key not in elem_set:
                    result["closure"] = False

        # Identity
        for a in elements:
            if op(identity, a) != a or op(a, identity) != a:
                result["identity"] = False

        # Inverses
        for a in elements:
            has_inv = False
            for b in elements:
                if op(a, b) == identity and op(b, a) == identity:
                    has_inv = True
                    break
            if not has_inv:
                result["inverses"] = False

        # Associativity (sample check for efficiency)
        import random
        for _ in range(min(100, len(elements) ** 3)):
            a, b, c = random.choices(elements, k=3)
            if op(op(a, b), c) != op(a, op(b, c)):
                result["associative"] = False
                break

        return result

    def subgroup_test(self, H: List, G: List, op: Callable, identity) -> bool:
        """Test if H is a subgroup of G."""
        if identity not in H:
            return False

        for a in H:
            # Check inverse
            has_inv = False
            for b in H:
                if op(a, b) == identity:
                    has_inv = True
                    break
            if not has_inv:
                return False

            # Check closure
            for b in H:
                if op(a, b) not in H:
                    return False

        return True

    def cosets(self, H: List, G: List, op: Callable) -> List[Set]:
        """Left cosets of H in G."""
        coset_list = []
        covered = set()

        for g in G:
            coset = frozenset(op(g, h) for h in H)
            if coset not in covered:
                coset_list.append(set(coset))
                covered.add(coset)

        return coset_list

    def lagrange_index(self, H: List, G: List) -> int:
        """Index [G:H] = |G|/|H| (Lagrange's theorem)."""
        return len(G) // len(H)

    # ==================== RING THEORY ====================

    def poly_add(self, p1: List[float], p2: List[float]) -> List[float]:
        """Add two polynomials."""
        n = max(len(p1), len(p2))
        result = [0.0] * n
        for i, c in enumerate(p1):
            result[i] += c
        for i, c in enumerate(p2):
            result[i] += c
        # Remove trailing zeros
        while len(result) > 1 and result[-1] == 0:
            result.pop()
        return result

    def poly_sub(self, p1: List[float], p2: List[float]) -> List[float]:
        """Subtract polynomials: p1 - p2."""
        return self.poly_add(p1, [-c for c in p2])

    def poly_mult(self, p1: List[float], p2: List[float]) -> List[float]:
        """Multiply two polynomials."""
        n1, n2 = len(p1), len(p2)
        result = [0.0] * (n1 + n2 - 1)
        for i in range(n1):
            for j in range(n2):
                result[i + j] += p1[i] * p2[j]
        return result

    def poly_div(self, dividend: List[float], divisor: List[float]) -> Tuple[List[float], List[float]]:
        """
        Polynomial division.
        Returns (quotient, remainder) such that dividend = quotient * divisor + remainder
        """
        # Remove trailing zeros
        while len(dividend) > 1 and dividend[-1] == 0:
            dividend = dividend[:-1]
        while len(divisor) > 1 and divisor[-1] == 0:
            divisor = divisor[:-1]

        if len(dividend) < len(divisor):
            return [0.0], dividend.copy()

        quotient = [0.0] * (len(dividend) - len(divisor) + 1)
        remainder = dividend.copy()

        for i in range(len(quotient) - 1, -1, -1):
            if len(remainder) >= len(divisor) + i:
                coef = remainder[len(divisor) + i - 1] / divisor[-1]
                quotient[i] = coef
                for j in range(len(divisor)):
                    remainder[i + j] -= coef * divisor[j]

        # Clean up remainder
        while len(remainder) > 1 and abs(remainder[-1]) < 1e-10:
            remainder.pop()

        return quotient, remainder

    def poly_gcd(self, p1: List[float], p2: List[float]) -> List[float]:
        """GCD of two polynomials using Euclidean algorithm."""
        while len(p2) > 1 or (len(p2) == 1 and p2[0] != 0):
            _, r = self.poly_div(p1, p2)
            p1, p2 = p2, r
        # Normalize
        if p1[-1] != 0:
            return [c / p1[-1] for c in p1]
        return p1

    def poly_eval(self, p: List[float], x: float) -> float:
        """Evaluate polynomial at x using Horner's method."""
        result = 0.0
        for c in reversed(p):
            result = result * x + c
        return result

    def poly_derivative(self, p: List[float]) -> List[float]:
        """Derivative of polynomial."""
        if len(p) <= 1:
            return [0.0]
        return [i * p[i] for i in range(1, len(p))]

    def poly_integral(self, p: List[float], c: float = 0) -> List[float]:
        """Indefinite integral of polynomial with constant c."""
        result = [c] + [p[i] / (i + 1) for i in range(len(p))]
        return result

    def poly_roots_quadratic(self, p: List[float]) -> List[complex]:
        """Roots of quadratic polynomial ax² + bx + c."""
        if len(p) != 3:
            raise ValueError("Must be quadratic (3 coefficients)")
        c, b, a = p
        disc = b*b - 4*a*c
        if disc >= 0:
            sqrt_disc = _math.sqrt(disc)
            return [(-b + sqrt_disc) / (2*a), (-b - sqrt_disc) / (2*a)]
        else:
            sqrt_disc = _math.sqrt(-disc)
            return [complex(-b, sqrt_disc) / (2*a), complex(-b, -sqrt_disc) / (2*a)]

    def poly_roots_cubic(self, p: List[float]) -> List[complex]:
        """Roots of cubic using Cardano's formula."""
        if len(p) != 4:
            raise ValueError("Must be cubic (4 coefficients)")

        d, c, b, a = p
        # Normalize
        b, c, d = b/a, c/a, d/a

        # Depressed cubic: t³ + pt + q = 0
        p_coef = c - b**2/3
        q_coef = 2*b**3/27 - b*c/3 + d

        disc = (q_coef/2)**2 + (p_coef/3)**3

        def cbrt(x):
            if x >= 0:
                return x ** (1/3)
            return -((-x) ** (1/3))

        if disc > 0:
            u = cbrt(-q_coef/2 + _math.sqrt(disc))
            v = cbrt(-q_coef/2 - _math.sqrt(disc))
            t1 = u + v
            t2 = complex(-(u+v)/2, (u-v)*_math.sqrt(3)/2)
            t3 = complex(-(u+v)/2, -(u-v)*_math.sqrt(3)/2)
        elif disc == 0:
            u = cbrt(-q_coef/2)
            t1 = 2*u
            t2 = t3 = -u
        else:
            r = _math.sqrt(-(p_coef/3)**3)
            theta = _math.acos(-q_coef/(2*r))
            t1 = 2*cbrt(r)*_math.cos(theta/3)
            t2 = 2*cbrt(r)*_math.cos((theta + 2*_math.pi)/3)
            t3 = 2*cbrt(r)*_math.cos((theta + 4*_math.pi)/3)

        offset = -b/3
        return [t1 + offset, t2 + offset, t3 + offset]

    # ==================== FIELD THEORY ====================

    def gf_add(self, a: int, b: int, p: int) -> int:
        """Addition in GF(p)."""
        return (a + b) % p

    def gf_sub(self, a: int, b: int, p: int) -> int:
        """Subtraction in GF(p)."""
        return (a - b) % p

    def gf_mult(self, a: int, b: int, p: int) -> int:
        """Multiplication in GF(p)."""
        return (a * b) % p

    def gf_inv(self, a: int, p: int) -> int:
        """Multiplicative inverse in GF(p)."""
        def extended_gcd(a, b):
            if b == 0:
                return (a, 1, 0)
            g, x, y = extended_gcd(b, a % b)
            return (g, y, x - (a // b) * y)

        g, x, _ = extended_gcd(a % p, p)
        if g != 1:
            raise ValueError(f"{a} has no inverse mod {p}")
        return x % p

    def gf_div(self, a: int, b: int, p: int) -> int:
        """Division in GF(p): a/b mod p."""
        return self.gf_mult(a, self.gf_inv(b, p), p)

    def gf_exp(self, a: int, n: int, p: int) -> int:
        """Exponentiation in GF(p)."""
        return pow(a, n, p)

    def gf_poly_mult(self, p1: List[int], p2: List[int], mod: int) -> List[int]:
        """Polynomial multiplication over GF(mod)."""
        n1, n2 = len(p1), len(p2)
        result = [0] * (n1 + n2 - 1)
        for i in range(n1):
            for j in range(n2):
                result[i + j] = (result[i + j] + p1[i] * p2[j]) % mod
        return result

    def gf2_poly_mult(self, p1: int, p2: int) -> int:
        """
        Polynomial multiplication in GF(2).
        Polynomials represented as integers (bit k = coefficient of x^k).
        """
        result = 0
        while p2:
            if p2 & 1:
                result ^= p1
            p1 <<= 1
            p2 >>= 1
        return result

    def gf2_poly_mod(self, a: int, m: int) -> int:
        """Polynomial modulo in GF(2)."""
        deg_m = m.bit_length() - 1
        while a.bit_length() > deg_m:
            shift = a.bit_length() - m.bit_length()
            a ^= m << shift
        return a

    def gf2_poly_mult_mod(self, a: int, b: int, m: int) -> int:
        """Polynomial multiplication modulo m in GF(2)."""
        return self.gf2_poly_mod(self.gf2_poly_mult(a, b), m)

    def is_irreducible_gf2(self, p: int) -> bool:
        """Test if polynomial p is irreducible over GF(2)."""
        deg = p.bit_length() - 1
        if deg <= 1:
            return deg == 1

        # Check if p divides x^(2^k) + x for k < deg
        x = 2  # x as polynomial
        for k in range(1, deg):
            x_pow = x
            for _ in range(2**k - 1):
                x_pow = self.gf2_poly_mult_mod(x_pow, 2, p)
            if self.gf2_poly_mod(x_pow ^ 2, p) == 0:  # gcd != 1
                return False

        return True

    # ==================== LINEAR ALGEBRA OVER FIELDS ====================

    def matrix_mult_gf(self, A: List[List[int]], B: List[List[int]], p: int) -> List[List[int]]:
        """Matrix multiplication over GF(p)."""
        m, n = len(A), len(B[0])
        k = len(B)
        result = [[0] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                for l in range(k):
                    result[i][j] = (result[i][j] + A[i][l] * B[l][j]) % p
        return result

    def matrix_inv_gf(self, A: List[List[int]], p: int) -> Optional[List[List[int]]]:
        """Matrix inverse over GF(p) using Gauss-Jordan elimination."""
        n = len(A)
        # Augment with identity
        aug = [row[:] + [1 if i == j else 0 for j in range(n)] for i, row in enumerate(A)]

        for col in range(n):
            # Find pivot
            pivot_row = None
            for row in range(col, n):
                if aug[row][col] != 0:
                    pivot_row = row
                    break
            if pivot_row is None:
                return None

            aug[col], aug[pivot_row] = aug[pivot_row], aug[col]

            # Scale pivot row
            pivot_inv = self.gf_inv(aug[col][col], p)
            aug[col] = [(x * pivot_inv) % p for x in aug[col]]

            # Eliminate column
            for row in range(n):
                if row != col and aug[row][col] != 0:
                    factor = aug[row][col]
                    aug[row] = [(aug[row][j] - factor * aug[col][j]) % p for j in range(2*n)]

        return [row[n:] for row in aug]

    def determinant_gf(self, A: List[List[int]], p: int) -> int:
        """Determinant over GF(p)."""
        n = len(A)
        M = [row[:] for row in A]
        det = 1

        for col in range(n):
            # Find pivot
            pivot_row = None
            for row in range(col, n):
                if M[row][col] != 0:
                    pivot_row = row
                    break
            if pivot_row is None:
                return 0

            if pivot_row != col:
                M[col], M[pivot_row] = M[pivot_row], M[col]
                det = (-det) % p

            det = (det * M[col][col]) % p
            pivot_inv = self.gf_inv(M[col][col], p)

            for row in range(col + 1, n):
                if M[row][col] != 0:
                    factor = (M[row][col] * pivot_inv) % p
                    for j in range(col, n):
                        M[row][j] = (M[row][j] - factor * M[col][j]) % p

        return det

    def rank_gf(self, A: List[List[int]], p: int) -> int:
        """Matrix rank over GF(p)."""
        m, n = len(A), len(A[0])
        M = [row[:] for row in A]
        rank = 0

        for col in range(n):
            # Find pivot
            pivot_row = None
            for row in range(rank, m):
                if M[row][col] != 0:
                    pivot_row = row
                    break
            if pivot_row is None:
                continue

            M[rank], M[pivot_row] = M[pivot_row], M[rank]
            pivot_inv = self.gf_inv(M[rank][col], p)

            for row in range(rank + 1, m):
                if M[row][col] != 0:
                    factor = (M[row][col] * pivot_inv) % p
                    for j in range(col, n):
                        M[row][j] = (M[row][j] - factor * M[rank][j]) % p

            rank += 1

        return rank

    # ==================== QUATERNIONS ====================

    def quat_mult(self, q1: Tuple[float, float, float, float],
                  q2: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """Quaternion multiplication."""
        a1, b1, c1, d1 = q1
        a2, b2, c2, d2 = q2
        return (
            a1*a2 - b1*b2 - c1*c2 - d1*d2,
            a1*b2 + b1*a2 + c1*d2 - d1*c2,
            a1*c2 - b1*d2 + c1*a2 + d1*b2,
            a1*d2 + b1*c2 - c1*b2 + d1*a2
        )

    def quat_conjugate(self, q: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """Quaternion conjugate."""
        return (q[0], -q[1], -q[2], -q[3])

    def quat_norm(self, q: Tuple[float, float, float, float]) -> float:
        """Quaternion norm."""
        return _math.sqrt(sum(x*x for x in q))

    def quat_inverse(self, q: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
        """Quaternion multiplicative inverse."""
        norm_sq = sum(x*x for x in q)
        conj = self.quat_conjugate(q)
        return tuple(x / norm_sq for x in conj)

    def quat_to_rotation_matrix(self, q: Tuple[float, float, float, float]) -> List[List[float]]:
        """Convert unit quaternion to 3x3 rotation matrix."""
        w, x, y, z = q
        return [
            [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w],
            [2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w],
            [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y]
        ]


# Singleton instance
algebra = AbstractAlgebra()
