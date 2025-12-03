# COMPUTING KNOWLEDGE - ADVANCED
## Deep Technical Internals

*The hidden depths of computing - internals, mathematics, and implementation details*

---

# TABLE OF CONTENTS

1. [Transistor Physics & VLSI](#1-transistor-physics--vlsi)
2. [CPU Microarchitecture Internals](#2-cpu-microarchitecture-internals)
3. [Cache Coherence Protocols](#3-cache-coherence-protocols)
4. [Memory Management Internals](#4-memory-management-internals)
5. [Operating System Kernel Internals](#5-operating-system-kernel-internals)
6. [Type Theory & Lambda Calculus](#6-type-theory--lambda-calculus)
7. [Algorithm Complexity Theory](#7-algorithm-complexity-theory)
8. [Cryptographic Internals](#8-cryptographic-internals)
9. [Consensus Algorithm Mathematics](#9-consensus-algorithm-mathematics)
10. [Database Engine Internals](#10-database-engine-internals)
11. [Neural Network Mathematics](#11-neural-network-mathematics)
12. [Compiler Optimization Internals](#12-compiler-optimization-internals)
13. [GPU Architecture Deep Dive](#13-gpu-architecture-deep-dive)
14. [Network Protocol Internals](#14-network-protocol-internals)
15. [Distributed Systems Theory](#15-distributed-systems-theory)
16. [Formal Verification](#16-formal-verification)
17. [Quantum Computing Mathematics](#17-quantum-computing-mathematics)
18. [Information Theory Deep Dive](#18-information-theory-deep-dive)
19. [Computational Complexity Classes](#19-computational-complexity-classes)
20. [Future Computing Architectures](#20-future-computing-architectures)

---

# 1. TRANSISTOR PHYSICS & VLSI

## 1.1 Semiconductor Physics

### Band Theory
```
Energy bands in solids:
- Conduction band: Electrons can move freely
- Valence band: Bound electrons
- Band gap: Energy difference (Eg)

Materials by band gap:
- Conductor: Eg ≈ 0 (overlapping bands)
- Semiconductor: Eg = 0.5-3 eV
- Insulator: Eg > 3 eV

Silicon: Eg = 1.12 eV at 300K
```

### Doping
```
n-type: Donor atoms (P, As)
- Extra electrons
- Majority carriers: electrons

p-type: Acceptor atoms (B)
- Holes (missing electrons)
- Majority carriers: holes

Carrier concentration:
n · p = ni² (mass action law)
ni = intrinsic carrier concentration
```

### PN Junction
```
Depletion region: No free carriers
Built-in voltage: Vbi = (kT/q) ln(NA·ND/ni²)

Forward bias: Reduces barrier, current flows
Reverse bias: Increases barrier, blocks current

I = Is(e^(qV/nkT) - 1)  (Shockley equation)
```

## 1.2 MOSFET Operation

### Structure
```
        Gate
         ▼
   ╔═══════════╗
   ║   Oxide   ║  ← SiO2
═══╬═══════════╬═══
│ S│ Channel │ D│  ← n+ doped
═══╬═══════════╬═══
   ║  p-type  ║   ← Body/Substrate
   ╚═══════════╝

S = Source, D = Drain, G = Gate
```

### Operating Regions
```
Cutoff: Vgs < Vth, no channel
  Id = 0

Linear (Triode): Vds < Vgs - Vth
  Id = μn·Cox·(W/L)·[(Vgs-Vth)·Vds - Vds²/2]

Saturation: Vds ≥ Vgs - Vth
  Id = (μn·Cox/2)·(W/L)·(Vgs-Vth)²

μn = electron mobility
Cox = oxide capacitance
W/L = width/length ratio
Vth = threshold voltage
```

### Short Channel Effects
```
DIBL: Drain-Induced Barrier Lowering
  - Drain field reduces Vth
  - Subthreshold leakage increases

Velocity Saturation:
  - v = vsat at high E-field
  - Id doesn't increase as expected

Hot Carrier Effects:
  - High energy electrons
  - Oxide damage, threshold shift

Solutions:
  - FinFET: 3D transistor structure
  - SOI: Silicon on Insulator
  - High-k dielectrics
  - Metal gates
```

## 1.3 VLSI Design

### Design Hierarchy
```
System → Chip → Block → Module → Gate → Transistor

Abstraction levels:
1. Behavioral: Algorithm, C/SystemC
2. RTL: Registers + logic, Verilog/VHDL
3. Gate: Logic gates, netlist
4. Transistor: MOSFETs
5. Physical: Layout, GDSII
```

### Standard Cell Design
```
Standard cells: Pre-designed gates
  - Fixed height, variable width
  - Power rails at top/bottom
  - Pins on routing grid

Cell library:
  - INV, NAND, NOR, XOR
  - D flip-flop, latch
  - Multiple drive strengths (1x, 2x, 4x)
```

### Physical Design Flow
```
1. Floorplanning: Block placement
2. Power Planning: Power grid design
3. Placement: Standard cell placement
4. Clock Tree Synthesis: Clock distribution
5. Routing: Wire connections
6. Timing Closure: Meet timing constraints
7. Physical Verification: DRC, LVS
8. Tape-out: GDSII generation
```

### Timing Analysis
```
Static Timing Analysis (STA):
  - Path-based, no simulation
  - Setup time: Data stable before clock
  - Hold time: Data stable after clock

Setup constraint:
  Tclk > Tcq + Tlogic + Tsetup + Tskew

Hold constraint:
  Tcq + Tlogic > Thold - Tskew

Slack = Required - Actual
  Positive slack: Timing met
  Negative slack: Timing violation
```

### Power Analysis
```
Dynamic power:
  Pdyn = α·C·V²·f
  α = activity factor
  C = capacitance
  V = voltage
  f = frequency

Static power:
  Pstatic = Ileak·V

Leakage current:
  Ileak = I0·e^((Vgs-Vth)/(n·Vt))

Power optimization:
  - Clock gating
  - Multi-Vth cells
  - Voltage scaling
  - Power gating
```

---

# 2. CPU MICROARCHITECTURE INTERNALS

## 2.1 Pipeline Deep Dive

### 5-Stage RISC Pipeline
```
IF: Instruction Fetch
  - PC → Instruction Memory → IR
  - PC ← PC + 4

ID: Instruction Decode
  - Decode opcode
  - Read register file
  - Sign-extend immediate

EX: Execute
  - ALU operations
  - Address calculation
  - Branch resolution

MEM: Memory Access
  - Load: Read data memory
  - Store: Write data memory

WB: Write Back
  - Write result to register file
```

### Pipeline Registers
```
IF/ID: {PC, IR}
ID/EX: {PC, Rs1, Rs2, Imm, Rd, Control}
EX/MEM: {ALU_result, Rs2_data, Rd, Control}
MEM/WB: {ALU_result, Mem_data, Rd, Control}

Control signals propagate with data
```

### Hazard Detection Unit
```python
def detect_data_hazard(ID_EX, IF_ID):
    # RAW hazard detection
    if ID_EX.MemRead:
        if (ID_EX.Rd == IF_ID.Rs1) or (ID_EX.Rd == IF_ID.Rs2):
            return STALL
    return NO_STALL

def forwarding_unit(EX_MEM, MEM_WB, ID_EX):
    # Forward from EX/MEM
    if EX_MEM.RegWrite and EX_MEM.Rd == ID_EX.Rs1:
        ForwardA = EX_MEM
    # Forward from MEM/WB
    elif MEM_WB.RegWrite and MEM_WB.Rd == ID_EX.Rs1:
        ForwardA = MEM_WB
    else:
        ForwardA = ID_EX
    # Similar for Rs2...
```

## 2.2 Out-of-Order Execution

### Tomasulo's Algorithm Details
```
Structures:
1. Reservation Stations (RS):
   - Op: Operation code
   - Qj, Qk: Tags for source operands
   - Vj, Vk: Values of source operands
   - A: Address for load/store
   - Busy: In use flag

2. Register Alias Table (RAT):
   - Maps architectural to physical registers
   - Tracks which RS will produce result

3. Reorder Buffer (ROB):
   - Circular buffer
   - Entries: {Type, Dest, Value, Ready}
   - In-order commit for precise exceptions

4. Common Data Bus (CDB):
   - Broadcasts results
   - Tag + Value
   - All waiting RS snoop
```

### Execution Flow
```
1. Issue:
   - Decode instruction
   - Allocate ROB entry
   - Allocate RS if available
   - Read ready operands
   - Update RAT with ROB tag

2. Execute:
   - When all operands ready (Qj=0, Qk=0)
   - Send to functional unit
   - Compute result

3. Write Result:
   - Broadcast on CDB
   - Waiting RS capture result
   - Mark ROB entry ready

4. Commit:
   - When ROB head is ready
   - Update architectural state
   - Deallocate ROB entry
   - Update RAT if needed
```

### Branch Prediction Details

**Tournament Predictor**:
```
Components:
1. Local predictor: Per-branch history
   - Branch History Table (BHT)
   - Pattern History Table (PHT)

2. Global predictor: All-branch history
   - Global History Register (GHR)
   - Global Pattern History Table

3. Choice predictor: Which to use
   - 2-bit saturating counter
   - Update based on accuracy

Prediction:
  if choice.predict() == LOCAL:
      return local.predict(PC)
  else:
      return global.predict(GHR)
```

**Branch Target Buffer (BTB)**:
```
Cache of branch targets
Indexed by PC (or part of PC)
Entries: {Tag, Target, Type}
Enables fetch from target before decode
```

## 2.3 Memory Subsystem

### Load-Store Queue
```
Load Queue (LQ):
  - Track in-flight loads
  - Detect store-load forwarding
  - Handle memory ordering

Store Queue (SQ):
  - Buffer stores until commit
  - Provide data for forwarding
  - Combine adjacent stores

Store-to-Load Forwarding:
  if load.addr matches store.addr:
      if store.data_ready:
          forward data
      else:
          stall load
```

### Memory Ordering
```
Total Store Order (x86/TSO):
  - Stores seen in program order
  - Loads can pass stores
  - Store buffer forwarding allowed

Relaxed Memory Order (ARM/RISC-V):
  - Reordering possible
  - Memory barriers enforce order
  - fence, dmb, dsb instructions

Memory Barriers:
  - LoadLoad: Complete loads before loads
  - LoadStore: Complete loads before stores
  - StoreLoad: Complete stores before loads
  - StoreStore: Complete stores before stores
```

## 2.4 Advanced Techniques

### Speculative Execution
```
Execute before knowing if correct:
  - Branch prediction → execute both paths
  - Memory disambiguation → load before store resolves
  - Exception handling → execute past potential exception

Recovery on misspeculation:
  - Flush pipeline
  - Restore checkpoint
  - Restart from correct path

Security concerns (Spectre):
  - Side channels leak speculative state
  - Cache timing reveals data
  - Mitigations: barriers, microcode updates
```

### Simultaneous Multithreading (SMT)
```
Multiple threads share pipeline

Resource sharing:
  - Shared: Execution units, caches
  - Partitioned: ROB entries, RS
  - Replicated: PC, RAT, architectural registers

Thread selection:
  - ICOUNT: Fewest instructions wins
  - Flush: Flush on cache miss
  - Round-robin

Benefits:
  - Hide memory latency
  - Better resource utilization
  - Higher throughput
```

---

# 3. CACHE COHERENCE PROTOCOLS

## 3.1 Coherence Problem

### Shared Memory Challenge
```
CPU0: Write X=1     CPU1: Read X=?
  ↓                    ↓
[Cache0: X=1]      [Cache1: X=0 (stale)]
        ↘            ↙
         [Memory: X=0]

Without coherence: CPU1 reads stale data
With coherence: CPU1 sees X=1
```

### Coherence Properties
```
1. Single Writer, Multiple Reader (SWMR):
   At any time, either:
   - One cache has write permission, OR
   - Multiple caches have read permission

2. Data Value Invariant:
   Value at start of epoch = value at end of last epoch

3. Write Propagation:
   Writes eventually visible to all processors

4. Write Serialization:
   All processors see writes in same order
```

## 3.2 Snooping Protocols

### MSI Protocol
```
States:
  M (Modified): Dirty, exclusive
  S (Shared): Clean, may be shared
  I (Invalid): Not in cache

Transitions (CPU events):
  I --PrRd/BusRd--> S
  I --PrWr/BusRdX--> M
  S --PrRd/--> S
  S --PrWr/BusRdX--> M
  M --PrRd/--> M
  M --PrWr/--> M

Transitions (Bus snoops):
  S --BusRdX/Flush--> I
  M --BusRd/Flush--> S
  M --BusRdX/Flush--> I
```

### MESI Protocol (Intel)
```
States:
  M (Modified): Dirty, exclusive
  E (Exclusive): Clean, exclusive
  S (Shared): Clean, may be shared
  I (Invalid): Not in cache

Key addition: E state
  - Data clean in cache only
  - Can upgrade to M without bus transaction
  - Optimization for single-reader patterns
```

### MOESI Protocol (AMD)
```
States:
  M (Modified): Dirty, exclusive
  O (Owned): Dirty, shared (owner)
  E (Exclusive): Clean, exclusive
  S (Shared): Clean, may be shared
  I (Invalid): Not in cache

Key addition: O state
  - Cache owns dirty line
  - Can share without writeback
  - Other caches have S copies
```

## 3.3 Directory Protocols

### Directory Structure
```
Directory entry per cache line:
{
  state: {Uncached, Shared, Exclusive, Modified}
  sharers: bitmap of caches with copies
  owner: ID of owning cache (if modified)
}

Located:
  - At home node (memory location)
  - Distributed based on address
```

### Directory Protocol Operations
```
Read Miss:
1. Requestor → Home: Read request
2. Home checks directory state
   - Uncached: Home → Requestor: Data + Shared
   - Shared: Home → Requestor: Data + add to sharers
   - Modified: Home → Owner: Forward
               Owner → Requestor: Data
               Owner → Home: Shared

Write Miss:
1. Requestor → Home: Exclusive request
2. Home invalidates sharers
3. Home → Requestor: Exclusive access
```

### Scalability
```
Snooping:
  - All transactions broadcast
  - O(N²) traffic with N processors
  - Limited to ~16-64 processors

Directory:
  - Point-to-point messages
  - O(N) storage per line
  - Scales to thousands of processors

Optimization:
  - Limited pointer directory
  - Coarse-grain tracking
  - Hierarchical directories
```

## 3.4 Memory Consistency

### Sequential Consistency (SC)
```
Definition: Result equivalent to some sequential interleaving
             that respects program order

Requirements:
  - Program order: Memory ops in program order
  - Write atomicity: All processors see write simultaneously

Too strict for performance:
  - No store buffers
  - No speculative loads
```

### Total Store Order (TSO)
```
Relaxations from SC:
  - Reads can bypass pending writes (to different addresses)
  - Store buffer allows reordering

Preserved:
  - Write order (StoreStore)
  - Read order (LoadLoad)
  - Read after write to same address

x86, SPARC TSO use this model
```

### Release Consistency
```
Synchronization primitives:
  - Acquire: Gain permission (e.g., lock)
  - Release: Relinquish permission (e.g., unlock)

Rules:
  - Acquire before accessing protected data
  - Release after modifications complete
  - Acquire visible before subsequent ops
  - Prior ops visible before Release

ARM, RISC-V use variants
```

---

# 4. MEMORY MANAGEMENT INTERNALS

## 4.1 Virtual Memory Implementation

### Page Table Walking
```
64-bit x86 (4-level):
Virtual Address: 48 bits used
┌───────┬───────┬───────┬───────┬──────────┐
│PML4[9]│PDPT[9]│PD[9]  │PT[9]  │Offset[12]│
└───────┴───────┴───────┴───────┴──────────┘

Walk:
1. CR3 → PML4 base
2. PML4[VA[47:39]] → PDPT base
3. PDPT[VA[38:30]] → PD base
4. PD[VA[29:21]] → PT base
5. PT[VA[20:12]] → Page frame
6. Physical = Frame + VA[11:0]
```

### Page Table Entry Format
```
x86-64 PTE (64 bits):
┌────────────────┬─────────────────────────────┐
│ Available (12) │ Physical Address (40)       │
├────────────────┼──┬──┬──┬──┬──┬──┬──┬──┬──┬──┤
│ AVL   │NX│...│G │PS│D │A │CD│WT│US│RW│P │
└────────────────┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘

P:  Present
RW: Read/Write
US: User/Supervisor
WT: Write-through
CD: Cache disable
A:  Accessed
D:  Dirty
PS: Page size (huge page)
G:  Global
NX: No execute (DEP)
```

### TLB Management
```
TLB Miss:
1. Hardware page table walk (x86)
   OR Software TLB miss handler (MIPS)
2. Load PTE into TLB
3. Retry memory access

TLB Shootdown:
1. One CPU modifies page table
2. Must invalidate other CPUs' TLBs
3. IPI (Inter-Processor Interrupt)
4. Each CPU runs INVLPG
5. Synchronize completion

ASID (Address Space ID):
  - Tag TLB entries by process
  - Avoid full flush on context switch
  - Limited ASIDs → flush when exhausted
```

## 4.2 Memory Allocators

### Buddy System
```
Split memory into power-of-2 blocks
Free list per size class

Allocate(64KB):
1. Find smallest free block ≥ 64KB
2. Split larger blocks recursively
3. Return 64KB block

Free(block):
1. Check buddy (adjacent same-size block)
2. If buddy free, merge
3. Repeat merge up to largest size

Fragmentation:
  Internal: Allocation rounded to power of 2
  External: None (all blocks same alignment)
```

### Slab Allocator
```
Per-object-size caches
Slabs contain multiple objects

struct kmem_cache {
    size_t object_size;
    size_t alignment;
    slab_list full;     // All objects used
    slab_list partial;  // Some objects free
    slab_list free;     // All objects free
};

Allocate:
1. Find partial slab
2. If none, allocate new slab
3. Return object from free list

Benefits:
  - Fast allocation (no splitting)
  - Good cache utilization
  - Object initialization reuse
```

### SLUB Allocator (Linux)
```
Per-CPU partial lists
Lock-free fast path

Allocate (fast path):
1. Check per-CPU free list
2. If available, return (no locks)

Allocate (slow path):
1. Refill from partial slab
2. Or allocate new slab
3. Lock required

Debugging features:
  - Red zones (detect overflow)
  - Poisoning (detect use-after-free)
  - Tracking (who allocated)
```

## 4.3 Page Replacement

### LRU Approximation
```
True LRU: Too expensive (ordered list)

Clock Algorithm:
  - Circular buffer of pages
  - Each page has reference bit
  - Hand sweeps, clears ref bit
  - Evict page with ref=0

Second Chance:
  - Like clock, but check dirty bit
  - Dirty pages get second chance
  - Reduces I/O for dirty pages

WSClock:
  - Working set + clock
  - Track last use time
  - Don't evict recent pages
```

### Page Replacement Policies
```
FIFO: First In First Out
  - Simple, but poor (Bélády's anomaly)

LRU: Least Recently Used
  - Good, but expensive

LFU: Least Frequently Used
  - Good for long-term patterns
  - Slow to adapt

ARC: Adaptive Replacement Cache
  - Balance recency and frequency
  - Self-tuning
```

## 4.4 Huge Pages

### Motivation
```
Standard 4KB pages:
  - 4-level page walk
  - TLB covers 4KB × TLB_entries
  - Many TLB misses for large data

2MB huge pages:
  - 3-level walk (skip PT)
  - TLB covers 2MB × TLB_entries
  - 512× better coverage

1GB huge pages:
  - 2-level walk (skip PT + PD)
  - Excellent for large databases
```

### Implementation
```
Transparent Huge Pages (THP):
  - Kernel promotes pages automatically
  - No application changes
  - Background khugepaged daemon

hugetlbfs:
  - Explicit huge page allocation
  - Reserved at boot or runtime
  - Application must request

Compaction:
  - Defragment memory for huge pages
  - Migrate pages to free contiguous blocks
```

---

# 5. OPERATING SYSTEM KERNEL INTERNALS

## 5.1 System Call Mechanism

### x86-64 System Call (syscall instruction)
```
User space:
  mov rax, SYS_write   ; System call number
  mov rdi, fd          ; Arg 1
  mov rsi, buf         ; Arg 2
  mov rdx, count       ; Arg 3
  syscall

Kernel entry:
1. Hardware saves RIP, RFLAGS to RCX, R11
2. Load kernel CS, SS from MSRs
3. Jump to LSTAR (syscall entry point)

Syscall entry (entry_SYSCALL_64):
1. Save user registers
2. Switch to kernel stack
3. Look up syscall table[rax]
4. Call handler
5. Restore user registers
6. sysret to user space
```

### System Call Overhead
```
Traditional (int 0x80): ~500+ cycles
syscall/sysret: ~100-200 cycles
vDSO (no syscall): ~10-20 cycles

vDSO: Virtual Dynamic Shared Object
  - Kernel page mapped to user space
  - gettimeofday, clock_gettime
  - No privilege transition
```

## 5.2 Process & Thread Internals

### Linux task_struct
```c
struct task_struct {
    // Scheduler
    volatile long state;          // TASK_RUNNING, etc.
    int prio, static_prio;       // Priorities
    struct sched_entity se;       // CFS scheduling

    // Memory
    struct mm_struct *mm;         // Address space

    // Files
    struct files_struct *files;   // Open files

    // Signals
    struct signal_struct *signal;

    // Credentials
    const struct cred *cred;

    // PID
    pid_t pid, tgid;             // Thread ID, Process ID

    // Parent/children
    struct task_struct *parent;
    struct list_head children;

    // ... many more fields
};
```

### Clone System Call
```c
long clone(unsigned long flags, void *stack, ...);

Flags:
  CLONE_VM:      Share address space
  CLONE_FS:      Share file system info
  CLONE_FILES:   Share file descriptors
  CLONE_SIGHAND: Share signal handlers
  CLONE_THREAD:  Same thread group

pthread_create → clone(CLONE_VM | CLONE_FS | ...)
fork → clone(SIGCHLD)
vfork → clone(CLONE_VM | CLONE_VFORK | SIGCHLD)
```

## 5.3 Scheduler Internals

### Completely Fair Scheduler (CFS)
```
Core idea: Virtual runtime
  vruntime = actual_runtime × (NICE_0_LOAD / weight)

Data structure: Red-black tree
  - Sorted by vruntime
  - Leftmost node = smallest vruntime
  - O(log n) insert/delete

Pick next:
1. Select leftmost node
2. If current vruntime > min + slice, switch
3. Update vruntime on tick

Weights (nice values):
  Nice  Weight
  -20   88761
    0   1024
   19   15

Load balancing:
  - Per-CPU runqueues
  - Periodic migration
  - Push/pull between CPUs
```

### Real-Time Scheduling
```
SCHED_FIFO:
  - Run until yield/block
  - Priority-based preemption

SCHED_RR:
  - Round-robin within priority
  - Time quantum

SCHED_DEADLINE:
  - Earliest Deadline First
  - Guaranteed CPU bandwidth
  - runtime/period/deadline parameters
```

## 5.4 Interrupt Handling

### Interrupt Flow
```
Hardware interrupt:
1. CPU checks IF flag
2. Save context to stack
3. Lookup IDT[vector]
4. Switch to kernel mode
5. Jump to handler

Top half (hardirq):
  - Disable interrupts
  - Minimal work
  - Acknowledge hardware
  - Schedule bottom half

Bottom half (softirq/tasklet):
  - Enable interrupts
  - Deferred processing
  - Run on softirqd kernel thread
```

### Interrupt Controllers
```
APIC (Advanced PIC):
  - Local APIC: Per-CPU
  - I/O APIC: Shared

MSI/MSI-X:
  - Message Signaled Interrupts
  - Direct to CPU via memory write
  - No shared lines

Interrupt routing:
  - Vector to handler mapping
  - Load balancing across CPUs
  - Affinity settings (irqbalance)
```

## 5.5 Kernel Synchronization

### Spinlocks
```c
typedef struct {
    atomic_t lock;
} spinlock_t;

void spin_lock(spinlock_t *lock) {
    while (atomic_xchg(&lock->lock, 1) != 0)
        cpu_relax();  // Hint to CPU
}

void spin_unlock(spinlock_t *lock) {
    atomic_set(&lock->lock, 0);
}

Variants:
  spin_lock_irq: Disable interrupts
  spin_lock_irqsave: Save/disable interrupts
  spin_lock_bh: Disable bottom halves
```

### RCU (Read-Copy-Update)
```
Optimized for read-heavy workloads

Read side:
  rcu_read_lock();
  // Read shared data (pointer)
  rcu_read_unlock();
  // No waiting, no memory barriers

Write side:
  1. Copy object
  2. Modify copy
  3. rcu_assign_pointer (memory barrier)
  4. synchronize_rcu (wait for readers)
  5. Free old object

Grace period:
  All CPUs passed through quiescent state
  (context switch, idle, user mode)
```

### Futex (Fast User-space Mutex)
```
Fast path in user space (no syscall)
Slow path uses kernel

struct {
    int val;  // User-space word
};

Lock:
1. CAS val: 0 → 1 (uncontended, no syscall)
2. If failed: syscall(FUTEX_WAIT)

Unlock:
1. CAS val: 1 → 0
2. If waiters: syscall(FUTEX_WAKE)
```

---

# 6. TYPE THEORY & LAMBDA CALCULUS

## 6.1 Untyped Lambda Calculus

### Syntax
```
Terms:
  M, N ::= x           (variable)
        |  λx.M        (abstraction)
        |  M N         (application)

Convention:
  - Application left-associative: M N P = (M N) P
  - Abstraction extends right: λx.M N = λx.(M N)
```

### Reduction Rules
```
β-reduction: (λx.M)N → M[x:=N]

Substitution M[x:=N]:
  x[x:=N] = N
  y[x:=N] = y (y ≠ x)
  (M₁ M₂)[x:=N] = (M₁[x:=N]) (M₂[x:=N])
  (λy.M)[x:=N] = λy.(M[x:=N]) (y ≠ x, y ∉ FV(N))

α-conversion: λx.M → λy.M[x:=y] (rename bound var)
η-conversion: λx.Mx → M (if x ∉ FV(M))
```

### Church Encodings
```
Booleans:
  TRUE  = λt.λf.t
  FALSE = λt.λf.f
  AND   = λp.λq.p q FALSE
  OR    = λp.λq.p TRUE q
  NOT   = λp.p FALSE TRUE

Numbers (Church numerals):
  0 = λf.λx.x
  1 = λf.λx.f x
  2 = λf.λx.f (f x)
  n = λf.λx.f^n x

  SUCC  = λn.λf.λx.f (n f x)
  PLUS  = λm.λn.λf.λx.m f (n f x)
  MULT  = λm.λn.λf.m (n f)

Recursion (Y combinator):
  Y = λf.(λx.f(x x))(λx.f(x x))
  Y F = F (Y F)
```

## 6.2 Simply Typed Lambda Calculus

### Types
```
Types:
  τ ::= α           (base type)
     |  τ₁ → τ₂     (function type)

Typing rules:

  x : τ ∈ Γ
  ─────────── (VAR)
  Γ ⊢ x : τ

  Γ, x : τ₁ ⊢ M : τ₂
  ───────────────────── (ABS)
  Γ ⊢ λx.M : τ₁ → τ₂

  Γ ⊢ M : τ₁ → τ₂   Γ ⊢ N : τ₁
  ───────────────────────────── (APP)
  Γ ⊢ M N : τ₂
```

### Properties
```
Type Safety:
  - Progress: Well-typed term either value or can step
  - Preservation: Reduction preserves types

Strong Normalization:
  - All reduction sequences terminate
  - No infinite loops possible
  - Y combinator not typeable!
```

## 6.3 Polymorphic Types

### System F (Polymorphic Lambda Calculus)
```
Types:
  τ ::= α | τ₁ → τ₂ | ∀α.τ

Terms:
  M ::= x | λx:τ.M | M N | Λα.M | M[τ]

Example:
  id = Λα.λx:α.x : ∀α.α → α
  id[Int] : Int → Int
  id[Int] 5 = 5
```

### Hindley-Milner Type System
```
Types:
  σ ::= ∀α₁...αn.τ  (type scheme)
  τ ::= α | τ₁ → τ₂ | T τ₁...τn

Let-polymorphism:
  let x = M in N
  - M is typed, generalized to scheme
  - N uses x with instantiated types

Algorithm W:
  - Syntax-directed type inference
  - Unification-based
  - Principal type property
```

## 6.4 Dependent Types

### Pi Types
```
Dependent function type:
  Π(x:A).B   or   (x:A) → B

B may depend on x

Example:
  Vector : Nat → Type → Type
  append : Π(n:Nat).Π(m:Nat).Vector n A → Vector m A → Vector (n+m) A

Length in the type!
```

### Sigma Types
```
Dependent pair type:
  Σ(x:A).B   or   {x:A & B}

Second component type depends on first

Example:
  {n:Nat & Vector n A}  -- Length and vector
```

### Curry-Howard Correspondence
```
Types = Propositions
Terms = Proofs

A → B        = A implies B
A × B        = A and B
A + B        = A or B
∀x:A.B(x)    = For all x in A, B(x)
∃x:A.B(x)    = Exists x in A such that B(x)

Proof assistant: Construct term of given type
  Coq, Agda, Lean, Idris
```

---

# 7. ALGORITHM COMPLEXITY THEORY

## 7.1 Complexity Classes

### Time Complexity Hierarchy
```
P ⊆ NP ⊆ PSPACE ⊆ EXPTIME ⊆ EXPSPACE

P: Polynomial time (deterministic)
  O(n^k) for some constant k

NP: Nondeterministic Polynomial time
  Certificate verifiable in polynomial time

PSPACE: Polynomial space
  Amount of memory, any time

EXPTIME: 2^(n^k) time
EXPSPACE: 2^(n^k) space
```

### NP-Completeness
```
Definition:
  L is NP-Complete if:
  1. L ∈ NP
  2. Every L' ∈ NP reduces to L (L is NP-Hard)

Cook-Levin Theorem:
  SAT is NP-Complete

Reduction:
  L₁ ≤p L₂ if function f computable in poly time
  such that x ∈ L₁ iff f(x) ∈ L₂

Classic NP-Complete problems:
  - SAT, 3-SAT
  - Clique, Independent Set, Vertex Cover
  - Hamiltonian Path/Cycle
  - Subset Sum, Knapsack
  - Graph Coloring
  - Traveling Salesman (decision)
```

### Space Complexity
```
L (Log space): O(log n) work tape
NL (Nondeterministic Log): Nondeterministic + O(log n)
PSPACE: Polynomial space

L ⊆ NL ⊆ P ⊆ NP ⊆ PSPACE

PSPACE-Complete:
  - QBF (Quantified Boolean Formula)
  - Generalized games (chess, go)
```

## 7.2 Approximation Algorithms

### Approximation Ratio
```
For minimization:
  ρ(n) = max(ALG(I)/OPT(I)) over all instances I

For maximization:
  ρ(n) = max(OPT(I)/ALG(I))

PTAS: Polynomial Time Approximation Scheme
  (1+ε)-approximation in time poly(n) for any ε > 0

FPTAS: Fully Polynomial TAS
  Time poly(n, 1/ε)
```

### Examples
```
Vertex Cover:
  2-approximation in O(E)
  Pick edge, add both endpoints, remove covered

Set Cover:
  O(log n)-approximation (greedy)
  Best unless P = NP

Traveling Salesman:
  Metric TSP: 3/2-approximation (Christofides)
  General TSP: No constant approximation unless P = NP

Knapsack:
  FPTAS exists
  (1-ε)-approximation in O(n³/ε)
```

## 7.3 Randomized Algorithms

### Types
```
Las Vegas:
  - Always correct
  - Expected polynomial time
  - Example: Randomized quicksort

Monte Carlo:
  - Probabilistic correctness
  - Guaranteed time bound
  - Example: Primality testing (Miller-Rabin)
```

### Complexity Classes
```
BPP: Bounded-error Probabilistic Polynomial
  - Correct with probability ≥ 2/3
  - Error reducible by repetition

RP: Randomized Polynomial
  - No → always correct
  - Yes → correct with probability ≥ 1/2

ZPP: Zero-error Probabilistic Polynomial
  - Always correct
  - Expected polynomial time
  - ZPP = RP ∩ co-RP
```

### Derandomization
```
Pseudorandom generators:
  - Stretch random bits
  - Fool bounded computation

P = BPP?
  - Widely believed
  - Hardness assumptions imply P = BPP
```

## 7.4 Parameterized Complexity

### Fixed-Parameter Tractability
```
Problem parameterized by k

FPT: f(k) · poly(n) time
  - Exponential in k, polynomial in n

W[1]-hard: Probably not FPT
  - Clique parameterized by clique size

Kernelization:
  - Reduce to equivalent instance of size f(k)
  - Polynomial kernel → FPT
```

### Examples
```
Vertex Cover (k = solution size):
  - FPT: O(2^k · n)
  - Kernel: 2k vertices

k-Clique:
  - W[1]-complete
  - Probably no f(k) · poly(n) algorithm
```

---

# 8. CRYPTOGRAPHIC INTERNALS

## 8.1 AES Internals

### State Array
```
128-bit block as 4×4 byte matrix:

┌────┬────┬────┬────┐
│ a₀ │ a₄ │ a₈ │a₁₂│
├────┼────┼────┼────┤
│ a₁ │ a₅ │ a₉ │a₁₃│
├────┼────┼────┼────┤
│ a₂ │ a₆ │a₁₀│a₁₄│
├────┼────┼────┼────┤
│ a₃ │ a₇ │a₁₁│a₁₅│
└────┴────┴────┴────┘
```

### Round Operations
```
1. SubBytes:
   - S-box substitution per byte
   - S(x) = A · x⁻¹ + b in GF(2⁸)

2. ShiftRows:
   - Row 0: no shift
   - Row 1: shift left 1
   - Row 2: shift left 2
   - Row 3: shift left 3

3. MixColumns:
   - Matrix multiplication in GF(2⁸)
   [02 03 01 01]
   [01 02 03 01] × column
   [01 01 02 03]
   [03 01 01 02]

4. AddRoundKey:
   - XOR with round key
```

### Key Schedule
```
AES-128: 10 rounds, 11 round keys
AES-192: 12 rounds, 13 round keys
AES-256: 14 rounds, 15 round keys

Key expansion:
- RotWord: Rotate 4-byte word
- SubWord: Apply S-box to each byte
- Rcon: Round constant
- W[i] = W[i-Nk] ⊕ (SubWord(RotWord(W[i-1])) ⊕ Rcon)
```

## 8.2 RSA Internals

### Key Generation
```
1. Choose primes p, q (≈1024 bits each)
2. n = p · q
3. φ(n) = (p-1)(q-1)
4. Choose e coprime to φ(n), typically 65537
5. d = e⁻¹ mod φ(n)

Public key: (n, e)
Private key: (n, d) or (p, q, d)
```

### Operations
```
Encryption: c = mᵉ mod n
Decryption: m = cᵈ mod n

Chinese Remainder Theorem optimization:
  dp = d mod (p-1)
  dq = d mod (q-1)
  qInv = q⁻¹ mod p

  m1 = c^dp mod p
  m2 = c^dq mod q
  h = qInv(m1 - m2) mod p
  m = m2 + h·q

~4× speedup using CRT
```

### Security Considerations
```
Padding: PKCS#1 v1.5, OAEP
  - Never encrypt raw message
  - OAEP is IND-CCA2 secure

Attacks:
  - Factoring (GNFS)
  - Side channels (timing, power)
  - Padding oracle
  - Low exponent (Coppersmith)

Minimum key size: 2048 bits (2024)
```

## 8.3 Elliptic Curve Cryptography

### Curve Definition
```
Weierstrass form: y² = x³ + ax + b (mod p)
Discriminant: Δ = -16(4a³ + 27b²) ≠ 0

Point at infinity: O (identity element)
```

### Group Operations
```
Point addition P + Q = R:
  λ = (y₂ - y₁)/(x₂ - x₁) mod p
  x₃ = λ² - x₁ - x₂ mod p
  y₃ = λ(x₁ - x₃) - y₁ mod p

Point doubling 2P:
  λ = (3x₁² + a)/(2y₁) mod p
  x₃ = λ² - 2x₁ mod p
  y₃ = λ(x₁ - x₃) - y₁ mod p
```

### Scalar Multiplication
```
Given point P and scalar k, compute kP

Double-and-add:
  R = O
  for bit in k (MSB first):
      R = 2R
      if bit == 1:
          R = R + P
  return R

Montgomery ladder (constant time):
  R0 = O, R1 = P
  for bit in k (MSB first):
      if bit == 0:
          R1 = R0 + R1
          R0 = 2R0
      else:
          R0 = R0 + R1
          R1 = 2R1
  return R0
```

### Standard Curves
```
secp256k1 (Bitcoin):
  p = 2²⁵⁶ - 2³² - 977
  a = 0, b = 7
  y² = x³ + 7

Curve25519 (modern):
  p = 2²⁵⁵ - 19
  Montgomery form: y² = x³ + 486662x² + x
  Fast, secure, constant-time
```

## 8.4 Hash Function Internals

### SHA-256
```
Message preprocessing:
1. Pad: msg || 1 || 0... || length (512-bit blocks)
2. Initialize H₀...H₇ (first 32 bits of √primes)

Compression function (per block):
1. Expand 16 words to 64:
   Wₜ = σ₁(Wₜ₋₂) + Wₜ₋₇ + σ₀(Wₜ₋₁₅) + Wₜ₋₁₆

2. 64 rounds:
   T₁ = h + Σ₁(e) + Ch(e,f,g) + Kₜ + Wₜ
   T₂ = Σ₀(a) + Maj(a,b,c)
   h=g, g=f, f=e, e=d+T₁, d=c, c=b, b=a, a=T₁+T₂

Functions:
  Ch(x,y,z) = (x ∧ y) ⊕ (¬x ∧ z)
  Maj(x,y,z) = (x ∧ y) ⊕ (x ∧ z) ⊕ (y ∧ z)
  Σ₀(x) = ROTR²(x) ⊕ ROTR¹³(x) ⊕ ROTR²²(x)
  Σ₁(x) = ROTR⁶(x) ⊕ ROTR¹¹(x) ⊕ ROTR²⁵(x)
```

### SHA-3 (Keccak)
```
Sponge construction:
1. Absorb: XOR message blocks into state
2. Squeeze: Extract output from state

State: 5×5×64 = 1600 bits
Capacity c = 2 × output_length
Rate r = 1600 - c

Permutation f (24 rounds):
  θ: Column parity mixing
  ρ: Bit rotation
  π: Lane permutation
  χ: Nonlinear S-box
  ι: Round constant XOR
```

---

# 9. CONSENSUS ALGORITHM MATHEMATICS

## 9.1 FLP Impossibility

### Theorem
```
In an asynchronous system with one faulty process,
no deterministic consensus protocol can guarantee
termination.

Implications:
  - Cannot distinguish slow from failed
  - Must use timeouts or randomization
  - Practical systems accept probability of non-termination
```

### Proof Sketch
```
1. Define bivalent configuration:
   Both 0 and 1 decisions reachable

2. Initial configuration is bivalent:
   Otherwise, single process determines outcome

3. From any bivalent config, can reach another:
   Delaying any single message maintains bivalence

4. Therefore: Can always delay decision
```

## 9.2 Paxos Analysis

### Safety Properties
```
Validity: Only proposed values can be chosen
  - Acceptors only accept values from proposals

Agreement: At most one value chosen
  - Quorum intersection guarantees uniqueness

Termination: Eventually a value is chosen (partial)
  - Not guaranteed (liveness requires assumptions)
```

### Quorum Analysis
```
Quorum = majority (> n/2)

Why majority works:
  - Any two majorities intersect
  - At least one acceptor in both
  - Carries information between phases

f fault tolerance requires:
  n ≥ 2f + 1 acceptors
  (majority of n survives f failures)
```

### Multi-Paxos
```
Optimization for multiple values:
1. Elect stable leader
2. Skip Phase 1 for subsequent values
3. Only Phase 2 needed

Amortized cost: 2 message delays per decision
```

## 9.3 Raft Analysis

### Leader Election
```
Term: Monotonically increasing epoch number

Election safety:
  - At most one leader per term
  - Candidate needs majority votes
  - Each server votes once per term

Election liveness:
  - Randomized timeouts prevent split vote
  - Eventually one candidate times out first
```

### Log Matching
```
Log Matching Property:
  If two logs contain entry with same index and term,
  then logs are identical up to that index

Maintained by:
  - Leader only appends
  - Follower checks consistency
  - Leader forces follower logs to match
```

### Safety Proof
```
Leader Completeness:
  If entry committed in term T, then present in all
  leaders of terms > T

State Machine Safety:
  If server applies entry at index, no other server
  applies different entry at same index

Proof relies on:
  - Quorum intersection
  - Term ordering
  - Log matching invariant
```

## 9.4 Byzantine Fault Tolerance

### PBFT
```
Phases:
1. Pre-prepare: Leader broadcasts ⟨PRE-PREPARE, v, n, m⟩
2. Prepare: Replica broadcasts ⟨PREPARE, v, n, d, i⟩
3. Commit: Replica broadcasts ⟨COMMIT, v, n, d, i⟩

Quorum certificates:
  - Prepared: 2f + 1 matching prepares
  - Committed: 2f + 1 matching commits

Message complexity: O(n²) per request

View change:
  - Timeout triggers view change
  - New leader collects prepared certificates
  - Ensures committed operations survive
```

### Practical Considerations
```
BFT requirements:
  - n ≥ 3f + 1 nodes
  - n - f honest nodes must communicate
  - Cryptographic signatures

Performance:
  - High message complexity
  - Network dominates cost
  - Optimistic protocols reduce overhead
```

---

# 10. DATABASE ENGINE INTERNALS

## 10.1 Storage Engine

### B+ Tree Implementation
```
Node structure:
struct Node {
    bool is_leaf;
    int num_keys;
    Key keys[ORDER - 1];
    union {
        Node* children[ORDER];    // Internal
        Value values[ORDER - 1];  // Leaf
    };
    Node* next;  // Leaf-only: sibling pointer
};

Search:
1. Start at root
2. Binary search keys in node
3. Follow appropriate child pointer
4. Repeat until leaf
5. Binary search in leaf for value

Insert:
1. Find leaf for key
2. Insert in sorted order
3. If overflow (≥ ORDER keys):
   - Split: create new node with half keys
   - Push middle key to parent
   - Recursively split if needed
```

### Log-Structured Merge Tree (LSM)
```
Structure:
  MemTable (RAM) → L0 → L1 → ... → Ln (disk)

Write:
1. Append to WAL
2. Insert into MemTable (sorted)
3. When full, flush to L0 SSTable

Read:
1. Check MemTable
2. Check Bloom filters for each level
3. Binary search in SSTable

Compaction:
  - Merge overlapping SSTables
  - Remove deleted/overwritten keys
  - Level compaction vs. size-tiered
```

## 10.2 Query Processing

### Query Optimization
```
Logical optimization:
  - Predicate pushdown
  - Projection pushdown
  - Join reordering

Physical optimization:
  - Access path selection (index vs. scan)
  - Join algorithm selection
  - Parallelization

Cost estimation:
  Cost = IO_cost + CPU_cost
  IO_cost = pages_read × page_read_cost
  CPU_cost = rows × cpu_tuple_cost

Cardinality estimation:
  Using histogram statistics
  Selectivity = |output| / |input|
```

### Join Algorithms
```
Nested Loop Join: O(n × m)
  for each row r in R:
      for each row s in S:
          if r.key == s.key:
              emit (r, s)

Index Nested Loop: O(n × log m)
  for each row r in R:
      lookup s in S.index(r.key)
      if found: emit (r, s)

Sort-Merge Join: O(n log n + m log m)
  sort R by key
  sort S by key
  merge sorted lists

Hash Join: O(n + m)
  build hash table on R
  probe with each row in S
```

## 10.3 Concurrency Control

### Two-Phase Locking (2PL)
```
Growing phase: Acquire locks
Shrinking phase: Release locks
No new locks after first release

Lock types:
  S (Shared): Multiple readers
  X (Exclusive): Single writer

Compatibility:
     S  X
  S  ✓  ✗
  X  ✗  ✗

Deadlock handling:
  - Timeout
  - Wait-die / Wound-wait
  - Deadlock detection (cycle in wait-for graph)
```

### Multi-Version Concurrency Control (MVCC)
```
Each write creates new version
Readers see snapshot without locking

Version chain:
  Key → V3 → V2 → V1
        ↓    ↓    ↓
      ts=5 ts=3 ts=1

Snapshot isolation:
  Transaction sees versions committed before start
  Write conflicts detected at commit

Read:
  Find version where ts ≤ txn.start_ts

Write:
  Create new version with ts = txn.id
  Check for write-write conflict at commit
```

## 10.4 Recovery

### Write-Ahead Logging (WAL)
```
Rules:
1. Log before data page
2. All logs for txn before commit
3. Commit record to log before return

Log record format:
  [LSN, TxnID, Type, PageID, Offset, Before, After]

ARIES recovery:
1. Analysis: Scan log, build dirty page table
2. Redo: Replay from checkpoint
3. Undo: Rollback uncommitted transactions
```

### Checkpoint
```
Fuzzy checkpoint:
1. Write checkpoint record
2. Flush dirty pages in background
3. No blocking of transactions

Log record:
  [CHECKPOINT, active_txns, dirty_pages]

Recovery starts from last checkpoint
```

---

# 11. NEURAL NETWORK MATHEMATICS

## 11.1 Backpropagation

### Chain Rule
```
Loss L = f(g(h(x)))

∂L/∂x = ∂L/∂f · ∂f/∂g · ∂g/∂h · ∂h/∂x

Computational graph:
  x → h → g → f → L

Backward pass:
  ∂L/∂L = 1
  ∂L/∂f = 1 · ∂L/∂f
  ∂L/∂g = ∂L/∂f · ∂f/∂g
  ...
```

### Layer Gradients
```
Dense layer: y = Wx + b

Forward:
  z = Wx + b
  a = σ(z)

Backward:
  ∂L/∂z = ∂L/∂a · σ'(z)
  ∂L/∂W = ∂L/∂z · x^T
  ∂L/∂b = ∂L/∂z
  ∂L/∂x = W^T · ∂L/∂z  (for previous layer)
```

### Activation Derivatives
```
ReLU: σ(x) = max(0, x)
  σ'(x) = 1 if x > 0 else 0

Sigmoid: σ(x) = 1/(1+e^(-x))
  σ'(x) = σ(x)(1 - σ(x))

Tanh: σ(x) = (e^x - e^(-x))/(e^x + e^(-x))
  σ'(x) = 1 - σ(x)²

Softmax: σ(x)_i = e^(x_i) / Σ_j e^(x_j)
  ∂σ_i/∂x_j = σ_i(δ_ij - σ_j)
```

## 11.2 Optimization Algorithms

### Stochastic Gradient Descent
```
θ_{t+1} = θ_t - η · ∇L(θ_t; x_i, y_i)

Problems:
  - High variance
  - Same learning rate for all parameters
  - Can get stuck in saddle points
```

### Momentum
```
v_{t+1} = γv_t + η∇L(θ_t)
θ_{t+1} = θ_t - v_{t+1}

γ ≈ 0.9 typical
Accelerates in consistent gradient direction
```

### Adam (Adaptive Moment Estimation)
```
m_t = β₁m_{t-1} + (1-β₁)g_t           (1st moment)
v_t = β₂v_{t-1} + (1-β₂)g_t²          (2nd moment)
m̂_t = m_t / (1-β₁^t)                  (bias correction)
v̂_t = v_t / (1-β₂^t)
θ_{t+1} = θ_t - η · m̂_t / (√v̂_t + ε)

Default: β₁=0.9, β₂=0.999, ε=10⁻⁸
```

## 11.3 Regularization

### L1 and L2
```
L2 (Ridge): L' = L + λΣw²
  Gradient: ∂L'/∂w = ∂L/∂w + 2λw
  Effect: Shrinks weights toward 0

L1 (Lasso): L' = L + λΣ|w|
  Subgradient: sign(w)
  Effect: Sparsity (some weights become 0)
```

### Dropout
```
Training:
  mask = Bernoulli(p)
  h' = h * mask / p  (inverted dropout)

Testing:
  No dropout (already scaled)

Effect:
  - Ensemble of subnetworks
  - Reduces co-adaptation
  - Implicit regularization
```

### Batch Normalization
```
μ_B = (1/m)Σx_i
σ²_B = (1/m)Σ(x_i - μ_B)²
x̂_i = (x_i - μ_B) / √(σ²_B + ε)
y_i = γx̂_i + β  (learnable)

Benefits:
  - Stabilizes training
  - Higher learning rates possible
  - Reduces internal covariate shift
```

## 11.4 Attention Mechanism

### Scaled Dot-Product Attention
```
Attention(Q, K, V) = softmax(QK^T / √d_k) V

Q: Queries (n × d_k)
K: Keys (m × d_k)
V: Values (m × d_v)

Scaling by √d_k:
  - Prevents softmax saturation
  - Keeps gradient magnitude stable
```

### Multi-Head Attention
```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O

head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)

Projections:
  W_i^Q ∈ ℝ^(d_model × d_k)
  W_i^K ∈ ℝ^(d_model × d_k)
  W_i^V ∈ ℝ^(d_model × d_v)
  W^O ∈ ℝ^(hd_v × d_model)

Benefits:
  - Different representation subspaces
  - Learn different attention patterns
```

### Positional Encoding
```
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))

Properties:
  - Unique encoding for each position
  - Relative positions learnable
  - Fixed (no training required)
```

---

# 12. COMPILER OPTIMIZATION INTERNALS

## 12.1 Static Single Assignment (SSA)

### SSA Form
```
Original:
  x = 1
  x = 2
  y = x

SSA:
  x1 = 1
  x2 = 2
  y = x2

Each variable assigned exactly once
```

### Phi Functions
```
Original:
  if (cond) x = 1 else x = 2
  y = x

SSA:
  if (cond) x1 = 1 else x2 = 2
  x3 = φ(x1, x2)
  y = x3

φ selects value based on control flow
```

### Dominance
```
Node A dominates B if every path to B goes through A
Immediate dominator: Closest dominator

Dominator tree used for:
  - SSA construction
  - Loop detection
  - Optimization placement
```

## 12.2 Data Flow Analysis

### Reaching Definitions
```
Forward analysis

Gen[B] = definitions in B
Kill[B] = definitions killed by B

Out[B] = Gen[B] ∪ (In[B] - Kill[B])
In[B] = ∪ Out[P] for P in predecessors

Iterate until fixed point
```

### Live Variables
```
Backward analysis

Gen[B] = variables used before defined in B
Kill[B] = variables defined in B

In[B] = Gen[B] ∪ (Out[B] - Kill[B])
Out[B] = ∪ In[S] for S in successors

Used for register allocation
```

### Available Expressions
```
Forward analysis

Gen[B] = expressions computed in B
Kill[B] = expressions with modified variables

Out[B] = Gen[B] ∪ (In[B] - Kill[B])
In[B] = ∩ Out[P] for P in predecessors

Used for common subexpression elimination
```

## 12.3 Loop Optimizations

### Loop Invariant Code Motion
```
Before:
  for i = 0 to n:
      x = y + z    // Invariant if y, z not modified
      a[i] = x + i

After:
  x = y + z
  for i = 0 to n:
      a[i] = x + i
```

### Strength Reduction
```
Before:
  for i = 0 to n:
      a[i*4] = 0

After:
  t = 0
  for i = 0 to n:
      a[t] = 0
      t = t + 4

Replace expensive ops with cheaper ones
```

### Loop Unrolling
```
Before:
  for i = 0 to n:
      a[i] = b[i] + c[i]

After (unroll 4):
  for i = 0 to n step 4:
      a[i] = b[i] + c[i]
      a[i+1] = b[i+1] + c[i+1]
      a[i+2] = b[i+2] + c[i+2]
      a[i+3] = b[i+3] + c[i+3]
  // Handle remainder

Benefits:
  - Reduce loop overhead
  - Enable more ILP
  - Better cache utilization
```

## 12.4 Register Allocation

### Graph Coloring
```
1. Build interference graph
   - Nodes = variables
   - Edges = simultaneously live variables

2. Simplify
   - Remove nodes with degree < k (registers)
   - Push onto stack

3. Potential spill
   - If all nodes have degree ≥ k
   - Mark node for potential spill

4. Select
   - Pop nodes from stack
   - Assign colors (registers)
   - If can't color, actually spill
```

### Linear Scan
```
1. Compute live intervals
2. Sort by start point
3. Iterate through intervals:
   - Expire old intervals (release registers)
   - If free register available, assign
   - Else spill (longest end point)

O(n log n) vs O(n²) for graph coloring
Used in JIT compilers
```

---

# 13. GPU ARCHITECTURE DEEP DIVE

## 13.1 NVIDIA GPU Architecture

### Streaming Multiprocessor (SM)
```
SM contains:
  - 64-128 CUDA cores (INT32, FP32)
  - Tensor cores (matrix ops)
  - Special function units (SFU)
  - Load/store units
  - Shared memory / L1 cache
  - Warp schedulers

Warp: 32 threads executing in lockstep
  - All execute same instruction
  - Divergence serializes branches
```

### Memory Hierarchy
```
Per-thread:
  - Registers: Fastest, limited (~256 per thread)
  - Local memory: Spill to device memory

Per-block:
  - Shared memory: ~48-96 KB, user-managed cache
  - L1 cache: Combined with shared memory

Per-device:
  - L2 cache: ~6 MB
  - Global memory: GB, high latency (~400 cycles)
```

### Occupancy
```
Occupancy = Active warps / Max warps per SM

Limited by:
  - Registers per thread
  - Shared memory per block
  - Block size

Higher occupancy:
  - Better latency hiding
  - More parallel execution
  - But not always better performance
```

## 13.2 CUDA Execution Model

### Thread Hierarchy
```
Grid
  └── Block (up to 1024 threads)
        └── Warp (32 threads)
              └── Thread

threadIdx: Thread within block
blockIdx: Block within grid
blockDim: Threads per block
gridDim: Blocks per grid

Global thread ID:
  idx = blockIdx.x * blockDim.x + threadIdx.x
```

### Memory Coalescing
```
Coalesced access:
  - Adjacent threads access adjacent memory
  - Single memory transaction per warp

Non-coalesced:
  - Random or strided access
  - Multiple transactions per warp

Example:
  // Coalesced (good)
  a[threadIdx.x] = b[threadIdx.x]

  // Strided (bad)
  a[threadIdx.x * stride] = b[threadIdx.x]
```

### Bank Conflicts
```
Shared memory: 32 banks
Each bank serves one 32-bit word per cycle

No conflict:
  - Each thread accesses different bank
  - Broadcast: All threads same address

Conflict:
  - Multiple threads access same bank (different addr)
  - Serialized access

Avoiding:
  - Padding arrays
  - Access pattern design
```

## 13.3 Tensor Cores

### Matrix Multiply-Accumulate
```
D = A × B + C

Tensor Core operation:
  - 4×4×4 matrix multiply
  - Single instruction
  - Mixed precision (FP16 input, FP32 accumulate)

Throughput:
  - Volta: 125 TFLOPS (FP16)
  - Ampere: 312 TFLOPS (FP16)
```

### Using Tensor Cores
```cpp
// WMMA (Warp Matrix Multiply Accumulate)
wmma::fragment<wmma::matrix_a, M, N, K, half, wmma::row_major> a_frag;
wmma::fragment<wmma::matrix_b, M, N, K, half, wmma::col_major> b_frag;
wmma::fragment<wmma::accumulator, M, N, K, float> c_frag;

wmma::load_matrix_sync(a_frag, a_ptr, lda);
wmma::load_matrix_sync(b_frag, b_ptr, ldb);
wmma::fill_fragment(c_frag, 0.0f);
wmma::mma_sync(c_frag, a_frag, b_frag, c_frag);
wmma::store_matrix_sync(c_ptr, c_frag, ldc, wmma::mem_row_major);
```

---

# 14. NETWORK PROTOCOL INTERNALS

## 14.1 TCP Deep Dive

### Sequence Numbers
```
Initial Sequence Number (ISN):
  - Randomized (RFC 6528)
  - Prevent segment injection

Sequence space: 32-bit, wraps around
SEG.SEQ: First byte number
SEG.ACK: Next expected byte
SEG.LEN: Data length
```

### Window Management
```
Receive window:
  rwnd = buffer_size - unread_data

Send window:
  swnd = min(rwnd, cwnd)

Available window:
  awnd = swnd - (SND.NXT - SND.UNA)

Window scale option:
  - Multiply by 2^scale
  - Support windows > 64KB
```

### Congestion Control Details
```
Slow Start:
  cwnd = cwnd + MSS for each ACK
  Doubles every RTT
  Exit when cwnd >= ssthresh

Congestion Avoidance:
  cwnd = cwnd + MSS²/cwnd for each ACK
  Linear increase (1 MSS per RTT)

Multiplicative Decrease:
  On loss (timeout): cwnd = 1, ssthresh = cwnd/2
  On loss (3 dup ACK): cwnd = cwnd/2, ssthresh = cwnd

CUBIC (Linux default):
  cwnd = C(t - K)³ + W_max
  K = ∛(W_max × β / C)
  More aggressive recovery
```

## 14.2 TLS 1.3 Handshake

### Full Handshake
```
Client                              Server
   │                                   │
   │─────── ClientHello ──────────────>│
   │        (key_share, psk)           │
   │                                   │
   │<────── ServerHello ───────────────│
   │        (key_share, psk)           │
   │                                   │
   │<────── {EncryptedExtensions} ─────│
   │<────── {Certificate*} ────────────│
   │<────── {CertificateVerify*} ──────│
   │<────── {Finished} ────────────────│
   │                                   │
   │─────── {Certificate*} ───────────>│
   │─────── {CertificateVerify*} ─────>│
   │─────── {Finished} ───────────────>│
   │                                   │

1-RTT handshake (vs 2-RTT in TLS 1.2)
```

### Key Derivation
```
(EC)DHE → Shared Secret

Early Secret = HKDF-Extract(0, PSK or 0)
Handshake Secret = HKDF-Extract(Early, ECDHE)
Master Secret = HKDF-Extract(Handshake, 0)

Traffic keys derived from secrets
Separate keys for client/server, handshake/application
```

## 14.3 HTTP/2 and HTTP/3

### HTTP/2 Framing
```
Frame format:
+-----------------------------------------------+
|                Length (24)                    |
+---------------+---------------+---------------+
|   Type (8)    |   Flags (8)   |
+-+-------------+---------------+
|R|                Stream ID (31)               |
+-+---------------------------------------------+
|                Frame Payload                  |
+-----------------------------------------------+

Types: DATA, HEADERS, PRIORITY, RST_STREAM,
       SETTINGS, PUSH_PROMISE, PING, GOAWAY,
       WINDOW_UPDATE, CONTINUATION
```

### HTTP/3 (QUIC)
```
Built on UDP
Features:
  - 0-RTT connection establishment
  - Multiplexed streams (no head-of-line blocking)
  - Connection migration (IP change)
  - Integrated TLS 1.3

Packet format:
  - Header: Connection ID, packet number
  - Payload: QUIC frames (encrypted)
```

---

# 15. DISTRIBUTED SYSTEMS THEORY

## 15.1 Time and Ordering

### Lamport Clocks
```
Rules:
1. Before event: C_i = C_i + 1
2. Send message: include timestamp
3. Receive: C_i = max(C_i, msg.ts) + 1

Properties:
  a → b implies C(a) < C(b)
  C(a) < C(b) does NOT imply a → b (partial order)
```

### Vector Clocks
```
Each process maintains vector of N clocks

Rules:
1. Before event: V_i[i]++
2. Send: include V_i
3. Receive: V_i[j] = max(V_i[j], msg.V[j]) for all j
            V_i[i]++

Comparison:
  V1 < V2 if V1[i] ≤ V2[i] for all i, and V1 ≠ V2
  V1 || V2 if neither V1 < V2 nor V2 < V1 (concurrent)
```

### Hybrid Logical Clocks
```
Combines physical and logical time
HLC = (physical_time, logical_counter)

Bounded drift from physical time
Captures causality like vector clocks
Constant space (vs linear for vector clocks)
```

## 15.2 Failure Detectors

### Properties
```
Completeness: Eventually detect all failures
Accuracy: Don't falsely suspect correct processes

Strong completeness + Weak accuracy:
  Eventually all correct suspect all failed
  Some correct process never suspected
```

### Perfect Failure Detector (P)
```
Strong completeness + Strong accuracy
Impossible in asynchronous systems
Possible with synchrony assumptions
```

### Eventually Perfect (◇P)
```
Eventually strong completeness + accuracy
After some time, behaves like P
Sufficient for consensus
```

## 15.3 Replication Theory

### Primary-Backup
```
Write:
1. Client → Primary
2. Primary → Backups (sync or async)
3. Primary → Client

Failover:
1. Detect primary failure
2. Elect new primary
3. Synchronize state

Split-brain:
  - Network partition
  - Both think they're primary
  - Need quorum or fencing
```

### Chain Replication
```
Structure: Head → ... → Tail

Write: Head → propagate → Tail → acknowledge
Read: Tail returns value

Benefits:
  - Simple recovery
  - Strong consistency
  - Load distribution

CRAQ: Chain Replication with Apportioned Queries
  - Read from any replica
  - Check version with tail
```

### Quorum Systems
```
Read quorum R, Write quorum W, N replicas

Constraints:
  R + W > N (read sees latest write)
  W + W > N (no concurrent writes)

Examples:
  Majority: R = W = ⌊N/2⌋ + 1
  Read-one-write-all: R = 1, W = N
  Write-one-read-all: R = N, W = 1
```

---

# 16. FORMAL VERIFICATION

## 16.1 Model Checking

### Temporal Logic (LTL)
```
Operators:
  □ (always): □p - p holds in all future states
  ◇ (eventually): ◇p - p holds in some future state
  ○ (next): ○p - p holds in next state
  U (until): p U q - p until q, then q

Examples:
  □(request → ◇grant): Every request eventually granted
  □¬deadlock: No deadlock ever
  □(ready → ○running): If ready, running next
```

### CTL (Computational Tree Logic)
```
Path quantifiers:
  A (for all paths)
  E (exists a path)

State formulas:
  AG p: All paths, all states, p holds
  EF p: Some path, some state, p holds
  AF p: All paths eventually p
  EG p: Some path, always p

Example:
  AG(request → AF grant): On all paths, request leads to grant
```

### Model Checking Algorithm
```
Explicit state:
1. Build state graph
2. Check property via graph traversal
3. Counterexample if property violated

Symbolic (BDD-based):
1. Represent states as Boolean formulas
2. Use BDD for efficient operations
3. Fixed-point computation

Bounded Model Checking:
1. Unroll to depth k
2. Convert to SAT problem
3. If SAT, counterexample found
```

## 16.2 Theorem Proving

### Hoare Logic
```
{P} S {Q}

Axioms:
  {P[x:=E]} x := E {P}                    (assignment)
  {P} skip {P}                            (skip)
  {P} S1 {Q}, {Q} S2 {R} ⊢ {P} S1;S2 {R}  (sequence)
  {P ∧ B} S1 {Q}, {P ∧ ¬B} S2 {Q} ⊢
    {P} if B then S1 else S2 {Q}          (conditional)
  {P ∧ B} S {P} ⊢ {P} while B do S {P ∧ ¬B}  (while)
```

### Separation Logic
```
Extends Hoare logic for heap

Assertions:
  emp: Empty heap
  x ↦ v: x points to v
  P * Q: P and Q hold on disjoint heaps

Frame rule:
  {P} S {Q}
  ───────────── (if S doesn't modify R)
  {P * R} S {Q * R}

Enables local reasoning about heap
```

## 16.3 Abstract Interpretation

### Lattice Framework
```
Abstract domain: Lattice (L, ⊑, ⊔, ⊓, ⊤, ⊥)

Abstraction: α: Concrete → Abstract
Concretization: γ: Abstract → Concrete

Galois connection:
  α(c) ⊑ a ⟺ c ⊆ γ(a)

Sound: α(f(γ(a))) ⊑ f#(a)
```

### Example: Sign Analysis
```
Abstract domain: {⊥, -, 0, +, ⊤}

Lattice:
        ⊤
      / | \
     -  0  +
      \ | /
        ⊥

Abstract addition:
  + + + = +
  - + - = -
  + + - = ⊤
  0 + x = x

Analyze: x = 1; y = -2; z = x + y
  x: +, y: -, z: ⊤
```

---

# 17. QUANTUM COMPUTING MATHEMATICS

## 17.1 Quantum Mechanics Foundations

### Hilbert Space
```
State space: Complex Hilbert space H
States: Unit vectors |ψ⟩ ∈ H
Observables: Hermitian operators A = A†

Single qubit: H = ℂ²
  |0⟩ = (1, 0)ᵀ
  |1⟩ = (0, 1)ᵀ
  |ψ⟩ = α|0⟩ + β|1⟩, |α|² + |β|² = 1
```

### Measurement
```
Projective measurement {P_m}:
  P_m² = P_m (projectors)
  Σ P_m = I (complete)

Probability: p(m) = ⟨ψ|P_m|ψ⟩
Post-measurement: |ψ'⟩ = P_m|ψ⟩ / √p(m)

Born rule: Probability = |amplitude|²
```

### Density Matrices
```
Pure state: ρ = |ψ⟩⟨ψ|
Mixed state: ρ = Σ p_i |ψ_i⟩⟨ψ_i|

Properties:
  ρ† = ρ (Hermitian)
  ρ ≥ 0 (positive semi-definite)
  Tr(ρ) = 1

Purity: Tr(ρ²) ≤ 1
  = 1 for pure states
```

## 17.2 Quantum Gates

### Single-Qubit Gates
```
Pauli matrices:
  X = |0⟩⟨1| + |1⟩⟨0| = [0 1; 1 0]  (bit flip)
  Y = -i|0⟩⟨1| + i|1⟩⟨0| = [0 -i; i 0]
  Z = |0⟩⟨0| - |1⟩⟨1| = [1 0; 0 -1]  (phase flip)

Hadamard:
  H = (X + Z)/√2 = [1 1; 1 -1]/√2
  H|0⟩ = (|0⟩ + |1⟩)/√2 = |+⟩
  H|1⟩ = (|0⟩ - |1⟩)/√2 = |-⟩

Phase gates:
  S = [1 0; 0 i]
  T = [1 0; 0 e^(iπ/4)]
```

### Multi-Qubit Gates
```
CNOT (Controlled-NOT):
  |00⟩ → |00⟩
  |01⟩ → |01⟩
  |10⟩ → |11⟩
  |11⟩ → |10⟩

  CNOT = |0⟩⟨0| ⊗ I + |1⟩⟨1| ⊗ X

Toffoli (CCNOT):
  Flips target if both controls are 1
  Universal for classical computation

CZ (Controlled-Z):
  Applies Z when control is |1⟩
```

## 17.3 Quantum Algorithms

### Quantum Fourier Transform
```
QFT|j⟩ = (1/√N) Σ_k e^(2πijk/N) |k⟩

Circuit:
  H gates + controlled rotations
  O(n²) gates for n qubits

Used in: Shor's algorithm, phase estimation
```

### Grover's Algorithm
```
Oracle: O|x⟩ = (-1)^f(x)|x⟩
Diffusion: D = 2|ψ⟩⟨ψ| - I

Algorithm:
1. |ψ⟩ = H^⊗n|0⟩^⊗n
2. Repeat O(√N) times:
   a. Apply oracle O
   b. Apply diffusion D
3. Measure

Speedup: O(√N) vs O(N) classical
```

### Shor's Algorithm
```
Factor N:
1. Choose random a < N
2. Quantum period finding:
   Find r where a^r ≡ 1 (mod N)
3. If r even, gcd(a^(r/2) ± 1, N) likely factor

Period finding uses QFT
Polynomial in log N (exponential speedup)
```

## 17.4 Quantum Error Correction

### Bit Flip Code
```
Encode: |0⟩ → |000⟩, |1⟩ → |111⟩

Error: X on one qubit
Syndrome: Measure ZZI, IZZ
  No error: +1, +1
  Flip qubit 1: -1, +1
  Flip qubit 2: -1, -1
  Flip qubit 3: +1, -1

Correct: Apply X to identified qubit
```

### Surface Code
```
2D grid of data and ancilla qubits
Stabilizer measurements detect errors

Code distance d:
  Corrects ⌊(d-1)/2⌋ errors
  Logical error rate ~ p^(d/2)

Threshold: ~1% physical error rate
Leading candidate for fault-tolerant QC
```

---

# 18. INFORMATION THEORY DEEP DIVE

## 18.1 Entropy Measures

### Shannon Entropy
```
H(X) = -Σ p(x) log₂ p(x)

Properties:
  - H(X) ≥ 0
  - H(X) ≤ log₂ |X|
  - H(X) = 0 iff X is deterministic
  - Maximum when X uniform
```

### Joint and Conditional Entropy
```
Joint: H(X,Y) = -Σ p(x,y) log₂ p(x,y)

Conditional: H(X|Y) = -Σ p(x,y) log₂ p(x|y)
                    = H(X,Y) - H(Y)

Chain rule: H(X₁,...,Xn) = Σ H(Xᵢ|X₁,...,Xᵢ₋₁)
```

### Mutual Information
```
I(X;Y) = H(X) - H(X|Y)
       = H(Y) - H(Y|X)
       = H(X) + H(Y) - H(X,Y)

Properties:
  - I(X;Y) ≥ 0
  - I(X;Y) = 0 iff X, Y independent
  - I(X;Y) = I(Y;X)
```

## 18.2 Channel Capacity

### Binary Symmetric Channel
```
Input: 0, 1 with equal probability
Crossover probability: p

Capacity: C = 1 - H(p)
         = 1 + p log₂ p + (1-p) log₂ (1-p)
```

### Noisy Channel Coding Theorem
```
For any rate R < C:
  There exists code with arbitrarily small error

For any rate R > C:
  Error probability bounded away from 0

Achievability: Random coding argument
Converse: Fano's inequality
```

### Gaussian Channel
```
Y = X + N, N ~ N(0, σ²)
Power constraint: E[X²] ≤ P

Capacity: C = (1/2) log₂(1 + P/σ²) bits

Shannon limit: SNR = 2^(2R) - 1 for rate R
```

## 18.3 Source Coding

### Entropy Coding
```
Huffman coding:
  - Optimal prefix-free code
  - L < H(X) + 1 bits per symbol

Arithmetic coding:
  - Approaches entropy
  - Represents sequence as interval

Lempel-Ziv:
  - Dictionary-based
  - Asymptotically optimal
  - Used in gzip, PNG
```

### Rate-Distortion Theory
```
Distortion measure d(x, x̂)
Rate-distortion function: R(D) = min I(X; X̂)
                                  s.t. E[d(X, X̂)] ≤ D

For Gaussian X, MSE distortion:
  R(D) = (1/2) log₂(σ²/D) for D ≤ σ²
```

---

# 19. COMPUTATIONAL COMPLEXITY CLASSES

## 19.1 Complexity Zoo

### Basic Classes
```
TIME(f(n)): Decidable in O(f(n)) time
SPACE(f(n)): Decidable in O(f(n)) space

P = ∪_k TIME(n^k)
PSPACE = ∪_k SPACE(n^k)
EXPTIME = ∪_k TIME(2^(n^k))

L = SPACE(log n)
NL = NSPACE(log n)
```

### Between P and NP
```
BPP: Bounded-error Probabilistic Polynomial
  P ⊆ BPP ⊆ Σ₂ ∩ Π₂
  Probably P = BPP

IP: Interactive Proofs
  IP = PSPACE

AM: Arthur-Merlin games
  AM[k] = AM for k ≥ 2
  Graph non-isomorphism in AM
```

### Counting Classes
```
#P: Count accepting paths of NP machine
  #SAT: Count satisfying assignments

PP: Majority of paths accept
  PP contains NP and co-NP

⊕P: Odd number of paths accept

#P-complete: #SAT, permanent
```

## 19.2 Hardness Assumptions

### One-Way Functions
```
Function f is one-way if:
  - f(x) computable in poly time
  - For any PPT A: Pr[f(A(f(x))) = f(x)] < negl(n)

Candidates:
  - Factoring: f(p,q) = p·q
  - Discrete log: f(g, x) = g^x
  - Lattice problems: LWE, SIS
```

### Cryptographic Assumptions
```
DDH (Decisional Diffie-Hellman):
  (g, g^a, g^b, g^ab) ≈ (g, g^a, g^b, g^c)

LWE (Learning with Errors):
  Distinguish (A, As + e) from random
  Quantum-resistant

RSA Assumption:
  Hard to find e-th root mod N = pq
```

## 19.3 Structural Complexity

### Polynomial Hierarchy
```
Σ₀ = Π₀ = P
Σᵢ₊₁ = NP^(Σᵢ)
Πᵢ₊₁ = co-NP^(Σᵢ)

PH = ∪_i Σᵢ

If PH collapses to level k:
  NP = co-NP implies Σ₂ = Π₂
```

### Oracles
```
P^A, NP^A: Polynomial access to oracle A

Baker-Gill-Solovay:
  There exist A, B such that:
  P^A = NP^A and P^B ≠ NP^B

Implications:
  P vs NP won't be resolved by relativizing techniques
```

---

# 20. FUTURE COMPUTING ARCHITECTURES

## 20.1 Beyond Moore's Law

### Dennard Scaling End
```
Dennard scaling (1974-2006):
  Shrink transistor → reduce voltage → constant power

End of scaling:
  - Leakage current dominates
  - Voltage can't decrease (reliability)
  - Power density constant

Response:
  - Multi-core (horizontal scaling)
  - Specialized accelerators
  - New computing paradigms
```

### 3D Integration
```
Stack dies vertically
Benefits:
  - More transistors per area
  - Shorter interconnects
  - Higher bandwidth

Challenges:
  - Heat dissipation
  - Manufacturing yield
  - Design complexity
```

## 20.2 Alternative Computing

### Neuromorphic Computing
```
Brain-inspired architecture:
  - Spiking neural networks
  - Event-driven computation
  - Massively parallel

Advantages:
  - Low power (pJ/spike)
  - Real-time learning
  - Sensor fusion

Hardware:
  - Intel Loihi
  - IBM TrueNorth
  - BrainScaleS
```

### DNA Computing
```
Use DNA for computation:
  - Massive parallelism
  - High density storage (1 bit/nm³)
  - Slow but energy efficient

Operations:
  - Hybridization (pattern matching)
  - PCR (amplification)
  - Restriction enzymes (cutting)

Applications:
  - Combinatorial optimization
  - Archival storage
```

### Photonic Computing
```
Use light for computation:
  - Speed of light propagation
  - Low power interconnects
  - Wavelength multiplexing

Applications:
  - Optical neural networks
  - Quantum computing (photons)
  - High-speed communication

Challenges:
  - Nonlinear operations
  - Integration with electronics
```

## 20.3 Quantum Computing Future

### Error Correction Overhead
```
Current: NISQ (50-100 noisy qubits)
Future: Fault-tolerant (millions of physical qubits)

Surface code requirements:
  - 1000+ physical per logical qubit
  - ~1% error threshold
  - Deep circuits require more

Timeline: Fault-tolerant QC in 10-20 years
```

### Quantum Applications
```
Near-term (NISQ):
  - Variational algorithms (VQE, QAOA)
  - Quantum machine learning
  - Quantum simulation

Long-term (fault-tolerant):
  - Shor's algorithm (cryptography)
  - Grover search
  - Quantum simulation (materials, chemistry)
```

## 20.4 Post-Moore Computing

### Domain-Specific Accelerators
```
GPU: Graphics, ML training
TPU: ML inference
FPGA: Flexible acceleration
ASIC: Maximum efficiency

Trend: Specialized hardware for specific domains
Trade-off: Flexibility vs efficiency
```

### Approximate Computing
```
Accept imprecision for efficiency:
  - Neural network inference
  - Media processing
  - Search and optimization

Techniques:
  - Reduced precision
  - Voltage scaling
  - Approximate circuits

Quality-power trade-off
```

### In-Memory Computing
```
Compute where data lives:
  - Reduce data movement
  - Analog computation in memory
  - Processing-in-Memory (PIM)

Technologies:
  - ReRAM crossbar arrays
  - SRAM compute
  - DRAM PIM
```

---

# SUMMARY

This advanced document covers the deep internals of computing:

1. **Hardware**: Transistor physics, CPU microarchitecture, cache coherence
2. **Systems**: Memory management, kernel internals, scheduling
3. **Theory**: Type theory, complexity, formal verification
4. **Security**: Cryptographic primitives, protocols
5. **Intelligence**: Neural network mathematics, optimization
6. **Infrastructure**: Database engines, network protocols
7. **Future**: Quantum computing, neuromorphic, photonic

Each section provides the mathematical and implementation details that underlie computing systems.

---

*Last Updated: 2024*
*Coverage: Deep Computing Internals*
