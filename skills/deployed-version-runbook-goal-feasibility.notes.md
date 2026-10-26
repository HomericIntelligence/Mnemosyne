# Notes: deployed-version-runbook-goal-feasibility

Privacy-safe session evidence for the skill. The facts below come from the
K2-Horizon BF16 enablement campaign on LLM360/comet M2 prod, October 2026.

## Source engagement

- Campaign issue: LLM360/comet#845 — enable six BF16 K2-Horizon pools
  (0p9b, 3p7b, 7b, 32b, mova-36b-a4b, 375b-a23b) on M2 prod.
- Deployed release at the time: tag v0.2.3, commit `69db2296`.
- The campaign lead posted a seal runbook on #845 keyed to v0.2.3. Each
  step had been validated against the live deployment: offline validation
  READY for all six cookbooks, byte hash of the container image equal to
  the cookbook pin, and pre-positioned checkpoint trees inspected file by
  file. A later audit showed the terminal seal operation was impossible on
  v0.2.3 and posted a correction
  (issuecomment-6378870570) and a pointer (issuecomment-6379449364) on the
  same issue.

## The version gate

- On v0.2.3, the seal path of the operator service
  (`perform_after_active_publisher_license_acceptance`) is wired to
  `_UnavailableIndependentAnchorVerifier`. Each seal attempt fails with the
  fixed error text: "The independent K2 source anchor is unavailable".
- The real independent anchor implementation ships in commit `4c075ccd`
  (PR LLM360/comet#2841). At the time of writing, that change was not in
  the deployed release. It travelled in promotion PR LLM360/comet#2951
  (main → prod, 16-commit delta).

## Decision changes the gate caused

- Order reversal: the promotion became a hard precondition for all six
  seals. Earlier plans had seals preceding or interleaved with promotion.
- The published v0.2.3 runbook received a same-day correction comment; the
  validated steps were retained as the post-promotion sequence.
- The 375B checkpoint (706 GiB, 76 files) was staged outside the service
  lane — a Slurm download-and-verify job into user staging — because no
  accepted K2 staging path exists on v0.2.3. The service account performs a
  same-filesystem move into the model store after promotion.
- Related failure analysis published as a comment on PR #2951
  (issuecomment-6380737507) and on #2851 (issuecomment-6380737806); the
  final sealing steps were delegated to the service account in issue #2953.

## Reusable observations

- Step-level validation produced strong evidence (READY verdicts, hash
  equality, file manifests) and still said nothing about goal reachability.
  The two checks measure different properties.
- The refusal was one placeholder class. Its name
  (`_UnavailableIndependentAnchorVerifier`) and its fixed error string made
  the version gate easy to detect at the deployed ref with a code read
  alone — no cluster access was needed.
- Comparing with `main` was useful exactly once: to identify the carrying
  change (`4c075ccd` / #2841) and its promotion vehicle (#2951). All other
  `main`-side behavior was irrelevant to the deployed capability.
- The correction cost was one comment cycle plus a re-sequenced campaign.
  The avoided cost was six failed service-account seal attempts against an
  incapable release, each of which would have looked like a data defect.
