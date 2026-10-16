# Notes: Verify the Issue Premise Against the Code Before Planning

Supporting evidence for `verify-issue-premise-against-code-before-planning.md`, from the
v1.3.0 session (2026-10-16). Host paths, repository and model names, and issue and pull
request identifiers are omitted; substitute site values.

## The v1.3.0 source case

A tracked issue asked to flip one serving-parallelism value from 16 to 8 in ONE named config
profile. The issue listed the assertion sites to update and claimed the value "does not
participate in the fast-start identity", implying no identity pins needed re-derivation.

### What the issue's prose got wrong at the current default branch

| Issue claim | Reality at the current default branch |
| ----------- | ------------------------------------- |
| Cited test file and line numbers for the pins | Drifted — the same contract shape now lives ~150 lines earlier in the same file |
| The value does not participate in the derived identity | FALSE at the current default branch — the identity input includes the value; both identity digests change when the value flips (confirmed by direct computation, not by reading prose) |
| Implied complete site list | Incomplete — only the value's literal flag/key form was named |

### The enumeration miss and how the suite closed it

- The first audit grepped only the value's literal forms: `ep: 16`, `"ep": 16`,
  `--ep-size 16`. That surface was clean after the intended edits.
- The missed surfaces, found later:
  - a bare topology tuple `(..., 16, 2)` in a parametrized serving-profiles test;
  - a field assertion `.ep == 16` in an acceptance test;
  - two sha256 identity digests (a digest contains no decimal `16`) pinned in an
    identity-stability test.
- The first full suite run after the change was summarized with `tail -3`: the truncated
  summary destroyed the failing-node list, which forced a 45-minute re-run. Second run used
  full-fidelity capture (`-rf` short summary + `tee` to a log file) and extracted the exact
  failing node IDs.

### The recorded base control

| Run | Scope | Result |
| --- | ----- | ------ |
| Suite with the change applied | 12 affected modules + the full render module | 61 failing node IDs across the affected modules; 378 passed / 5 failed in the render module |
| Base control: change stashed, IDENTICAL 58 suspect-environmental node IDs on the unmodified base commit | same node list | 58/58 failed identically on base → proven PRE-EXISTING host-environment failures |
| Change-only remainder of the 61 | — | exactly 3 nodes: the tuple pin, the identity-digest pin (one test asserting both digests), the acceptance field assert → the missed binding sites |
| Render module classification | full module | 4 of 5 failures environmental (path/trust-ancestor assertions under a network mount); 1 change-only: the topology-contract pin |

Environment fact (host facts probed during the session): home and tmp resolve under a
network-mounted shared filesystem on this host; assertions that expect a non-mounted
scratch path fail for any change, including no change. See
`testing-shared-host-env-pinning-and-baseline` for the general pinning discipline.

### Closure

- The 4 pins were re-derived from the new value and updated; the identity digests were
  recomputed by invoking the identity function on the rendered pre-old and post-change
  payloads, not guessed.
- Local verification: 533 tests passed across the config and acceptance modules; the render
  module at 378 passed / 5 classified. Static gates (format, lint, type check) green.
- One suspect failure that passed when re-run ALONE with the change was recorded as a
  load-dependent flake, not a regression.
- Upstream CI was pending at write time.
