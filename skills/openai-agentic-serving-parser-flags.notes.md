# OpenAI Agentic Serving Parser Flags — Notes

Supporting evidence for the main entry. Organizational details are generalized.

## Source case, v1.1.0: parser auto-detection across a revision refresh

### Context

- A serving registry keeps one generated launch manifest (cookbook) per model
  checkpoint revision, with `engine_extra_args` as the source of truth.
- A hotfix added a new checkpoint revision of a long-context mixture-of-experts
  family on a TP8 H200 SGLang surface, copying the parser values of the prior
  revision of the same family and pinning the tool-call parser to the new
  revision's family-parser name.

### Failure mode

- The new revision changed its tool-call markup: its DSML-style tags are
  leading-spaced differently from the prior revision. The pinned prior-revision
  parser silently corrupts tool calls for the new revision.
- The engine's server accepts `auto` for both parser flags. With `auto`, the
  engine maps the checkpoint's architecture name to its native implementation
  and selects the revision-aware DSML tool-call parser and the family
  reasoning parser without a pinned name.
- The registry's own preparation document already quoted the pinned upstream
  engine recipe for that H200 profile, and the recipe selected `auto` for both
  flags. The local override, not the recipe, was the outlier.

### Resolution

- Review requested `auto` on both inline comments. The fix was two value
  changes:

```text
- "--reasoning-parser"
- "auto"
- "--tool-call-parser"
- "auto"
```

- Full repository CI passed after the change (complete test shard matrix and
  root profile). Both review threads were resolved with the fix commit
  reference. The pull-request body table was updated so the record matched the
  pushed head.

### Boundary and scope

- `auto` is the preference when the engine and the upstream recipe offer
  detection for the exact revision; it is not a universal default.
- Other manifests in the same registry keep explicit family parser names where
  the engine has no auto-mapping, and multi-model launcher defaults still pin
  per-family parser names so ad hoc launches match generated manifests.
- On vLLM surfaces, `--enable-auto-tool-choice` remains a separate gate.
  `auto` selects the parser; it does not enable automatic tool choice.

### Commands used

- Cookbook diff review and YAML parse check; pre-commit YAML validation.
- Two review-thread replies, then thread resolution through the forge GraphQL
  API (`resolveReviewThread`).
- Pull-request check watch until exit 0.
