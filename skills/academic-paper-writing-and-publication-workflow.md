---
name: academic-paper-writing-and-publication-workflow
description: "Use when: (1) assembling a large LaTeX research paper from parallel-agent-written parts and need to merge sections into a compilable .tex with unified bibliography; (2) performing pre-submission quality validation of a LaTeX paper covering data accuracy, statistical methodology, statistical power analysis, and arXiv build preparation; (3) polishing an arXiv paper for submission — voice normalization, pronoun changes, duplicate heading removal, BibTeX deduplication, inline arXiv href removal; (4) conducting a final publication-readiness review checklist pass before camera-ready; (5) preparing a LaTeX arXiv paper for final review with a myrmidon swarm of specialist reviewers; (6) wiring a pipeline-computed power analysis to interpret null results as small effects vs underpower; (7) consolidating scattered verdict codes into a Future Work longtable section and fixing \\verb/\\texttt underscore and cite-key-collision issues during parallel assembly."
category: documentation
date: 2026-06-07
version: "1.1.0"
user-invocable: false
history: academic-paper-writing-and-publication-workflow.history
tags: [latex, arxiv, paper, publication, validation, bibtex, assembly, review, statistical-rigor, swarm]
---

# Academic Paper Writing and Publication Workflow

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-06-07 |
| **Objective** | End-to-end LaTeX research-paper workflow: parallel assembly, data/statistical validation, arXiv polish, final publication-readiness review |
| **Outcome** | Operational — verified across multiple papers (Taming Scylla, Haiku analysis, 38-idea architecture paper); clean compiles, 0 unresolved refs |
| **Verification** | verified-ci |

## When to Use

- Assembling a large LaTeX paper from parts written by N parallel agents (a single agent cannot hold >40 pages / >50 sections in context).
- Validating quantitative claims, statistical methodology, and named-test correctness against source data before submission.
- Fixing post-assembly compilation errors: Unicode, missing/duplicate bib keys, `\citeauthor` without natbib, tabular column drift, unescaped underscores.
- Polishing an arXiv paper: voice/pronoun normalization, duplicate-heading removal, inline arXiv href removal, bibliography reduction to cited-only.
- Running a final 10-category GO / CONDITIONAL GO / NO-GO publication-readiness review after multiple prior passes.
- Coordinating a parallel myrmidon swarm of specialist reviewers for large papers (>1,000 lines LaTeX).

**Trigger phrases**: "assemble the paper", "validate the paper", "polish for arXiv", "final review", "publication readiness", "GO/NO-GO".

**Out of scope**: paper accuracy/citation auditing (separate skill), blog writing, sci-fi mechanism design.

## Verified Workflow

### Quick Reference

```bash
# --- Canonical LaTeX build cycle (run after ANY bibliography change) ---
cd docs/arxiv/<paper>
pdflatex -interaction=nonstopmode paper.tex   # pass 1: emit .aux + cite keys
bibtex paper                                   # build .bbl
pdflatex -interaction=nonstopmode paper.tex   # pass 2: pull in refs
pdflatex -interaction=nonstopmode paper.tex   # pass 3: resolve cross-refs/pages
# Preferred where available: pixi run --environment docs paper-build (tectonic)

# --- Universal verification (every phase ends here) ---
grep -c "^!"  paper.log                        # LaTeX errors → expect 0
grep "??" paper.log | grep -v pdfTeX           # unresolved refs → expect empty
pdfinfo paper.pdf | grep Pages                 # page count sanity
grep -c "@" references.bib                      # bib entry count

# --- Unicode → math mode (MUST run before first pdflatex) ---
grep -P "[\x80-\xFF]" paper.tex                 # find non-ASCII first
```

**Core principles that span all phases**:

1. **Data accuracy is non-negotiable and comes first** — recompute every number from source CSV/JSON before accepting it.
2. **Fix the pipeline, not the paper** — when claims come from a Python pipeline, fix the generator, regenerate data, then update text. Never hand-patch generated numbers or tables.
3. **Edit by category with unique `old_string`, never by line number** — line numbers shift after each edit; default `replace_all=false` with surrounding context.
4. **Grep ALL sections after any fix** — Abstract / Intro / Contributions / Discussion / Conclusions / Appendix / Future Work routinely retain the old phrasing.
5. **Verify the verifier** — reviewer checklists and automated agent findings may be wrong; recompute against the actual source file before acting.

### Detailed Steps

#### Example A — Parallel LaTeX assembly from agent-written parts

Use when a single agent cannot write the whole paper. Partition into independent slices, farm to N agents, then merge.

1. **Partition**: Part 1 = full preamble (`\documentclass` … `\maketitle`) + intro + first idea slice. Parts 2..N = body content only (start at first `\subsection`); NO `\documentclass`, NO `\begin/\end{document}`.
2. **Farm**: launch N agents in one message; give each the preamble template (column widths, package list, macros) plus its idea slice; each writes `partN.tex` to a known path.
3. **Assemble** with `head` + `awk`:

   ```bash
   head -717 part1.tex > paper.tex                                   # preamble + sections 1-2
   printf '\n\\section{Detailed Analyses}\n\\label{sec:analyses}\n' >> paper.tex
   awk '/^\\subsection/{found=1} found{print}' part2.tex >> paper.tex  # skip part preambles
   awk '/^\\subsection/{found=1} found{print}' part3.tex >> paper.tex
   cat part4.tex >> paper.tex                                         # body-only part
   wc -l paper.tex
   ```

4. **Unicode → math mode** (before any compile):

   ```python
   import pathlib
   tex = pathlib.Path("paper.tex").read_text(encoding="utf-8")
   for ch, latex in {
       "é": r"\'{e}", "è": r"\`{e}", "à": r"\`{a}", "ç": r"\c{c}",
       "ü": r'\"u', "ö": r'\"o', "×": r"$\times$", "—": "---",
       "–": "--", "ρ": r"$\rho$", "σ": r"$\sigma$", "α": r"$\alpha$",
       "μ": r"$\mu$", "Δ": r"$\Delta$", "≤": r"$\leq$", "≥": r"$\geq$",
       "≈": r"$\approx$", "±": r"$\pm$",
   }.items():
       tex = tex.replace(ch, latex)
   pathlib.Path("paper.tex").write_text(tex, encoding="utf-8")
   ```

5. **First compile to discover problems** (`pdflatex + bibtex + pdflatex×2`). Do not fix manually mid-pass.
6. **Stub missing bib keys** — extract from the log and append `@misc{}` stubs so the paper compiles; fill real entries later:

   ```python
   import re, pathlib
   log = pathlib.Path("paper.log").read_text()
   bib = pathlib.Path("references.bib").read_text()
   existing = set(re.findall(r'@\w+\{([^,]+),', bib))
   missing = set(re.findall(r"Citation '([^']+)' on page", log)) - existing
   with open("references.bib", "a") as f:
       for k in sorted(missing):
           f.write(f"\n@misc{{{k},\n  title={{STUB: {k}}},\n  author={{Unknown}},\n  year={{2024}},\n  note={{Auto-generated stub.}}\n}}\n")
   ```

7. **Fix `\citeauthor{}` without natbib**: `re.sub(r'\\citeauthor\{([^}]+)\}(?:~\\cite\{\1\})?', r'\\cite{\1}', tex)`.
8. **Fix tabular column drift** — grep the log for `Misplaced \noalign` / `Extra alignment tab`; align column specs to cell counts. Give agents a shared table macro to prevent divergence.
9. **Deduplicate bib entries** from parallel agents (uppercase vs lowercase cite keys cause "Case mismatch" / "Repeated entry"). After editing `.bib`, ALWAYS `rm -f paper.aux paper.bbl paper.blg` before the clean rebuild.
10. **arXiv build directive**: add `\pdfoutput=1` to the preamble. Final compile is 4 runs (`pdflatex + bibtex + pdflatex + pdflatex`).
11. **Cite-key collision PREVENTION** — two agents independently inventing the same cite key for different papers silently corrupts the merged `.bib` (BibTeX keeps the first, drops the second). Prevent it up front: give each agent a namespaced cite-key prefix (`part1_foo2024`, `part2_foo2024`) OR a shared reference list with agreed keys before they write. Do not try to fix collisions by hand after the merge.
12. **`\verb` inside `\textit{}` breaks** — agents writing research-doc pointers as `\textit{Full analysis: \verb|research_X_Y.md|}` trigger `\verb ended by end of line`. Use `\texttt{research\_X\_Y\_slug.md}` with explicitly escaped underscores instead (`str.replace('_', r'\_')`), since bare `_` inside `\texttt{}` causes `Missing $ inserted`:

    ```python
    import re, pathlib
    tex = pathlib.Path("paper.tex").read_text(encoding="utf-8")
    tex = tex.replace('\\\\_', '\\_')   # first un-double-escape from prior passes
    def esc(m): return r'\texttt{' + re.sub(r'(?<!\\)_', r'\\_', m.group(1)) + '}'
    tex = re.sub(r'\\texttt\{([^}]*research[^}]*)\}', esc, tex)
    pathlib.Path("paper.tex").write_text(tex, encoding="utf-8")
    ```

13. **Verdict-code consolidation** — when parallel parts scatter verdict codes (PURSUE/INVESTIGATE/DEPRIORITIZE), consolidate into one section. In **body prose** replace with neutral wording (high-priority / candidate for investigation / lower-priority); in **table cells** replace with `\textbf{P}`/`\textbf{I}`/`\textbf{D}` + a footnote pointing to the verdict section. Create a `\section{Future Work and Implementation Verdicts}` containing a `\description` list defining P/I/D, a `longtable` per tier, and an `\enumerate` implementation sequence. Requires `\usepackage{longtable}` (environment) and `\usepackage{booktabs}` (`\toprule`/`\midrule`/`\bottomrule`) in the preamble. Restrict replacement to body/table — keep the codes intact as defined terms inside the verdict section; afterward `grep -n 'PURSUE\|INVESTIGATE\|DEPRIORITIZE' paper.tex` should match only that section.

#### Example B — Data accuracy and statistical methodology validation

Run before submission whenever the paper presents experimental results, especially small-N studies.

1. **Plan first, do not fix immediately.** Read the whole paper; build a severity-ordered issue list (CRITICAL data/path errors → IMPORTANT stats/consistency → MINOR style). Consult prior `.notes.md` review rounds.
2. **Data accuracy (CRITICAL, first)** — recompute every numeric claim from `find . -name "*.csv" -o -name "*.json"`. Common errors: broad ranges where all values are identical, rounding that obscures precision, percentages that don't match. Document `Location | Current | Ground Truth | Fix`.
3. **Verify statistical test NAMES against data field names** — the JSON field is ground truth:

   ```bash
   # "u_statistic" → Mann-Whitney U (NOT Dunn's);  "H_statistic" → Kruskal-Wallis;  "dunn_statistic" → Dunn's
   python3 -c "import json;d=json.load(open('statistical_results.json'));print([k for k in d[0] if 'stat' in k.lower()])"
   python3 -c "import json;d=json.load(open('statistical_results.json'));print('comparisons:',len(d))"  # do NOT assume C(k,2)
   ```

4. **Multiple-comparison family size** — state Holm-Bonferroni `$m$` explicitly in captions; ensure all comparisons (incl. first→last contrast) go through the SAME `raw_p_values` list in the pipeline.
5. **Degenerate-test framing** — a single-model Scheirer-Ray-Hare reduces to one-way Kruskal-Wallis (agent_model df=0, interaction not estimable); the paper must say so. Prefer Clopper-Pearson exact CIs over BCa bootstrap for binary data at n ≤ 15.
5a. **Pipeline-computed power analysis (Phase 2c)** — power functions often exist but are never called from `export_data.py`, so the paper quotes hand-calculated estimates. Wire them in: import the power function, add `"power_analysis": []` to the results dict, and after the effect-sizes loop compute power at the **observed** δ AND at a **reference medium effect δ=0.3** for every adjacent-tier transition:

   ```python
   results["power_analysis"] = []   # add to results dict init
   for model in models:
       for i in range(len(tier_order) - 1):
           observed_delta = next(
               (es["cliffs_delta"] for es in results["effect_sizes"]
                if es["model"]==model and es["metric"]=="pass_rate"
                and es["tier1"]==tier_order[i] and es["tier2"]==tier_order[i+1]), None)
           if observed_delta is None:
               continue
           results["power_analysis"].append({
               "model": model, "metric": "pass_rate",
               "tier1": tier_order[i], "tier2": tier_order[i+1], "n1": n1, "n2": n2,
               "observed_delta": float(observed_delta),
               "power_at_observed": float(mann_whitney_power(n1, n2, abs(observed_delta))),
               "power_at_medium_0_3": float(mann_whitney_power(n1, n2, 0.3)),
           })
   ```

   Verify with `python3 -c "import json;d=json.load(open('statistical_results.json'));print('power entries:',len(d.get('power_analysis',[])))"`. **Interpret null results correctly**: when power at medium δ=0.3 is high (0.95–0.98) a non-significant result reflects a genuinely small effect, NOT underpower — only flag transitions where power@medium is low (e.g. δ≈0.43 at n=30/15 gives power 0.37 → underpowered) as inconclusive.
6. **Statistical language strength must match power** — hedge results, not methodology:
   - "confirms / proves / demonstrates" → "is consistent with / suggests / indicating".
   - "consistently outperform" → "outperform in aggregate" (when per-task varies).
   - "eliminates the possibility" → "provides no evidence of" (non-significant under low power).
   - Keep "validates" for methodology/pipeline validation. Causal verbs → "is associated with" in observational designs.
7. **Cross-reference infrastructure** — add `\label{}` to all sectioning commands; replace hardcoded "Section 4" with `Section~\ref{sec:...}`; remove manual numbering from titles; compile twice and confirm `grep -c "??" paper.log` is 0.
8. **LaTeX compilation fixes** — Unicode→math (`$\rho$`), match tabular column counts, escape underscores in auto-generated tables at the Python write site (`criterion.replace("_", r"\_")`) AND in the static `.tex` for the immediate build; place `\appendix` before appendix content.
8a. **Table column-semantics footnote (Phase 3)** — tables that mix per-row means with a "Total" row of absolute sums are ambiguous. When tier rows show per-run averages but the Total row shows absolute totals, add `\footnote{Token columns show per-run means for tier rows; the Total row shows absolute totals.}` to the table caption.
8b. **Superlative-vs-aggregate check (Phase 8)** — guard against "X achieves the highest Y" when a low-n, wide-CI tier shows a spuriously higher value (e.g. T6=0.933 from 1 subtest/15 runs, CI [0.667, 1.000], vs T2=0.831 from 14 subtests/130 runs). Scope the superlative: "highest among tiers with representative coverage (T0--T4: 83.1\%, compared to T6's 93.3\% from a single subtest with wide CI [0.667, 1.000])".
9. **Path / reproducibility** — extract archived data referenced by missing dirs; verify script paths with `ls`; for arXiv, transform ALL prefix variants (`docs/paper-dryrun/figures/` AND bare `paper-dryrun/figures/` → `figures/`). Verify build-script globs match actual file extensions (a `*.pdf` glob over PNG figures yields a tarball with zero figures even though LaTeX compiles).
10. **Parallel swarm review** (papers >1,000 lines) — role-stratified myrmidons:
    - Coordinator (Opus): subdivide, aggregate, **independently verify every CRITICAL finding** before escalating (agents often search the wrong JSON — e.g. `cost_usd` lives only in `srh_tier_experiment.json`).
    - Specialists (Opus/Sonnet): statistical methodology, data accuracy, writing/framing, cross-references/bibliography. Students (Haiku): line-by-line typo/number/ref verification split by line range.
    - Read each figure's `.vl.json` spec BEFORE touching its caption.

#### Example C — arXiv polish and final publication-readiness review

Run after validation, on a paper that has passed initial review, to apply a structured fix list and a GO/NO-GO checklist.

1. **Apply fixes by category** (precision, terminology, bibliography, paths, grammar/style) using unique `old_string`. Cascade terminology changes (e.g. "container" → "git worktree" also requires removing Docker from required-software lists).
2. **Bibliography reduction** — keep only cited entries (`Read` before `Edit` on `.bib`); rebuild with the full 4-step cycle. Commit `paper.bbl` for arXiv (it does not run bibtex; check `.gitignore` for `*.bbl`).
3. **Voice / pronoun normalization (URL-safe)** — single-author drift into "we/our/us". Protect emails/URLs with sentinels first, then substitute, then restore:

   ```python
   import re, pathlib
   p = pathlib.Path("paper.tex"); text = p.read_text(); protected = []
   for m in re.finditer(r'\S+@\S+|https?://\S+', text):
       s = f"__P_{len(protected)}__"; protected.append((s, m.group(0))); text = text.replace(m.group(0), s, 1)
   for pat, rep in [(r"\bWe\b","I"),(r"\bwe\b","I"),(r"\bOur\b","My"),(r"\bour\b","my"),
                    (r"\bus\b","me"),(r"\bourselves\b","myself")]:
       text = re.sub(pat, rep, text)
   for s, orig in protected: text = text.replace(s, orig)
   p.write_text(text)
   # Guard verbs BEFORE substitution: grep -nE '\b(we are|we were|we have)\b' paper.tex
   ```

4. **Remove inline arXiv hrefs** from the body (`grep -c 'arxiv.org' paper.tex` → 0); strip `\href{arxiv...}{...}` wrappers while preserving inner `\cite{}`.
5. **Detect duplicate `\subsubsection{}` headings** (orphaned refactor stubs):

   ```bash
   awk '/^\\subsubsection\{/ {print NR, $0}' paper.tex | sort -k2- | uniq -d -f1
   ```

6. **Single-model table cleanup** — drop noise `Model` / `Agent Models` columns from the Python generators AND fix already-published `.tex`/`.md` in place when the loader rejects the current data layout (fix generator for future runs regardless).
7. **10-category GO/NO-GO review** — grade each independently:

   | # | Category | Check |
   | --- | -------- | ----- |
   | 1 | Numerical accuracy | numbers match data within rounding tolerance |
   | 2 | Internal consistency | terminology + cross-refs + methodology-vs-implementation |
   | 3 | Clarity | logical flow, jargon defined before use |
   | 4 | Grammar/spelling | agreement, missing words, typos |
   | 5 | LaTeX formatting | compiles clean, figures/math/refs resolve |
   | 6 | Citations | all `\cite` resolve, `.bib` complete |
   | 7 | Reproducibility | paths match repo, commands copy-pasteable, versions pinned |
   | 8 | Figures/tables | render, captioned, referenced |
   | 9 | Scientific rigor | claims scoped to data, limitations acknowledged |
   | 10 | Completeness | no TODOs/placeholders |

8. **Verify reproducibility paths against the real repo** — authors write from memory. `ls config/models/` and `ls tests/fixtures/tests/` to confirm filenames (dashes vs dots, nesting).
9. **Fix everything in one atomic commit**, rebuild, then grep-verify all fixes resolve to 0 matches; confirm page count and PDF size are sane.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Edit by line number | Applied fixes in line-number order | Line numbers shift after every edit; later edits hit wrong text | Edit by category with unique `old_string`; default `replace_all=false` |
| Single agent for full 38-idea paper | One agent writes the whole `paper.tex` | Context exhaustion; lost earlier sections; inconsistent macros | Partition into 4–6 disjoint slices; farm to parallel agents |
| `\documentclass` in every part | Each part was standalone-compilable | Assembly produced multiple `\documentclass` → pdflatex rejects | Only part 1 carries the preamble; parts 2..N start at first `\subsection` |
| `\citeauthor{}` without natbib | Agents wrote `\citeauthor{key}~\cite{key}` | Plain BibTeX does not define `\citeauthor` | Regex-replace to `\cite{key}` before compiling |
| Skip bibtex after `.bib` change | Recompiled pdflatex only | `.bbl` never regenerated; refs/case-mismatch persist | Always run pdflatex→bibtex→pdflatex×2; `rm paper.aux .bbl .blg` after bib edits |
| Compile before fixing Unicode | Fed raw Greek/accents to pdflatex | `Unicode character not set up for use with LaTeX` | Run the full replacement dict (and `grep -P "[\x80-\xFF]"`) before first compile |
| Assume auto-generated tables are LaTeX-safe | Used CSV-derived tables with `_` | `Missing $ inserted` on `code_quality &` | Escape underscores at the Python write site AND in the static `.tex` |
| Incomplete path transformation | Fixed `docs/paper-dryrun/` only | `File 'paper-dryrun/tables/...' not found` | Transform ALL prefix variants; `grep -r "paper-dryrun" paper.tex` |
| Trust build-script figure glob | `figures/*.pdf` glob but figures were PNG | LaTeX compiled fine but tarball had zero figures | Verify packaging globs against actual file extensions |
| `replace_all=true` for stat language | Replaced every "confirms" / "container" at once | Some uses are correct (methodology validation; code listings) | Review each in context; keep "validates" for methodology |
| Fix language in one section only | Hedged "consistently" in Abstract | Same word survived in Conclusions/Appendix | After any fix, grep ALL sections |
| Hand-patch generated numbers | Edited stats directly in `paper.tex` | Numbers re-diverged when pipeline was later corrected | Fix pipeline → regenerate JSON → update paper |
| Assume C(k,2) comparisons | Claimed "21 pairwise C(7,2)" | JSON had only 7 (6 adjacent + T0–T6) | Count actual comparisons in the data file |
| Trust automated/reviewer findings | Accepted agent "5 contractions" / reviewer's δ thresholds | Zero contractions existed; paper used a valid alternative threshold standard | Independently verify with your own grep and the cited source; coordinator re-checks every CRITICAL finding |
| Agent searched wrong JSON | Looked for `cost_usd` in `statistical_results.json` | `cost_usd` lives in `srh_tier_experiment.json` | Coordinator must check ALL data files before accepting "unverifiable" |
| Write `.bib` without prior Read | First Edit on `references.bib` failed | Edit requires prior Read baseline | Always Read → Edit for bibliography files |
| `gh pr merge --auto --rebase` | Followed project docs saying rebase | `Merge method rebase merging is not allowed` | Use `--squash`; branch protection requires squash auto-merge |
| Claim Pareto-dominance from one significant dimension | Asserted "strictly Pareto-dominant" when the cost difference was non-significant (p=0.676) | Cannot claim Pareto dominance on a dimension where the null hypothesis is not rejected | When "Pareto" language appears, verify BOTH dimensions are established; a non-significant result "provides no evidence of" a difference, it does not "eliminate" one |
| Claim "monotonic relationship" without checking ordering | Paper stated a monotonic capability-gap vs judge-agreement relationship | J2–J3 MAD (0.270) > J1–J3 MAD (0.210) despite a smaller capability gap — violates monotonicity | Before asserting monotonicity, verify the actual data ordering in the source file |

## Results & Parameters

### Canonical compile + verification (copy-paste)

```bash
cd docs/arxiv/<paper>
rm -f paper.aux paper.bbl paper.blg          # only after a .bib change
pdflatex -interaction=nonstopmode paper.tex
bibtex paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
grep -c "^!" paper.log                        # 0 errors
grep "??" paper.log | grep -v pdfTeX          # empty (no unresolved refs)
pdfinfo paper.pdf | grep Pages
```

### arXiv submission contents

```text
INCLUDE: paper.tex, paper.bbl (pre-compiled — REQUIRED), 00README.json,
         figures/*.{pdf|png matched to glob}, tables/*.tex (only \input'ed ones)
EXCLUDE: *.aux *.blg *.log *.out, references.bib, data/ raw/ archives/
Preamble: \pdfoutput=1   |   Figures: PDF ≤1.5 (arXiv may reject 1.7)
```

### Verified outcomes

| Paper / context | Result |
| --------------- | ------ |
| 38-idea architecture paper (parallel assembly) | 4 agents, head+awk merge, 342 stub + 53 real bib entries, 102 pages, 0 errors |
| Taming Scylla (arXiv polish) | 5 fix categories, bib 36→10 (-307 lines), 32 pages, 0 errors/refs |
| Taming Scylla (final review) | 10-category GO/NO-GO, 5 minor fixes atomic, 29 pages, 0 errors/warnings |
| Haiku analysis (data/stat validation) | 60+ claims verified, caught Dunn's-vs-Mann-Whitney mislabel + 21-vs-7 comparison error, arXiv build produced |

### Power-analysis reference values (interpret null results)

| Transition | N1, N2 | Observed δ | Power@observed | Power@medium(0.3) |
| ------------ | -------- | ------------ | ---------------- | ------------------- |
| T0→T1 | 117, 83 | 0.094 | 0.20 | 0.95 |
| T2→T3 | 130, 122 | -0.068 | 0.16 | 0.98 |
| T4→T5 | 123, 30 | -0.313 | 0.77 | 0.73 |
| T5→T6 | 30, 15 | +0.433 | 0.68 | 0.37 (underpowered) |

Key insight: T0–T4 null results reflect genuinely small effects (power 0.95–0.98 at medium δ), not insufficient power; only δ≈0.43 at n=30/15 is underpowered.

### Pre-commit double-stage pattern

```bash
git add <files> && git commit -m "..."   # if end-of-file-fixer fires:
git add <fixed-files> && git commit -m "..."   # re-stage + commit again
```

## Verified On

| Project | Context | Details |
| --------- | --------- | --------- |
| ProjectScylla | Taming Scylla arXiv polish + final review (2026-02-07, PR #371) | 5-category polish, bib 36→10, URL-safe pronoun pass, 10-category GO/NO-GO, clean 29-32pp compiles |
| ProjectScylla | Haiku analysis paper validation (2026-04-06–08, 04-27) | 60+ claims verified, statistical-test naming + comparison-count fixes, underscore-escaping pipeline fix, tectonic build |
| ProjectScylla | Haiku post-review mechanical revisions (2026-05-05, PR #1912) | pronoun substitution, single-model column drop, duplicate `\subsubsection` + `\item` dedup |
| ArchIdeas | 38-idea architecture paper (2026-04-14) | 4 parallel agents, head+awk assembly, 342 bib stubs, arXiv href + verdict-code cleanup, 102 pages, 0 errors |

## References

- LaTeX errors: https://www.overleaf.com/learn/latex/Errors
- arXiv TeX submission: https://arxiv.org/help/submit_tex
- Romano, J. et al. (2006) — Cliff's δ thresholds (FAIR conference: 0.11/0.28/0.43; journal: 0.147/0.33/0.474 — verify which the codebase uses)
