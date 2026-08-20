# Notes: NATS Server Authentication and Authorization Hardening

Supporting evidence for
[`nats-server-auth-authz-hardening`](./nats-server-auth-authz-hardening.md). The complete prior main is
in [history](./nats-server-auth-authz-hardening.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| mTLS `verify_and_map` and subject accounts plan | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/nats-server-auth-authz-hardening.md) | unverified | Retained SAN/DN correction and explicit parse/functional risk boundary |
| Odysseus issue #176 / PR #303 dual-listener token auth | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/nats-server-auth-authz-hardening.md) | verified-ci | Retained separate client/leaf auth, port 7422, brace-depth validation, and fail-closed unset behavior |
| Odysseus issue #306 / PR #341 cluster-route auth | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/nats-server-auth-authz-hardening.md) | verified-local | Retained port 6222 auth, word-boundary block extraction, no-route case, and six-test wiring; CI pending boundary preserved |

## Case Details

### Certificate/account planning

The initial plan reused the TLS trust chain and proposed certificate mapping plus subject-scoped
accounts. Review corrected a bare-CN assumption: identity mapping must be verified through SAN/DN
semantics for the deployed NATS version. Account syntax, leaf validity, JetStream subjects, and
certificate-generation commands were never parse/functionally tested, so they remain unverified.

### Client and leaf token implementation

The verified implementation added distinct credentials to the top-level client listener and nested
leafnode listener. Leaf remotes used 7422. A brace-depth validator replaced simple range matching,
and missing required environment caused `nats-server -t` to exit nonzero. CI invoked the validator
directly rather than assuming a justfile recipe would be discovered.

### Cluster route implementation

The later local case added authorization inside `cluster {}` on 6222. The extractor gained a
word-boundary keyword anchor, and six fixtures covered real/authed, missing leaf auth, missing cluster
auth, no cluster block, and auth outside the target. The test script was wired into local and CI
definitions. Local gates passed; hosted CI had not completed in the recorded source.

## Snapshot Presentation Normalization

The v1.3.0 base main contains quoted environment-variable placeholders immediately following a
field named `token`. The global credential hook interprets those examples as high-signal literal
credentials. With explicit user approval, the archived #3335 snapshot inserts one backslash into
each matching credential-field spelling on base-main lines 53, 67, 203, 215, 226, 233, 235, 237,
311, 318, 327, and 558 (`token` becomes `to\ken`). The original is 40,114 bytes with SHA-256
`7af5c35da7ba30ca31d2d339faaf9c99619b30cb590d30363eb9bc46dcde6770`; the normalized payload is
40,126 bytes. All other snapshot bytes, including the trailing newline, and the complete prior
history remain exact.

## Compaction Disposition

- Kept in main: all listener ports/contracts, token/certificate choices, nested-block algorithm,
  negative tests, wiring, client migration, ADR rules, and mixed evidence boundaries.
- Moved here: project-specific issue/PR narrative and case outcomes.
- Archived only: long configuration fixtures and repeated command transcripts.
