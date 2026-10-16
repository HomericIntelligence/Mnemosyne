# Notes: Retroactive State-Label Audit of Closed Pull Requests

Supporting detail for `pr-state-label-retroactive-audit.md`. Readers need these commands
only when they execute the audit themselves; the decision rules live in the main entry.

## Inventory

```bash
gh pr list --repo OWNER/REPO --state closed --author AUTHOR \
  --search "created:>=YYYY-MM-DD" --limit 1000 \
  --json number,title,state,createdAt,closedAt,mergedAt,labels > all-prs.json
# unlabeled candidates:
jq '[.[] | select(.labels | map(.name) | contains(["state:implementation-go"]) | not)]'
```

Expect the merged/unlabeled subset to dominate the work. Closed-unmerged PRs cannot be
"prematurely merged"; audit them as informational only.

## Verdict carriers and formats observed

PR review objects (`repos/OWNER/REPO/pulls/N/reviews`):

- `## Terminal review exchange` with `Verdict: GO` and `Reviewed head: \`<full-sha>\``,
  plus a machine-readable state JSON containing `"verdict":"GO"` and phase data.
- Round verdicts such as `**Verdict: GO**`, `**Verdict: NO-GO**`, inline
  `— source review: GO`, and multi-round exchanges whose LAST verdict at the newest head
  governs.
- `## Verdict` section headers where the verdict word is on a following line.
- `Verdict: CONDITIONAL GO` — not a backfill GO; route to the authority owner.

Issue comments (`repos/OWNER/REPO/issues/N/comments`):

- Legacy `## Implementation review — GO at \`<sha>\``.
- Coordinator head-refresh notes recording a terminal GO plus a content-preserving rebase;
  the note itself names the prior carrier and the refreshed head.
- Status comments ("all required checks green at head <sha>") carry NO verdict.

Timeline (`repos/OWNER/REPO/issues/N/timeline`): event COUNTS are enough for triage
(`reviewed`, `commented`, `labeled`, `unlabeled`, `auto_squash_enabled`, `merged`).
A `labeled` + later `unlabeled` pair on the GO label records a withdrawn authorization.

## Digest approach (token discipline)

- One script emits one JSON object per PR: head, merge_commit, reviews[], comments[],
  timeline counts — with only verdict-relevant lines per body (first lines matching
  header/verdict patterns, capped length).
- `gh api --paginate --jq` prints one JSON document PER PAGE. Decode with an incremental
  JSON decoder (`json.JSONDecoder().raw_decode` in a whitespace-skipping loop) or slurp.

## Delegated classification rules that worked

Give every batch agent the same written rule file: verdict formats, supersede ordering
(later NO-GO at newer head wins unless re-authorized), the exact-head rule (GO at a
superseded head is ambiguous, not GO), the bare-timeline rule (no reviewed/commented
events and empty records = premature), one strict JSON line per PR with a short note
field, and a completeness requirement (every input PR exactly once). Validate counts and
uniqueness before acting.

## Coordinator binding checks for positive votes

- Head equality: reviewed head == final PR head; or blob/tree equality of the reviewed
  files at both heads (a rebase changes tree SHAs even with identical diffs — compare
  per-file content if a content claim matters).
- Ordering: no material commit after the terminal verdict (compare final verdict
  timestamp to last commit timestamp).
- Later disclaimers: a merge-fidelity NO-GO or an explicit observer "did not authorize"
  note after the GO blocks backfill.

## Label writes and invariant read

```bash
gh pr edit N --repo OWNER/REPO --add-label state:implementation-go \
  --remove-label state:implementation-no-go   # one exclusive transition
# bulk no-go path is analogous; --add-label is idempotent on GitHub

# closing invariant read:
gh pr list ... --json number,labels | \
  # require: every audited PR has exactly one state:* label; no PR has both
```
