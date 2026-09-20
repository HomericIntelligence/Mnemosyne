# Advisory Guidance Review

This report describes the advisory-guidance parent change. The subsequent
[history migration](../history-migration.md) retains its guidance and moves
companion provenance to immutable Git sources.

## Intent and Scope

This change applies the user's approved plan to Mnemosyne's active instructions
and flat skill corpus. It uses the
[OpenAI article on skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
as context. Short triggers, task-specific detail, and clear completion criteria
help reduce unnecessary process. The guidance remains suitable for multiple
models. It does not change model defaults or install plugins.

Use the [ASD-STE100 guidance](../asd-ste100.md) for this report and changed prose.
The official standard and a human technical-English review were not available
for this change. No natural-language conformance claim is made.

The source baseline is `366015d7b78f522b6bc68f4de67b22229f9e7c4d`.
The inventory records a disposition for each main skill and active instruction
surface. Historical records, raw evidence, legal text, and machine-enforced
contracts remain distinct from recommendations about agent behavior.

## Coverage

The [per-file inventory](advisory-guidance-inventory.json) records all 786 main
skills: 501 changed and 285 retained. Review covered descriptions, active
instruction prose, and active prompt templates. It was not a new technical
verification of every historical command or result.

The baseline inventory contains 1,344 tracked paths: 786 main skills, 501
companions, 11 active guidance documents, 40 technical or configuration files,
and 6 protected records. Its sorted-path SHA-256 digest is
`a80e120083a07b69403c315b9ca8b69ef468deb9e6eea723241234b61511b5ba`.
Technical files received instruction-surface discovery, not a full code audit.

Changed skills have version and archive records. Thirty-three prior versions
use privacy-redaction records instead of copying private details. Existing
history remains unchanged apart from appended amendment records; this is not
a purge of legacy data. Two notes files retain clearly labeled historical
examples outside normal retrieval.

Existing tests were adjusted for eight current skill versions and the intended
advisory wording. Their schema, provenance, and generated-principles protections
remain in place. No parser, retrieval API, model default, or validation behavior
was changed.

## Decision Rules

- Recommend a workflow when its conditions make it useful. Explain why it helps.
- Prefer the general decision rule to a fixed sequence of agent actions.
- Use existing authorization for routine choices and reversible work in scope.
- Ask for input when evidence cannot resolve a material ambiguity or authority
  is genuinely missing. Identify the protected action and source of the boundary.
- Continue through implementation and useful verification. A plan, review round,
  first implementation, or unavailable optional tool does not finish the task.
- Continue independent work when one action is unavailable. Report the remaining
  dependency and verification limits honestly.
- Suggest unrelated improvements without making them prerequisites.

This is a contextual prose review, not a replacement of every occurrence of
"must", "stop", or "required". Such words can describe actual software behavior,
failed attempts, quotations, or technical dependencies. Changing those passages
without context would change the knowledge rather than improve the guidance.

## Retained Boundaries

| Source | Protected action or contract | Treatment |
| --- | --- | --- |
| User request and applicable host permissions | Destructive work outside scope, external commitments, or actions with missing authority | Ask only for the missing decision; continue independent authorized work. |
| `AGENTS.md` validation delegation | Execution of repository-controlled tests, lint, type checks, and builds | Preserve the required isolation conditions. Missing capability leaves a coverage gap. |
| Existing skill parser, schema, and validator | Retrieval metadata, required sections, Failed Attempts columns, and main-file size | Describe these as compatibility facts. No schema migration. |
| Pinned Athena principles and installed workflow skills | External ownership, source provenance, and shared contracts | Preserve original principles. Explain task-specific use; do not claim to override external instructions. |
| Security and privacy policy | Secret disclosure, unsafe publication, and private evidence copied into archives | Preserve protection. Use generalized placeholders and eligible legacy privacy-redaction records where needed. |
| GitHub rulesets and release configuration | Merge, queue activation, and release publication | Preserve actual external controls; a draft does not claim readiness to merge. |

## Scenario Review

These are source-review scenarios, not executed model evaluations.

| Scenario | Intended guidance |
| --- | --- |
| The user has authorized a routine edit | Make the edit and useful corrections without a second permission request. |
| A reversible implementation choice is unspecified | Use context and evidence; state an assumption when it matters. |
| Two interpretations would produce materially different results | Inspect available evidence, then ask for the unresolved choice. |
| An action would destroy unrelated work | Preserve the work and ask for action-specific authority. |
| An optional advisor, document, or tool is unavailable | Use available evidence and continue useful work; report the limit. |
| Validation cannot run in the required boundary | Complete source changes and review, and report unexecuted checks. |
| One dependency blocks part of a task | Complete independent work and identify the remaining dependency. |
| A first implementation exposes a defect | Continue correction and relevant verification within scope. |
| A possible improvement is unrelated to the request | Suggest it separately without blocking the requested result. |

## Evidence and Limits

The validation specialist used `gpt-5.6-luna` with `xhigh` reasoning to inspect
host capability. No trusted host-fixed command plan or compliant validation
runner was exposed. The ordinary sandbox does not establish the required
read-only source, restricted outputs, denied network and credentials, scrubbed
environment, unprivileged identity, and resource limits together.

No tests, lint, type checks, builds, or automated privacy and link checks were
run locally. Repository CI remains necessary execution evidence. Source review
is not a substitute for those results or a runtime model-behavior evaluation.

Existing Athena installation instructions can still impose workflow steps.
They are outside this Mnemosyne-only change. The pinned principles remain exact
for compatibility; local guidance explains that they aid design judgment rather
than introduce a checklist or extra permission stages.

## Shared-Guidance Review Decisions

A separate source reviewer examined the shared guidance and relevant existing
tests. The review did not execute checks. It identified three corrections:
clarify delegated execution of task recipes, align filename advice, and avoid
implying merge authority in the contribution example. Those corrections are
included. Wording now distinguishes required isolation conditions from an
available runner.

The review also proposed restoring mandatory workflow and writing language.
That proposal conflicts with the approved advisory-guidance change. The
implementation retains explicit compatibility, security, and external-authority
boundaries while leaving process and review recommendations advisory. PR review
prompts are deliberately suggestions rather than mandatory checkboxes. Existing
CI and external publication rules are unchanged.

## Corpus Cross-Review

Separate reviewers inspected changed instruction hunks across the five batches.
Corrections addressed stale mandatory steps inside copyable prompts, unsupported
assumption-to-fact transitions, validation of the wrong checkout, broad staging
commands, overclaims from training-loss trends, and unsafe shell placeholders.
A final integration pass removed additional private context and reconciled
historical checker behavior with continuation of independent work.

Suggestions to make every check or review stage mandatory again were not adopted.
The user's requested behavior is advisory process with accurate evidence and
real authorization boundaries. Required output formats for actual consumers
remain distinct from optional workflow preferences.

Security-sensitive operational material was retained without capability
expansion. The inventory records those exceptions and technical concerns found
outside this migration. This change does not certify those legacy procedures or
claim to correct every technical defect in the corpus.

## Rebase Integration

On 2026-09-20, the branch was rebased onto `1528432a1873e93e0c16609dd3c3cfd3c5f0d545`
at the user's request. Nineteen skills had textual conflicts. Resolutions retain
short descriptions and advisory guidance while preserving upstream distinctions
between active tasks, completed tasks, and ordinary CI/CD integration. Upstream
immutable-candidate evidence guidance is retained.

34 migration skills also changed upstream. Their versions and history
amendments identify the combined content and immutable upstream predecessors.
The inventory retains its original review baseline and records the new target,
inherited changes, and current result hashes. The original review does not claim
to certify upstream additions. No execution validation ran during this rebase;
the previously documented runner limitation remains.

## Pre-Merge Corrections

Fresh source review found residual examples that contradicted the advisory prose.
Corrections align cleanup, CI reruns, environment selection, endpoint reuse, agent
lifecycle handling, PR grouping, charter authority, and fleet scope with the task.
A separate reviewer examined the correction diff. Hosted Markdown lint identified
blank-line and placeholder-rendering errors; those locations were corrected.
Changed main skills have patch versions and immutable predecessor references.
These edits do not claim new local execution evidence.
