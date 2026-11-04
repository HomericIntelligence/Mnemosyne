# Supporting Notes: research-report-narrative-standard

## Provenance

Authored 2026-11-04 from an operator review of a 140-segment frozen-model
research program. The operator read the program's final report and synthesis
documents and found them unreadable because prose inline in each segment
carried content digests, detailed dates, runtime values, and completion
counts. The operator specified the rules that this entry generalizes:

- no detailed dates or hash listings outside reproducible-environment
  documentation;
- no inline runtime values or completion counts in report prose;
- a report tells a story;
- no legacy information;
- no narration of what the report omits;
- no repetition across runs;
- one report for the research line; sequential segments give a linear
  history; campaign boundaries are not scientifically special.

All project-specific names, paths, and identifiers were removed. No public
equivalent of the source documents exists to cite.

## Corpus context at authorship

Duplicate discovery ran against the retrievable corpus at the resolved
default-branch commit. Four entries were confirmed adjacent without sharing
this entry's intent:

- academic-paper-writing-and-publication-workflow (LaTeX assembly and
  publication machinery)
- evaluation-paper-rewrite-after-data-fix (bulk rewrite after data
  correction)
- academic-paper-accuracy-and-citation-audit (number and citation audit
  passes; supplies the mechanical residual-narrative audit model)
- evaluation-analysis-pipeline-reporting (generated evidence artifacts)

No open pull request in the delivery repository touched `skills/` paths at
authorship time.

## Application checklist

Use this order when revising an existing hash-dense report:

1. Extract every digest, timestamp, runtime, count, path, and job identifier
   from prose into the reproducible-environment appendix (or delete it when
   an artifact already records it).
2. Insert one prose reference to the appendix.
3. Replace superseded numbers and claims in full; search for each old value
   afterward and confirm zero matches.
4. Delete absence narration; re-keep any constraining negative result as a
   stated finding.
5. Remove restated facts that a later segment repeats from an earlier one;
   keep one statement per fact in the linear order.
6. Run the sweep token classes; zero matches outside the appendix.
7. Update any verification script that asserted the removed inline metadata
   so the check targets the appendix instead.
