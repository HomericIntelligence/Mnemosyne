# Notes: Mint Test Evidence Through the Compared Authority

Supporting measurements and environment detail for the main entry. These notes are
not part of normal retrieval.

## Verification environment

- A shared-filesystem development host whose process euid differs from the
  hosted-runner default uid 1001.
- CI-like masked runs: deployment credential environment variables unset and the
  proprietary scheduler client binaries masked out of `PATH`, which reproduces
  the hosted-runner conditions on the development host.
- Unmasked runs: the plain host shell environment.
- Pristine runs: the same tree with the proposed change removed (`git stash`).

## Measurements

- Target module (89 nodes, about 440 seconds per full run):
  - Pristine, masked: 12 failed, 77 passed. Error shapes: 6 ownership-drift
    rejections at the identity comparison, 5 foreign-evidence rejections at a
    second guard, 1 capacity-limit error downstream of a rejected terminal
    record.
  - Patched (local helper mints the owner through the resolver at call time),
    masked: the 12 previously failing nodes pass in 69 seconds; full module
    sweep 89 passed in 430 seconds; the 3 pinned-suite regression probes pass.
- Attempted shared-factory change (reverted): 75 failures across three modules
  that pin the resolver to the constant; the same representative nodes pass
  pristine. First cause recorded before the re-run, per the repository
  discipline.
- Independent reviewer spot-check on the divergent host: 4 of the 12 fixed
  nodes pass (22.8 seconds); the reviewer also confirmed that deliberate-drift
  tests differ through fields other than the owner (generation, state, end
  time, context id) and do not rely on the constant default.
- ruff check and ruff format --check pass on the changed file.

## Authority chain (generalized)

- The product identity comparison resolves the registered service principal
  through the principal database (`pwd.getpwnam` shape) and rejects on owner
  drift when the observed owner differs.
- The session-wide test fixture remaps that lookup to the process euid for the
  service account, so the authority follows the host.
- The shared evidence factory defaulted the owner to 1001, which equals the
  hosted-runner euid and nothing else.
- Three sibling modules pin the resolver function itself to uid 1001 through
  `monkeypatch.setattr` on the module attribute; evidence for those suites must
  keep the 1001 default.
- The accepted fix passes an explicit owner from the local helper of the
  affected module, minted as
  `authority_module.resolve_identity(context.spec.service_principal).uid`, so
  pinned, session-remapped, and live resolvers each stay authoritative for
  their own suites.
