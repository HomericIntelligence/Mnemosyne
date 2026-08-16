---
name: state-file-persistence-refactor-planning-risks
license: BSD-3-Clause
description: "Planning-risk checklist for JSON automation state, including fail-closed persisted agent-session resume. Use when: (1) extracting repeated prefix-<issue>.json load/save mechanics, (2) mixing raw session probes with Pydantic validation, (3) requiring explicit supported provider metadata before resuming a durable session, or (4) preserving monkeypatch seams and corrupt-file logging contracts."
category: architecture
date: 2026-08-06
version: "1.1.0"
user-invocable: false
verification: unverified
history: state-file-persistence-refactor-planning-risks.history
tags:
  - architecture
  - refactoring
  - planning
  - state-files
  - persistence
  - pydantic
  - json
  - corrupt-state
  - monkeypatch-seams
  - import-cycles
  - agent-sessions
  - session-resume
  - provider-metadata
  - fail-closed
---

# State-File Persistence Refactor Planning Risks

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-06 |
| **Objective** | Capture planning risks for automation state-file refactors and for fail-closed persisted agent sessions: a resumable non-empty session ID must carry explicit metadata naming the same supported provider currently selected. |
| **Outcome** | Planning artifacts only. ProjectHephaestus issues #1395 and #2476 were analyzed, but the described implementations and behavioral suites were not executed during these captures. |
| **Verification** | unverified — the proposed provider invariant, boundary validation, pytest suites, Ruff, mypy, and CI results remain to be observed. |
| **History** | [changelog](./state-file-persistence-refactor-planning-risks.history) |

## When to Use

- Planning a refactor that centralizes repeated JSON state-file load/save mechanics across multiple automation callers.
- A helper must support both fully validated Pydantic models and raw partial dict payloads used for session probing or resume behavior.
- Persisted agent sessions can be resumed by more than one provider and legacy state omits provider metadata or assumes a default provider.
- A state model can be mutated after construction, so construction-time validation alone does not protect the durable write boundary.
- Existing tests patch private methods such as `_load_review_state`, `_save_state`, `_get_worktree_path`, or `_load_impl_session_id`, and the plan assumes delegating wrappers preserve those seams.
- The proposed helper imports a filesystem or security write primitive from another module, and the new import edge could create layering or import-cycle risk.
- A plan cites exact source or test line numbers as anchors, but the line numbers were gathered before implementation and no live test run confirmed them.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat as a hypothesis until CI confirms.

<!-- Validator compatibility token: ## Verified Workflow -->

### Quick Reference

```bash
# Recheck planning anchors against current HEAD before implementation.
rg -n "def (_load|_save|load_all|_load_impl_session_id|_get_worktree_path)" \
  hephaestus/automation tests/unit/automation

# Enumerate every persisted filename contract before changing helpers.
rg -n "review-.*\\.json|issue-.*\\.json|prefix|state_dir|session_state" \
  hephaestus/automation tests/unit/automation

# Confirm raw partial implementer session files are still raw dict loads.
rg -n "issue-.*json|ImplementationState|model_validate|model_validate_json" \
  hephaestus/automation tests/unit/automation

# Find the single provider authority and every production resume consumer.
rg -n "AgentName|AGENT_CHOICES|session_agent_matches|load_impl_session_id" \
  hephaestus/agents hephaestus/automation tests/unit/automation

# Check the proposed dependency edge before importing write_secure into a helper module.
python - <<'PY'
import importlib
for name in [
    "hephaestus.automation._review_utils",
    "hephaestus.automation.github_api",
    "hephaestus.automation.implementer_state",
]:
    importlib.import_module(name)
print("import smoke OK")
PY

# Verification design from the plans; these are not observed pass results.
uv run pytest \
  tests/unit/automation/test_session_agent_resume_matrix.py \
  tests/unit/automation/test_review_utils.py \
  tests/unit/automation/test_models.py \
  tests/unit/automation/state/test_implementer.py \
  tests/unit/automation/test_stage_phases.py \
  tests/unit/automation/test_follow_up.py \
  tests/unit/automation/test_learn.py -v
uv run ruff check hephaestus/agents/runtime.py hephaestus/automation tests/unit/automation
uv run mypy hephaestus/agents/runtime.py hephaestus/automation
```

### Detailed Steps

1. **Start by classifying every state-file reader as raw payload or full model.**
   Do not centralize on Pydantic validation until each caller is categorized. Some callers only
   need partial session payloads, while `ImplementationStateManager.load_all()` expects full
   `ImplementationState` validation.

2. **Treat resume as a paired-field capability, not a session-ID lookup.**
   A session is resumable only when `session_id` is a non-empty string, `session_agent` is a
   string in the supported provider set, the selected provider is also supported, and the two
   provider values match exactly. Missing, empty, malformed, unknown, and cross-provider metadata
   must all start a fresh session. Historical state is migration input, not authority to infer a
   default provider.

3. **Reuse the runtime's provider authority.**
   Import the existing `AgentName` type and `AGENT_CHOICES` collection from the agent runtime.
   Do not introduce another enum or hard-coded provider tuple in persistence code. The shared
   matcher must accept `object` for raw JSON input and reject non-string values before membership
   or equality checks.

4. **Enforce the paired-field invariant at both durable boundaries.**
   On deserialization, type `session_agent` as `AgentName | None` and add a Pydantic model validator
   that rejects a present `session_id` without provider metadata. On persistence, revalidate
   `state.model_dump()` immediately before writing so assignment after construction cannot bypass
   the invariant. A validation failure must occur before the secure writer creates or replaces a
   state file.

5. **Preserve raw probes while validating their authority-bearing fields.**
   A partial reader may intentionally avoid full `ImplementationState` validation because it lacks
   fields such as `issue_number`. It must still require the decoded JSON value to be an object,
   require a non-empty string `session_id`, and pass the raw `session_agent` through the shared
   matcher. Raw compatibility does not mean legacy-provider inference.

6. **Preserve filename layout exactly.**
   Treat `review-<issue>.json` and `issue-<issue>.json` as public persistence contracts. Build
   tests that assert the path strings produced by the migrated callers, not just helper unit tests.

7. **Separate corrupt-file handling from caller log semantics.**
   A central `load_state_file()` may catch missing, malformed, unreadable, validation-failing,
   and non-dict raw payloads, but each caller's prior log level, message shape, and retry behavior
   must be preserved or deliberately changed with reviewer signoff.

8. **Treat `save_state_file()` as a layering decision, not just a helper.**
   If the helper accepts only Pydantic `BaseModel` instances and writes via `write_secure()` from
   `github_api`, verify the new `_review_utils.py -> github_api` dependency does not create an
   import cycle or broaden a low-level utility module into product-layer concerns.

9. **Keep test monkeypatch seams as wrappers until proven unnecessary.**
   Methods such as `_load_impl_session_id`, `_load_review_state`, `_get_worktree_path`, and
   `_save_state` may look redundant after helper extraction, but tests and downstream automation
   may patch them. Make them delegate first; remove them only in a separate compatibility review.

10. **Run type checks before trusting overloads and literals.**
   Helper overloads involving `BaseModel` and raw `dict[str, object]` returns are type-sensitive.
   Adding `AgentName` to model fields and accepting raw `object` at the matcher boundary can also
   expose caller annotations that were previously too narrow. Run mypy on every changed production
   module rather than only the helper.

11. **Make caller-level contract tests accompany helper tests.**
   Add focused helper tests for malformed JSON, unreadable files, validation failure, non-dict raw
   payloads, and secure writes. Also keep caller tests for wrapper seams, cross-agent session
   filtering, malformed filename handling, and continuing to load valid neighboring files after one
   corrupt state file. Use one provider matrix covering exact matches, mismatches, `None`, empty and
   unknown strings, numbers, objects, and unsupported selected providers; then exercise the same
   invariant at model construction, model load, manager save, raw load, follow-up, and learn paths.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Treat all state files as full models | Planned a single validation path for all persisted issue files | Address-review and CI resume paths may inspect partial `issue-<n>.json` payloads that lack `issue_number`; full `ImplementationState` validation would reject legitimate partial session probes | Classify raw session probes separately from full model loads before extracting helpers |
| Centralize corrupt-file handling without preserving logs | Proposed one `load_state_file()` to handle missing, malformed, unreadable, validation-failing, and non-dict payloads | The plan did not execute caller tests or compare existing log levels/messages, so it could silently change operator-facing retry diagnostics | Helper behavior is not enough; caller log semantics and retry behavior are part of the contract |
| Assume `dict(json.loads(text))` covers raw payloads | Used `dict(json.loads(text))` as the raw object parser | It intentionally rejects arrays/scalars through exception handling, but no sweep verified that every existing partial state file is object-shaped | Verify real fixtures/state files before relying on object-only raw parsing |
| Import `write_secure()` into a shared helper by assumption | Planned `save_state_file()` in `_review_utils.py` using `github_api.write_secure()` | This may introduce a new dependency edge from a generic review utility to GitHub API code; import-cycle and layering risk were not executed away | Run import smoke tests and review module ownership before moving secure-write behavior |
| Remove private seams during cleanup | Considered replacing methods such as `_load_review_state` and `_save_state` directly with helper calls | Tests patch these private seams; removing them can break monkeypatch behavior even when runtime behavior is equivalent | Keep delegating wrappers first, then separately decide whether seam removal is worth the compatibility break |
| Trust cited source/test line numbers | Used exact line anchors in `_review_utils.py`, `_reviewer_base.py`, `address_review.py`, `ci_driver.py`, `implementer_state.py`, and related tests | The plan was written from a snapshot and no live test run confirmed the anchors; current HEAD can drift before implementation starts | Re-derive anchors with `rg` against current HEAD immediately before editing |
| Infer missing provider metadata as Claude | Treated a non-empty legacy session ID with absent `session_agent` as a Claude session | The ID is opaque and may have been created by another provider; inference can send cross-provider state to the wrong resume API | Legacy or incomplete state must fail closed and start fresh; only explicit exact provider metadata authorizes resume |
| Validate provider metadata only when the model is constructed | Added a paired-field validator but persisted the already-created model directly | Pydantic assignment validation may be disabled, so later mutation can create `session_id` without `session_agent` and write invalid durable state | Revalidate a serialized model snapshot immediately before any write |
| Duplicate the provider list in persistence code | Added a second enum or local tuple for allowed providers | Runtime support and persistence validation can drift, causing valid providers to be rejected or retired providers to remain resumable | Import `AgentName` and `AGENT_CHOICES` from the runtime as the single authority |
| Check provider equality without validating raw JSON types | Compared the raw `session_agent` value directly with the selected provider | Raw JSON can supply numbers, objects, empty strings, or unknown strings; equality alone does not prove supported metadata | Require both values to be supported strings before exact equality |

## Results & Parameters

### Proposed Reference Shapes

These snippets encode the issue #2476 plan; they are not yet verified implementation results.

```python
# hephaestus.agents.runtime remains the single provider authority.
AgentName = Literal["claude", "codex", "pi"]
AGENT_CHOICES: tuple[AgentName, ...] = ("claude", "codex", "pi")


def session_agent_matches(session_agent: object, selected_agent: str) -> bool:
    """Return whether explicit session metadata matches a supported provider."""
    return (
        isinstance(session_agent, str)
        and session_agent in AGENT_CHOICES
        and selected_agent in AGENT_CHOICES
        and session_agent == selected_agent
    )
```

```python
class ImplementationState(BaseModel):
    """Durable implementation state with paired session-provider metadata."""

    session_id: str | None = None
    session_agent: AgentName | None = None

    @model_validator(mode="after")
    def require_session_provider(self) -> Self:
        """Require supported provider metadata for every persisted session ID."""
        if self.session_id is not None and self.session_agent is None:
            raise ValueError(
                "session_agent must name a supported provider when session_id is set"
            )
        return self


def save(self, state: ImplementationState) -> None:
    """Revalidate the current snapshot before any durable write."""
    validated_state = ImplementationState.model_validate(state.model_dump())
    save_state_file(
        self.state_dir,
        "issue",
        validated_state.issue_number,
        validated_state,
    )
```

```python
# Raw partial readers retain compatibility without inferring a provider.
data = json.loads(state_file.read_text())
if not isinstance(data, dict):
    raise ValueError("expected JSON object")

session_id = data.get("session_id")
session_agent = data.get("session_agent")
if not isinstance(session_id, str) or not session_id:
    return None
if not session_agent_matches(session_agent, selected_agent):
    return None
return session_id
```

Expected resume decisions:

| Persisted metadata | Selected provider | Resume? |
|--------------------|-------------------|---------|
| `session_id="opaque", session_agent="claude"` | `claude` | Yes |
| `session_id="opaque", session_agent="codex"` | `claude` | No — cross-provider |
| `session_id="opaque"` with no provider | `claude` | No — legacy metadata is incomplete |
| Unknown, empty, numeric, or object provider | Any supported provider | No — malformed or unsupported |
| Empty or non-string session ID | Matching supported provider | No — no resumable ID |

### Reviewer Focus Checklist

```text
- [ ] Are raw partial session probes still loaded as dicts, not full Pydantic models?
- [ ] Do `review-<issue>.json` and `issue-<issue>.json` paths remain byte-for-byte compatible?
- [ ] Do corrupt-file cases preserve prior caller log levels, message meaning, and retry behavior?
- [ ] Does importing `write_secure()` into the helper avoid import cycles and unwanted layering?
- [ ] Do helper overloads pass `mypy-pkg` at the migrated call sites?
- [ ] Are monkeypatched seams kept as delegating wrappers?
- [ ] Does `load_all()` skip malformed or corrupt files while continuing valid neighboring files?
- [ ] Does every non-empty durable `session_id` carry an `AgentName` accepted by the runtime?
- [ ] Does the pre-write boundary revalidate models that may have been mutated after construction?
- [ ] Do raw session probes reject non-object JSON, non-string/empty IDs, and absent/malformed/unknown provider metadata?
- [ ] Do all resume consumers use the shared matcher and log missing metadata as absent/invalid rather than as Claude?
- [ ] Does one parameterized matrix cover exact supported matches, cross-provider state, unsupported selected providers, and non-string raw metadata?
```

### Unverified Assumptions From Issue #1395 Planning

| Assumption | Verification Needed |
|------------|---------------------|
| `load_state_file()` can centralize all corrupt-file handling without changing callers' logs or retry behavior | Compare caller-level tests and log assertions before and after migration |
| `dict(json.loads(text))` is sufficient for raw payloads | Sweep existing partial state fixtures/files and add non-object JSON regression tests |
| `save_state_file()` should accept only `BaseModel` instances and call `write_secure()` | Import smoke test plus architecture review of the new dependency edge |
| `BaseModel` overloads satisfy `mypy-pkg` | Run `pixi run mypy-pkg` after migrating representative callers |
| Delegating wrappers preserve patched seams | Keep caller tests that monkeypatch the private methods, not just helper tests |
| Implementer-session probing must remain raw dict loading | Add/retain tests with partial `issue-<n>.json` payloads lacking `issue_number` |

### Unverified Provider-Resume Contract From Issue #2476 Planning

| Proposed Contract | Verification Needed |
|-------------------|---------------------|
| `session_agent_matches()` accepts only exact members of runtime `AGENT_CHOICES` | Run the provider matrix for Claude, Codex, Pi, missing/empty/unknown metadata, unsupported selected providers, numbers, and objects |
| `ImplementationState` rejects a session ID without a supported `AgentName` | Exercise `model_validate()` with every supported provider and invalid metadata values |
| `ImplementationStateManager.save()` rejects post-construction invalid mutation before writing | Mutate a valid model, assert `ValidationError`, and assert the target file does not exist |
| `load_state_file()` skips legacy durable state without provider metadata | Write a legacy `issue-<n>.json`, call `load_all()`, and assert the issue is absent from manager state |
| Raw partial probes fail closed without requiring a complete model | Cover valid explicit metadata, mismatch, malformed/unknown metadata, non-string IDs, non-object JSON, and filename precedence |
| Follow-up and `/learn` never invoke a provider for invalid or mismatched metadata | Patch both provider call paths and assert neither is called for missing Claude metadata or cross-provider metadata |

### External Anchors To Recheck

- Source files cited by the plan: `hephaestus/automation/_review_utils.py`, `_reviewer_base.py`,
  `address_review.py`, `ci_driver.py`, and `implementer_state.py`.
- Provider-resume anchors cited by issue #2476: `hephaestus/agents/runtime.py`,
  `hephaestus/automation/models.py`, `hephaestus/automation/state/implementer.py`,
  `_followup_phase.py`, `_review_utils.py`, `follow_up.py`, and `learn.py`.
- Tests cited by the plan: `tests/unit/automation/test_address_review.py` and
  `tests/unit/automation/test_ci_driver.py`.
- Provider-resume suites cited by issue #2476: `test_session_agent_resume_matrix.py`,
  `test_review_utils.py`, `test_models.py`, `state/test_implementer.py`,
  `test_stage_phases.py`, `test_follow_up.py`, and `test_learn.py`.
- APIs relied on without execution: Pydantic `model_validate_json`,
  `BaseModel.model_dump_json(indent=2)`, and `write_secure()`.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Planning phase for issue #1395, state-file persistence helper extraction | Plan produced, NOT executed. This skill records assumptions and reviewer risks for a future implementation pass. |
| ProjectHephaestus | Planning phase for issue #2476, fail-closed persisted agent-session resume | Plan produced, NOT executed. The provider matrix, read/write boundary validation, caller diagnostics, and focused verification commands remain unverified. |
