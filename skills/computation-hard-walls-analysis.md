---
name: computation-hard-walls-analysis
description: "Framework for analyzing 14 fundamental hard walls against exotic computation schemes in sci-fi mechanism design. Use when: (1) evaluating how many physical limits a fictional compute device breaks, (2) scoring mechanism plausibility against known physics limits, (3) writing scientifically rigorous speculative technology documents."
category: architecture
date: 2026-06-01
version: "1.2.0"
user-invocable: false
verification: unverified
history: computation-hard-walls-analysis.history
tags: [physics, computation, limits, hard-walls, scifi, worldbuilding, mechanism-design, tqc, topological, bekenstein, planck-density]
---

# Computation Hard Walls Analysis Framework

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-06-01 |
| **Objective** | Systematically evaluate exotic/fictional compute mechanisms against 14 known physical hard limits |
| **Outcome** | Framework developed and applied: AdS/CFT holographic (M02) defeats 10/14; asymptotic-safety RG (M16) defeats 5/14 + 3 partial; anyon topological braiding (M44) defeats 9/14 — with Wall 11 (Analog Precision) most decisively defeated by topological protection. Planck-density substrate mechanisms (LQG spin-network M14, anyon fabric M44) share a recurring failure mode: Planck energy density implies black hole collapse. |
| **Verification** | unverified — theoretical framework, not implemented |
| **History** | [changelog](./computation-hard-walls-analysis.history) |

## When to Use

- Scoring a speculative or fictional computation mechanism for plausibility
- Writing mechanism design documents for sci-fi worldbuilding
- Checking which physical laws a proposed device must break and why
- Comparing multiple exotic compute mechanisms on a common rubric
- Grounding "impossible technology" in real physics language

## Verified Workflow

> **Warning (Proposed Workflow):** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms. Verification level: `unverified` — theoretical framework only.

### Quick Reference

```
The 14 Hard Walls (reference list):
 1. Holevo bound (classical bits extractable from qubits)
 2. Landauer floor (k_BT ln2 per bit erased)
 3. Cube-square thermal (volume heat vs surface cooling)
 4. Exponential Hilbert-space scaling (Feynman)
 5. NP-hard fermionic sign problem
 6. Chaos/Lyapunov limit (λ_L ≤ 2πk_BT/ℏ)
 7. Computational irreducibility (Wolfram)
 8. Data-movement/memory-wall energy
 9. Gravity's weakness (G_N extremely small)
10. Force energy-scale ladder (electroweak >> gravity)
11. Analog precision/noise wall (~5-10 bits classical)
12. Bekenstein/holographic bound (S ≤ A/4G_N)
13. Thompson AT²=Ω(n²) I/O lower bound (VLSI)
14. Causality/speed-of-light latency

Mechanism comparison (walls defeated):
AdS/CFT holographic boundary (M02):         10/14 defeated  — Parsimony 2/10
Asymptotic-safety RG substrate (M16):        5/14 defeated  — Parsimony 4/10
LQG spin-network processor (M14):           ~8/14 defeated  — Parsimony 3/10
Anyon topological braiding fabric (M44):     9/14 defeated  — Parsimony 3/10
Inviolable (any mechanism):                  3/14 standing  — Walls 6, 7, 14

WALL 11 CHAMPION: Topological mechanisms (M44) defeat Wall 11 most rigorously —
  topological protection makes gate fidelity exactly discrete; error rate ~ e^{-E_gap/kT}.
```

### Detailed Assessment Steps

1. **For each wall, ask: does the mechanism's operating principle bypass the assumption?**
   - Wall 1 (Holevo): Only applies to classical readout. If output is quantum, it doesn't apply.
   - Wall 2 (Landauer): Only applies to irreversible erasure. Logically reversible / topologically protected → zero cost.
   - Wall 3 (Cube-square): Only applies to volumetric computers. A surface computer (2D) has no cube-square problem. Topological mechanisms: if Planck-gap energy scale, room temperature is negligibly cold — thermal dissipation problem inverted.
   - Wall 4 (Hilbert-space scaling): AdS/CFT trades exponential bulk Hilbert space for polynomial boundary CFT. TQC/Fibonacci anyons: fusion Hilbert space grows as φ^N — the physical anyon system IS the exponential register, no classical simulation needed. BUT: TQC is still BQP; arbitrary quantum simulation remains exponentially hard.
   - Wall 5 (Sign problem): THREE distinct defeat mechanisms: (A) AdS/CFT — large-N saddle absorbs fermionic determinant into classical bulk; (B) CDT/Lorentzian RG (M16) — causal ordering eliminates Euclidean oscillatory sign problem; (C) TQC/Fibonacci (M44) — braid group representation is algebraically exact, no Monte Carlo sampling required, no sign problem exists.
   - Wall 6 (Lyapunov): NOT bypassable. The MSS bound (λ_L ≤ 2πk_BT/ℏ) applies to any physical system. AdS/CFT saturates this bound, never exceeds it.
   - Wall 7 (Irreducibility): NOT bypassable. A physical system is always computationally irreducible — it evolves at its own rate. No mechanism lets you skip ahead.
   - Wall 8 (Memory wall): Entanglement encodes correlations nonlocally — no data transport, zero movement energy. TQC: information encoded in non-local fusion channels; gate operations are local braid crossings at Planck spacing.
   - Wall 9 (Gravity weakness): G_N smallness = 1/N suppression in boundary theory — a feature of the duality, not a bug. At Planck scale: G m_P²/ℏc = 1 exactly — gravity is not weak. Planck-substrate mechanisms operate where gravity is strong.
   - Wall 10 (Force ladder): All forces appear as operator families in the CFT spectrum. In analogue RG: energy-scale ladder collapsed by analogue Planck rescaling. In Planck-substrate mechanisms: new-physics postulate required to bridge macroscopic control to Planck-scale excitation.
   - Wall 11 (Analog precision): Quantum shot noise 1/√N with N~10⁶⁶ gives ~10³³ digit precision for AdS/CFT. TQC (M44): braiding is a discrete topological event — no analog precision requirement at all. Error rate = exp(-E_gap/k_BT). At Planck gap, room temp: error ~ exp(-10^32) ≈ 0. This is the most rigorous Wall 11 defeat across all M-series mechanisms.
   - Wall 12 (Holographic bound): Surface computer operating at exactly the bound — saturated, not defeated. Accessible register for 1 kg, 5 mm radius device: ~10^40 bits. Planck-substrate fusion Hilbert spaces (dim ~ 10^(10^97)) vastly exceed this — surplus is formally inaccessible (see Black Hole Failure Mode below).
   - Wall 13 (Thompson AT²): Requires wires in classical VLSI. CFT has nonlocal correlators built into physics — Thompson bound doesn't apply. 3D braid architecture: all gates are nearest-neighbor; AT² 2D VLSI bound inapplicable.
   - Wall 14 (Causality/latency): NOT bypassable. Entanglement wedge reconstruction is bounded by the bulk causal wedge. Anyon motion is subluminal. No-communication theorem applies universally.

2. **Score: count DEFEATED walls for Capability Score, count new postulates for Parsimony Score.**

3. **Identify genuinely inviolable walls:** Walls 6 (Lyapunov), 7 (irreducibility), and 14 (causality) cannot be defeated by any physical mechanism without violating the foundations of physics. Treat these as permanent constraints in any mechanism design.

4. **Name new-physics postulates explicitly (NP-N taxonomy):** Each law broken requires a labeled postulate. Count postulates for Parsimony Score = 10/(number of postulates).

5. **Check for the Planck Density Black Hole failure mode** (see below) — applies to ALL mechanisms using Planck-scale matter density.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Claiming all 14 walls defeated | Trying to argue every wall is bypassable to maximize capability score | Walls 6, 7, 14 are definitionally inviolable — bypassing them requires redefining causality or computation itself | Honest mechanism design requires stating which walls genuinely stand; 3 inviolable walls is a strength (shows rigor) |
| Conflating Holevo with Shannon | Treating Holevo bound as equivalent to Shannon channel capacity limit | Holevo applies specifically to classical extraction from quantum states; if output stays quantum, it does not apply | Always check if the bound's assumption (classical output) matches the mechanism's actual output channel |
| Treating Bekenstein bound as a wall to defeat | Trying to break the holographic bound to fit more information | The holographic bound IS the operating principle of a surface computer — operating at the bound is the goal | Reframe: saturating a bound is different from breaking it; saturation is optimal operation |
| Claiming d_s=2 implies 2D CFT tractability | Assuming spectral dimension flow to 2 makes computation exactly solvable via Virasoro symmetry | Spectral dimension characterizes diffusion properties only; it does not imply the geometry is a smooth 2-manifold with Virasoro symmetry | Distinguish between effective (diffusion-measured) dimension and actual geometric dimension; d_s=2 is a probe property, not a Lagrangian property |
| Treating Planck-density fusion Hilbert space as accessible register | Claiming φ^(10^98) dimensional anyon Hilbert space as the usable register | Bekenstein bound limits accessible bits to ~10^40 for a 1 kg device; the rest is topologically inaccessible and requires global measurement exponentially costly to process | Always cross-check claimed register size against Bekenstein-accessible bits; use ~10^40 bits for 1 kg, 5 mm device |
| Ignoring black hole collapse for Planck-density substrates | Designing a "palm-sized" device with Planck-scale energy density | Schwarzschild radius of 1 cm³ of Planck-density matter (ρ ~ 5×10^96 kg/m³) is astronomically large — device is a black hole | ALL Planck-density substrate mechanisms must address this failure mode explicitly; it requires additional new-physics or reframing |

## Results & Parameters

### Capability Score Rubric

```
Capability Score = (Walls Defeated) / 14
High (>8/14):    Mechanism has strong physics-based arguments for most walls
Medium (5-8/14): Several walls defeated; others require new-physics postulates
Low (<5/14):     Mechanism relies heavily on breaking physics with no argument

Parsimony Score = 10 / (number of new-physics postulates)
Score 10: 1 postulate (most parsimonious)
Score 5:  2 postulates
Score 2:  5 postulates (highly exotic)
Score 1:  10+ postulates (pure fantasy)
```

### Multi-Mechanism Comparison Table

```
Mechanism               Walls Defeated  Walls Standing  New-Physics Postulates  Capability  Parsimony
M02 AdS/CFT holo        10/14           3 (6,7,14)      5                       71%         2/10
M16 AS-RG sub           5/14 + 3 part   3 (6,7,14)      3                       ~50%        4/10
M14 LQG spin-network    ~8/14           4 (6,7,12,14)   3                       ~57%        3/10
M44 Anyon TQC fabric    9/14 + 2 part   3 (6,7,14)      3                       ~64%        3/10
```

### Wall 5 Sign Problem — Three Distinct Defeat Mechanisms

```
Mechanism A (AdS/CFT):   Large-N saddle point → classical bulk gravity; fermionic
                         determinant absorbed into bulk geometry. Requires large N.

Mechanism B (CDT/AS):    Lorentzian (causal) path integral eliminates oscillatory
                         Euclidean sign problem directly via causal ordering constraint.
                         Works at any N. Requires Lorentzian formulation (CDT or similar).

Mechanism C (TQC/Fibonacci anyons, M44):
                         Braid group representation theory is algebraically exact — braid
                         matrices are computed from representation theory, not Monte Carlo.
                         No sign problem exists because there is no path integral sum with
                         oscillatory signs; braiding unitaries are exact finite group matrices.
```

### Wall 11 — Analog Precision: Defeat Hierarchy

```
Weakest defeat:  AdS/CFT — quantum shot noise 1/√N gives ~10^33 digit precision (probabilistic)
Moderate defeat: LQG spin-network — spin labels are discrete integers (area spectrum is discrete)
Strongest defeat: TQC/Fibonacci anyons (M44) — braiding is a DISCRETE TOPOLOGICAL EVENT.
                  No continuous parameter involved in gate application.
                  Error rate = exp(-E_gap/k_BT).
                  At Planck gap (E_P/k_BT ~ 10^32): error ~ exp(-10^32) ≈ 0.
                  This is the only mechanism where Wall 11 defeat is rigorous by construction.
```

### The Three Inviolable Walls

```
Wall 6 — Chaos/Lyapunov: λ_L ≤ 2πk_BT/ℏ (Maldacena-Shenker-Stanford bound)
  Any physical quantum system saturates but cannot exceed this.
  AdS/CFT is a maximal chaos system — it saturates exactly.

Wall 7 — Computational Irreducibility:
  A physical system always evolves at its own rate.
  No mechanism provides speedup over the physical time of the system itself.

Wall 14 — Causality/Speed-of-Light Latency:
  Information cannot propagate faster than c, even via entanglement.
  Entanglement wedge reconstruction is bounded by the causal wedge.
  No-communication theorem applies universally.
```

### Bekenstein Accessible Bits Calculation

```
For a handheld device — canonical calculation (1 kg, 5 mm radius):
  S_max ≤ 2πRE / (ℏc)
  R = 0.005 m
  E = 1 kg × (3×10^8 m/s)² = 9×10^16 J
  S_max ≤ 2π × 0.005 × 9×10^16 / (10^-34 × 3×10^8)
         ≈ 2π × 4.5×10^14 / 3×10^-26
         ≈ 9.4×10^40 bits

→ Any mechanism claiming more than ~10^40 accessible bits in a handheld device
  violates the Bekenstein bound for that device.
  The surplus is either holographically inaccessible or the mechanism breaks Wall 12.

Compare to claimed registers in M-series mechanisms:
  M14 LQG (10^50-edge spin network in nuclear volume): claims 10^51 bits → INCONSISTENT
  M44 Fibonacci anyons (φ^(10^98) fusion Hilbert space): formally ~10^(5×10^97) → VASTLY INCONSISTENT
  Accessible in both cases via readout: ~10^40 bits (Bekenstein-consistent)
```

### CRITICAL FAILURE MODE: Planck-Density Black Hole Collapse

```
APPLIES TO: Any mechanism using Planck-scale matter density (ρ ~ m_P/ℓ_P³ ~ 5×10^96 kg/m³)

CALCULATION:
  Mass of 1 cm³ device at Planck density:
    M = ρ × V = 5×10^96 kg/m³ × 10^-6 m³ = 5×10^90 kg

  Schwarzschild radius:
    r_S = 2GM/c² = 2 × 6.67×10^-11 × 5×10^90 / (3×10^8)² ≈ 7.4×10^52 m

  Observable universe radius: ~4.4×10^26 m

  The Schwarzschild radius is ~10^26 times larger than the observable universe.
  → The device is not a palm-sized gadget. It IS a black hole many orders of magnitude
    larger than the observable universe.

RESOLUTION OPTIONS (all require additional new physics):
  A) Topological/holographic energy: The Planck-scale quantum effects don't require
     classical energy density — the topological phase is a ground-state property
     with zero classical energy density above vacuum. (Conceptually possible; no model.)
  B) Holographic encoding: Information stored on 2D surface (ℓ_P² per bit) rather than
     volumetrically; device volume is not filled with Planck-density matter.
  C) Acknowledge and state it explicitly as a failure mode requiring additional new physics.

RECOMMENDATION: Always note this failure mode for Planck-substrate mechanisms.
  Do NOT ignore it. State it as Failure Mode #N and note which resolution option the
  narrative adopts.
```

### Analogue Gravity Energy Rescaling (Wall 10 defeat, M16 pattern)

```
True Planck energy: E_P = 1.22×10¹⁹ GeV
Analogue Planck length: ℓ_P^eff ~ 10⁻¹⁰ m  (vs true ℓ_P = 1.6×10⁻³⁵ m)
Rescaling factor: ~6×10²⁴
Analogue Planck energy: ℏc/ℓ_P^eff ≈ 2×10⁻²⁴ J ≈ 12 eV  (soft X-ray)
Result: Planck-scale physics accessible at laboratory energies in the analogue
Caveat: Only within the analogue; real gravitational physics still requires Planck energy
```

### Laws Broken Ledger Template

```markdown
| Law / Principle | Status | Note |
|---|---|---|
| [Law name] | PRESERVED / BENT / BROKEN | [Brief justification] |
```

Status definitions:
- `PRESERVED`: Mechanism obeys this law completely
- `BENT`: Mechanism operates near the boundary; technically valid but unusual
- `BROKEN`: Mechanism requires this law to not hold; must state new-physics postulate

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/Story | M02 holographic boundary mechanism design, Myrmidon swarm physics agent | Applied to AdS/CFT boundary computer; see Research/Mechanisms/M02-holographic-boundary.md |
| HomericIntelligence/Story | M16 asymptotic-safety RG substrate mechanism design, Myrmidon swarm physics agent | Applied to AS smooth substrate; see Research/Mechanisms/M16-asymptotic-safety-substrate.md |
| HomericIntelligence/Story | M44 anyon topological braiding fabric, Myrmidon swarm physics agent, 2026-06-01 | Applied to Fibonacci anyon fabric; Planck-density black hole failure mode documented; see Research/Mechanisms/M44-anyon-braiding-fabric.md |
