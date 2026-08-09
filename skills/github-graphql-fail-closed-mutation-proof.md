---
name: github-graphql-fail-closed-mutation-proof
description: "Centralize automation-owned GitHub GraphQL execution behind a typed, fail-closed, non-sleeping one-attempt boundary that distinguishes retryable reads from mutation outcomes that cannot be proven. Use when: (1) GraphQL calls validate status, envelopes, or payloads inconsistently, (2) a mutation might be replayed after an ambiguous transport failure, (3) durable workflows need correlation-bound receipts and resumable partial progress, or (4) restart recovery must reconcile read-only instead of reissuing mutations."
category: architecture
date: 2026-08-08
version: "1.0.0"
user-invocable: false
verification: unverified
tags:
  - github
  - graphql
  - automation
  - fail-closed
  - mutation
  - outcome-unknown
  - correlation-id
  - receipts
  - single-attempt
  - retry-safety
  - partial-progress
  - reconciliation
  - state-machine
---

# Fail-Closed GitHub GraphQL Mutation Proof

## Overview

| Field | Value |
|-------|-------|
| **Date** | 2026-08-08 |
| **Objective** | Give every automation-layer GitHub GraphQL operation one trustworthy execution and validation boundary while preventing mutation replay whenever dispatch cannot be excluded. |
| **Outcome** | Proposed a typed query/mutation split, executor-owned correlation IDs, exact mutation receipts, resumable phase progress, reconciliation-only restart handling, and an ordered failure taxonomy. |
| **Verification** | `unverified` — the architecture and acceptance matrix were specified, but no implementation, focused test suite, live schema probe, or CI run was completed in the source session. |

The governing rules are:

1. A successful process is not yet a successful GraphQL operation. Status, JSON,
   envelope, top-level errors, operation identity, schema, and exact payload all
   require validation.
2. A query can be retryable after an ambiguous transport failure because it has no
   intended side effect. A mutation becomes **outcome unknown** whenever dispatch
   cannot be disproved, even if the response looks deterministic.
3. Only proven pre-dispatch rejection permits a fresh mutation invocation. Once
   dispatch may have occurred, do not replay, compensate, or infer failure from a
   missing response.
4. Mutation success is a correlation-bound receipt, not a truthy payload. The
   executor creates a fresh `clientMutationId` immediately before dispatch, and the
   validator requires that exact ID plus the exact target and resulting state.
5. Multi-mutation work persists each proven phase before proceeding. Restarted
   work either resumes from retained proof or performs read-only reconciliation;
   it never reconstructs permission to mutate from an old intent journal.

## When to Use

- Automation invokes `gh api graphql` from more than one module or constructs
  free-form GraphQL documents at call sites.
- Callers independently inspect return codes, call `json.loads()`, traverse
  permissive `.get()` chains, or treat missing data as an empty connection.
- Query and mutation failures share one generic exception or retry loop.
- A timeout, broken pipe, connection error, rate limit, or nonzero process result
  could occur after a mutation reached GitHub.
- A mutation caller supplies or reuses `clientMutationId`.
- A successful mutation payload is accepted without checking the exact target,
  requested content/state, repository or pull-request identity, and echoed
  correlation ID.
- A batch creates a parent review, posts several replies, submits the review, or
  resolves several threads and needs to resume without duplicating completed work.
- A restart journal contains mutation intent but cannot prove what GitHub accepted.
- A specialized deterministic domain rejection, such as a review comment that is
  not editable, is the only condition allowed to activate a fallback write.
- A repository needs a static guard proving that every GraphQL execution crosses
  one typed boundary.

## Proposed Workflow

> **Warning:** This workflow has not been validated end-to-end. Treat it as a
> hypothesis until the implementation tests, read-only live schema probe, and CI
> pass.

### Quick Reference

```python
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Generic, TypeVar, overload
from uuid import uuid4

T = TypeVar("T")
GraphQLScalar = int | str


@dataclass(frozen=True)
class GraphQLQuerySpec(Generic[T]):
    operation: str
    document: str
    validate: Callable[[dict[str, Any]], T]

    def __post_init__(self) -> None:
        require_root_operation(self.document, "query")


@dataclass(frozen=True)
class GraphQLMutationIntent:
    operation: str
    correlation_id: str
    targets: tuple[tuple[str, str], ...]
    content_hashes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class GraphQLMutationSpec(Generic[T]):
    operation: str
    document: str
    variables: Mapping[str, GraphQLScalar]
    target_fields: tuple[str, ...]
    content_fields: tuple[str, ...]
    validate: Callable[[dict[str, Any], GraphQLMutationIntent], T]

    def __post_init__(self) -> None:
        require_root_operation(self.document, "mutation")
        if "clientMutationId" in self.variables:
            raise ValueError("clientMutationId is executor-owned")
```

```python
def prepare_mutation(spec: GraphQLMutationSpec[T]) -> PreparedMutation[T]:
    correlation_id = uuid4().hex
    intent = GraphQLMutationIntent(
        operation=spec.operation,
        correlation_id=correlation_id,
        targets=tuple(
            (field, str(spec.variables[field])) for field in spec.target_fields
        ),
        content_hashes=tuple(
            (
                field,
                sha256(str(spec.variables[field]).encode("utf-8")).hexdigest(),
            )
            for field in spec.content_fields
        ),
    )
    return PreparedMutation(
        spec=spec,
        intent=intent,
        variables={**spec.variables, "clientMutationId": correlation_id},
    )
```

```python
result = raw_gh_call(
    graphql_argv(prepared.document, prepared.variables),
    check=False,
    retry_on_rate_limit=False,
    max_retries=1,
    log_on_error=False,
    throttle=False,
)
return validate_process_envelope_and_payload(prepared, result)
```

### Detailed Steps

1. **Inventory the real execution surface.** Search for raw GraphQL documents,
   `gh api graphql`, `/graphql`, subprocess launchers, generic GitHub wrappers,
   response decoders, and helpers that silently return empty collections. Include
   protocols, compatibility facades, pipeline adapters, and tests. Count operations,
   not just transport calls: one generic transport may serve many free-form queries
   and mutations.

2. **Preserve dependency direction.** Put the typed executor in the product or
   automation layer and let it call the lower-level GitHub client. Shared library
   code must not import the product-layer executor. Add a guarded product-layer
   facade for non-GraphQL GitHub calls that rejects exact `graphql` or `/graphql`
   endpoint tokens, including option-interposed argv forms.

3. **Make operation kind structural.** Query specs accept invocation variables and
   require a root `query`. Mutation specs require a root `mutation`, own all
   mutation variables, reject caller-supplied `clientMutationId`, and declare which
   fields are immutable targets versus mutable content. Keep constructors private
   to one module through an AST guard; expose named operation factories instead of
   caller-authored documents.

4. **Prepare mutation intent at the last possible moment.** Generate
   `uuid.uuid4().hex` inside the executor immediately before each actual transport
   attempt. Derive target identifiers from bound variables and represent mutable
   values in diagnostics only as SHA-256 hashes. A second invocation after a proven
   pre-dispatch rejection receives a fresh correlation ID; callers cannot reuse one.

5. **Use exactly one non-sleeping transport attempt.** Retain circuit-breaker
   admission but disable global/thread throttling, internal rate-limit retry, generic
   retry, automatic status raising, and duplicate error logging. The executor owns
   classification. Verify exact transport arguments and prove that disabling
   throttles does not bypass the circuit breaker.

6. **Validate the response in a fixed order.** First classify launch/transport and
   process status. Then require nonempty valid JSON with an object root, a `data`
   object, and either no `errors` member or a valid nonempty list of objects whose
   `message` values are nonempty strings. `errors: null`, `errors: []`, malformed
   entries, missing/non-object `data`, and partial-looking output are malformed.

7. **Classify top-level errors before trusting data.** If every well-formed error is
   rate-limit evidence, a query is retryable and a mutation is outcome unknown,
   regardless of accompanying `data`. Other top-level errors are query-deterministic
   or mutation-outcome-unknown. Permit a specialized deterministic mutation error
   only for an exact domain predicate, such as the sole normalized,
   case-insensitive `Body is not editable` message; mixed errors do not qualify.

8. **Run an operation-specific exact validator.** Require repository owner/name,
   issue or pull-request number, node IDs, connection types, page information,
   target state, commit, and every requested alias as applicable. Preserve a typed
   response exception raised by the validator. Normalize any other ordinary
   `Exception` into query-deterministic or mutation-outcome-unknown; do not catch
   `KeyboardInterrupt` or `SystemExit`.

9. **Return exact mutation receipts.** A mutation validator must require the echoed
   correlation ID and exact target. If the mutation changes content or state,
   require the exact requested body, commit, review state, resolution state, or
   viewer ownership. Separate operations with incompatible proofs instead of using
   an optional argument—for example, a reply attached to a known pending review and
   a reviewer-feedback reply returned in a new `COMMENTED` review need distinct
   factories and receipt types.

10. **Model multi-mutation publication as explicit phases.** A useful reply workflow
    is `create_review -> post_replies -> verify_reply -> submit_review ->
    verify_submission`. Persist the proven pending-review ID, validated reply
    receipts, active correlation-bound receipt awaiting readback, completed target
    IDs, and remaining targets before starting the next phase.

11. **Resume only from positive proof.** A retryable pre-dispatch error retains the
    progress record and retries only the current phase with a fresh invocation. A
    read-only visibility check may retry without issuing another mutation. Never
    recreate a proven parent object, repost a proven reply, resubmit a proven
    review, or restart a whole partial batch.

12. **Make ambiguous mutation outcomes terminal for the intent.** Timeout, broken
    pipe, connection failure, status-less interruption, rate limit, nonzero result,
    malformed output, top-level errors, and validator failure all become
    mutation-outcome-unknown once dispatch cannot be excluded. Preserve already
    proven prior batch results, block all unproven targets, clear replayable intent
    and retry counters, and do not compensate with inverse mutations.

13. **Treat restart journals as read-only evidence.** New journals may record an
    armed one-shot intent plus typed progress, while old formats remain parseable.
    Any handoff reconstructed after restart is `reconciliation_only=True`. It may
    read marker-bound state and report completion, but it may not create, edit,
    reply, submit, resolve, or otherwise mutate.

14. **Narrow caller catches.** Let typed GraphQL failures propagate through helper
    layers. A valid empty connection is empty only after complete validation. Catch
    a specialized deterministic rejection only where a documented fallback is
    safe; an outcome-unknown edit must prevent shadow or fresh publication.

15. **Mechanize the architecture.** Add AST/runtime tests proving one raw client
    import, one GraphQL process invocation, no direct subprocess GraphQL launch,
    private spec construction, and guarded option-interposed calls. Add
    table-driven tests for every transport, status, envelope, error, validator, and
    receipt branch.

16. **Probe schema drift without mutating GitHub.** Add an opt-in authenticated
    contract test that uses GraphQL introspection to verify every selected query
    field, mutation input, payload field, and nested receipt field. The probe is
    read-only and does not establish that mutation behavior has been tested.

## Verified Workflow

_Not applicable yet._ The actionable design remains under **Proposed Workflow**.
This compatibility heading makes no verification claim. Promote the skill to
`verified-local` only after the executor, migrations, state-machine tests, static
guards, and live read-only schema contract pass locally; use `verified-ci` only
after the required CI confirms them.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---------|----------------|---------------|----------------|
| Scattered transport and validation | Each helper launched GraphQL and interpreted status, JSON, errors, and nested data independently. | Error handling drift allowed malformed or partial responses to look like empty state or success. | Centralize transport, envelope, error, identity, and schema validation behind one typed executor. |
| Generic retry around mutations | A timeout, rate limit, nonzero status, or broken pipe was treated as a normal transient failure. | The server may already have applied the mutation, so retry can duplicate or contradict durable state. | Retry a mutation only after proven pre-dispatch rejection; otherwise mark its outcome unknown. |
| HTTP 200 as mutation success | Any parsed `data` member was accepted when the process returned zero. | GraphQL can return top-level errors with HTTP 200 and partial or apparently complete data. | Classify well-formed top-level errors before trusting any data. |
| Failure-to-empty reads | Broad `Exception` catches returned `[]`, `{}`, or `None`. | Transport, pagination, schema, and identity failures became authoritative absence and could trigger duplicate writes. | A valid empty connection is evidence produced only by a complete validated read. |
| Caller-owned correlation IDs | Callers supplied or retained `clientMutationId` with mutation variables. | A retry could reuse correlation identity, and logs could not prove that the receipt belongs to the current dispatch. | Generate a fresh ID inside the executor immediately before each actual attempt. |
| Truthy mutation payloads | Validators checked that a payload object or ID existed. | A response for the wrong target, body, commit, review state, or correlation could advance the workflow. | Require an exact correlation-bound receipt for every mutation. |
| One reply helper with an optional review ID | Implementation replies and reviewer-feedback replies shared a mutation path. | The two modes require incompatible proof: known pending-review ownership versus a newly returned commented review. | Give different mutation contracts different factories, methods, and receipt validators. |
| Replay the whole partial batch | A safe retry recreated the parent review or reposted all replies. | Proven progress was discarded, creating duplicates and making readback ambiguous. | Persist phase, parent identity, receipts, active readback, and remaining targets; resume only the unfinished phase. |
| Compensate after an unknown outcome | An inverse mutation such as unresolve was considered after a later operation failed ambiguously. | Compensation can undo a successful original mutation or introduce another unknown outcome. | Preserve proven progress, block unproven work, and perform no compensation when dispatch may have occurred. |
| Reissue journaled intent after restart | Recovery treated a persisted intent as permission to mutate again. | A crash can happen after remote success but before local persistence, so the journal does not prove non-dispatch. | Recovered handoffs are reconciliation-only and may perform reads, never mutations. |
| Log raw mutation bodies | Diagnostic context included caller-provided mutable content. | Logs could expose sensitive or untrusted text and were unnecessary for correlation. | Log operation, correlation ID, target IDs, and SHA-256 content hashes only. |

## Results & Parameters

This skill records a proposed contract, not observed production results.

### Transport parameters

```yaml
graphql_transport:
  attempts: 1
  sleeps: false
  circuit_breaker_admission: true
  check: false
  retry_on_rate_limit: false
  max_retries: 1
  log_on_error: false
  throttle: false
mutation_correlation:
  source: executor
  algorithm: uuid4-hex
  caller_override: forbidden
diagnostic_content:
  raw_values: forbidden
  hash: sha256
```

### Ordered failure taxonomy

| Evidence | Query | Mutation |
|----------|-------|----------|
| Open circuit rejects before dispatch | Retryable with `pre_dispatch=True` | Same; a fresh invocation is safe |
| Executable missing or launch permission denied | Deterministic | Deterministic because launch did not occur |
| Rate-limit exception, timeout, broken pipe, connection failure, other `OSError`, or status-less process failure | Retryable; preserve reset metadata | Outcome unknown |
| Nonzero process result with rate-limit evidence | Retryable | Outcome unknown |
| Nonzero result with authorization, target-resolution, syntax, schema, or HTTP 400/401/403/404/422 evidence | Deterministic | Outcome unknown |
| Sole normalized `Body is not editable` message | Deterministic | Specialized not-editable rejection |
| Other nonzero result | Retryable | Outcome unknown |
| Empty, invalid, non-object, or malformed response envelope | Deterministic | Outcome unknown |
| All well-formed top-level errors are rate-limit errors | Retryable | Outcome unknown, even with `data` |
| Other top-level errors | Deterministic | Outcome unknown except the sole specialized rejection |
| Operation validator failure | Deterministic | Outcome unknown |
| Valid envelope and exact payload | Validated query result | Correlation-bound receipt |

### Response-envelope invariant

```text
stdout is nonempty valid JSON
root is an object
data exists and is an object
errors is absent
  OR errors is a nonempty list of objects with nonempty string messages
operation-specific identity and schema are exact
mutation receipt echoes the executor-owned correlation ID
```

`errors: null`, `errors: []`, malformed entries, or partial-looking data with an
invalid error member are malformed responses.

### Resumable reply progress

```yaml
phase:
  - create_review
  - post_replies
  - verify_reply
  - submit_review
  - verify_submission
proof:
  pull_request_id: required
  pending_review_id: retained_after_create
  replied_thread_ids: monotonic
  receipts: exact-and-correlation-bound
  active_thread_id: optional-readback-target
  active_comment_id: optional-readback-target
restart:
  reconstructed_handoff: reconciliation_only
  allowed_operations: reads-only
unknown_outcome:
  preserve_proven_prior_progress: true
  clear_replayable_intent: true
  retry_mutation: false
  compensate: false
```

### Minimum validation matrix

```text
query success; mutation success; wrong operation kind; caller correlation rejected
fresh IDs on separate pre-dispatch attempts; exact one-attempt/no-throttle transport
open circuit; launch failure; rate limit; timeout; broken pipe; connection failure
status-less subprocess failure; deterministic nonzero evidence; unknown nonzero evidence
primary/secondary rate limits; reset metadata; sole vs mixed not-editable errors
empty/invalid/non-object JSON; missing/non-object data; malformed errors
HTTP-200 mutation errors with absent/null/partial/complete data
validator typed exception preservation; ordinary exception normalization
wrong repository/issue/PR/thread/comment/review/commit/correlation identity
safe summaries exclude raw mutable content
pre-dispatch create/reply/submit resumption; readback-only retry
partial progress; restart reconciliation without mutation; no replay or compensation
AST one-boundary guards; read-only live schema introspection
```

### Related skills

- [Safe GitHub GraphQL Parameterisation](./automation-graphql-parameterisation-prevent-injection.md)
  covers `-f` versus `-F` encoding and leading-`@` strings at the same transport boundary.
- [Fail-Closed JSON Result Validation for External Tools](./tooling-subprocess-json-fail-closed-result-validation.md)
  covers the generic subprocess/JSON shape principle without GraphQL mutation semantics.
- [GitHub API Secondary Rate-Limit Backoff](./github-api-secondary-rate-limit-backoff.md)
  covers sleeping client retry; this skill deliberately disables sleeping and returns typed
  evidence to the owning workflow.
- [Automation Review Comment Validation with Host Receipts](./automation-review-comment-validation-host-receipts.md)
  covers immutable test evidence; mutation receipts here instead prove an exact remote write.

## Verified On

| Project | Context | Details |
|---------|---------|---------|
| ProjectHephaestus | Architecture plan tracking issue #2393 | Proposed central executor, named operation factories, correlation-bound mutation receipts, partial-progress reply state machine, reconciliation-only journals, static boundary guards, and read-only schema introspection. No implementation or tests were executed in the source session. |
