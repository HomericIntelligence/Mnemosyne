---
name: scifi-mechanism-single-device-design
description: "Design a single speculative-but-rigorous physics mechanism for a fictional sci-fi device, grounded in real cited science, with a Laws-Broken Ledger, Walls Defeated table, Parsimony/Capability scores, and Failure Modes. Use when: (1) a Myrmidon swarm agent is assigned one mechanism (MNN-name) to design in isolation, (2) the mechanism file must follow the HomericIntelligence/Story M-series template, (3) you need real cited papers (URL+date, ≥4) anchoring speculative extrapolations, (4) the prompt says 'pure science — no story/plot/character content'."
category: documentation
date: 2026-06-01
version: "1.2.0"
user-invocable: false
verification: verified-local
history: scifi-mechanism-single-device-design.history
tags: [scifi, worldbuilding, mechanism-design, physics, citations, hard-walls, m-series, homeric-intelligence, speculative-science, laws-broken, parsimony, capability, monopole, topological-soliton, exotic-particles, false-vacuum, higgs, vacuum-decay, coleman-bounce]
---

# Sci-Fi Single Mechanism Device Design (M-Series)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-01 |
| **Objective** | Design one rigorous speculative-physics mechanism for a fictional sci-fi device (e.g., a Planck-scale reality simulator), following the HomericIntelligence Story M-series file format: real cited papers, Laws-Broken Ledger, 14 Hard Walls table, Parsimony/Capability scores, Failure Modes, and Feasibility tags — pure science, no narrative. |
| **Outcome** | Successful: M15 (String/T-Duality Minimum-Length Substrate) produced at `Story/Research/Mechanisms/M15-string-tduality-substrate.md`, ~2000 words, ≥7 real cited papers with URLs and dates, all 14 Hard Walls addressed, Laws-Broken Ledger table complete, Parsimony 4/10 and Capability 9.5/10 scored, 5 Failure Modes documented. |
| **Verification** | verified-local (file written and confirmed at target path; not CI-gated). |

## When to Use

- A Myrmidon swarm dispatches you as a **single mechanism specialist** (prompt says "Your Assigned Mechanism: MNN — ...") tasked with writing one M-series file.
- The output path is `Story/Research/Mechanisms/MNN-<slug>.md` (HomericIntelligence/Story repo).
- The prompt includes the 14 Hard Walls list and requires all 14 to be addressed.
- The mechanism is **physics-grounded speculative fiction** — real science anchor + clearly labeled departures, no narrative prose.
- You need ≥4 real cited papers (URL + access date) sourced via WebSearch/WebFetch before writing.

**Do NOT use when:**

- You are the swarm orchestrator dispatching agents (use `myrmidon-research-grounding-swarm-with-counterfactual-track` instead).
- The request is for narrative/plot/character content (this skill is pure-science only).
- The mechanism requires a full research survey across many dimensions (use the swarm grounding skill instead).

## Verified Workflow

### Quick Reference

```
Step 1: WebSearch ≥4 real papers covering the mechanism's physics domain.
        Search terms: "<mechanism> minimum length review", "<author> <year> <topic>",
        "generalized uncertainty principle string theory", etc.

Step 2: WebFetch the 2-3 most important arXiv/journal pages for:
        - authors, title, year, journal/volume/pages
        - key equations or claims to quote accurately

Step 3: Read ONE existing M-series file for format reference:
        /Story/Research/Mechanisms/M01-microbh-lattice.md (lines 1-60 sufficient)

Step 4: Write the file at the EXACT assigned path. Sections (in order):
        # MNN — Title
        **One-line mechanism** + **Class**
        ## Premise Correction  (address Planck CONSTANT vs Planck LENGTH confusion)
        ## How It Works       (numbered subsections; label [REAL], [NEW-PHYSICS], [SPECULATIVE])
        ## Real-Science Anchor (≥4 citations: author, title, venue, year, URL, access date)
        ## Laws-Broken Ledger  (markdown table: #, Law/Wall, Status, How broken)
        ## Walls Defeated vs Left Standing (prose summary of all 14)
        ## Parsimony Score    (X/10 with justification)
        ## Capability Score   (X/10 with justification)
        ## Failure Modes / No-Go Cascades (3-5 numbered failure modes)
        ## Feasibility Tags   (bullet list of tagged assessments)

Step 5: Run /hephaestus:learn after writing the file (this skill).
```

### Detailed Steps

**Step 1 — Parallel WebSearches (run all at once):**

Run 4 independent searches simultaneously:
1. `"<mechanism core concept> review <key author>"` — for canonical review papers
2. `"<specific 1989/1993 foundational paper> <author> <journal>"` — for primary sources
3. `"<mechanism> computation register quantum information"` — for computational reinterpretation
4. `"<supporting concept> string theory information storage bits"` — for holographic/information angle

**Step 2 — WebFetch the arXiv abstract pages** (not PDFs — abstracts have clean metadata):

```
https://arxiv.org/abs/<id>
Prompt: "Extract title, authors, year, journal/volume/pages, and key claims about <topic>."
```

**Step 3 — Read format reference (first 60 lines of M01):**

```
Read /home/mvillmow/HomericIntelligence/Story/Research/Mechanisms/M01-microbh-lattice.md
lines 1-60
```

Key format observations from M01:
- Labels: `[NEW-PHYSICS]`, `[REAL]`, `[SPECULATIVE]`, `[FRONTIER]` inline in subsection headers
- Postulates are named `NP-N (Name)` for new-physics departures
- Laws-Broken Ledger uses `**BROKEN**`, `**SIDESTEPPED**`, `**EXPLOITED**`, `**LEFT STANDING**`
- Power source is a required subsection

**Step 4 — Write the file.** Key discipline rules:

| Rule | Detail |
|------|--------|
| Premise Correction | ALWAYS address "Planck constant (h, J·s) ≠ Planck length (ℓ_P, ~1.6×10⁻³⁵ m)"; also note if string scale ≠ Planck scale |
| Citation format | Author (year). "Title." *Venue* vol:pp. [URL] Accessed YYYY-MM-DD. |
| All 14 walls | Address every wall; never skip; mark each BROKEN/SIDESTEPPED/EXPLOITED/LEFT STANDING |
| No narrative | Zero story/character/plot content; pure physics mechanism prose |
| Word count | 1500–2500 words |

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Searching for "string winding modes computation register" | Expected to find explicit string-theoretic computation papers | Results returned generic quantum harmonic oscillator and CV computing papers, not string-theory-specific registers | The computational-register reinterpretation of string modes is novel — cite oscillator/Fock-space QC papers + string theory separately, then bridge them explicitly as new-physics reinterpretation |
| WebFetch on full PDF URL (arxiv.org/pdf/...) | Attempted to get full paper text for equation extraction | PDFs return raw text hard to parse cleanly; abstracts page (/abs/) gives cleaner metadata | Always WebFetch the `/abs/` page not the `/pdf/` page for citation metadata |
| Relying only on search summaries for citation details | Used WebSearch text summaries for paper metadata | Summaries sometimes omit page numbers, exact volumes, or conflate multiple papers | Always WebFetch at least 2 key papers directly for precise citation data |
| WebFetch on Nature.com article (SSL error) | Attempted to fetch https://www.nature.com/articles/nature06433 for Castelnovo-Moessner-Sondhi 2008 citation details | SSL certificate validation failure on nature.com — returns "unable to verify the first certificate" | For Nature.com articles, use the corresponding arXiv preprint URL (arxiv.org/abs/XXXX.XXXXX) or the ADS abstract page (ui.adsabs.harvard.edu) instead; the arXiv abstract for Castelnovo 2008 is https://arxiv.org/abs/0710.5515 |
| Attempting to cite Parker 1970 from original journal | Searched for "Parker 1970 Astrophys J 160 383 monopole flux" — results returned modern re-analyses, not the original paper | Parker (1970) predates open-access archives; original paper is paywalled and not on arXiv | For foundational pre-arXiv papers (Parker bound, Dirac 1931), cite via DOI/journal volume info extracted from review papers or Wikipedia, then verify the key quantitative claim (flux limit, charge relation) via a modern review that quotes it |

## Results & Parameters

### Target File Path Pattern

```
/home/mvillmow/HomericIntelligence/Story/Research/Mechanisms/M<NN>-<slug>.md
```

### The 14 Hard Walls (reference list for all M-series files)

```
1. Holevo          2. Landauer           3. Cube-square thermal
4. Exponential Hilbert-space (Feynman)   5. NP-hard sign problem
6. Chaos/Lyapunov  7. Computational irreducibility  8. Data-movement energy
9. Gravity's weakness  10. Force energy-scale ladder  11. Analog precision (~5-10 bits)
12. Bekenstein/holographic  13. Thompson AT²=Ω(n²)  14. Causality/c latency
```

### Premise Correction Boilerplate

```markdown
## Premise Correction

The author's phrase "Planck-level fields" requires disambiguation.

**Planck CONSTANT vs. Planck LENGTH.** The Planck constant h = 6.626×10⁻³⁴ J·s is a fixed
unit of action governing quantum-mechanical phase; it is NOT the geometric scale relevant
to this mechanism. The relevant scale is the **Planck LENGTH** ℓ_P = √(ℏG/c³) ≈ 1.616×10⁻³⁵ m,
where quantum gravitational effects become O(1).

[Add mechanism-specific nuance here, e.g. string scale ≥ Planck length.]
```

### Key Physics Constants for M-Series Files

```
ℓ_P = 1.616×10⁻³⁵ m     (Planck length)
m_P = 2.176×10⁻⁸ kg      (Planck mass, ~1.22×10¹⁹ GeV)
t_P = 5.39×10⁻⁴⁴ s       (Planck time)
T_P = 1.42×10³² K         (Planck temperature)
ℓ_s = √α' ≈ 10⁻³³–10⁻³⁴ m  (string length, slightly above ℓ_P)
M_s = 1/√α' ~ 10¹⁷–10¹⁹ GeV  (string mass scale, standard)
M_s_ADD ~ 1–19 TeV          (string scale with large extra dimensions, LHC-constrained)
```

### Scoring Rubric

```
Parsimony Score (X/10):
  10 = mechanism follows from one elegant real-physics extension
   5 = 2-3 new-physics postulates, each coherent
   1 = cascade of unrelated ad hoc postulates

Capability Score (X/10):
  10 = defeats all 14 walls, unlimited information capacity
   5 = defeats 7-9 walls, adequate for simulation purpose
   1 = defeats ≤3 walls, barely plausible
```

### Real Citations Reusable for String-Theory Mechanisms

```
Amati, Ciafaloni & Veneziano (1989). "Can space-time be probed below the string size?"
  Phys. Lett. B 216(1-2):41-47.
  https://www.sciencedirect.com/science/article/abs/pii/0370269390919274

Maggiore, M. (1993). "A Generalized Uncertainty Principle in Quantum Gravity."
  Phys. Lett. B 304:65-69.
  https://arxiv.org/abs/hep-th/9301067

Alvarez, Alvarez-Gaumé & Lozano (1994). "An Introduction to T-Duality in String Theory."
  Nucl. Phys. B Proc. Suppl. 41.
  https://arxiv.org/abs/hep-th/9410237

Smailagic, Spallucci & Padmanabhan (2003). "String theory T-duality and the zero point length."
  arXiv:hep-th/0308122.
  https://arxiv.org/abs/hep-th/0308122

Kachru, Kallosh, Linde & Trivedi (2003). "de Sitter Vacua in String Theory."
  Phys. Rev. D 68:046005.
  https://arxiv.org/abs/hep-th/0301240

Maldacena, J. (1997). "The Large N Limit of Superconformal Field Theories and Supergravity."
  Int. J. Theor. Phys. 38(4):1113-1133.
  https://arxiv.org/abs/hep-th/9711200

Polchinski, J. (1998). String Theory, Vol. I & II. Cambridge University Press.
```

### Real Citations Reusable for Exotic-Particle / Topological-Soliton Mechanisms

These are pre-verified (accessed 2026-06-01) for mechanisms in the magnetic-monopole, topological-soliton, or GUT-scale exotic-particle class (M43, and similar skyrmion/instanton/vortex mechanisms):

```
Dirac, P.A.M. (1931). "Quantised Singularities in the Electromagnetic Field."
  Proc. R. Soc. London A 133(821):60-72.
  https://www.semanticscholar.org/paper/Quantised-Singularities-in-the-Electromagnetic-Dirac/16c075e422432ced4c96d2f7c8ad9c912e19468f
  Key claim: magnetic monopole existence ↔ electric charge quantization (Dirac relation: eg = nℏc/2)

't Hooft, G. (1974). "Magnetic Monopoles in Unified Gauge Theories."
  Nucl. Phys. B 79:276-284.
  Wikipedia summary + formula: https://en.wikipedia.org/wiki/%27t_Hooft%E2%80%93Polyakov_monopole
  Key claim: non-singular finite-energy monopole soliton from SU(2)→U(1) symmetry breaking;
  topological stability from π₂(G/H) = ℤ; mass m_M ~ m_W/α ≈ 10¹⁶ GeV at GUT scale.
  (Companion paper: Polyakov, A.M. (1974). JETP Lett. 20:194-195.)

Castelnovo, C., Moessner, R. & Sondhi, S.L. (2008). "Magnetic monopoles in spin ice."
  Nature 451:42-45.
  arXiv preprint: https://arxiv.org/abs/0710.5515   ← USE THIS URL (Nature SSL fails)
  Key claim: dipole moments in pyrochlore spin-ice (Dy₂Ti₂O₇, Ho₂Ti₂O₇) fractionalize
  into deconfined emergent magnetic monopoles; Coulomb-like 1/r interaction; liquid-gas
  phase transition under applied field.

MoEDAL Collaboration (2024). "MoEDAL Search in the CMS Beam Pipe for Magnetic Monopoles
  Produced via the Schwinger Effect."
  Phys. Rev. Lett. 133:071803.
  https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.133.071803
  Key claim: null result; mass limits up to 3.9 TeV for 1-10 g_D monopoles; strongest limits
  for Schwinger-mechanism monopoles 2-45 g_D (up to 80 GeV excluded).
  phys.org coverage: https://phys.org/news/2024-04-large-hadron-collider-zeroes-magnetic.html

Parker, E.N. (1970). "The Origin of Magnetic Fields." Astrophys. J. 160:383.
  Extended Parker bound (modern): arXiv:2404.04926 (Baines & Sherrat 2024, JHEP)
  https://arxiv.org/abs/2404.04926
  Key claim: galactic B-field draining → flux limit F_M ≲ 5.3×10⁻¹⁹ cm⁻² s⁻¹ sr⁻¹ for
  GUT monopoles (10¹³–10¹⁶ GeV).

Rajantie, A. (2012). "Introduction to Magnetic Monopoles." Contemp. Phys. 53(3):195.
  arXiv: https://arxiv.org/pdf/1204.3077
  Good general review: Dirac monopole, 't Hooft-Polyakov, GUT monopole problem, cosmological
  constraints, detection methods. Useful for Wall 10 (force energy-scale ladder) discussion.
```

### Key Pattern: Topological-Charge Register Architecture

For any mechanism using topological invariants (monopoles, skyrmions, vortices, instantons) as compute registers, the canonical structure is:

```
1. Topological charge Q ∈ ℤ → classical discrete register (immune to thermal noise below
   pair-production threshold, but CLASSICAL — Wall 4 / Feynman exponential still stands)

2. Annihilation/pair-creation event → irreversible logic gate
   (each event: ~2m_soliton c² energy released; recycling must be asserted to avoid
   power catastrophe — this is the required fiction for any soliton-compute mechanism)

3. Internal excitations of soliton core → multi-level (analog) register
   (limited by Wall 11 / analog precision unless reset protocol maintained)

4. Control plane mismatch: all known macroscopic analogs (spin-ice, etc.) operate at
   ~10⁻²²–10⁻²¹ J per event; GUT solitons at ~10⁻¹² J — gap of ~10¹⁰ in energy scale.
   Bridge requires "father's new physics" postulate.

5. Force energy-scale ladder (Wall 10) is the hardest wall for all GUT-scale mechanisms.
   Macroscopic fields cannot reach GUT symmetry-restoration scale (need B ~ 10⁴⁵ T;
   available lab fields ~ 10⁵ T; gap: 10⁴⁰). Black hole collapse precedes GUT threshold.
```

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| HomericIntelligence/Story | M15 string/T-duality mechanism design, 2026-06-01 | M15-string-tduality-substrate.md, ~2000 words, 7 citations, all 14 walls addressed |
| HomericIntelligence/Story | M43 magnetic-monopole register design, 2026-06-01 | M43-magnetic-monopole-register.md, ~3000 words, 7 real citations (Dirac 1931, 't Hooft/Polyakov 1974, Castelnovo 2008, MoEDAL 2024, Parker bound, Bekenstein, Schwinger); all 14 walls addressed; Parsimony 3/10, Capability 8/10; 4 no-go cascades documented; Wall 10 (force energy-scale ladder) identified as hardest wall for all GUT-scale mechanisms |
