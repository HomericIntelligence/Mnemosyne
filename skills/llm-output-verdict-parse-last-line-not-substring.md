---
name: llm-output-verdict-parse-last-line-not-substring
description: "Parse discrete LLM-emitted verdicts (APPROVED/REVISE/BLOCK, GO/NOGO, SAFE/UNSAFE) using last-line regex extraction, not substring `in` checks. Use when: (1) adding a Python/shell consumer that reads a classification marker from LLM output, (2) the prompt instructs the LLM that 'readers take the LAST matching line', (3) the LLM may discuss multiple options before settling on a verdict, (4) a substring-in check would fire on quoted/discussed markers, (5) auditing an existing parser for false-positive verdict reads."
category: architecture
date: 2026-05-25
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - llm-output-parsing
  - verdict-gate
  - regex
  - last-line-wins
  - claude-output
  - prompt-parser-contract
  - false-positive
  - substring-vs-regex
---

# LLM Output Verdict Parse: Last-Line Regex, Not Substring

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-05-25 |
| **Objective** | Prevent false-positive verdict reads when a Python/shell consumer parses a discrete classification marker (`**Verdict: APPROVED**` etc.) from LLM output, by matching the prompt's stated semantics ("readers take the LAST matching line") with a line-anchored, last-match-wins regex rather than a substring `in` check. |
| **Outcome** | SUCCESS — defect localized in `hephaestus/automation/plan_reviewer.py:342` where `_FINAL_VERDICT_MARKER in latest_review_body` accepted body content containing both an early APPROVED line and a later overriding BLOCK, and accepted quoted/argued-against markers. Corrected to a `re.MULTILINE` regex with `matches[-1]` semantics. |
| **Verification** | verified-local — bug confirmed in source by a `pc-research-reviewer` agent, fix shape validated against the prompt's contract in `hephaestus/automation/prompts.py:474-475`; fix is being implemented by a parallel sub-agent and is not yet in CI as of skill creation. |

## When to Use

- You are adding a Python or shell consumer that reads a classification marker (verdict, severity, action, command) from LLM output.
- The prompt that generated the output explicitly says "readers take only the LAST matching line" (or equivalent: "use the last verdict", "the final marker wins").
- The LLM is permitted (explicitly or implicitly by the task) to discuss multiple options before settling on a single verdict — so multiple matching markers may legitimately appear in the response.
- A substring `in` check would fire on a quoted/discussed marker (e.g., "we should NOT mark this **Verdict: APPROVED**…") and produce a false positive.
- You are auditing an existing parser (skip-gate, finalize-gate, ship-gate) for false-positive verdict reads.

## Verified Workflow

### Quick Reference

```python
import re

# Anchored to start/end of line; MULTILINE so ^/$ match line boundaries.
_VERDICT_PATTERN = re.compile(
    r'^\*\*Verdict: (APPROVED|REVISE|BLOCK)\*\*\s*$',
    re.MULTILINE,
)

def is_approved(body: str) -> bool:
    """Return True iff the LAST verdict line in `body` is APPROVED."""
    matches = _VERDICT_PATTERN.findall(body)
    return bool(matches) and matches[-1] == "APPROVED"
```

Three guarantees this provides that `MARKER in body` does not:

1. **Line-anchored**: the marker must occupy its own line (modulo trailing whitespace) — quoted/inline mentions cannot trigger.
2. **Last-match wins**: if the LLM emits an early APPROVED then a later overriding BLOCK, BLOCK wins, matching the prompt's contract.
3. **Strict token equality**: comparing `matches[-1] == "APPROVED"` rejects look-alikes like `APPROVED_WITH_CHANGES`.

### Detailed Steps

1. **Read the prompt template used to generate the LLM output.** Find the explicit "format" instruction. Examples:
   - `hephaestus/automation/prompts.py:474-475`:
     > *"End your response with exactly one of the following verdict lines (including the bold markers) — readers take only the LAST matching line in your response: `**Verdict: APPROVED**`, `**Verdict: REVISE**`, `**Verdict: BLOCK**`."*
   - Or any prompt with "respond with one of: GO, NOGO" / "the last line of your response must be SAFE or UNSAFE".

2. **Match the prompt's stated semantics in the parser.**

   | Prompt instruction | Correct parser |
   |---|---|
   | "last matching line wins" | `re.findall(pattern, text, re.MULTILINE)[-1]` |
   | "exactly one verdict at the end" | `text.strip().splitlines()[-1]` plus format assertion |
   | "JSON block at end" | `re.findall(r'```json\n(.*?)\n```', text, re.DOTALL)[-1]` then `json.loads` |
   | "verdict on its own line, anywhere" + "if multiple, treat as error" | `findall` then assert `len(matches) == 1` |

3. **Add tests covering at minimum:**

   - Single matching line at end of body → matches expected verdict.
   - Multiple matching lines (early APPROVED, late BLOCK) → asserts last wins (BLOCK).
   - Quoted/argued-against marker in discussion → asserts NOT triggered.
   - Marker with surrounding whitespace (trailing spaces, CRLF) → still matches.
   - Marker with surrounding text on the same line (e.g., "Final: **Verdict: APPROVED** ✓") → matches your stated requirement (line-anchored = reject; relaxed = accept). Pick one and lock it in a test.
   - Empty body / body with no verdict → returns False (or sentinel), does not raise.

4. **Co-locate the prompt and the parser in a single review.** The defect that motivated this skill shipped because the prompt lived in `prompts.py` and the parser lived in `plan_reviewer.py`, and they were touched in separate PRs by separate contributors. When opening any PR that touches a verdict prompt OR its consumer, include both files in the diff — even if the change appears one-sided — so the reviewer can verify the contract.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---|---|---|---|
| 1 | `if "APPROVED" in text:` (substring `in` check, originating defect in `plan_reviewer.py:342`) | Matches the substring anywhere — quoted markers, "NOT APPROVED" prose, an early APPROVED followed by an overriding BLOCK all return True. Violates the prompt's "last matching line wins" contract. | Substring `in` against an LLM body cannot enforce line position or last-match semantics — never use it for discrete classification markers. |
| 2 | `if text.endswith("APPROVED"):` | Brittle. Claude may emit trailing whitespace, a postscript, markdown emphasis (`**APPROVED**`), or a sign-off line after the verdict. Returns False when the verdict is actually APPROVED. | `endswith` assumes literal trailing position, which Claude's free-form formatting breaks routinely. Always anchor on regex line boundaries, not on absolute body position. |
| 3 | `text.split("\n")[-1] == "APPROVED"` | Assumes the verdict is the literal last line of the entire body. Breaks the moment Claude adds a "Let me know if you have questions." postscript, even though a properly formatted verdict line is still present. | "Last line of body" ≠ "last matching line of body". Filter for matching lines first, then take the last; don't take the last line and check whether it matches. |
| 4 | `re.search(r"APPROVED", text)` | Identical false-positive surface to substring `in` — no line anchoring, no last-match semantics. The `re` import gives a false sense of rigor without any of regex's actual power. | A regex without anchors (`^`/`$`), without `re.MULTILINE`, and using `search` instead of `findall(...)[-1]` provides zero additional safety over `in`. The flags matter as much as the pattern. |

## Results & Parameters

**Recommended regex (Python):**

```python
re.compile(r'^\*\*Verdict: (APPROVED|REVISE|BLOCK)\*\*\s*$', re.MULTILINE)
```

**Recommended consumer logic:**

```python
matches = _VERDICT_PATTERN.findall(body)
verdict = matches[-1] if matches else None
is_approved = verdict == "APPROVED"
```

**Cross-language equivalents:**

| Language | Pattern | Notes |
|---|---|---|
| Python | `re.compile(r'^\*\*Verdict: (APPROVED\|REVISE\|BLOCK)\*\*\s*$', re.MULTILINE)` | Use `findall(...)[-1]`. |
| JavaScript / TypeScript | `/^\*\*Verdict: (APPROVED\|REVISE\|BLOCK)\*\*\s*$/gm` | Use `[...body.matchAll(re)].at(-1)?.[1]`. |
| Go | `regexp.MustCompile(`(?m)^\*\*Verdict: (APPROVED\|REVISE\|BLOCK)\*\*\s*$`)` | `FindAllStringSubmatch(body, -1)`; take last element. |
| Rust | `Regex::new(r"(?m)^\*\*Verdict: (APPROVED\|REVISE\|BLOCK)\*\*\s*$")?` | `captures_iter(body).last()`. |
| Bash | `grep -E '^\*\*Verdict: (APPROVED\|REVISE\|BLOCK)\*\*\s*$' \| tail -1` | Pipe through `tail -1` to enforce last-match-wins. |

**Required test cases (minimum):**

1. `body = "**Verdict: APPROVED**\n"` → APPROVED.
2. `body = "**Verdict: APPROVED**\n\nOn reflection…\n\n**Verdict: BLOCK**\n"` → BLOCK (last-match-wins).
3. `body = "we should NOT mark this **Verdict: APPROVED** because the plan is incomplete — **Verdict: REVISE**\n"` → REVISE (the inline marker on the discussion line is not line-anchored; the trailing line-anchored REVISE wins).
4. `body = "**Verdict: APPROVED**   \r\n"` → APPROVED (trailing whitespace / CRLF tolerated).
5. `body = "No verdict here."` → None (returns False from `is_approved`).
6. `body = ""` → None / False.

**Cross-reference these related skills:**

- [[audit-driven-remediation-workflow]] — being amended in parallel to add a "downstream consumer drift" section that surfaced this bug.
- [[debugging-silent-pipeline-stage-via-argparse-required-grep]] — covers a related "consumer silently fails" pattern from the same automation pipeline (`run_automation_loop.sh` orchestrator).

## Verified On

| Project | File / Issue | Notes |
|---|---|---|
| ProjectHephaestus | `hephaestus/automation/prompts.py:474-475` | Prompt source — explicit "readers take only the LAST matching line" instruction. |
| ProjectHephaestus | `hephaestus/automation/plan_reviewer.py:342` | Defective consumer — `_FINAL_VERDICT_MARKER in latest_review_body`. Fix in flight. |
| ProjectHephaestus | Issue #552 (epic #550) | Originating issue under the 1.0 audit remediation epic. |
