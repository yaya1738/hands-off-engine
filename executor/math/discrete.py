#!/usr/bin/env python3
"""
Discrete Mathematics - Combinatorics, Graph Theory, and Coding Theory

Covers:
- Combinatorics (permutations, combinations, partitions)
- Graph theory (paths, connectivity, coloring)
- Coding theory (error correction, Hamming codes)
- Boolean algebra
- Recurrence relations
- Generating functions
- Set theory operations

USAGE:
    from executor.math.discrete import discrete

    discrete.permutations(5, 3)  # 60
    discrete.combinations(10, 3)  # 120
    discrete.shortest_path(graph, start, end)
"""

import math as _math
from typing import List, Tuple, Dict, Set, Optional, Callable
from collections import defaultdict, deque
from functools import lru_cache
import heapq


class DiscreteMath:
    """Comprehensive discrete mathematics."""

    # ==================== COMBINATORICS ====================

    def factorial(self, n: int) -> int:
        """n! = n × (n-1) × ... × 1."""
        if n < 0:
            return 0
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    def permutations(self, n: int, r: int = None) -> int:
        """P(n,r) = n! / (n-r)!"""
        if r is None:
            r = n
        if r > n or r < 0:
            return 0
        result = 1
        for i in range(n - r + 1, n + 1):
            result *= i
        return result

    def combinations(self, n: int, r: int) -> int:
        """C(n,r) = n! / (r! × (n-r)!)"""
        if r > n or r < 0:
            return 0
        r = min(r, n - r)
        result = 1
        for i in range(r):
            result = result * (n - i) // (i + 1)
        return result

    def combinations_with_repetition(self, n: int, r: int) -> int:
        """Stars and bars: C(n+r-1, r)."""
        return self.combinations(n + r - 1, r)

    def multinomial(self, n: int, groups: List[int]) -> int:
        """Multinomial coefficient: n! / (k1! × k2! × ... × km!)"""
        if sum(groups) != n:
            return 0
        result = self.factorial(n)
        for k in groups:
            result //= self.factorial(k)
        return result

    @lru_cache(maxsize=1000)
    def catalan(self, n: int) -> int:
        """Catalan number C_n."""
        if n <= 1:
            return 1
        return self.combinations(2 * n, n) // (n + 1)

    @lru_cache(maxsize=1000)
    def bell(self, n: int) -> int:
        """Bell number B_n (number of partitions of n-set)."""
        if n == 0:
            return 1
        return sum(self.combinations(n - 1, k) * self.bell(k) for k in range(n))

    @lru_cache(maxsize=1000)
    def stirling_first(self, n: int, k: int) -> int:
        """Unsigned Stirling number of the first kind s(n,k)."""
        if n == k == 0:
            return 1
        if n == 0 or k == 0:
            return 0
        return (n - 1) * self.stirling_first(n - 1, k) + self.stirling_first(n - 1, k - 1)

    @lru_cache(maxsize=1000)
    def stirling_second(self, n: int, k: int) -> int:
        """Stirling number of the second kind S(n,k)."""
        if n == k == 0:
            return 1
        if n == 0 or k == 0:
            return 0
        return k * self.stirling_second(n - 1, k) + self.stirling_second(n - 1, k - 1)

    def derangements(self, n: int) -> int:
        """D_n = number of derangements (permutations with no fixed points)."""
        if n == 0:
            return 1
        if n == 1:
            return 0
        return (n - 1) * (self.derangements(n - 1) + self.derangements(n - 2))

    def partition_count(self, n: int) -> int:
        """p(n) = number of integer partitions of n."""
        if n < 0:
            return 0
        if n == 0:
            return 1

        dp = [0] * (n + 1)
        dp[0] = 1

        for i in range(1, n + 1):
            for j in range(i, n + 1):
                dp[j] += dp[j - i]

        return dp[n]

    def integer_partitions(self, n: int) -> List[List[int]]:
        """Generate all integer partitions of n."""
        def partition_helper(n, max_val):
            if n == 0:
                return [[]]
            partitions = []
            for i in range(min(n, max_val), 0, -1):
                for p in partition_helper(n - i, i):
                    partitions.append([i] + p)
            return partitions

        return partition_helper(n, n)

    def subset_sum_count(self, nums: List[int], target: int) -> int:
        """Count subsets summing to target."""
        dp = [0] * (target + 1)
        dp[0] = 1
        for num in nums:
            for j in range(target, num - 1, -1):
                dp[j] += dp[j - num]
        return dp[target]

    def generate_permutations(self, items: List) -> List[List]:
        """Generate all permutations."""
        if len(items) <= 1:
            return [items[:]]

        result = []
        for i in range(len(items)):
            rest = items[:i] + items[i+1:]
            for perm in self.generate_permutations(rest):
                result.append([items[i]] + perm)
        return result

    def generate_combinations(self, items: List, r: int) -> List[List]:
        """Generate all r-combinations."""
        if r == 0:
            return [[]]
        if len(items) < r:
            return []

        result = []
        for i in range(len(items) - r + 1):
            for comb in self.generate_combinations(items[i+1:], r - 1):
                result.append([items[i]] + comb)
        return result

    def powerset(self, items: List) -> List[List]:
        """Generate power set (all subsets)."""
        result = [[]]
        for item in items:
            result += [subset + [item] for subset in result]
        return result

    # ==================== GRAPH THEORY ====================

    def adjacency_list_to_matrix(self, adj_list: Dict[int, List[int]], n: int) -> List[List[int]]:
        """Convert adjacency list to adjacency matrix."""
        matrix = [[0] * n for _ in range(n)]
        for u, neighbors in adj_list.items():
            for v in neighbors:
                matrix[u][v] = 1
        return matrix

    def adjacency_matrix_to_list(self, matrix: List[List[int]]) -> Dict[int, List[int]]:
        """Convert adjacency matrix to adjacency list."""
        n = len(matrix)
        adj_list = {i: [] for i in range(n)}
        for i in range(n):
            for j in range(n):
                if matrix[i][j]:
                    adj_list[i].append(j)
        return adj_list

    def bfs(self, adj_list: Dict[int, List[int]], start: int) -> Tuple[Dict[int, int], Dict[int, int]]:
        """
        Breadth-first search.
        Returns (distances, parents) from start.
        """
        distances = {start: 0}
        parents = {start: None}
        queue = deque([start])

        while queue:
            u = queue.popleft()
            for v in adj_list.get(u, []):
                if v not in distances:
                    distances[v] = distances[u] + 1
                    parents[v] = u
                    queue.append(v)

        return distances, parents

    def dfs(self, adj_list: Dict[int, List[int]], start: int) -> Tuple[List[int], Dict[int, int]]:
        """
        Depth-first search.
        Returns (traversal_order, discovery_times).
        """
        visited = set()
        order = []
        times = {}
        time = [0]

        def dfs_visit(u):
            visited.add(u)
            times[u] = time[0]
            time[0] += 1
            order.append(u)
            for v in adj_list.get(u, []):
                if v not in visited:
                    dfs_visit(v)

        dfs_visit(start)
        return order, times

    def shortest_path(self, adj_list: Dict[int, List[Tuple[int, float]]],
                      start: int, end: int) -> Tuple[float, List[int]]:
        """
        Dijkstra's algorithm for weighted shortest path.
        adj_list[u] = [(v, weight), ...]
        Returns (distance, path).
        """
        distances = {start: 0}
        parents = {start: None}
        pq = [(0, start)]

        while pq:
            d, u = heapq.heappop(pq)
            if d > distances.get(u, float('inf')):
                continue

            if u == end:
                break

            for v, weight in adj_list.get(u, []):
                new_dist = d + weight
                if new_dist < distances.get(v, float('inf')):
                    distances[v] = new_dist
                    parents[v] = u
                    heapq.heappush(pq, (new_dist, v))

        if end not in distances:
            return float('inf'), []

        # Reconstruct path
        path = []
        node = end
        while node is not None:
            path.append(node)
            node = parents[node]
        path.reverse()

        return distances[end], path

    def bellman_ford(self, edges: List[Tuple[int, int, float]], n: int,
                     start: int) -> Tuple[Dict[int, float], bool]:
        """
        Bellman-Ford algorithm (handles negative weights).
        edges = [(u, v, weight), ...]
        Returns (distances, has_negative_cycle).
        """
        distances = {i: float('inf') for i in range(n)}
        distances[start] = 0

        for _ in range(n - 1):
            for u, v, w in edges:
                if distances[u] + w < distances[v]:
                    distances[v] = distances[u] + w

        # Check for negative cycles
        for u, v, w in edges:
            if distances[u] + w < distances[v]:
                return distances, True

        return distances, False

    def floyd_warshall(self, adj_matrix: List[List[float]]) -> List[List[float]]:
        """All-pairs shortest paths."""
        n = len(adj_matrix)
        dist = [row[:] for row in adj_matrix]

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i][k] + dist[k][j] < dist[i][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]

        return dist

    def topological_sort(self, adj_list: Dict[int, List[int]], n: int) -> Optional[List[int]]:
        """Topological sort using Kahn's algorithm."""
        in_degree = {i: 0 for i in range(n)}
        for u in adj_list:
            for v in adj_list[u]:
                in_degree[v] = in_degree.get(v, 0) + 1

        queue = deque([u for u in range(n) if in_degree[u] == 0])
        result = []

        while queue:
            u = queue.popleft()
            result.append(u)
            for v in adj_list.get(u, []):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(result) != n:
            return None  # Has cycle
        return result

    def connected_components(self, adj_list: Dict[int, List[int]], n: int) -> List[Set[int]]:
        """Find all connected components (undirected graph)."""
        visited = set()
        components = []

        for start in range(n):
            if start in visited:
                continue
            component = set()
            queue = deque([start])
            while queue:
                u = queue.popleft()
                if u in visited:
                    continue
                visited.add(u)
                component.add(u)
                for v in adj_list.get(u, []):
                    if v not in visited:
                        queue.append(v)
            components.append(component)

        return components

    def is_bipartite(self, adj_list: Dict[int, List[int]], n: int) -> Tuple[bool, Dict[int, int]]:
        """Check if graph is bipartite and return coloring."""
        color = {}

        for start in range(n):
            if start in color:
                continue
            queue = deque([start])
            color[start] = 0

            while queue:
                u = queue.popleft()
                for v in adj_list.get(u, []):
                    if v not in color:
                        color[v] = 1 - color[u]
                        queue.append(v)
                    elif color[v] == color[u]:
                        return False, {}

        return True, color

    def minimum_spanning_tree(self, edges: List[Tuple[int, int, float]], n: int) -> List[Tuple[int, int, float]]:
        """Kruskal's MST algorithm."""
        # Union-Find
        parent = list(range(n))
        rank = [0] * n

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px == py:
                return False
            if rank[px] < rank[py]:
                px, py = py, px
            parent[py] = px
            if rank[px] == rank[py]:
                rank[px] += 1
            return True

        edges_sorted = sorted(edges, key=lambda e: e[2])
        mst = []

        for u, v, w in edges_sorted:
            if union(u, v):
                mst.append((u, v, w))
                if len(mst) == n - 1:
                    break

        return mst

    def graph_chromatic_number(self, adj_list: Dict[int, List[int]], n: int) -> int:
        """Greedy upper bound on chromatic number."""
        colors = {}
        for u in range(n):
            neighbor_colors = {colors[v] for v in adj_list.get(u, []) if v in colors}
            c = 0
            while c in neighbor_colors:
                c += 1
            colors[u] = c
        return max(colors.values()) + 1 if colors else 0

    def euler_path_exists(self, adj_list: Dict[int, List[int]], directed: bool = False) -> Tuple[bool, Optional[int]]:
        """
        Check if Euler path exists.
        Returns (exists, start_vertex).
        """
        if not directed:
            # Undirected: all vertices even degree, or exactly 2 odd degree
            degrees = {u: len(neighbors) for u, neighbors in adj_list.items()}
            odd_vertices = [u for u, d in degrees.items() if d % 2 == 1]

            if len(odd_vertices) == 0:
                return True, next(iter(adj_list), None)
            elif len(odd_vertices) == 2:
                return True, odd_vertices[0]
            else:
                return False, None
        else:
            # Directed: at most one vertex with out-in=1, at most one with in-out=1
            in_deg = defaultdict(int)
            out_deg = defaultdict(int)
            for u, neighbors in adj_list.items():
                out_deg[u] = len(neighbors)
                for v in neighbors:
                    in_deg[v] += 1

            start_candidates = []
            end_candidates = []
            for u in set(in_deg.keys()) | set(out_deg.keys()):
                diff = out_deg[u] - in_deg[u]
                if diff == 1:
                    start_candidates.append(u)
                elif diff == -1:
                    end_candidates.append(u)
                elif diff != 0:
                    return False, None

            if len(start_candidates) == 0 and len(end_candidates) == 0:
                return True, next(iter(adj_list), None)
            elif len(start_candidates) == 1 and len(end_candidates) == 1:
                return True, start_candidates[0]
            else:
                return False, None

    # ==================== CODING THEORY ====================

    def hamming_distance(self, x: int, y: int) -> int:
        """Hamming distance between two integers."""
        return bin(x ^ y).count('1')

    def hamming_distance_str(self, s1: str, s2: str) -> int:
        """Hamming distance between two strings."""
        return sum(c1 != c2 for c1, c2 in zip(s1, s2))

    def hamming_encode_7_4(self, data: int) -> int:
        """
        Hamming(7,4) encoding.
        Takes 4-bit data, returns 7-bit codeword.
        """
        # Data bits: d1, d2, d3, d4
        d = [(data >> i) & 1 for i in range(4)]

        # Parity bits
        p1 = d[0] ^ d[1] ^ d[3]  # positions 1,3,5,7
        p2 = d[0] ^ d[2] ^ d[3]  # positions 2,3,6,7
        p4 = d[1] ^ d[2] ^ d[3]  # positions 4,5,6,7

        # Codeword: p1 p2 d1 p4 d2 d3 d4
        return (p1 << 6) | (p2 << 5) | (d[0] << 4) | (p4 << 3) | (d[1] << 2) | (d[2] << 1) | d[3]

    def hamming_decode_7_4(self, codeword: int) -> Tuple[int, bool]:
        """
        Hamming(7,4) decoding with error correction.
        Returns (data, had_error).
        """
        bits = [(codeword >> (6-i)) & 1 for i in range(7)]

        # Syndrome
        s1 = bits[0] ^ bits[2] ^ bits[4] ^ bits[6]
        s2 = bits[1] ^ bits[2] ^ bits[5] ^ bits[6]
        s4 = bits[3] ^ bits[4] ^ bits[5] ^ bits[6]

        error_pos = s1 + 2*s2 + 4*s4
        had_error = error_pos > 0

        if error_pos > 0:
            bits[error_pos - 1] ^= 1

        # Extract data bits (positions 3,5,6,7 -> indices 2,4,5,6)
        data = (bits[2] << 3) | (bits[4] << 2) | (bits[5] << 1) | bits[6]
        return data, had_error

    def parity_check(self, data: List[int]) -> int:
        """Simple parity bit."""
        return sum(data) % 2

    def crc(self, data: int, polynomial: int) -> int:
        """CRC (Cyclic Redundancy Check) remainder."""
        poly_degree = polynomial.bit_length() - 1
        data_shifted = data << poly_degree

        while data_shifted.bit_length() >= polynomial.bit_length():
            shift = data_shifted.bit_length() - polynomial.bit_length()
            data_shifted ^= polynomial << shift

        return data_shifted

    # ==================== BOOLEAN ALGEBRA ====================

    def boolean_eval(self, expr: str, values: Dict[str, bool]) -> bool:
        """Evaluate boolean expression."""
        # Simple parser for AND (&), OR (|), NOT (~), XOR (^)
        expr = expr.replace('AND', '&').replace('OR', '|').replace('NOT', '~').replace('XOR', '^')
        for var, val in values.items():
            expr = expr.replace(var, str(val))
        return eval(expr)

    def truth_table(self, expr: str, variables: List[str]) -> List[Tuple[Tuple[bool, ...], bool]]:
        """Generate truth table for boolean expression."""
        n = len(variables)
        table = []

        for i in range(2**n):
            values = {}
            for j, var in enumerate(variables):
                values[var] = bool((i >> (n-1-j)) & 1)
            result = self.boolean_eval(expr, values)
            table.append((tuple(values[v] for v in variables), result))

        return table

    def dnf_from_truth_table(self, table: List[Tuple[Tuple[bool, ...], bool]],
                             variables: List[str]) -> str:
        """Disjunctive Normal Form from truth table."""
        terms = []
        for inputs, output in table:
            if output:
                term = []
                for var, val in zip(variables, inputs):
                    if val:
                        term.append(var)
                    else:
                        term.append(f"~{var}")
                terms.append("(" + " & ".join(term) + ")")

        return " | ".join(terms) if terms else "False"

    def cnf_from_truth_table(self, table: List[Tuple[Tuple[bool, ...], bool]],
                             variables: List[str]) -> str:
        """Conjunctive Normal Form from truth table."""
        clauses = []
        for inputs, output in table:
            if not output:
                clause = []
                for var, val in zip(variables, inputs):
                    if val:
                        clause.append(f"~{var}")
                    else:
                        clause.append(var)
                clauses.append("(" + " | ".join(clause) + ")")

        return " & ".join(clauses) if clauses else "True"


# Singleton instance
discrete = DiscreteMath()
