---
name: multi-repo-dependency-provenance-audit
license: BSD-3-Clause
---

# Notes: Multi-Repo Dependency Provenance Audit

Supporting evidence for `multi-repo-dependency-provenance-audit.md`. Read this file when you need the
fuller command set, the failure signatures, or the audit result format.

## Provenance

- Date: 2026-11-01.
- Source: one read-only audit session across four sibling Python repositories in a shared home
  directory. The question was whether a named package reaches any of the repositories, and through
  what.
- Method limits: tracked files only, `git grep`, and installed metadata of the declaring parent. No
  lockfile solve and no image inspection was done.

## Command set

```bash
# Bind each candidate to its real root. Print the remote when you report provenance.
for d in <dir1> <dir2> <dir3>; do
  r="$(git -C "$d" rev-parse --show-toplevel 2>/dev/null)" || { echo "$d: not a repo"; continue; }
  echo "### $r"
  git -C "$r" remote get-url origin 2>/dev/null
done

# Tracked-file search per root.
git -C <repo> grep -il "<package>"

# Near-miss spelling check on the repositories that report clean.
git -C <repo> grep -in "<pack>.\?<age>"

# Role context for each hit.
git -C <repo> grep -in "<package>" -- <hit-path>

# Parent requirement metadata.
grep -E '^Requires-Dist: <package>' <site-packages>/<parent>-<ver>.dist-info/METADATA
```

## Failure signatures seen in this session

| Signature | Meaning | Action |
| --- | --- | --- |
| Recursive search stops with a timeout | The tree includes installed environments, container layers, or large captures | Stop the recursive search and use `git grep` per root |
| A repository name resolves to a home directory | The directory is a workspace, not a repository | Bind with `rev-parse --show-toplevel` before you report |
| Hits are all inside site-packages or a container image | Installed copies, not declarations | Report as tool environment, not a repository dependency |
| Hits are CSV, JSONL, or model-card files | Captured text that quotes the name | Report as a match that is not a dependency |
| A pin exists with no declaration | The parent package supplies the requirement | Read the parent metadata, report the parent and the pin |
| A comment mentions an evaluator or runtime by name | Prose, not a dependency | Report separately from the role classification |

## Role classification detail

| Role | Typical location | Answers "what pulls it in"? |
| --- | --- | --- |
| Declaration | Manifest dependency list, requirements file | Yes |
| Constraint or override | Constraints file, lock pin, floor or cap | Partially. It sets the resolved version, not the need |
| Consumer | Source imports, call sites, docstrings | No. It shows usage of an already-present package |
| Install step | Image build, setup script, environment smoke test | Yes, for that environment |
| Captured artifact | Data files, logs, model cards, reports | No |
| Tool environment | Installed site-packages, container images | Not repository source. Name it, and name the owner |

## Audit result format

```text
scope: <roots> ; tracked files only
<root>: <clean | hits>
  <path>: <role> -- <detail>
declaring parent: <package> (Requires-Dist: <specifier>)
selected pin: <version>
limits: ignored files and uncommitted edits not searched
```

## Observations that change a recommendation

- The parent framework was the only source of the requirement. The repository pin matched the
  lower bound of the parent specifier exactly. A reader who wants to drop the package must change the
  parent, not the pin.
- One source comment read as a dependency but was prose about a different component. Classify prose
  before you add it to the count.
- One repository was assessed as clean from tracked files alone. Ignored or generated trees were not
  searched. Report that limit rather than imply full coverage.