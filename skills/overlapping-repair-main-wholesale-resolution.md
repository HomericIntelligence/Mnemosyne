---
name: overlapping-repair-main-wholesale-resolution
description: "Resolve a merge where main and your branch repair the same defect class with different mechanisms: take main's repair wholesale, re-apply only branch-unique coverage as additive tests, and prove regenerated derived artifacts identical by semantic comparison. Use for conflict resolution against a fast-moving main."
category: ci-cd
date: 2026-10-30
version: "1.0.0"
user-invocable: false
tags:
  - merge-conflict
  - conflict-resolution
  - overlapping-repair
  - prefer-main-wholesale
  - additive-re-apply
  - regenerated-artifact
  - semantic-equality
  - derived-artifact
  - merge-tree
  - fast-moving-main
---

# Overlapping repairs on main and branch: prefer main wholesale, then port only unique coverage

**Supporting cases:** [notes](./overlapping-repair-main-wholesale-resolution.notes.md)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-30 |
| **Objective** | Resolve conflicts where both sides fixed the same defect differently, without double-repairing, losing branch-unique coverage, or trusting a textual auto-merge of a derived artifact. |
| **Outcome** | Successful. Two divergent repairs were resolved to main's mechanism with one additive test ported; a generated contract block was proven semantically identical to a fresh generation; all behavior suites stayed green. |

A branch that lives across heavy merge traffic meets the same defect twice:
once repaired by main, once by the branch, often with different mechanisms.
Resolving such a conflict by union-merging both repairs produces a double
repair: two incompatible invariants in one file, where each side can mask the
other's regressions. The disciplined resolution prefers main's mechanism
wholesale (main owns the invariant going forward), re-applies only coverage
that is unique to the branch as additive tests, and treats every derived or
regenerated artifact as unproven until it matches a fresh generation
semantically.

## When to Use

- A merge conflict falls in a file where main and the branch both changed the same tests or fixtures for the same root cause.
- Main landed a repair commit that names the same defect class your branch already repaired differently.
- A generated or derived block (rendered contract, golden data, migration manifest) auto-merged cleanly, and you must prove correctness, not merely the absence of conflict markers.
- You resolve conflicts against a fast-moving base and need a repeatable catalog of conflicts before touching files.

## Verified Workflow

### Quick Reference

```bash
# 1. Trial-merge first: enumerate conflicts without touching the worktree.
git merge-tree --write-tree origin/main HEAD | grep CONFLICT

# 2. For an overlapping repair: take main's mechanism wholesale.
git checkout --theirs path/to/file

# 3. Enumerate branch-unique additions in that file; port only those.
git log --oneline <merge-base>..HEAD -- path/to/file

# 4. For derived artifacts: regenerate at the merged tree and compare as data,
#    never as text. Formatter normalization makes text comparison meaningless.
<repo generator command> > /tmp/gen.new
python3 - <<'EOF'
import ast
old = ast.literal_eval(open('path/to/artifact').read().split('=', 1)[1].strip())
new = ast.literal_eval(open('/tmp/gen.new').read().split('=', 1)[1].strip())
assert old == new, 'regenerated artifact differs semantically'
EOF
```

### Suggested Approach

- Classify every conflicting file before resolving: content-identical overlap (keep one side, keep the better comment), divergent repair overlap (main wholesale + additive port), unrelated overlap (normal three-way judgment).
- When keeping one side of an identical edit, keep the version with the better rationale comment if one side carries it and the other does not; cite the shared root cause in the comment.
- After the wholesale takeover, list the branch's unique assertions (test names, helper functions, pins) from the branch history of that file. Port each one that still expresses behavior main's repair does not cover as a *new, separately named* test. Do not merge it into main's version of a same-named test; both come back in the next sync.
- Drop branch coverage that main's repair now duplicates. Keeping both is the double-repair failure in test form.
- "Auto-merged clean" is an absence of conflict, not a correctness proof. Any artifact derived from a generator (a rendered contract block, a blessed golden file) must be regenerated at the merged tree and compared semantically; quote style and wrapping drift under the formatter and defeat text comparison.
- Verify the whole resolution with the behavior suites for the touched modules before declaring the merge done.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Union-merge both repairs | Kept the branch's helper and main's helper in one file. | Two mechanisms encode two identity invariants; fixtures pass for contradictory reasons and a later regression in either is masked by the other. | Prefer main's mechanism wholesale; port branch-unique coverage additively with new names. |
| Text-diff the regenerated block | Compared the merged generated block to a fresh generation with `diff`. | Formatter normalization (quote style, wrapping) made a semantically identical block look different in every line. | Compare generated artifacts as parsed data — literal evaluation or structural equality — never as text. |
| Trust textual auto-merge | Accepted the clean auto-merge of a generated block as correct by inspection. | Auto-merge guarantees no conflict markers; it does not guarantee the merged block equals a fresh generation. | Regenerate at the merged tree and require semantic equality before closing the resolution. |

## Results & Parameters

### Configuration

- `merge-tree --write-tree` needs a recent git; it writes no files and leaves the worktree untouched.
- The semantic-comparison harness adapts to the artifact: `ast.literal_eval` for a literal block, `json.loads` for JSON, or the repository's own parser.
- Branch-unique enumeration uses the true merge base, not a remembered base: `git merge-base HEAD origin/main`.

### Expected Output

- Conflict catalog before any edit (trial merge).
- Each divergent-overlap file resolves to main's mechanism plus zero or more additive tests with new names; the behavior suite for the module is green.
- Each derived artifact compares equal to a fresh generation by semantic equality.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| An internal deployment-control codebase | A branch merged a main that landed an identical one-line fixture fix, a divergent eight-fixture repair of the same identity change, and a regeneration of a CLI contract block; resolution used main wholesale, one additive drift pin, and an AST-literal equality proof; all suites green (185 + 980 + 888 passed). | See [notes](./overlapping-repair-main-wholesale-resolution.notes.md). |

## References

- Related orchestrator-boundary variant for conflicts under signed-commit ownership: [ci-cd-git-boundary-merge-conflict-staged-handoff](ci-cd-git-boundary-merge-conflict-staged-handoff.md)
- Related intra-file splice guard for the re-applied additive test: [reapply-splice-dead-tail-guard](reapply-splice-dead-tail-guard.md)
