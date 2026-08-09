---
name: prompt-fencing-refactor-plan-risks
description: "Test prompt builders through production consumers and security boundaries instead of pinning editorial text. Use when: (1) GitHub- or Git-derived metadata enters agent prompts, (2) nonce fencing must prove hostile payload containment, (3) Jinja templates contain JSON examples consumed by real parsers, (4) provider or iteration routing must remain stable while prompt wording evolves."
category: testing
date: 2026-08-07
version: "2.1.0"
user-invocable: false
verification: unverified
history: prompt-fencing-refactor-plan-risks.history
tags:
  - prompt-builders
  - prompt-schemas
  - production-parsers
  - untrusted-content
  - nonce-fencing
  - routing-tests
  - jinja
  - behavior-contracts
  - projecthephaestus
---

# Prompt Tests Should Exercise Parsers, Fences, and Routing

## Overview

| Field | Value |
| ------- | ------- |
| **Date** | 2026-08-07 |
| **Objective** | Replace tests that freeze prompt prose with contracts over machine-consumed schemas, adversarial payload containment, provider selection, iteration routing, and host-produced job wiring. |
| **Outcome** | Proposed workflow now also covers commit-message and PR-message prompts: allocate one fencer per rendered prompt, fence every GitHub/Git string including empty fallbacks, keep only host-owned policy and numeric identifiers outside fences, and preserve JSON-only response contracts. The implementation plan was not executed. |
| **Verification** | `unverified` — the supplied ProjectHephaestus plan was consolidated here, but no templates or tests were changed and no focused suite or CI run was observed. |
| **History** | [changelog](./prompt-fencing-refactor-plan-risks.history) |

Prompt text is an implementation detail unless a downstream consumer parses it. Tests that
pin headings, phrases, rubric markers, example counts, or builder docstrings make harmless
editing expensive while missing malformed JSON and injection-boundary defects. Treat the
consumer, fence, route, and host-owned job as the contract.

## When to Use

- A prompt test asserts that exact instructions, headings, rubric phrases, or forbidden
  editorial strings occur in rendered output.
- A template shows JSON that looks plausible to a model but is invalid JSON or rejected by
  the production parser.
- A security test checks only that `BEGIN_` and `END_` marker substrings exist, without
  pairing their nonce and label or proving hostile text stays inside the block.
- Commit-message or PR-message agents receive issue titles, issue bodies, changed-file
  output, diff statistics, commit history, or static fallbacks derived from those fields.
- Prompt builders select providers or iteration-dependent fragments and those outcomes can
  be asserted without freezing the selected fragment's wording.
- A stage constructs an agent job whose prompt builder, parser, structured kwargs, and tool
  permissions are host-owned policy.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a hypothesis until CI confirms.

### Quick Reference

Use the production parser as the oracle for every machine-readable example:

```python
def test_prompt_example_is_accepted_by_consumer() -> None:
    rendered = build_prompt(...)
    parsed = production_parser(rendered)
    assert parsed.valid
```

Pair nonce and label in fence extraction, compare exact block bodies, then remove all fenced
regions and prove hostile payloads are absent from the trusted remainder:

```python
_FENCE_RE = re.compile(
    r"BEGIN_(?P<nonce>[0-9A-F]+)_(?P<label>[A-Z0-9_]+)\n"
    r"(?P<body>.*?)\n"
    r"END_(?P=nonce)_(?P=label)",
    re.DOTALL,
)


def assert_fenced(rendered: str, expected: dict[str, str]) -> None:
    matches = list(_FENCE_RE.finditer(rendered))
    blocks = {match.group("label"): match.group("body") for match in matches}
    assert {label: blocks[label] for label in expected} == expected

    trusted_text = _FENCE_RE.sub("", rendered)
    assert all(payload not in trusted_text for payload in expected.values())
```

Allocate exactly one fencer in each top-level builder, then pass the shared notice and
individually labelled blocks to the template:

```python
fenced = fence_content()
return PromptCatalog.current().render(
    "pr_management/commit_message.j2",
    issue_number=issue_number,
    issue_title_block=fenced.fence("ISSUE_TITLE", issue_title),
    issue_body_block=fenced.fence("ISSUE_BODY", issue_body or "(empty)"),
    changed_files_block=fenced.fence(
        "CHANGED_FILES", changed_files or "(none reported)"
    ),
    diff_stat_block=fenced.fence("DIFF_STAT", diff_stat or "(none reported)"),
    untrusted_notice=fenced.untrusted_notice,
)
```

### Detailed Steps

1. **Inventory real consumers before editing templates.** Map each structured example to
   the production parser that consumes it: review audit, addressed replies, comment
   classification, validation partition, follow-up issue classification, or another
   domain parser.
2. **Make examples valid and semantically admissible.** Use valid JSON, one allowed enum
   value per field, all required fields, and any required exhaustive/non-overlapping
   partition. Avoid pseudo-values such as `"easy|medium|hard"` and language-level union
   expressions inside JSON.
3. **Render through the public builder.** Do not validate a copied fixture that can drift
   from the Jinja template. Render the real prompt and pass that result through the real
   consumer or extract the example exactly as production does.
4. **Assert semantic results.** Check parsed grades, findings, reply maps, classifications,
   partition membership, and follow-up categories. Do not compare serialized formatting or
   the explanatory sentence surrounding the example.
5. **Classify every template input by authority.** Fence all GitHub- and Git-derived strings,
   including host-supplied empty-value fallbacks occupying those fields. Keep only trusted
   template policy, host-owned allowlists, and validated scalar identifiers such as an integer
   issue number outside the fences.
6. **Fence adversarial payloads exactly.** Supply payloads containing fake verdicts, closing
   markers, braces, and instruction text. Pair each `BEGIN` with an `END` carrying the same
   nonce and label, compare the exact body, and prove the payload appears nowhere in trusted
   text after fenced regions are removed.
7. **Preserve response contracts independently of input fencing.** Keep JSON-only directives,
   exact response schemas, conventional-commit allowlists, and downstream parsing and
   normalization unchanged. Test those trusted contracts separately from containment.
8. **Assert routing outcomes directly.** Monkeypatch or call provider-selection helpers and
   compare the selected builder/callable. For iteration-dependent prompts, compare which
   fragment or route is selected at each boundary, not the selected fragment's prose.
9. **Assert host-owned job contracts at construction time.** At the stage seam, inspect the
   produced job's builder identity, parser identity, allowed-tool scope, and decoded
   structured kwargs. This is stronger evidence for permissions and routing than a sentence
   in the prompt claiming what the agent may do.
10. **Retain useful round-trip coverage.** Keep adversarial input round-trips, curly-brace
   rendering, externally required PR-description output, parser behavior, fence security,
   provider selection, and iteration routing. Delete editorial marker and docstring tests.

## Verified Workflow

No verified workflow exists for v2 yet. This compatibility heading satisfies the current
Mnemosyne validator; follow **Proposed Workflow** and keep the result unverified until the
templates, focused suites, pre-commit hooks, and CI pass.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| ------- | -------------- | ------------- | -------------- |
| Pin prompt headings and phrases | Asserted rubric markers, editorial instructions, headings, and forbidden strings | Harmless rewording broke tests while malformed structured examples could remain undetected | Parse machine-consumed output and assert semantic results |
| Count examples or markers | Required an exact number of JSON blocks, headings, or directive occurrences | Reorganization changes counts without changing the contract, and duplicated bad examples can still satisfy the count | Identify each consumer-owned example and validate it with that consumer |
| Marker-presence fencing test | Checked only that expected `BEGIN_` and `END_` substrings appeared | Mismatched nonces or labels, duplicated blocks, and payload leakage outside the fence were not excluded | Pair nonce and label with regex backreferences and remove fenced blocks before leakage checks |
| Fence only non-empty values | Left `"(empty)"` or `"(none reported)"` outside because the fallback was static | The same template slot changed trust treatment based on runtime content, making review and regression tests brittle | Fence the complete field value after fallback selection |
| Interpolate metadata directly into trusted prose | Rendered issue titles, bodies, changed files, diff stats, or commits as raw Jinja values | Instruction-shaped repository content could appear indistinguishable from agent policy | Pre-fence every external string in the builder and expose only `*_block` variables to the template |
| JSON-like pseudo-schema | Used enum unions or language expressions inside a JSON example | The example was not valid JSON and could not be accepted by the runtime parser | Use one valid representative enum value and all parser-required fields |
| Compare full rendered prompt text | Treated formatting and prose as the behavior-preservation oracle | Whitespace and editorial changes caused churn; equality did not prove the downstream parser accepted the schema | Render the real template, invoke the production parser, and assert its domain object |
| Encode permissions in prose tests | Asserted wording about allowed tools inside a prompt | The host can construct a differently scoped job regardless of what the prompt says | Assert the stage-produced job's permission field at the host boundary |

## Results & Parameters

### Consumer-backed example shapes from the Hephaestus plan

```json
{"addressed": ["<thread_id>"], "replies": {"<thread_id>": "what was fixed"}}
```

```json
{"classifications": {"<thread_id>": "medium"}}
```

```json
{
  "resolved": ["<resolved_thread_id>"],
  "unaddressed": [
    {
      "thread_id": "<unaddressed_thread_id>",
      "path": "module.py",
      "line": 1,
      "original_body": "original finding",
      "detail": "remaining problem"
    }
  ]
}
```

```json
{
  "follow_ups": [
    {
      "category": "core",
      "title": "Short specific title",
      "body": "module.py:1: Concrete defect and proposed fix"
    }
  ],
  "rejected": [
    {
      "title": "Excluded candidate",
      "reason": "It does not meet a supported scope category."
    }
  ]
}
```

These are representative objects, not wording snapshots. The actual acceptance gate is
that the corresponding production parser accepts them and returns the intended domain
result.

### Proposed ProjectHephaestus verification

```bash
uv run pytest \
  tests/unit/automation/test_prompts.py \
  tests/unit/automation/test_review_audit.py \
  tests/unit/automation/test_address_review_property.py \
  tests/unit/automation/test_follow_up.py \
  tests/unit/automation/test_comment_difficulty.py \
  tests/unit/automation/pipeline/test_agent_allowed_tools_scoping.py \
  tests/unit/automation/pipeline/stages/test_stage_implementation.py -v
uv run pre-commit run --all-files
```

### Commit/PR metadata prompt contract

For each rendered metadata prompt:

- Patch `hephaestus.automation.prompts._shared.secrets.token_hex` with known distinct
  values and prove successive builder calls receive fresh uppercase nonces.
- Extract blocks with nonce-and-label backreferences; assert exact label-to-body equality
  and one shared nonce across every block in that prompt.
- Remove all matched blocks and assert every instruction-shaped payload is absent from the
  trusted remainder, while `Issue #<int>` remains there.
- Assert `get_untrusted_notice()` is present.
- Assert the commit and PR templates retain `Return JSON only, with exactly:` and their
  exact schema keys. Do not change `_parse_agent_json()` or downstream normalization and
  fallback paths merely to add input fencing.

```bash
uv run pytest tests/unit/automation/test_pr_manager.py \
  -k "metadata_prompts or instruction_shaped_inputs_only_in_fences" -v
uv run pytest tests/unit/automation/test_pr_manager.py -v
```

### Review checklist

- Every structured example is valid JSON and accepted by its real consumer.
- Resolved and unaddressed thread examples form the partition required by the validator.
- Every hostile payload is present in its exact nonce/label block and absent from trusted
  text.
- Provider selection and iteration routing tests compare callables or domain outcomes.
- Stage tests assert prompt builder, parser, decoded kwargs, and host-owned tool scope.
- No test exists solely to freeze a heading, editorial phrase, example count, source string,
  or prompt-builder docstring.

## Verified On

| Project | Context | Details |
| ------- | ------- | ------- |
| ProjectHephaestus | Issue #1399 original prompt-fencing refactor plan | The v1 planning risks are archived; no implementation was verified. |
| ProjectHephaestus | Issue #1950 behavior-first prompt-test refactor plan | V2 parser, fence, routing, and host-job contracts are proposed; implementation and CI are pending. |
| ProjectHephaestus | Commit/PR metadata hardening plan | V2.1 field-authority classification, fenced fallbacks, fresh prompt-scoped nonces, and preserved JSON contracts are proposed; implementation and CI are pending. |
