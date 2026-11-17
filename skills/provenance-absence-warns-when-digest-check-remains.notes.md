# Notes: provenance-absence-warns-when-digest-check-remains

Supporting evidence for the main entry. Generalized; no internal identifiers.

## Source case

An inference-serving control plane had two admission paths for one model
serving image:

- A launch-time walk: verifies the image magic, hashes the bytes, and
  compares the digest against the value pinned at registration. A missing or
  unverifiable embedded build record was already a warning there; the image
  admitted on its digest alone.
- A registration verb: refused every image whose byte walk touched the
  embedded build record, with one message for all failures.

Because the registration verb refused, a deployment lane whose images carried
no build record could not serve a model, although the identical image passed
the launch walk. The record was traceability, not a gate.

## Change shape

The registration verb moved to the launch contract:

| Case | Before | After |
| --- | --- | --- |
| Receipt exists and verifies | registers | registers, provenance mode `receipt-verified` |
| Receipt pins different image bytes | refuses | refuses |
| No receipt, or record absent, unreadable, or schema-invalid | refuses | registers, provenance mode `digest-only`, gap reason recorded, one warning |
| Bytes unhashable or unreadable | refuses | refuses |

The receipt option became optional; omitting it selects the digest-only
path. The registered digest stays the trust check: the launch walk compares
the bytes against it at every submission.

## Verification evidence

Focused test suites for the change, all green unless stated:

- Registration and rollback contract suite: 8 passed, 0 failed.
- Admission walk suite: 69 passed, 0 failed, including the grant
  re-validation test.
- Operator service suite: 231 passed, 1 failed. The failure is
  environment-specific: the container's `/tmp` is mode `1777` and owned by
  the service user, so an ancestor-mode check that expects a root-owned
  sticky directory refuses. Unrelated to the change.
- Render, registrar, and admin-verb suites: 837 passed with the one fixture
  defect fixed (see below).

## Findings that shaped the rule

1. One wrapper message for all verification failures masked a test. The
   byte-mismatch test passed while the walk refused at a read-only mode
   check before it reached the digest comparison. The fixture needed its
   intended precondition (the forged image had to be read-only) before the
   test exercised its named branch.
2. The provenance gap belongs in the durable record. The gap reason and the
   provenance mode travel with the pinned digest, so a later process reads
   them without a log search. A log-only warning does not survive a process
   restart.

## Test-environment caveat

A default temp directory that exceeds a unix socket path bound emitted one
extra drift note per test and shifted index-based drift assertions in the
admission suite. A short node-local temp directory gave a clean verdict on
this host. This is a test-harness condition, not part of the rule.
