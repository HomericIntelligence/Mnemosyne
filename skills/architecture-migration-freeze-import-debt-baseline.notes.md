# Freeze Partial-Migration Import Debt - Notes

Supporting evidence for `architecture-migration-freeze-import-debt-baseline.md`.
These notes are not retrieved as guidance.

## Provenance

| Item | Value |
| ---- | ----- |
| Initial capture | 2026-07-20, planning and review session for a provider-runtime migration; no implementation, tests, or CI observed. |
| Amendment | 2026-11-01, review of a structural-debt change in an isolated checkout. |
| Amendment | 2026-11-04, read-only planning session for a product-layer-to-library move. |

## Amendment example: retract an upward edge

Context:

- A lower (service/runtime) module imported an upper (command-layer) module at
  function scope to run a group of job-submission actions.
- A layer-policy file listed the permitted upward import edges.
- A boundary test compared the observed edges with that list by exact
  equality, and counted package `__init__` re-exports as edges.

Change shape:

1. A new lower module took ownership of the job-submission action group.
2. The upper module kept its own handlers and called the new lower module.
3. The policy file lost the upward edge in the same commit.
4. The old upper module did not re-export the moved actions. Tests that
   patched the old import site now patch the new module.

Why the re-export variant is weaker:

- A forwarding import in the old module is a new edge. The guard accepts it
  only when it is recorded, and it delays the retirement of each consumer.
- If the export is added to a package `__init__` that the guard counts as a
  module, the guard reports a new edge and fails the policy check.

## Amendment example: move a unit from the upper layer to the lower layer

Context:

- An issue asked to move three provider-runtime modules from an opt-in
  product layer into a library subpackage.
- The issue stated that the three modules have no product-layer imports. The
  statement was true for two modules.
- The third module imported its product-layer configuration owner for model
  selection, a generic timeout, and deterministic session identity.
- The third module also imported a product-layer alias module. That alias
  assigned `sys.modules[name] = implementation`, so it was the same module
  object as a library module.

Change shape:

1. A new library module took ownership of the cohesive session, model, and
   timeout family that the moved module needs.
2. The product-layer configuration owner re-exported those symbols because ten
   product-layer consumers still import it.
3. The moved module imported the library module directly, because the library
   boundary guard rejects a re-export of the product layer.
4. The alias import was replaced with a direct import of the library module.
   The module-scoped patches that resolve through the alias kept working, so
   they needed no retarget.
5. A path that used `parents[1]` to reach a sibling subpackage stayed correct,
   because both layers sit one level below the package root. The plan stated
   this check instead of assuming it.

Why the direction of the re-export matters:

- An upper module that imports a lower unit keeps that edge. The edge is
  recorded debt, and the guard continues to see it.
- A lower module cannot keep a re-export of its old upper home. The boundary
  guard rejects it, so the moved module must not forward.

## Amendment 2026-11-04: enumeration of test derivers after a move

Context:

- An issue plan retired three allowlisted upward import edges by moving a
  cohesive action group into a new lower module, lowering one lifecycle
  constant family to a service module, and injecting one command executor
  into a service constructor.
- The plan listed a test-update step and stated that all existing stubs
  already absorb the added argument.
- The plan listed five focused test commands.

Findings from a read-only plan review:

| Class | Evidence pattern | Plan gap |
|-------|------------------|----------|
| Narrow stub | A test imported the upper module and stubbed the moved function with a lambda that names exactly the old parameters | The added parameter raises `TypeError` at call time |
| Removed import | A test imported the moved helper from the upper module at module scope | The import fails once the symbol leaves that module |
| Removed attribute patch | A test patched the moved helper as an attribute of the upper module | The patch target fails with `AttributeError` |
| Direct construction | A test builds the service directly and asserts success on the action that the new default fails closed | The default turns a passing test into a `PermissionError` |

Decision rule derived:

1. Search `tests/` for each moved symbol name and each old module path.
2. Group the hits by file.
3. Read each stub signature.
4. Add every file to the focused test command.
5. Keep the fail-closed default only when every direct construction is fixed in
   the same change, or choose a default that preserves the current branch.

The moved-symbol work itself follows the existing retirement and retarget
rules. This amendment therefore extends the canonical entry instead of adding
an entry.

## Discovery limits of this amendment

- The advise helper listed the corpus from the resolved checkout. The open-PR
  query returned one open pull request, and it changed an unrelated entry.
- No implementation, test run, or CI was observed. This branch comes from
  read-only plan inspection.

## Discovery limits of the 2026-07-20 and 2026-11-01 amendments

- The advise helper was not installed in the 2026-07-20 session environment.
  Duplicate discovery used a direct regular-file listing of the resolved
  knowledge checkout, `skills/*.md`, with notes and history companions
  excluded.
- Open pull requests were checked with a read-only forge query against the
  resolved delivery revision. No open pull request changed the selected
  canonical entry.
- CI for the reviewed source change was not observed. The retirement rules are
  generalized from the reviewed diff, not from a green pipeline.
