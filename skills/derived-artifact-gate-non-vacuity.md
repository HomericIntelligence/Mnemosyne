---
name: derived-artifact-gate-non-vacuity
description: "Make a shipped gate that scans a derived or extracted artifact fail closed when the artifact comes back empty or degraded. Use when a build, release, or deployment pipeline greps a pin, constraint, or manifest file produced by an earlier step, when a byte-nonempty artifact can still carry an empty content set, when the producing step can degrade silently, or when a vacuously-clean gate can defer failure to a late downstream check."
category: ci-cd
date: 2026-11-02
version: "1.0.0"
user-invocable: false
verification: verified-ci
tags:
  - vacuous-gate
  - non-vacuity
  - fail-closed
  - derived-artifact
  - extraction
  - negative-scan
  - gate-evidence
  - seed-or-stop
  - pin-audit
  - pipeline
---

# Derived-Artifact Gate Non-Vacuity

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-02 |
| **Objective** | Stop a validation gate from passing vacuously when the artifact it scans comes back empty or degraded from an earlier pipeline step. |
| **Outcome** | Operational. Merged and green in the source repository: the producing step now refuses a degraded extraction, the gate asserts content before it records any verdict, and the pipeline stops early with an error that names the cause. The full end-to-end rerun against a new-generation base artifact is pending; see Evidence Boundary. |

A gate that greps an artifact produced by an earlier step inherits that step's
failure modes. Extraction can degrade quietly: the artifact file exists and can
be byte-nonempty while its content set is empty. Every scan over it is then
vacuous. Absence checks find nothing because there is nothing, and presence
checks skip a set that has no members. The pipeline then pays its full cost and
fails later at a check that does not name the real cause.

Make the producer refuse the degraded set, assert content at the mint point,
and decide explicitly between seeding and stopping when the authoritative
source legitimately lacks the asserted content.

## When to Use

- You write or review a shipped gate (build, release, deployment) that scans a
  derived or extracted artifact: a pin, constraint, or manifest subset
  extracted from a base image or package, a generated lockfile subset, or a
  filtered report.
- The producing step can yield an empty or partial set without failing: a
  filter finds zero rows, an extractor misses every key, a silent fallback
  emits a placeholder.
- The gate includes a negative scan (forbidden content must be absent). A
  clean verdict over an empty input proves nothing.
- A byte-level input check (file exists, size above zero) would pass on the
  degraded artifact, so consumer-side checks do not reach the semantic
  content.
- A new base or source legitimately lacks the asserted content, and you must
  choose between weakening the gate, letting it re-vacuate, or seeding the
  content.
- A failure surfaced late and far from the cause: a long pipeline stage
  failed at an import, smoke, or install check after the gate had passed.

## Verified Workflow

### Quick Reference

```bash
# 1. The producer refuses a degraded set: fail at the mint point, where the
#    context is complete. Build through a temp file and publish atomically.
extract_pins "$SOURCE" > "$PINS.tmp" || die "pin extraction failed for $SOURCE"
grep -qE '.' "$PINS.tmp" || die "pin extraction from $SOURCE produced an empty set"
mv "$PINS.tmp" "$PINS"

# 2. The gate asserts semantic non-vacuity before any scan verdict: a content
#    count above zero, and every required marker present in the extracted set.
count=$(grep -cE '^[a-z0-9_.-]+==' "$PINS")
[ "$count" -gt 0 ] || die "gate input carries zero pins; refusing to scan"
for token in $REQUIRED_TOKENS; do
  grep -q "^${token}==" "$PINS" || die "required pin ${token} absent from extracted set"
done

# 3. Only then scan. No unconditional success fallback around a scan. A scan
#    error is INCONCLUSIVE (stop), never CLEAN.
if grep -nE "$FORBIDDEN_PATTERNS" "$PINS"; then
  die "forbidden pins present (see matches above)"
fi
echo "pin audit clean: $count pins scanned, all required tokens present"

# 4. Source legitimately lacks the pins (a new base): seed them or stop.
#    Record the decision. Do not weaken the gate and do not let it re-vacuate.
```

### Suggested Approach

1. **Attest content, not bytes.** File existence and byte size do not prove
   that the artifact carries the set the gate asserts on. Assert at the
   semantic level: an entry count above zero and a required-marker probe — a
   short list of tokens that must survive extraction. This is the same
   non-vacuity invariant as a probe row in a set-containment test, applied to
   gate inputs (see References).
2. **Fail at the producer, not only at each consumer.** A refusal at the mint
   point gives every downstream consumer the invariant for free and stops
   where the context is complete: the source that degraded. Consumer-side
   checks alone force each consumer to re-derive the same check — and one can
   miss it. Keep a consumer-side assert as a backstop, not as the owner of the
   invariant.
3. **Separate the verdicts.** Keep CLEAN distinct from "did not check". No
   `|| echo CLEAN`-style fallback. A scan exit above the no-match code is
   INCONCLUSIVE and stops the gate. Record the coverage count with the clean
   verdict, so a later reader can tell an attested verdict from a vacuous one.
4. **Decide seed-or-stop explicitly when the source legitimately lacks the
   content.** A new base artifact can validly carry none of the protected
   content. The recorded options are: the recipe seeds the required set at
   build time so the gate still scans a non-empty set, or the gate stops
   early with an error that names the missing input. Choose per change and
   record the choice. Weakening the gate, or letting an empty set pass
   unexamined, is not an option — it drops the invariant for every future
   run.
5. **Prefer an early stop over a complete diagnosis.** The gate's duty is to
   refuse a run it cannot vouch for, with an error that names the input and
   the violated invariant. Do not spend gate complexity on repairing the
   source.
6. **Prove the hardened gate bites.** Exercise each hostile path by hand:
   empty extraction, missing marker, forbidden entry present. Each must stop
   the pipeline at the gate. Do not commit the fault; revert it after the
   stop is observed. Then trust the happy path only after its verdict line
   shows the attested count.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Scan an extracted pin set with a byte-level input check | A build gate extracted a protected-pin constraint set from a base artifact, verified the artifact file was produced, then scanned it for forbidden and required pins | The extraction silently degraded to an almost-empty set; the file existed, so the input check passed, every scan over the empty set was vacuously clean, and the pipeline paid about 8.5 minutes of build time to fail later at an import smoke check that did not name the cause | A byte-level check cannot reach semantic emptiness: assert a content count and required-marker probes at the mint point, and make the producer refuse a degraded extraction, so no consumer can scan an empty set |

## Results & Parameters

### Configuration

```text
non-vacuity assert = entry count > 0 over the extracted set,
                     AND every required marker present;
                     assert both before any scan verdict is recorded
producer contract  = extract to a temp file; refuse an empty result;
                     publish by atomic replace; consumers never see a
                     partial set
verdict vocabulary = CLEAN only with the attested count and markers recorded;
                     INCONCLUSIVE (stop) on any scan error or missing input;
                     never an unconditional success fallback
seed-or-stop       = when a new authoritative source legitimately carries none
                     of the asserted content: seed the required set in the
                     recipe, or stop early naming the missing input;
                     re-vacuating or weakening the gate is not an option
```

### Expected Output

- A degraded extraction stops the pipeline at the gate with an error that
  names the input and the violated invariant.
- A healthy run records the attested count and markers with the clean verdict.
- Each hostile condition (empty set, missing marker, forbidden entry) stops
  early; none reaches a later stage.
- Cost of the assertions is seconds. The vacuous alternative cost about 8.5
  minutes per silent miss in the triggering case, plus the diagnosis of an
  unrelated-looking late failure.

## Evidence Boundary

- Merged and green in the source repository: the extraction refusal and the
  audit guards shipped with the repository suite green (45 checks pass),
  including simulation fixtures for the empty-set and missing-marker paths.
- Not yet exercised end-to-end: a full pipeline run whose base artifact
  carries the new-generation toolchain waits on a separate base update. The
  seed-or-stop branch gets its live exercise there. The interim behavior on a
  legitimately-empty source is the early stop, which is the intended
  fail-closed posture.
- The general shape (a scan over zero inputs proves nothing; attest coverage
  with the verdict) is verified across the sibling entries in References. This
  entry adds the producer-side refusal, the semantic content assertion, and
  the seed-or-stop branch.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A proprietary image-build and deployment pipeline (unnamed per the privacy policy) | Gate hardening change, merged with repository CI green; live end-to-end rerun pending on a separate base update | Generalized incident detail and the generalization map in [the notes](derived-artifact-gate-non-vacuity.notes.md). |

## References

- [negative-scan-coverage-attestation](negative-scan-coverage-attestation.md) —
  the consumer-side sibling: attest what a negative scan read before recording
  it as delivery evidence. This entry covers the shipped-gate case: the
  invariant must hold on every unattended run, owned by the producer.
- [union-containment-vacuous-pass](union-containment-vacuous-pass.md) — the
  probe-row discipline for set assertions in tests; this entry applies the
  same non-vacuity invariant to gate inputs.
- [testing-non-vacuous-regression-guards-behavior-unchanged](testing-non-vacuous-regression-guards-behavior-unchanged.md)
  — test-code vacuity from green-from-start guards; distinct trigger and
  repair.
- [testing-retired-lever-inertness-guard](testing-retired-lever-inertness-guard.md)
  — pair rejection-only guards with an acceptance contrast so the rejection is
  attributable to the intended branch.
- [plan-authoring-ci-justfile-fix-risk-surfacing](plan-authoring-ci-justfile-fix-risk-surfacing.md)
  — the plan-authoring sibling: "exit 0 ≠ the linter ran", with the
  counter-caution that a count assert can hard-fail a benign empty glob. This
  entry's seed-or-stop step is where that emptiness decision is made explicit.
