# Planning Against an Unmerged Parent Notes

Supporting cases for
[`planning-unmerged-parent-contract-compile-smoke-gate.md`](planning-unmerged-parent-contract-compile-smoke-gate.md).

## Case Index

| Case | Source | Verification | Material result |
| --- | --- | --- | --- |
| Approved parent contract and first compile smoke | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-unmerged-parent-contract-compile-smoke-gate.md) | unverified | Distinguished proposed interfaces from landed facts and required compile-first reconciliation |
| Reviewer NOGO on unread APIs | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-unmerged-parent-contract-compile-smoke-gate.md) | unverified | Four flagged call-shape assumptions were read and the plan was revised at every dependent step |
| Validation-only child and log parser | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-unmerged-parent-contract-compile-smoke-gate.md) | unverified | Added entrypoint, container, artifact, sample-count, and trend checks |
| Unmerged sibling dispatch package | [Immutable source](https://github.com/HomericIntelligence/Mnemosyne/blob/e7f342098c41f3d5fda1bf7c7fedf754abdaaad2/skills/planning-unmerged-parent-contract-compile-smoke-gate.md) | unverified | Required an absent-path stop gate and one concrete callable per dispatch case |

## Detailed Case Notes

The source case involving proposed tensor APIs showed why an approved design is not a substitute for
reading declarations: keyword arguments, target representation, store semantics, and tuple return
shape all affected downstream steps. The reusable main keeps the source-reading and assumption-map
rules without preserving project-local file paths.

The validation-only case exposed three independent false-green risks: an invalid container command,
a parser accepting zero records, and a short noisy run judged by endpoint averages alone. Its useful
lesson is to validate the execution surface and sample population before evaluating the criterion.

The dispatch case added details commonly missed after a sound high-level design: use `BaseException`
where callback futures surface arbitrary worker failure, name lock paths, derive invariant targets
from public exports, and prevent vacuous empty-set success.

## Provenance

- Superseded main SHA-256: `a34932ad15b9961c0f1f2ffbe6e05545b0f0725c24ae73a220cdffb9b7f0e269`
- Issue #3335 base: `e7f342098c41f3d5fda1bf7c7fedf754abdaaad2`
- Old/new version: `1.3.0` → `2.0.0`
