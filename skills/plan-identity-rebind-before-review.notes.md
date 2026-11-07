# plan-identity-rebind-before-review — notes

Supporting evidence for [plan-identity-rebind-before-review.md](./plan-identity-rebind-before-review.md).
The repository and issue numbers of the source session are withheld.

## Evidence type

- verified-live: the read-only checks ran against the live tracker and the live default branch.
- The result is a review disposition, not an implementation.

## Observed mismatch pattern

One plan review prompt supplied three fixed blocks: the issue body, the plan text, and a prior review.
The live issue had changed after the plan was written. The recomputation found these results:

- The plan's "current requirements" digest and its separate "binding" digest both differed from the
  live digest. The plan's binding also carried a requirements update time that was older than the live
  update time.
- The plan's "required dependencies" was a strict subset of the issue dependency list. It also named
  two dependencies that the issue body does not contain, and it omitted most of the issue list.
- The plan asserted that four dependencies were open. Three were closed and one was open.
- The plan cited a default-branch commit that was about two months older than the live head. Its
  install, schema, and upgrade steps waited for a merge of a dependency that was already closed.
- The plan placed most of its steps on a subject token that the issue body does not contain. The live
  scope carried other tokens that the plan did not name.
- The plan stated that no previous plan existed and also cited a previous plan digest.

## Decision effect

Each mismatch alone justified a no-go. Read as a set, they showed that the plan served an earlier
planning epoch. A content rubric applied to it would have graded the wrong scope. The gaps that it
reported could not help the author.

## Limits

- The prior review in that loop was a recovery artifact. It started with "conversation recovery
  required" and ended with a blocked state, with no findings. The recovered content was not available.
  This entry makes no claim about it.
- The source session was a read-only review. It did not test the producer-side fix, which would make
  one canonical producer reject a stated digest that differs from the live digest.
- The knowledge checkout used for discovery was dirty or partly behind its default branch. The entry
  does not depend on that state.

## Relation to other entries

- `planning-verify-issue-premise-before-implementing` sweeps anchors and authority records at the
  hand-off between plan approval and implementation.
- This entry covers the gate before a review, and it covers the issue and dependency identity.
  The two triggers differ, and a plan can pass one check and fail the other.