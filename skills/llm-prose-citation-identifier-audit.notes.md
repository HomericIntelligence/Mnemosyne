# Notes: LLM Prose Citation Identifier Audit

Supporting evidence for `llm-prose-citation-identifier-audit.md`. These notes
are not part of normal retrieval.

## Source case (privacy-generalized)

A private repository runs a pipeline that generates a dated weekly engineering
report: deterministic collectors produce JSON intermediates (merged PRs,
closed issues, commits; fleet and usage telemetry), and an LLM writes section
prose from a compacted prompt. Across one report period, three prose
revisions were generated (style prompt changed twice; data window pinned).

## Audit rounds and results

| Revision | Cited refs | Verified in dataset | Outliers | Outlier resolution |
| -------- | ---------- | ------------------- | -------- | ------------------ |
| R1 (initial STE-style prose) | 67 | 66 | 1 | Confirmed real OPEN tracker (repair-backlog umbrella) in the derived plan section |
| R2 (natural-voice rewrite) | 58 | 55 | 3 | All confirmed real OPEN trackers used only in the derived plan |
| R3 (narrative rewrite, telemetry backfilled) | 128 with range expansion | 104 | 24 | Prior outliers re-verified; a 20-item backlog range spot-checked (real tracker items; two sampled members still OPEN) |
| R4 (final, window coverage extended) | 67 | 65 | 2 | Both previously verified OPEN trackers |

No fabricated references were found in any revision. The notable
near-misses the audit caught or clarified:

- A merged PR cited in a plan item with phrasing that implied it was
  interrupted work; its actual tracker title showed the claim was a stretch
  ("read the key only from the saved credential file" merged). Flagged as
  acceptable in an explicitly derived plan, but worth tightening.
- A "closed the backlog #A–#B" claim where two sampled range members were
  still OPEN. The range was real; the disposition claim was imprecise.
- A 3-digit tracking-ticket reference that a 4+-digit pattern would have
  missed. Identifier patterns must cover every reference shape in the prose.

## Method details

- Extraction: `#(\d{3,4})` plus range expansion `#A–#B` (en dash and hyphen),
  expanding only when `B - A <= 50`.
- Dataset membership: exact key sets from the collected JSON
  (`merged_prs[].number`, `closed_issues[].number`, `commits[].sha`; tag
  names matched as strings).
- Outlier verification: one tracker-CLI call per outlier
  (`issue view <n> --json number,state,title`, falling back to the PR
  equivalent). State was checked against the prose claim (e.g., "umbrella
  campaign" cited as work-in-progress must be OPEN).
- Presence checks were also run on figure assets: every `figNN` reference in
  the prose resolved to a rendered SVG/PNG pair.

## Privacy and provenance

All inputs to the audit were aggregate JSON and prose; no personal data was
involved. Tracker states were read-only lookups. Internal host, model, and
repository identifiers are intentionally omitted here; the counts above are
the safe evidence. Provenance for this entry: a single multi-revision
report-generation session on 2026-10-18/19 in a private repository.
