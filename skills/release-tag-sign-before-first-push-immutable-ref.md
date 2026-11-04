---
name: release-tag-sign-before-first-push-immutable-ref
license: BSD-3-Clause
description: "Sign a release tag before the first push when the host protects tags, and recover with a signed release asset when you missed it. Use when: (1) you are about to push a release tag in a repository whose rules restrict tags, (2) a push to replace or delete a pushed tag is refused as a protected ref, (3) the owner asks for a signed release after an unsigned tag exists."
category: tooling
date: 2026-10-29
version: "1.0.0"
user-invocable: false
verification: verified-local
tags: [release, git-tag, signing, tag-protection, immutable-ref, detached-signature, ssh-signing]
---

# Sign a Release Tag Before the First Push

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-10-29 |
| **Objective** | Publish a signed release without rewriting a protected tag. |
| **Outcome** | Operational. An unsigned annotated tag was pushed first. A later push of a signed replacement and a delete were both refused by the host's tag rules. The release was published off the existing tag, and the release manifest carries a detached signature that verifies. |

Tag protection rules usually allow creation (often through a bypass for an administrator) and
refuse update and deletion. The first push of a tag is therefore final. Decide on the signature
before that push.

## When to Use

- You run a release script that creates and pushes the tag.
- A host rule says "Cannot update this protected ref" or "Cannot delete this tag".
- A signed tag is required and the unsigned one is already on the remote.

## Verified Workflow

### Quick Reference

```bash
git tag -s vX.Y.Z <commit> -m "<Product> X.Y.Z"   # sign at creation, annotated
git tag -v vX.Y.Z                                   # must print a good signature
git push origin refs/tags/vX.Y.Z                    # the only push
# after a miss, do not retry update or delete: publish off the existing tag and sign the asset
ssh-keygen -Y sign -f <signing key> -n file <manifest>        # writes <manifest>.sig
ssh-keygen -Y verify -f <allowed_signers> -I <signer> -n file -s <manifest>.sig < <manifest>
```

### Suggested Approach

1. Make the release script create the tag with `git tag -s` (or fail), and verify the signature
   before the push. Read the host's tag rules in the repository settings first, and ask the
   owner whether a pushed tag can ever be replaced.
2. After an unsigned push, do not try to update or delete the ref. The host refuses both, and an
   agent permission layer can also block a forced tag push. Do not look for a bypass: the rule
   is the intended control.
3. Publish the release from the existing tag (`gh release create <tag> --verify-tag`). Attach the
   release manifest and a detached signature of it. Verify the signature against the allowed signers.
4. Say in the release notes that the tag is unsigned, why (the rule made it immutable), and how
   to verify the asset.
5. Restore your local tag to the remote object (`git fetch --force origin refs/tags/<tag>:refs/tags/<tag>`).
   A local signed tag with a different object invites a rejected push later.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Replace the tag with a signed one | Force push of the signed tag with a lease | The host refused: protected ref | Sign before the first push |
| Delete the tag, then push again | Deleted the remote tag | The host refused: cannot delete this tag | Tag rules block delete as well as update |
| Create the tag in a script | The script ran `git tag -a` | Annotated but unsigned; the push was final | Make the script sign and verify |

## Results & Parameters

### Configuration

```yaml
tag: annotated and signed, verified before the push
release: created with --verify-tag off the pushed tag
asset_signature: detached OpenSSH signature, namespace "file"
notes: state that the tag is unsigned and how to verify the asset
```

### Expected Output

`git tag -v` shows a good signature before the push. After a miss, the release page lists the
manifest and its `.sig`, and `ssh-keygen -Y verify` prints a good signature.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| A scheduler-managed model-serving deployment | Release cut, 2026-10 | Tag update and delete refused; release published with a signed manifest. |

## References

- [release-auto-tag-token-trigger-and-doc-guard-traps](release-auto-tag-token-trigger-and-doc-guard-traps.md) — other traps of immutable tags
