---
name: multi-repo-dependency-provenance-audit
license: BSD-3-Clause
description: "Find which repositories pull in a named package and what declares it. Use when a package must be traced across several repositories, licensing or SBOM review needs an origin, or a dependency claim must be separated from installed or captured artifacts."
category: ci-cd
date: 2026-11-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - dependency-audit
  - transitive-dependency
  - provenance
  - multi-repo
  - sbom
  - license-review
  - requirements
  - constraints
  - git-grep
  - false-positive-artifact
---

# Multi-Repo Dependency Provenance Audit

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-11-01 |
| **Objective** | Answer "which of these repositories pull in package X, and what declares it" with evidence that separates source declarations from transitive, installed, and captured occurrences. |
| **Outcome** | Operational. A read-only audit method that gives a per-repo answer plus the declaring parent and the pin. |
| **Verification** | verified-local. One four-repository audit, tracked files only. See [notes](./multi-repo-dependency-provenance-audit.notes.md). |

## When to Use

- A named package must be traced across a set of sibling repositories. Examples are a license or security review, an SBOM origin question, or a question from a reviewer.
- A package appears in an install log, a lockfile, or a scan report. You must find the repository and the manifest that declare it.
- A direct pin or an override exists for a package that no manifest declares. You must record the parent that supplies it.
- Search output is noisy because installed environments, captures, or vendored trees are in the working directory.

## Verified Workflow

### Quick Reference

```bash
# 1. Bind each candidate to a real repository root BEFORE you search.
git -C <dir> rev-parse --show-toplevel

# 2. Search tracked content only. This skips installed environments,
#    ignored output, and nested checkouts.
git -C <repo> grep -il "<package>"

# 3. Confirm there is no near-miss spelling in the clean repos.
git -C <repo> grep -in "<pack>.\?<age>"
```

A hit means that the repository contains the text. A hit does not mean that the repository declares the dependency.

### Suggested Approach

1. **Bind roots first.** Run `git rev-parse --show-toplevel` on each directory that you were given. A parent directory, or a name that looks like a repository, can resolve to a different root than you expect. A path that is not a repository gives no tracked-file evidence.
2. **Use tracked-file search.** Use `git grep` in each root. An untracked recursive search also matches installed site-packages, virtual environments, build output, container layers, and captured data. A single installed copy of the package then reports the whole repository as a match.
3. **Classify every hit by role.** Put each path into one of these groups before you report it:
   - **declaration**: a direct list in a manifest or a requirements file;
   - **constraint or override**: a pin, floor, or cap that changes resolution but is not a direct need;
   - **consumer**: import or call sites in source;
   - **install step**: an imperative install in a script or image build;
   - **captured artifact**: data, model cards, logs, or CSV files that quote the text.
   Only the first two groups answer "what pulls it in".
4. **Read the parent package metadata.** If no hit is a declaration, find the parent. Read the installed metadata of the parent (`Requires-Dist` entries, or the package metadata in the lockfile) to get the requirement specifier. Then compare it with the repository pin. Report the lowest specifier that the parent allows and the pin that was chosen.
5. **Report scope and limits.** State the search scope (tracked files, named roots) and the limits. Ignored files and uncommitted edits were not searched. A name that resolves to a home or parent directory is not a repository.
6. **Use the result.** For license or SBOM questions, name the declaring parent, not only the package. This is the link that a reader must act on.

If a repository has no tracked-file match, report it as clean. Do not infer an indirect path from another repository's similarity.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | -------------- |
| Recursive working-tree search | `grep -ril` from a parent directory over several trees | The scan matched installed site-packages and a container image, and the command timed out. One directory was the home directory, not a repository. | Bind each directory with `rev-parse --show-toplevel` and use `git grep` on tracked files. |
| Treating a package pin as a direct dependency | Found the pin in the constraints file and listed it as a direct dependency | No manifest declared the package. The pin only suspended the specifier that the parent package requires. | Classify every hit as declaration, constraint, consumer, install step, or captured artifact. Report the declaring parent. |
| Counting a data hit as a dependency | Reported a repository as matching because of a CSV and a model-card file | These files quote the name and are captured text. They do not affect resolution. | Restrict the answer to declarations and constraints. Name captured artifacts as matches that are not dependencies. |

## Results & Parameters

### Configuration

```bash
root_of() { git -C "$1" rev-parse --show-toplevel 2>/dev/null; }

for d in <dir1> <dir2> <dir3>; do
  r="$(root_of "$d")" || { echo "$d: not a repository"; continue; }
  echo "### $r"
  git -C "$r" grep -il "<package>"
done
```

For the parent evidence, use the installed metadata:

```bash
grep -E '^Requires-Dist: <package>' <site-packages>/<parent>-<ver>.dist-info/METADATA
```

### Expected Output

- Each input directory is bound to a repository root, or is marked as not a repository.
- Each matching repository has a hit list with a role for every path.
- Each match has the declaring parent and the allowed specifier, or the pin and the reason for it.
- Clean repositories appear explicitly.

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| Four sibling Python repositories | Read-only audit of one transitive package origin, 2026-11-01 | Tracked-file search gave one repository with a pinned constraint and no declaration; the parent metadata gave the requirement. [notes](./multi-repo-dependency-provenance-audit.notes.md) |

## References

- [`python-sca-pip-audit-update-transitive-lock`](./python-sca-pip-audit-update-transitive-lock.md) — trace `Required-by` when the goal is a lockfile remediation.
- [`dependency-manifest-single-source-of-truth`](./dependency-manifest-single-source-of-truth.md) — reconcile floors and caps once the declaring parent is known.
- [`sbom-syft-preserve-native-dependency-graph`](./sbom-syft-preserve-native-dependency-graph.md) — keep the dependency graph when you publish SBOM evidence.