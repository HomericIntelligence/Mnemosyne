# Git Workflow Rebase Worktree Signing — Notes

## Case index

| Case | Source | Verification | Disposition |
| --- | --- | --- | --- |
| Fourteen sibling branches rebased with isolated worktrees | [immutable source case index](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/git-workflow-rebase-worktree-signing.md) | `verified-local` operational record | Retained one-branch/one-worktree parallelism |
| Stale remote branch selected when creating submodule worktree | [immutable source case index](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/git-workflow-rebase-worktree-signing.md) | `verified-local` operational record | Retained explicit remote-head verification |
| Rejected PR salvaged by semantic cherry-pick | [immutable source case index](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/git-workflow-rebase-worktree-signing.md) | `verified-local` operational record | Retained portable-versus-feature-specific classification |
| Six commits accidentally made on local main | [immutable source case index](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/git-workflow-rebase-worktree-signing.md) | `verified-local` operational record | Retained create-preservation-branch-first recovery |
| Plan artifacts missing because implementation branch was stale | [ProjectHephaestus PR #1259](https://github.com/HomericIntelligence/ProjectHephaestus/pull/1259) | `verified-local` | Retained upstream comparison and rebase-before-edit rule |
| Valid tag signature remained unverified on hosted Git | [immutable source case index](https://github.com/HomericIntelligence/Mnemosyne/blob/af4676cc2c54565a41c1e196ad964cf8ccc51e5b/skills/git-workflow-rebase-worktree-signing.md) | Live API readback in source session | Retained four-identity signing model |

## Preservation audit worksheet

| Object | Identity | Unique work check | Review/merge evidence | Safe action |
| --- | --- | --- | --- | --- |
| Worktree | Path and HEAD | Dirty/staged/untracked inventory | Owning branch/PR | Preserve unless explicitly authorized |
| Branch | Local and remote SHA | Patch/file comparison to main | PR state and merge SHA | Delete only after proof and authority |
| Stash | Stash SHA/message | Inspect patch and base | Replacement commit if any | Keep until recovery proven |
| Submodule | Child HEAD | Child status and remote reachability | Parent pointer diff | Update parent deliberately |

## Signing diagnostic matrix

| Symptom | Check |
| --- | --- |
| Local signature bad/unknown | Full fingerprint and local keyring |
| Local good, hosted unverified | Registered key fingerprint |
| Correct key, still unverified | Commit/tagger email equals key UID |
| Email equals UID, still unverified | Email verified on owning account |

## Evidence boundary

The source combines operational cases across repositories. Treat each row's scope independently;
do not generalize a hosted provider's verification behavior or a repository's cleanup policy beyond
the recorded evidence.
