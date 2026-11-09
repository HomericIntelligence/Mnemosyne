# Notes: per-user-writable-path-under-closed-root

Supporting detail for the main entry. Nothing here is required for operation.

## Evidence shape (generalized)

A plan issue asked for a derived batch-input root of the form
`<service-root>/<context>/batches/<user>`, with no cluster key and no mount
string. Four plan revisions were reviewed.

1. Revision 3 accepted an operator-only provisioning model. Ordinary users
   could not place a file at the path, so the acceptance criterion "a path
   under the derived root is accepted" was only testable with mocks. The
   operator had no source to stage, because no user file existed in the
   closed tree.
2. Revision 4 copied the existing requester drop-directory pattern with mode
   `0o3733`. The ancestors stayed `0o2750` and `0o750`. The other class got no
   `x` at the first component, so the drop directory was unreachable.
3. Revision 4 also let the service create the leaf on first use. A service
   account without `CAP_CHOWN` produced a service-owned `0o2750` leaf. The
   sticky parent stopped the user from removing it, so first use made the
   leaf permanent and unusable.
4. Revision 5 stated one mode for each directory and one creator for each
   directory. Ancestors became `0o2751` and `0o751`, the drop directory stayed
   `0o3733`, and the leaf stayed user-owned. The gateway never creates a
   leaf. The plan also named each predicate that pins the root mode: the
   loader, the verifier, the declared repair mode, and the policy table.

## Verify pattern

The checks are read-only and need no live cluster:

- For each ancestor, open it as a non-owner, non-member account and confirm
  that traverse succeeds and that listing fails.
- For the drop directory, create one entry as the account, confirm that
  listing fails, and confirm that a second account cannot remove that entry.
- For the leaf, confirm that the creator holds the owner class. A leaf
  created by the service account is the failure shape.
- For the file, confirm that the service account reads it through the group
  class with a user umask of `027`.
- Grep each mode predicate and confirm that each one accepts the new value.
  A verifier that compares `mode & 0o777` to an access-bit mask accepts the
  set-group-ID form, while a loader that compares to an exact value does not.

## Limit

No code was merged in the source session. The modes and the predicates come
from reading the repository, not from a completed run.