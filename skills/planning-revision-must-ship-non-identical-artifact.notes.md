# planning-revision-must-ship-non-identical-artifact — notes

Evidence detail for the main entry. These notes stay outside normal retrieval.

## Source evidence checked (read-only)

- The retained revision of the plan artifact was byte-identical to the revision already reviewed twice; the review recorded "unchanged for the third consecutive review" and listed three standing findings.
- Finding 1 (base claim): the plan stated that a deploy script "is not in the repository". At the current head the script was tracked, with one commit that is an ancestor of the head. That commit had already delivered three of the issue's four requested behaviors.
- Finding 2 (dead anchors): the plan cited and edited a runbook file and an inventory file. Both were deleted by later merged changes; neither path resolves at the head.
- Finding 3 (shared module): the plan refactored a shared shell library that every numbered script sources. The consumers existed and the plan named none of them.
- Mechanically consumed surface: one documentation page is parsed by a repository test that accepts only fixed-shape command-table rows; a prose section is safe, a new table is not.
- Consumer of the subject script: a unit test extracts a heredoc from the script with a fixed regular expression. Any restructure of that block breaks the consumer.

## Verification performed

- `git log --oneline -3 -- <script>` and `git show --stat <commit>`: dated the script addition and confirmed ancestry.
- `git show --stat` on the deletion commits: dated each removed anchor.
- `grep -n` on the consumer test: located the extraction pattern and the read of the script path.
- Reads of the current script, the shared library, and the documentation page: established the current line numbers used in the re-bound evidence.
- No revision was published; the work was a planning-context re-plan.

## Limits

- verified-local: the checks ran in one checkout at one head; no second head was compared.
- The main entry states the rule only. How to prove an individual premise in depth stays with the premise-verification and post-review entries.
- The entry does not prescribe a storage format for the revision diff; a repository may keep revisions in Git only.