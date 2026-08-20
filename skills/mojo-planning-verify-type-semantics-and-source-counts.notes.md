# Mojo Planning Verification — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| ResNet-18 activation cache and named velocity/result planning | [ProjectOdyssey issue #5514](https://github.com/HomericIntelligence/Odyssey/issues/5514) | R0 plan unverified; R1 source probes `verified-local`; target feature not implemented | Retained direct-count, AnyTensor, fieldwise constructor, tuple-shape, and residual-risk guidance |
| Immutable source at corpus migration base | [Mnemosyne base source](https://github.com/HomericIntelligence/Mnemosyne/blob/d377a8924aff84e5cc193b720130b4c57e38c5c3/skills/mojo-planning-verify-type-semantics-and-source-counts.md) | Verified read; does not upgrade Mojo feature evidence | Supplies detailed original coordinates without duplicating the snapshot |
| Corpus compaction | [Mnemosyne issue #3335](https://github.com/HomericIntelligence/Mnemosyne/issues/3335) | Batch checks only | Added the missing main-file history reference and moved case detail here |

## R1 observed facts

| Claim | Observed evidence | Boundary |
| --- | --- | --- |
| Fieldwise kwargs | Existing `PrecisionConfig(...)` keyword call sites and declaration | Source read on pinned main; not a universal Mojo-version guarantee |
| AnyTensor snapshot idiom | Refcounted storage documentation and Copyable/ImplicitlyCopyable/Movable conformances | Supports replacement-style use inspected in plan; exact mutation still deserves a run probe |
| Tuple precedent | Largest observed comparable tuple had six elements | Codebase precedent, not compiler limit |
| Parameter count | Exact pattern returned 82 | Pattern counted trainable tensor fields; “84” included two running stats |

## Probe recording template

For each claim, preserve repository SHA, Mojo version, source command/output, disposable probe
source, build/run command, observed result, and design consequence. A compiler success and a
maintainability decision are separate findings.

## Evidence boundary

The R1 probes justify `verified-local`. No target-feature build or CI result was observed, so the
skill must not be described as CI-verified.
