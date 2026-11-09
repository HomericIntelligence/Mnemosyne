# Notes: Public Client Without Environment Selectors

Supporting evidence for
[`public-client-resolve-without-environment`](public-client-resolve-without-environment.md).
This file is not part of normal retrieval. Read it when you need the exact commands, the failure
text, or the case list.

## Source

- One implementation lane of an operator-service repository.
- The change removed a documented public selector environment variable and the rendered-identity
  exports from the public client path.
- One commit changed 14 files: 3 source modules, 5 documents including 1 new reference page, and
  6 test files.

## Client selection function (after the change)

Signature:

```python
def resolve_public_runtime(
    *,
    explicit_path: Path | None = None,
    code_path: Path | None = None,
    contexts_dir: Path = DEPLOYMENT_CONTEXTS_DIR,
) -> PublicRuntime:
```

Behavior that matters for review:

- The `environ` parameter is gone.
- The function passes `environ={}` to `registry.resolve`. The registry therefore reads no selector.
- An auto-resolved selection also runs the default gateway link check. An explicit selection does
  not. This keeps the earlier contract for explicit selection.

## Auto-resolution helper

Decision order:

1. Candidates: registered entries with the production lane, the canonical purpose, and a root
   directory that exists on this host.
2. More than one candidate: keep the entries whose root is an ancestor of the resolved running
   code path. An installed client always lives below its root.
3. Exactly one candidate: return it.
4. All other cases: raise one `ValueError` with the sorted candidate identifiers and the
   `--deployment-context` remedy.

The error lists the step-1 candidates, not the post-tie-break set. One plan test requires both
identifiers in the message when both roots hold.

## Test design

The resolution tests stub only two registry attributes:

```python
def _read_only_registry(public_context, monkeypatch, *entries):
    def resolve(*, explicit_path, environ):
        assert environ == {}, "public resolution must not pass the environment to the registry"
        return next(entry.spec for entry in entries if entry.path == explicit_path)

    registry = SimpleNamespace(entries=entries, resolve=resolve)
    monkeypatch.setattr(public_context.DeploymentContextRegistry, "load", lambda _path: registry)
```

The `assert environ == {}` line makes the invariant empirical. The loader receives no values.

Hostile inputs used by the parametrized cases:

| Case | Input |
| --- | --- |
| `unknown-deployment-id` | A selector for a target that does not exist |
| `empty-deployment-id` | An empty selector value |
| `other-deployment-id` | A selector for another registered target |
| `other-context-file` | An explicit path to another context file, in the environment |
| `unknown-cluster` | An unknown cluster name |
| `wrong-root` | A root path that is not the target root |
| `administrative-root` | An administrative root path |
| `development-root` | A development root path |
| `stale-rendered-set` | A complete identity set with stale values |
| `partial-rendered-set` | Two identity variables only |

Each case runs two tests: one with no explicit selection, one with an explicit selection. Both
must resolve the canonical target.

## Service boundary

The rendered-identity completeness check stays for service startup. Only its message changed. It
now names the offending variables and gives the interactive unset remedy. The selector conflict
guard and the empty-value guard stay at the registry level, with their tests. They are no longer
reachable from the public path, and the commit states that as a superseded criterion.

## Caller error split

| Failure class | Caller message |
| --- | --- |
| Selection failure (`ValueError`) | Explicit-selection remedy, such as `--deployment-context` |
| Record or publication failure (`OSError`) | Operator publication advice |

## Commands and results

Run from the worktree, with the project's locked environment.

```bash
# Red phase before the change: the new cases failed.
# Green phase after the change: all new behavior cases pass.
uv run --locked --extra dev pytest tests/test_flat_discovery.py \
  tests/test_deployment_context.py::test_registry_resolves_only_exact_and_consistent_selectors \
  tests/test_deployment_context.py::test_registered_id_conflict_precedes_release_read \
  tests/test_deployment_context.py::test_auto_detection_no_match_keeps_selector_error \
  tests/test_deployment_context.py::test_explicit_selector_overrides_auto_detection \
  tests/test_deployment_context.py::test_partial_rendered_identity_precedes_release_read \
  tests/test_source_runtime.py::test_source_rendered_environment_requires_full_runtime \
  tests/test_sdk.py::test_public_discovery_does_not_open_the_administrative_locator \
  tests/test_sdk.py::test_base_url_from_gateway_json \
  tests/test_sdk_credential_publication.py -q
# Result: 233 passed.

uv run --locked --extra dev ruff check <changed paths>          # all checks passed
uv run --locked --extra dev ruff format --check <changed paths> # all files formatted
uv run --locked --extra dev ty check <changed paths>           # all checks passed
```

Use `uv run --locked --extra dev` for a plain `uv run` invocation. Without the extra and the lock, a
host environment can supply a different test runner and a different package install.

## Fixture consolidation

Four test call sites passed a stub environment mapping to the selection function. After the
parameter removal, they call the function directly. The publish helper that two test files used
moved into the shared discovery test module, and both files import it from there.

## Limits

- One repository and one session. The numbers above are local evidence.
- The plan verification run used the repository's own test selection. Continuous integration was
  not part of the local evidence.