# Supporting Notes: sealed-receipt-runtime-revival

## Provenance

Authored 2026-11-11 from an operator session reviving a sealed research
campaign runtime. The sealed receipt chain (layouts, identities, manifests,
runner bundles) governed whether any code could run, and several sealed
modules and artifact trees were missing from every reachable storage
location. The session ended with the full offline evidence chain passing,
and project-specific names, paths, hashes, and identifiers removed under the
private and proprietary information rules.

## Corpus context at authorship

Duplicate discovery against the resolved corpus found adjacent entries with
different intents: bounded-campaign-publication-aggregation (publication-size
governance) and architecture-config-pass-frozen-authority-directly
(config-passing refactor, unverified). No open pull request in the delivery
repository covered this intent at authorship.

## The fourteen walls, generalized

Each submission failed at exactly the previous gate once that gate was
proven offline:

1. Missing runner bundles: rebuilt via dev substitutes plus preserved sealed
   pieces, all hash-pinned.
2. Sealed absolute layout: rebuilt byte-for-byte at its declared paths.
3. Static qualification bindings: all files staged and hash-verified.
4. Sealed producer identities: passed in the CPU dry run.
5. One irreplaceable identity hash: accepted only through the caller's
   declared field substitution; no sealed bytes touched.
6. Backend-compat import: the campaign's own hash-verified compat guard
   applied to exactly one installed file.
7. Kernel extras: the runtime's optional kernel extra added to the sync.
8. Directory ownership rule: fresh environment directory modes tightened
   to be owner-controlled.
9. Publication path independence: private site paths replaced with required
   CLI flags over placeholder anchors.
10. Environment-variable policy: per-run inputs as long CLI flags with a
    CONFIG block beside job artifacts.
11. Runner-spec registry gaps: missing report registry entries added where
    sealed callers demanded them.
12. Staging inode pollution: frozen copies staged by copy only.
13. Receipt marker trees: full nested completion trees staged, marker
    contracts re-verified.
14. Compute driver probes: clean on the host, verified on the allocation.

## Validation evidence

- The full sealed chain (`prepare → loader → static qualification →
  producer identity → runtime build`) completed on a CPU host; only the
  compute driver probe required the allocation.
- The campaign's own static qualification entry point reported `qualified`
  for the affected report set against the restored layout.
- The publication-organized test suite passed with zero new failures.
