---
name: validation-fixture-poison-literal-self-scan
license: BSD-3-Clause
description: Assemble gate-forbidden seed literals at run time so the fixture's copy of the test module never trips the gate. Use when a regression test copies the scanned repository into a fixture and seeds violation data under a directory the gate ignores by default.
category: testing
date: 2026-11-24
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - testing
  - fixture
  - validation-gate
  - regression-test
  - forbidden-token
  - self-scan
  - copytree
  - ignore-set
---

# Validation-Fixture Poison-Literal Self-Scan

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-24 |
| **Objective** | Find and stop the mass failure that starts when a regression test seeds a forbidden literal, and the fixture's copy of the test module carries that literal into the scanned surface. |
| **Outcome** | Successful. One added contiguous literal made a whole test class fail at once. Run-time assembly of the literal removed the collateral failure and left only the intended regression failure. |

## When to Use

- A test setup builds the fixture with a copy operation (`shutil.copytree` or the
  same) from the repository that a gate or validator later scans for forbidden
  content, such as banned prefixes, marker tokens, or disallowed file types.
- The same test writes seed data that must fail the gate only when a protected
  directory is inspected, for example a compiled artifact in a cache directory
  or a forbidden-token payload file under a host-state directory.
- After such a test is added, the whole fixture-based class fails at once and
  the gate report names the fixture's copy of the test module itself.
- A new local-state directory (one made by a worktree agreement or a host
  tool) is missing from the gate's default ignore set, and a test must pin
  that it stays ignored.

## Verified Workflow

### Quick Reference

```python
# Assemble the gate-forbidden literal at run time, so its one-piece
# form never exists in any source the gate scans.
part = "Proj"
(runtime_dir / "payload.gen.d.ts").write_text(f"{part}ectListData")
```

### Suggested Approach

1. Read the first failing file name in the gate report before you suspect the
   environment. When the fixture's copy of your test module appears as the
   offender, the cause is a content self-reference, not fixture decay.
2. Check each recent seed writer for literals that also appear in the test
   module's own source. The fixture copy carries them, and the gate flags its
   own test copy.
3. Assemble each such literal at run time (a formatted combination or a join),
   so the contiguous form never appears in any scanned source file.
4. Leave a short comment in the test that names the reason. Without it, a
   later cleanup pass can simplify the assembly back into a contiguous
   literal and re-arm the cascade.
5. Prove the test keeps its discriminating power: it must fail before the
   ignore-set change and pass after it. A passing fixture suite that never
   failed before the fix is evidence the test is empty, not that the gate is
   correct.

See also the sibling rule
[tech-debt-discovery-grep-self-match](tech-debt-discovery-grep-self-match.md):
a gate's own status strings must stay free of the tokens they report on.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Treat the failure as environmental | The first sweep attributed a 24-test class failure to fixture drift or a runner problem | The gate named the fixture's copy of the test module; one new contiguous literal in that module was the only change | A mass failure after one test change points at content the change itself introduced; check seed literals before the environment |
| Write the seed literal verbatim | The new test wrote the payload as one contiguous string in the test source | The fixture copy operation copied that source into the fixture, and the gate scanned and flagged it like any other file | Seed content under protected directories must use run-time assembly, never a contiguous literal in scanned source |

## Results & Parameters

- **Seed layout used in the supporting evidence:** one compiled artifact under
  a worktree directory, and one forbidden-prefix payload file under a
  host-state package directory. Both directories belong to the gate's default
  ignore set.
- **Run-time assembly rule:** no gate-forbidden token may appear as one
  contiguous string in a source file the gate scans.
- **Diagnostic rule:** when a fixture-based suite fails in mass after a single
  test change, diff the change's literals, not the environment.
- **Verification status:** verified by execution in one project. The mass
  failure reproduced with the contiguous literal present, and only the
  intended failure remained after run-time assembly.

See [notes](validation-fixture-poison-literal-self-scan.notes.md) for the
generalized fixture shape, seed layout, and the run evidence.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| One project | Add a regression test for a validator ignore set that omitted local-state directories | The new test cascaded into a 24-test class failure because its seed literal appeared in the fixture's copy of the test module. Run-time assembly isolated the intended pre-fix failure. See the linked notes for detail. |

## References

- [tech-debt-discovery-grep-self-match](tech-debt-discovery-grep-self-match.md)
- [source-policy-assertion-scope](source-policy-assertion-scope.md)
