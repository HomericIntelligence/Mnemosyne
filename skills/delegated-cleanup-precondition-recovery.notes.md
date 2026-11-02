# Notes: delegated-cleanup-precondition-recovery

Supporting evidence for the main entry. Generalized per the privacy rules: no
repository, organization, host, path, or identifier names.

## Incident (date of record: 2026-11-01)

- Target: the primary project checkout of a production repository. Several
  agent sessions share it; each leaves scratch directories in the working tree.
- Trigger: a dependency-locked cleanup delegation of the installed automation
  toolchain, run after a feature branch had merged through the forge.
- First run: exit code 1. The delegated tool logged a working-tree cleanliness
  error (uncommitted changes) and ran no cleanup step.
- Reconciliation:
  - `git status --porcelain=v1 -b` showed a clean tracked tree, four untracked
    scratch directories from other sessions, and a trunk one commit behind its
    remote.
  - Appended the four exact directory names to `.git/info/exclude`
    (clone-local, reversible, touches no shared configuration).
  - `git pull --ff-only` fast-forwarded the trunk by one commit.
  - `git status --porcelain=v1 -b` then printed only the branch line.
- Dependency state: the toolchain's standing automation checkout had local
  modifications to three tracked files, one untracked directory, and a branch
  diverged from its remote (1 ahead, 80 behind). It was preserved untouched.
- Replacement dependency: a fresh clone of the canonical upstream under the
  primary project's ignored worktrees directory. Identity checks: origin URL
  matched the canonical upstream, `git status --porcelain` was empty, and the
  delegation contract's required revision was an ancestor of the clone HEAD
  (`git merge-base --is-ancestor <required-sha> HEAD`, exit 0).
- Retry: the delegation helper re-invoked with the fresh clone as its first
  operand. Exit code 0.
- Result: the delegation removed the session's merged feature worktree and
  branch, removed several other merged leftovers, kept every dirty, unlanded,
  or unverifiable worktree, and reported completion without branch failures.
  The scaffolding clone was removed after the run because it held no unique
  work.

## Command sequence (generalized)

```bash
# 1. Observe
git status --porcelain=v1 -b --untracked-files=normal

# 2. Reconcile visibility (exact observed paths only)
printf '<dir-a/>\n<dir-b/>\n<dir-c/>\n<dir-d/>\n' >> .git/info/exclude

# 3. Fast-forward the trunk
git pull --ff-only

# 4. Gate
git status --porcelain=v1 -b        # branch line only

# 5. Dependency replacement (dirty or diverged checkout)
git clone <canonical-upstream-url> <primary-project>/.worktrees/<dependency>-<purpose>
git -C <clone> remote get-url origin
git -C <clone> status --porcelain=v1
git -C <clone> merge-base --is-ancestor <contract-required-sha> HEAD

# 6. Delegate (helper by absolute path; dependency checkout as first operand)
python3 <installed-helper>.py <clone-path>

# 7. Verify and clean scaffolding
rm -rf <clone-path>                 # only when it holds no unique work
```

## Decision boundaries observed

- The cleanliness gate counted untracked directories, not only modified tracked
  files. "No modified tracked files" is not sufficient; the untracked set must
  be empty or locally ignored.
- The delegated tool auto-deletes merged branches without prompting under its
  noninteractive flag set, but it preserves dirty, unlanded, and
  detached-or-unverifiable worktrees. The reconcile-then-retry flow never
  bypassed those safeguards.
- The delegated exit status remained the terminal status of the whole
  invocation, per the delegation contract.

## Related evidence limits

- Single verified incident; the workflow generalizes the invariant (reconcile
  preconditions, preserve foreign and dependency-local work, one bounded retry)
  but has one data point per case branch.
