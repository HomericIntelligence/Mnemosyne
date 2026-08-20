# Notes: Git Commit Signing Failures and Setup

Supporting evidence for
[`git-commit-signing-failures-and-setup`](./git-commit-signing-failures-and-setup.md). The complete
prior main is archived in [history](./git-commit-signing-failures-and-setup.history).

## Case Index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| GPG email/UID mismatch across blocked PRs | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/git-commit-signing-failures-and-setup.md) | verified-ci | Retained REST diagnosis, canonical noreply identity, full-range re-author/sign, and byte-identical diff |
| SSH signing on a headless host | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/git-commit-signing-failures-and-setup.md) | verified-ci | Retained public-key config, allowed signers, signing-key registration, and email-privacy boundary |
| Cryptographic pr-policy gate | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/git-commit-signing-failures-and-setup.md) | verified-ci | Retained every-commit verification and local-versus-hosted distinction |
| Mnemosyne PR #3021 sibling-head desynchronization | [immutable base source](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/git-commit-signing-failures-and-setup.md) | verified-local | Retained patch-replay recovery as partial evidence; no green merge inferred |

## Case Details

### Identity and hosted verification

Several commits were locally signed but GitHub returned `no_user` because the author/committer email
did not match an attributable key UID/account identity. Rewriting the full introduced range with the
canonical noreply identity and a registered key produced valid hosted signatures. GraphQL lagged in
some cases, while REST by commit SHA reflected verification promptly.

### Headless SSH setup

The setup case configured `gpg.format=ssh`, used the public-key path, created an allowed-signers file,
and registered the key as type signing. A private email caused an independent push privacy rejection;
switching to the canonical noreply address fixed push acceptance without changing signature validity.

### Sibling lineage

Amending a commit created a same-parent/same-tree sibling SHA. Close/reopen did not adopt it, and
update-branch added a merge whose unsigned ancestor still violated policy. The source session escaped
through a fresh PR, so the preferred patch-replay recovery remains verified-local rather than a
completed merged procedure.

## Compaction Disposition

- Kept in main: all diagnostic states, key/identity parameters, complete-range rewrite, content
  preservation, force-with-lease scope, PR-head proof, and sibling recovery boundary.
- Moved here: repository-specific PRs, incident chronology, and fleet statistics.
- Archived only: exhaustive status-code tables, command transcripts, and repeated examples.
