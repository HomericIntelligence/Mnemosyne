# Notes: shared-worktree-branch-head-overtake-before-push

Supporting evidence for the main entry. Use these notes when you must decide whether a
detached head or a swept-in diff needs further handling.

## Session sequence (generalized)

1. The reviewer checked out a pull request at one head and confirmed a clean working tree.
2. The reviewer applied four fixes to source and test files. The reviewer did not commit them.
3. A long read-only run continued. The worktree moved to a new head that another publisher
   pushed. The working tree was clean at the new head, and all four fixes were gone.
4. The reviewer re-applied the fixes.
5. The reviewer ran a second long test batch. The reviewer also wrote a commit message file
   outside the worktree.
6. The reviewer ran one stage command that matched every dirty path, then committed and
   pushed. The commit summary listed more files than the reviewer edited.
7. Inspection showed a peer's in-flight change for the same review finding. That peer change
   added new symbols and new tests, and the pushed head failed lint.
8. The reviewer verified the union empirically: with the peer change included, the target
   test file passed fully. The reviewer kept the union and committed the missing finishing
   delta.
9. The branch advanced again after the verdict was posted. The reviewer posted one addendum
   that named the new head.

## Why each decision is correct

- **Read the head before every write.** A reset from an unpredicted source is not a failure
  signal that needs investigation first. It is an expected condition in a shared worktree
  that other publishers can write. The control is to know the current head, not to prevent
  the change.
- **Commit the verified part before more work.** Long validation runs increase the window.
  A commit is durable. An uncommitted fix in a shared tree is not.
- **Keep a peer change only with evidence.** The union is acceptable when the peer change
  serves the same intent, is inactive without its own tests, and the combined run is green.
  An unverified union is not acceptable. Report it to the owner instead.
- **Never rewrite the shared history.** The other publisher owns its commits. Re-integrate
  your change on the new head.

## Signals that your edit was overtaken

- `git status --short` is empty after an edit that you did not revert.
- A file read shows the previous content again.
- `git rev-parse HEAD` differs from the value that you read before the edit.

In each case, re-apply the edit on the current head. Then commit and push immediately.

## Limit

The evidence is from one session in one project. The rule is generalized to the condition,
not to the project. Each record in the delivery text uses the general pattern only.