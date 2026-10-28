# Notes: testing-authority-subtraction-surrogate-repoint

Privacy-safe session evidence for the skill. Facts from issue #3178 and PR
#3409 on LLM360/comet, 28 October 2026.

## The trigger

- Issue #3178 asked to disable the `kimi-k3` BF16 KV-cache lane so that
  tenants and autoscaler signals cannot start it; only an administrator
  context change can enable it again.
- The change removed `kimi-k3` from the `policy.models` mappings of
  `deployment/contexts/m1-production.yaml`, `m2-production.yaml`,
  `m1-main.yaml`, and `m2-main.yaml`. The entry remained in
  `m1-development.yaml`, `m2-development.yaml`, `m2-qualification.yaml`,
  and `k3-cache-432.yaml`, and in `cookbooks/kimi-k3.yaml`.

## The failure shape

- CI shards 25 and 29 on the first merge attempt reported exactly two
  failures, both in `tests/test_deployment_context_coexistence.py`:
  `render model check failed: expected one of [14 m2-production models],
  but observed 'kimi-k3'.`
- `test_one_physical_profile_renders_two_complete_contexts` and
  `test_container_mounts_do_not_expose_sibling_context_roots` rendered a
  pinned `kimi-k3` recipe against `m2-development` AND `m2-production`.
- Other pinned uses of `kimi-k3` in the same file stayed green because
  they build tree-independent fixtures through `make_test_context` with
  an explicit `models=` override, so CI was the first environment to
  surface the coupling.

## The surrogate selection

- Membership intersection of `m2-development` and `m2-production`
  `policy.models`: ten shared entries (deepseek-v4-flash-0731,
  deepseek-v4-pro, deepseek-v4-pro-fp8, glm-5.3-flash-fp8, and six
  k2-horizon recipes).
- First candidate `deepseek-v4-pro`: recipe has a top-level `fast_start`,
  and its m2 cluster section has an image but no `image_sha256`.
  `src/comet/render.py` (fast-start branch when no launch image resolves)
  then raised `fast-start replica rendering requires a healthy donor`.
- Second candidate `k2-horizon-32b`: no top-level `fast_start`, and the
  m2 cluster section carries an immutable `image_sha256`; replica renders
  need no standby node.
- The donor render in `test_one_physical_profile_renders_two_complete_contexts`
  requires an SGLang fast-start recipe
  (`donor rendering requires an SGLang fast_start cookbook`,
  `src/comet/render.py` render gate) and an immutable runtime image.
  No intersection survivor supplies fast-start top-level, so the donor
  fixture copies `k2-horizon-32b` and injects `k3.fast_start` at the
  recipe TOP LEVEL through `model_copy`.
- A first injection set `fast_start` on the m2 CLUSTER section of the
  donor fixture. Verified with the cookbook resolver that
  `Cookbook.for_cluster("m2").fast_start` stayed resolved `False` even
  though the cluster field was set: cluster-scoped `fast_start` is
  schema-legal and resolution-inert.

## Related coupling found in the same drive

- `tests/deployment_context_helpers.py` derived a recipe template from
  the FIRST entry of the shipped policy (`next(iter(policy.models.values()))`).
  When both m1 files legitimately went empty (intended off state), the
  helper raised `StopIteration`. The repair routes to an m1-development
  template fallback. Registered-context loads also validate EVERY shipped
  context file, so one schema-invalid file breaks `make_test_context` for
  unrelated tests.
- Removing `kimi-k3: cache_aware` (the only cache-aware route in the m1
  files) orphaned four KV-usage threshold keys
  (`balance_token_usage_threshold`, `overload_token_usage_threshold`,
  `max_cached_owners_per_prefix`, `cache_owner_spill_cooldown_s`). The
  schema allows them only with a cache-aware route, so the subtraction
  forced their removal to defaults.
- Test-mutant anchors that named the removed model became inert
  (`model_policies={"kimi-k3": ...}` no longer raises for an unknown
  model). Mutants moved to `deepseek-v4-pro`, the surviving model in the
  fair-share profiles and admission partitions.
- The companion subtraction guard, `tests/test_kimi_k3_lane_disable.py`,
  checks: zero shipped `kimi-k3` keys in the four contexts (x4
  parametrized), gateway replica records (schema v2) fail closed against
  the shipped policy (x4), surviving models keep complete autoscale bounds
  (x4). The fail-closed check builds a positive record and asserts the
  predicate rejects it, which keeps the check non-vacuous.

## Verification evidence

- Targeted pair run after the fix: 2 passed in ~45 s.
- Full `tests/test_deployment_context_coexistence.py`: 68 passed in
  ~12.5 min. Earlier full validation of
  `tests/test_kimi_k3_lane_disable.py tests/test_capacity.py
  tests/test_config.py`: 724 passed, 1 skipped in ~7 min (session
  record, pre-merge).
- PR #3409 merged as squash commit `873f44a1e6`; the merge-commit file
  list contains exactly the 11 change files. The push-run lint/typecheck
  failure in the same window (`resolve_public_runtime` `environ`
  argument) traces to co-merged lane c783935d54 (#3418), not to this
  change; attribution followed the file-list method.
