# Notes — Model-Weight License Scope for Internal Hosting

Supporting evidence for [the main entry](model-weight-license-internal-hosting-scope.md).
This file is not in normal retrieval. It holds source shape and checks, not rules.

## Privacy handling

The source session compared two model releases from one vendor. To keep this note
shareable, this note keeps these items:

- no model name, vendor name, organization name, person, or URL;
- no mirrors, hostnames, internal paths, issue IDs, or environment names;
- no quoted license passages beyond the short generic fragments below.

The generic fragment of the internal-use exemption, as it usually appears:

> "...use that does not make the Software, its outputs, or its underlying
> capabilities available to third parties"

The generic shape of a service-threshold clause, as it usually appears:

> "If the Licensee ... operates a <service type> business, and the aggregate revenue
> ... exceeds <amount> ... over any consecutive 12 months, the Licensee must enter
> into a separate agreement ... before using the Software ... for any commercial purpose."

## Generic term pattern observed

| Element | Shape found |
| --- | --- |
| Opening grant | "deal in the Software without restriction" (wide) |
| Condition 1 | notice retention + comply with applicable law |
| Condition 2 | service-type + revenue threshold → separate agreement |
| Condition 3 | user-count OR monthly-revenue threshold → visible branding |
| Condition 4 | carve-out: internal use; official or certified-partner access |
| Condition 5 | as-is, no warranty, no liability |
| Family difference | branding literal only (model name string) |

## Checks that changed the answer

1. **License file, not the card.** The rendered page and the raw `LICENSE` file gave
   different framing about which terms cover weights against code. The raw file is
   authoritative.
2. **Normalized diff.** The two family licenses were byte-identical except for the
   model-name string in the branding clause. A title-based comparison would have
   reported a false difference.
3. **Definition keying.** The exemption keys on outputs and capabilities, not on
   network reachability. A private endpoint that a customer can call is still a
   third-party exposure.
4. **Exemption scope.** The carve-out removed the threshold and branding clauses only.
   The notice, law, and warranty clauses remained.

## Interpretation limits to report

- "Third party" was not defined in the text. The conservative reading (not the
  licensee or its affiliates) was applied and labelled as an interpretation.
- The card footnotes were empty, so threshold-adjacent claims could not be verified
  further.
- The final answer stated that it is not legal advice and named the published
  license contact for edge cases.

## Verification

- Workflow tested against two live licenses in one session.
- No command in this note was executed with a real vendor path; the Quick Reference
  uses placeholders by design.

## Related entries

- [license-scan-marker-excluded-fallback](../skills/license-scan-marker-excluded-fallback.md)
- [notice-dependency-license-inventory-completeness](../skills/notice-dependency-license-inventory-completeness.md)