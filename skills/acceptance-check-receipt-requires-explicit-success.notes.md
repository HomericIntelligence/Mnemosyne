# Acceptance Check Receipt Requires Explicit Success — Notes

Supporting evidence for the main entry. These notes are not part of normal retrieval.

## Source case (generalized)

A release-cut acceptance procedure defined a stop rule: the cut stops when a check prints
output. The procedure's acceptance criteria each print nothing when they pass. Six review
findings blocked the pull request. Five were real defects, and each was one instance of the
same fail-open rule. The sixth was already fixed and was proved from the files.

## Finding to fix map

| Class | Defect at head | Fix | Verification |
| --- | --- | --- | --- |
| Empty producer | An archive extract of a directory that is not committed exits non-zero; the extract produces no directory; the recursive diff reports only on stderr, so the check prints nothing and the stop rule does not fire. | Test the extracted directory after the extract and print one receipt line on stdout. | Staged repository without the directory: the guard line prints. With the directory: no output. |
| Empty stream | `git show rev:path | sha256sum` on a missing blob returns the empty-string digest instead of an absence value. | Test `git cat-file -e rev:path` first and return the schema's absence value. | Missing blob and missing revision both return `absent`; an existing blob returns its digest. |
| Partial state | The clean check reads `git diff --name-only HEAD`, so an untracked leftover file passes. | Read `git status --porcelain --untracked-files=all --no-renames`, strip the status prefix, and test each path. | Untracked file prints a dirty line; tracked modification still prints a dirty line; clean checkout prints nothing. |
| Stale binding | A row bound a digest to a document path that a later pull request deleted, and a citation named a decision-record path that no longer exists. | Re-bind the row to the current location of the guide and drop the retired citation. | `git cat-file -e` confirms the new path; the rebind runs both `git show` targets against a staged history. |

## Harness pattern that proved each branch

1. Extract each fenced shell block from the page and run `bash -n` on it.
2. Build a throwaway git repository with a base commit, a commit that adds the expected
   section, and a tag at the cut.
3. Run each changed block with the variables set to the throwaway tree.
4. Assert the exact stdout. One line for each negative case, empty output for the good case.

The harness caught its own wrong expectations. One expectation asserted the empty-stream
digest. The fixed function returned `absent`, which is the correct value.

## Pitfall: a harness can hit the same fail-open shape

A harness that reads a stream of lines into a loop misses a final line without a trailing
newline. Use an explicit terminator or compare whole output strings.

## Pitfall: an annotated tag in the harness opens an editor

A harness that runs `git tag <name>` respects a repository or user `tag.gpgSign` setting. It
then opens an interactive editor and blocks. Pass `-c tag.gpgSign=false` or `GIT_EDITOR=true`.

## Provenance

- Date: 2026-11-01
- Verification: `verified-local`. A staged shell harness ran every changed block. A strict
  documentation build and the repository documentation tests passed.
- Limits: the case comes from one repository. The rules generalize to any procedure that
  reads stdout as its pass signal.