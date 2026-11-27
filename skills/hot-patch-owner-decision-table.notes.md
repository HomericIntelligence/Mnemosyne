# Hot Patch Owner Decision Table — Notes

Supporting evidence for `hot-patch-owner-decision-table`.

## Source incident (generalized)

- An urgent rule change was sent to several agents through a shared coordination board.
- A helper relayed the rule as a sentence; the applied patch acted on every other active object of the user, while the rule named only the object that the client had saved.
- Later in the same incident the owner refined the rule again, after the patch was already applied and reported as live.
- A separate interim patch implemented a comparison more broadly than the durable fix under review, which kept a narrower check inside one process.

## Decision value

- The destructive side effect (acting on shared objects) is what makes the table mandatory; a read-only patch does not need it.
- The divergence record matters when the interim patch and the durable fix coexist across a release boundary.
- The correction branch (re-check after an owner refinement) is distinct from the initial-table branch.

## Privacy screen

No product, organization, host, path, user, key identifier, or ticket number is included. The relay detail is summarized, not quoted.