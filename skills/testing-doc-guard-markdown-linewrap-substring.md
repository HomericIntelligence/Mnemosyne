---
name: testing-doc-guard-markdown-linewrap-substring
description: "A doc-content presence guard that asserts a required multi-word phrase via a raw `in` substring check yields FALSE FAILURES the moment a formatter (markdownlint / mdformat / prettier / manual 80-col wrapping) line-wraps that phrase across a newline — a plain substring does not span `\\n`. Normalize `\\s+`→single-space BEFORE the `in` check. Use when: (1) a regression test asserts `'some documented phrase' in section` against prose and fails even though the phrase is visibly present in the source markdown (it is wrapped, e.g. `**auto tag\\nrelease**`), (2) you are writing a doc-content membership/presence guard that pins required wording in a doc so a future edit can't silently re-vague it, (3) a freshly-authored `test_*` function trips ruff D103 (missing-docstring-in-public-function) in a repo with pydocstyle enabled, (4) a single-file `pixi run pytest <file>` run fails the repo's `--cov-fail-under` coverage gate."
category: testing
date: 2026-07-01
version: "1.0.0"
user-invocable: false
verification: verified-local
tags:
  - doc-content-guard
  - presence-guard
  - substring-match
  - markdown-linewrap
  - whitespace-normalization
  - regression-guard
  - ruff-d103
  - test-docstring
  - coverage-gate
  - single-file-pytest
  - pixi
  - hephaestus
---

# Testing: Doc-Content Presence Guard vs Markdown Line-Wrap (Normalize Before Substring)

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-07-01 |
| **Objective** | Ship a regression guard that pins required wording in a prose doc (ProjectHephaestus `docs/ROADMAP.md` "## Updating This Roadmap" section — rewritten from vague "typically monthly" to an explicit release-driven trigger/driver/owner) so a future edit cannot silently re-vague it, asserting the phrases are PRESENT (a hard membership check), NOT asserting an inferred cadence value. |
| **Outcome** | Success — `tests/unit/docs/test_roadmap_cadence.py` passes locally (`pixi run pytest tests/unit/docs --no-cov` → 11 passed) and `pre-commit run --files docs/ROADMAP.md tests/unit/docs/test_roadmap_cadence.py` passed (Ruff, Mypy, Markdown Lint). The plan's raw-substring assertion FAILED first because the required phrase was line-wrapped in the source markdown; the fix normalized whitespace before the `in` check. **CI validation pending** — not confirmed on the PR at capture time. |
| **Verification** | verified-local (CI on the ProjectHephaestus issue #1493 PR pending at capture time) |

## When to Use

Apply this pattern when you are writing (or debugging) a **doc-content presence guard** — a test that asserts a required multi-word phrase is present in a prose document so a future edit cannot silently drop or re-vague it:

- Your regression test does `assert "some documented phrase" in section` (or `.lower()`) against markdown prose, and it **FAILS even though the phrase is visibly present** in the source. The cause is almost always that a formatter wrapped the phrase across a newline — `**auto tag\nrelease**` — and a plain substring check does not span the `\n`.
- You are turning a **vague documented convention into an explicit, pinned one** (e.g. "typically monthly" → "each release cuts a roadmap update; driver = release manager") and want a guard that fails if the explicit wording is later removed — a doc-content analogue of an executable convention guard, but the assertion is a **membership/presence check on required phrases**, NOT a check of an inferred value.
- You are copying a plan's verbatim test source into a repo that enforces **pydocstyle / ruff D-rules**, and the plan omitted a docstring on the new `test_*` function.
- You are iterating on a **single new test file** with `pixi run pytest <file>` and hit the repo's `--cov-fail-under` coverage gate because one file exercises almost no lines of the whole package.

**Key trigger:** you wrote `'multi word phrase' in prose_doc` and it returned `False` while the phrase is clearly in the file — the phrase straddles a line-wrap boundary. Collapse `\s+`→single space before the `in` check.

## Verified Workflow

> Verification level: **verified-local**. `pixi run pytest tests/unit/docs --no-cov` → 11 passed, and `pre-commit run --files docs/ROADMAP.md tests/unit/docs/test_roadmap_cadence.py` passed (Ruff, Mypy, Markdown Lint). CI on the ProjectHephaestus issue #1493 PR was NOT confirmed at capture time — do NOT read this as verified-ci.

### Quick Reference

```python
import re
from pathlib import Path

_ROADMAP = Path(__file__).resolve().parents[3] / "docs" / "ROADMAP.md"


def _updating_section() -> str:
    """Return the '## Updating This Roadmap' section body (raw markdown)."""
    text = _ROADMAP.read_text(encoding="utf-8")
    start = text.index("## Updating This Roadmap")
    rest = text[start + len("## Updating This Roadmap") :]
    end = rest.find("\n## ")  # next top-level section, or EOF
    return rest if end == -1 else rest[:end]


def test_cadence_is_release_driven_not_vague_monthly() -> None:
    """Fail if the roadmap cadence prose is not explicitly release-driven."""
    # CRITICAL: collapse whitespace BEFORE the `in` check. Markdownlint / mdformat
    # / prettier / manual 80-col wrapping can wrap a bold phrase across a newline
    # (`**auto tag\nrelease**`); a raw substring check does NOT span `\n`.
    section = re.sub(r"\s+", " ", _updating_section().lower())
    for phrase in ("release", "auto tag release", "driver"):
        assert phrase in section, f"missing required phrase: {phrase!r}"
```

```bash
# Iterate on ONE new test file without tripping the repo's --cov-fail-under gate:
pixi run pytest tests/unit/docs/test_roadmap_cadence.py --no-cov
# ...or run the whole dir so total coverage clears the gate:
pixi run pytest tests/unit/docs
# NOTE: `-p no:cov` does NOT work here — pyproject `addopts` inject --cov args
# that then become "unrecognized"; the working flag is `--no-cov`.
```

### Detailed Steps

1. **Normalize whitespace BEFORE any substring assertion against prose.** A doc-content guard that asserts a multi-word phrase against markdown a formatter may reflow must collapse `\s+`→single space first: `section = re.sub(r"\s+", " ", _updating_section().lower())`. The failing run made the defect concrete: the phrase appeared as `**auto tag\nrelease**` in the lowercased section string, so `"auto tag release" in section` was `False` even though the words are all present in order. This is the doc-guard analogue of "anchor on normalized text, not raw source" — a plain `in` check does not span `\n`, so any phrase that straddles a wrap boundary yields a false failure. Any formatter (markdownlint, mdformat, prettier, or a human hard-wrapping at 80 cols) can introduce that boundary on the next edit, so normalize unconditionally, not just when you observe a current wrap.

2. **Assert the HARD invariant (phrase presence), not an inferred/soft value.** The guard pins that the wording is explicit and release-driven (`release`, `auto tag release`, `driver`/owner present) — it does NOT assert a specific cadence NUMBER or a monthly interval. Presence of the required wording is derivable from the doc; an inferred cadence is not. Assert only what the source of truth actually carries. (This mirrors the "guard a mixed table by membership only" principle from the executable-convention-guard family: assert the verifiable column, never the inferred one.)

3. **Give every new `test_*` function a one-line docstring (ruff D103).** In a repo with pydocstyle / ruff D-rules enabled, `ruff check` flags `def test_...() -> None:` with `D103 Missing docstring in public function` — tests are NOT exempt. Add a single-line docstring matching sibling doc tests' style (e.g. `tests/unit/docs/test_version_currency.py` uses `"""Fail if ..."""`). Before copying a plan's verbatim test source, check a sibling test in the SAME dir for the docstring convention — a plan that ships test source without one will red the lint gate. (See the ProjectHephaestus-specific skill `projecthephaestus-d103-test-docstrings` for the full policy.)

4. **Use `--no-cov` (not `-p no:cov`) to iterate on one test file under a coverage gate.** A single-file `pixi run pytest <file>` run reports the whole-package total coverage (here 2.05% for one file), which trips `--cov-fail-under=83` even when the test itself passes. `-p no:cov` FAILS here because pyproject `addopts` already inject `--cov` args, which then become "unrecognized" once the plugin is disabled. The working flags are `--no-cov` (disable coverage entirely for the iterate loop) or just run the whole directory (`pixi run pytest tests/unit/docs`) so total coverage clears the gate.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Raw substring against wrapped prose | `assert "auto tag release" in section.lower()` in the doc-content guard | The source markdown wraps the bold phrase across a newline — the lowercased section string contained `**auto tag\nrelease**`, and a plain `in` substring check does NOT span the `\n`, so the assertion was `False` even though every word is present in order | Normalize whitespace BEFORE the `in` check: `section = re.sub(r"\s+", " ", _updating_section().lower())`. Any presence guard asserting a multi-word phrase against prose a formatter may line-wrap must collapse `\s+`→single space first, or it yields false failures whenever the phrase straddles a wrap boundary |
| Ship the plan's test verbatim, no docstring | Copied `def test_cadence_is_release_driven_not_vague_monthly() -> None:` from the approved plan, which had no docstring | `pixi run ruff check` failed with `D103 Missing docstring in public function` — ProjectHephaestus's ruff config does NOT exempt `tests/`; every `test_*` is a public function to ruff | In a repo with pydocstyle/D-rules enabled, every new public test function needs a one-line docstring; check a sibling test in the same dir (e.g. `test_version_currency.py`'s `"""Fail if ..."""`) for the convention before copying a plan's verbatim source |
| `pixi run pytest <one-file> -v` to iterate | Ran the single new test file directly to iterate quickly | The one file exercised ~2.05% of the package, so the repo's `--cov-fail-under=83` gate failed the run even though the test passed; and `-p no:cov` did NOT fix it — pyproject `addopts` inject `--cov` args that become "unrecognized" once the plugin is disabled | Iterate on a single test file with `--no-cov` (disables coverage for the run) OR run the whole `tests/unit/docs` dir so total coverage clears the gate; do NOT reach for `-p no:cov` when `addopts` already inject `--cov` |

## Results & Parameters

**Reusable doc-content presence-guard core (copy-paste ready):**

```python
import re
from pathlib import Path


def _section(doc: Path, heading: str) -> str:
    """Return the body of a `## <heading>` section (raw markdown, no next section)."""
    text = doc.read_text(encoding="utf-8")
    start = text.index(heading)
    rest = text[start + len(heading) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def assert_phrases_present(section: str, phrases: tuple[str, ...]) -> None:
    """Assert each phrase is present, tolerant of markdown line-wrapping."""
    normalized = re.sub(r"\s+", " ", section.lower())  # collapse \s+ → single space
    for phrase in phrases:
        assert phrase.lower() in normalized, f"missing required phrase: {phrase!r}"
```

**The one load-bearing line:**

```python
section = re.sub(r"\s+", " ", raw_section.lower())  # BEFORE any `in` check
```

**Coverage-gate iterate command:**

```bash
pixi run pytest tests/unit/docs/test_roadmap_cadence.py --no-cov   # NOT `-p no:cov`
```

**Generalization (the durable, reusable rule):** A doc-content presence guard that asserts a multi-word phrase against prose is broken by ANY formatter that may line-wrap the phrase (markdownlint, mdformat, prettier, manual 80-col wrapping) — a raw `in` substring check does not span `\n`. **Always collapse `\s+`→single space before the substring check.** Assert only the HARD invariant (phrase presence, derivable from the doc), never an inferred value (a cadence number). Two repo-mechanics gotchas ride along in any pydocstyle/coverage-gated repo: (1) every new `test_*` function needs a one-line docstring or ruff D103 reds the lint gate (see `projecthephaestus-d103-test-docstrings`); (2) a single-file pytest run trips `--cov-fail-under` — use `--no-cov` to iterate (NOT `-p no:cov`, which breaks when `addopts` inject `--cov`).

## Verified On

| Repository | Issue / PR | What was applied |
| ------------ | ------------ | ------------------ |
| ProjectHephaestus | issue #1493 (branch `1493-auto-impl`; **verified-local**, CI pending) | Doc-content presence guard `tests/unit/docs/test_roadmap_cadence.py` pinning the rewritten `docs/ROADMAP.md` "## Updating This Roadmap" section (vague "typically monthly" → explicit release-driven trigger/driver/owner). Plan's raw `assert "auto tag release" in section.lower()` FAILED because the phrase wrapped as `**auto tag\nrelease**`; fix normalized whitespace (`re.sub(r"\s+", " ", ...)`) before the `in` check. Added a one-line docstring to satisfy ruff D103; used `--no-cov` to iterate the single file past the `--cov-fail-under=83` gate. `pixi run pytest tests/unit/docs --no-cov` → 11 passed; pre-commit (Ruff/Mypy/Markdown Lint) green locally |

## Tags

`#doc-content-guard` `#presence-guard` `#substring-match` `#markdown-linewrap` `#whitespace-normalization` `#regression-guard` `#ruff-d103` `#test-docstring` `#coverage-gate` `#single-file-pytest` `#pixi` `#hephaestus`
