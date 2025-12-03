"""
Computing Knowledge Base
========================

Complete Earth computing knowledge - breadth and depth.

KNOWLEDGE FILES:
----------------
- KNOWLEDGE.md: Complete computing reference (20 sections)
- KNOWLEDGE_ADVANCED.md: Deep technical internals (20 sections)

TOPICS COVERED (KNOWLEDGE.md):
-----------------------------
1. Nature of Computation - Theory, models, computability
2. Computer Architecture - Von Neumann, CPU, pipelining
3. Digital Logic & Circuits - Boolean algebra, gates, FSM
4. Memory Systems - Hierarchy, virtual memory, cache
5. Operating Systems - Processes, threads, file systems
6. Programming Languages - Paradigms, types, memory
7. Algorithms - Complexity, sorting, searching, DP
8. Data Structures - Arrays, trees, graphs, hashes
9. Networking - OSI, TCP/IP, protocols
10. Distributed Systems - CAP, consensus, queues
11. Databases - SQL, NoSQL, transactions
12. Security & Cryptography - Encryption, hashing, auth
13. Artificial Intelligence - Search, knowledge, NLP
14. Machine Learning - Supervised, unsupervised, deep
15. Software Engineering - Agile, patterns, testing
16. Computer Graphics - Rendering, shaders, 3D
17. Human-Computer Interaction - UI/UX, accessibility
18. Compilers & Language Processing - Parsing, optimization
19. Parallel & Concurrent Computing - Threading, GPU
20. Emerging Computing Paradigms - Quantum, neuromorphic

ADVANCED TOPICS (KNOWLEDGE_ADVANCED.md):
--------------------------------------
1. Transistor Physics & VLSI - MOSFETs, timing, power
2. CPU Microarchitecture - Tomasulo, branch prediction
3. Cache Coherence Protocols - MSI, MESI, directory
4. Memory Management Internals - Page tables, TLB
5. OS Kernel Internals - Syscalls, scheduler, RCU
6. Type Theory & Lambda Calculus - Formal systems
7. Algorithm Complexity Theory - NP, approximation
8. Cryptographic Internals - AES, RSA, ECC
9. Consensus Algorithm Mathematics - Paxos, Raft, BFT
10. Database Engine Internals - B+ trees, MVCC
11. Neural Network Mathematics - Backprop, attention
12. Compiler Optimization - SSA, dataflow, register alloc
13. GPU Architecture Deep Dive - CUDA, tensor cores
14. Network Protocol Internals - TCP, TLS, HTTP/2
15. Distributed Systems Theory - Clocks, FLP, replication
16. Formal Verification - Model checking, theorem proving
17. Quantum Computing Mathematics - Gates, algorithms, QEC
18. Information Theory Deep Dive - Entropy, channel capacity
19. Computational Complexity Classes - PH, #P, oracles
20. Future Computing Architectures - Beyond Moore's Law

KEY CONCEPTS:
-------------
- Turing Machine: Universal computation model
- Big-O: Algorithm complexity notation
- Cache: Fast memory hierarchy level
- Process: Running program instance
- Thread: Lightweight execution unit
- TCP: Reliable transport protocol
- SQL: Structured query language
- SHA: Secure hash algorithm
- Neural Network: ML computation graph
- Quantum Bit: Superposition state |ψ⟩ = α|0⟩ + β|1⟩

USAGE:
------
```python
# Read the knowledge
from executor.computing import KNOWLEDGE_PATH, KNOWLEDGE_ADVANCED_PATH

# Or import constants
from executor.computing import (
    COMPLEXITY_CLASSES,
    SORTING_ALGORITHMS,
    DATA_STRUCTURES,
    NETWORK_LAYERS,
)
```
"""

import os

# Knowledge file paths
KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), "KNOWLEDGE.md")
KNOWLEDGE_ADVANCED_PATH = os.path.join(os.path.dirname(__file__), "KNOWLEDGE_ADVANCED.md")

# ===========================================
# COMPLEXITY CLASSES
# ===========================================

COMPLEXITY_CLASSES = {
    "O(1)": "Constant - Hash table lookup",
    "O(log n)": "Logarithmic - Binary search",
    "O(n)": "Linear - Array scan",
    "O(n log n)": "Linearithmic - Merge sort",
    "O(n²)": "Quadratic - Nested loops",
    "O(n³)": "Cubic - Matrix multiplication (naive)",
    "O(2^n)": "Exponential - Subset enumeration",
    "O(n!)": "Factorial - Permutations",
}

# ===========================================
# ALGORITHM COMPLEXITY
# ===========================================

SORTING_ALGORITHMS = {
    "bubble_sort": {"best": "O(n)", "average": "O(n²)", "worst": "O(n²)", "space": "O(1)", "stable": True},
    "selection_sort": {"best": "O(n²)", "average": "O(n²)", "worst": "O(n²)", "space": "O(1)", "stable": False},
    "insertion_sort": {"best": "O(n)", "average": "O(n²)", "worst": "O(n²)", "space": "O(1)", "stable": True},
    "merge_sort": {"best": "O(n log n)", "average": "O(n log n)", "worst": "O(n log n)", "space": "O(n)", "stable": True},
    "quick_sort": {"best": "O(n log n)", "average": "O(n log n)", "worst": "O(n²)", "space": "O(log n)", "stable": False},
    "heap_sort": {"best": "O(n log n)", "average": "O(n log n)", "worst": "O(n log n)", "space": "O(1)", "stable": False},
    "counting_sort": {"best": "O(n+k)", "average": "O(n+k)", "worst": "O(n+k)", "space": "O(k)", "stable": True},
    "radix_sort": {"best": "O(nk)", "average": "O(nk)", "worst": "O(nk)", "space": "O(n+k)", "stable": True},
}

SEARCH_ALGORITHMS = {
    "linear_search": {"time": "O(n)", "space": "O(1)", "requires_sorted": False},
    "binary_search": {"time": "O(log n)", "space": "O(1)", "requires_sorted": True},
    "hash_lookup": {"time": "O(1) average", "space": "O(n)", "requires_sorted": False},
    "bfs": {"time": "O(V+E)", "space": "O(V)", "type": "graph"},
    "dfs": {"time": "O(V+E)", "space": "O(V)", "type": "graph"},
}

# ===========================================
# DATA STRUCTURES
# ===========================================

DATA_STRUCTURES = {
    "array": {
        "access": "O(1)",
        "search": "O(n)",
        "insert": "O(n)",
        "delete": "O(n)",
    },
    "linked_list": {
        "access": "O(n)",
        "search": "O(n)",
        "insert": "O(1)",
        "delete": "O(1)",
    },
    "hash_table": {
        "access": "N/A",
        "search": "O(1) avg",
        "insert": "O(1) avg",
        "delete": "O(1) avg",
    },
    "binary_search_tree": {
        "access": "O(log n)",
        "search": "O(log n)",
        "insert": "O(log n)",
        "delete": "O(log n)",
    },
    "heap": {
        "access": "O(1) for min/max",
        "search": "O(n)",
        "insert": "O(log n)",
        "delete": "O(log n)",
    },
}

# ===========================================
# NETWORK LAYERS
# ===========================================

NETWORK_LAYERS = {
    "OSI": {
        7: ("Application", ["HTTP", "FTP", "DNS", "SMTP"]),
        6: ("Presentation", ["SSL/TLS", "JPEG", "ASCII"]),
        5: ("Session", ["NetBIOS", "RPC"]),
        4: ("Transport", ["TCP", "UDP"]),
        3: ("Network", ["IP", "ICMP", "OSPF"]),
        2: ("Data Link", ["Ethernet", "WiFi", "PPP"]),
        1: ("Physical", ["Cables", "Radio"]),
    },
    "TCP/IP": {
        4: ("Application", ["HTTP", "DNS", "FTP"]),
        3: ("Transport", ["TCP", "UDP"]),
        2: ("Internet", ["IP", "ICMP"]),
        1: ("Network Access", ["Ethernet", "WiFi"]),
    },
}

# ===========================================
# PROGRAMMING PARADIGMS
# ===========================================

PARADIGMS = {
    "imperative": "Sequential statements that change state",
    "declarative": "Describe what result you want",
    "functional": "Pure functions, immutability, composition",
    "object_oriented": "Encapsulation, inheritance, polymorphism",
    "logic": "Facts and rules, query engine",
    "concurrent": "Multiple execution flows",
}

# ===========================================
# CRYPTOGRAPHIC CONSTANTS
# ===========================================

CRYPTO = {
    "symmetric": {
        "AES": {"key_sizes": [128, 192, 256], "block_size": 128},
        "ChaCha20": {"key_size": 256, "nonce_size": 96},
    },
    "asymmetric": {
        "RSA": {"min_key_size": 2048, "common": [2048, 4096]},
        "ECC": {"curves": ["P-256", "P-384", "P-521", "Curve25519"]},
    },
    "hash": {
        "SHA-256": {"output": 256},
        "SHA-384": {"output": 384},
        "SHA-512": {"output": 512},
        "SHA3-256": {"output": 256},
    },
}

# ===========================================
# DATABASE ISOLATION LEVELS
# ===========================================

ISOLATION_LEVELS = {
    "read_uncommitted": {
        "dirty_read": True,
        "non_repeatable_read": True,
        "phantom_read": True,
    },
    "read_committed": {
        "dirty_read": False,
        "non_repeatable_read": True,
        "phantom_read": True,
    },
    "repeatable_read": {
        "dirty_read": False,
        "non_repeatable_read": False,
        "phantom_read": True,
    },
    "serializable": {
        "dirty_read": False,
        "non_repeatable_read": False,
        "phantom_read": False,
    },
}

# ===========================================
# MACHINE LEARNING
# ===========================================

ML_ALGORITHMS = {
    "supervised": {
        "linear_regression": "Continuous output",
        "logistic_regression": "Binary classification",
        "decision_tree": "Tree-based classification/regression",
        "random_forest": "Ensemble of decision trees",
        "svm": "Maximum margin classifier",
        "neural_network": "Universal function approximator",
    },
    "unsupervised": {
        "k_means": "Centroid-based clustering",
        "hierarchical": "Tree-based clustering",
        "pca": "Dimensionality reduction",
        "autoencoder": "Neural network compression",
    },
    "reinforcement": {
        "q_learning": "Value-based, off-policy",
        "policy_gradient": "Direct policy optimization",
        "actor_critic": "Combined value and policy",
    },
}

# ===========================================
# HELPER FUNCTIONS
# ===========================================

def get_knowledge() -> str:
    """Read the main computing knowledge document."""
    with open(KNOWLEDGE_PATH, 'r') as f:
        return f.read()


def get_advanced_knowledge() -> str:
    """Read the advanced computing knowledge document."""
    with open(KNOWLEDGE_ADVANCED_PATH, 'r') as f:
        return f.read()


def get_complexity(algorithm: str) -> dict:
    """Get complexity information for an algorithm."""
    if algorithm in SORTING_ALGORITHMS:
        return SORTING_ALGORITHMS[algorithm]
    if algorithm in SEARCH_ALGORITHMS:
        return SEARCH_ALGORITHMS[algorithm]
    return None


def get_data_structure_complexity(ds: str) -> dict:
    """Get operation complexities for a data structure."""
    return DATA_STRUCTURES.get(ds)


def compare_sort_algorithms(metric: str = "worst") -> list:
    """Compare sorting algorithms by a metric."""
    items = [
        (name, info[metric])
        for name, info in SORTING_ALGORITHMS.items()
    ]
    return sorted(items, key=lambda x: x[1])


def estimate_time_complexity(n: int, complexity: str) -> str:
    """Estimate operations for given n and complexity class."""
    import math

    complexities = {
        "O(1)": 1,
        "O(log n)": math.log2(n) if n > 0 else 0,
        "O(n)": n,
        "O(n log n)": n * math.log2(n) if n > 0 else 0,
        "O(n²)": n ** 2,
        "O(n³)": n ** 3,
        "O(2^n)": 2 ** min(n, 30),  # Cap to prevent overflow
        "O(n!)": math.factorial(min(n, 12)),  # Cap
    }

    ops = complexities.get(complexity)
    if ops is None:
        return "Unknown complexity class"

    if ops < 1000:
        return f"{ops:.0f} operations"
    elif ops < 1_000_000:
        return f"{ops/1000:.1f}K operations"
    elif ops < 1_000_000_000:
        return f"{ops/1_000_000:.1f}M operations"
    else:
        return f"{ops/1_000_000_000:.1f}B operations"


def get_network_layer(layer_num: int, model: str = "OSI") -> tuple:
    """Get network layer information."""
    layers = NETWORK_LAYERS.get(model, {})
    return layers.get(layer_num)


# ===========================================
# EXPORTS
# ===========================================

__all__ = [
    # Paths
    "KNOWLEDGE_PATH",
    "KNOWLEDGE_ADVANCED_PATH",

    # Constants
    "COMPLEXITY_CLASSES",
    "SORTING_ALGORITHMS",
    "SEARCH_ALGORITHMS",
    "DATA_STRUCTURES",
    "NETWORK_LAYERS",
    "PARADIGMS",
    "CRYPTO",
    "ISOLATION_LEVELS",
    "ML_ALGORITHMS",

    # Functions
    "get_knowledge",
    "get_advanced_knowledge",
    "get_complexity",
    "get_data_structure_complexity",
    "compare_sort_algorithms",
    "estimate_time_complexity",
    "get_network_layer",
]
