# Notes: Git Unmerged Branch File Access

Supporting evidence for the canonical skill. These notes sit outside normal retrieval; the
rules required for operation live in the main entry.

## v2.3.0 — presence-based false attribution in a shared hotfix checkout

Generalized from a live multi-agent incident-response session; all organization, product,
repository, host, path, and issue identifiers are removed.

### Session shape

- One shared Git checkout of a release repository, with two concurrent agent lanes holding
  explicit file-ownership boundaries (a "hotfix lane" and a "release-record lane").
- Lane A needed to decide whether a durable repository change was still required for a fix
  that had already been hot-applied to the deployed artifact on shared storage.

### What went wrong (timeline)

1. Lane A compared the working-tree file against the patched deployed artifact: byte-equal.
2. Lane A greped the working tree, saw the fix lines, and — because an earlier
   `git status --short` had shown those paths clean — concluded the release tag already
   contained the fix: "no repository change needed; the durable defect is in the build
   pipeline only." This conclusion was reported to the operator as a correction.
3. In reality, lane B had applied the same hotfix to the working-tree files between lane A's
   probes and committed the change within the same session window. The tree lane A read was
   lane B's in-flight state, not tag content.
4. Ground truth recovered with `git show <release-tag>:<path>`: the tag contained only the
   declarative configuration knob; the two concrete flag lines were absent at the tag.
5. Lane A retracted the wrong correction in-session and confirmed lane B's open pull request
   as the durable carrier — no duplicate PR was opened.

### Diagnostic pattern that exposed it

A *surprisingly clean* `git diff` between the working tree and a patched deployed artifact,
when you believe the patch is unlanded, is itself evidence: it means the tree and the
artifact were patched together by someone else. Act on that signal immediately:

```bash
git show <tag>:<path> | grep -n "<fix-lines>"     # immutable ground truth
git log -3 --oneline -- <path>                    # did HEAD move under you?
git status --porcelain -- <path>                  # uncommitted peer edits?
git diff <tag> -- <path>                          # exact tree-vs-tag delta
```

### Evidence-decay rule of thumb

In a shared or reused checkout, treat every working-tree observation as perishable evidence
with a lifetime measured in minutes. Re-probe `git status` and `git log --oneline` for the
exact paths *immediately before* acting on earlier observations (committing, reporting, or
deciding against a change). Immutable-revision reads (`git show <rev>:<path>`) do not decay.

### Why this is the inverse of phantom code

The main entry's original failure family is false *absence* (file not in tree → wrongly
declared nonexistent). This case is false *presence* (content in tree → wrongly attributed
to a revision). Both share one decision rule: the working tree is not authoritative for a
revision; bind every existence/absence/content claim to an explicit revision before
concluding.

### Verification

All probes in the timeline and the diagnostic block above were executed live in the source
session and produced the cited outcomes. The downstream durable fix shipped through the
partner lane's pull request; no code change from this lesson's source session was required
beyond the correction itself.
