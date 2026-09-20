---
name: valuation-private-securities-platform-data-beats-web-research
license: BSD-3-Clause
description: "Reconcile private-security quantities, exercise status, and dated valuation records across platform exports, executed documents, and issuer updates."
category: documentation
date: 2026-06-12
version: "1.2.0"
user-invocable: false
verification: verified-local
history: valuation-private-securities-platform-data-beats-web-research.history
tags:
  - private-securities
  - crowdfunding
  - reg-cf
  - startengine
  - valuation
  - due-diligence
  - fl-142
  - divorce-disclosure
  - platform-data
  - web-research
  - investor-platform-primary-source
  - form-3921
  - vesting-decomposition
  - schedule-of-purchasers
  - safe-conversion
  - no-409a
---

# Reconcile Private-Security Records Across Sources

## Overview

| Field | Value |
|---|---|
| Date | 2026-06-12 |
| Objective | Reconcile private-security records without confusing quantities, exercise status, and dated valuation marks. |
| Outcome | The recorded reconciliation found gaps in both platform records and document archives. Personal holdings and legal-case details are omitted. |
| Verification | verified-local; the historical observation does not establish a current valuation or a legal reporting method. |
| History | [changelog](./valuation-private-securities-platform-data-beats-web-research.history) |

## When to Use

- A platform export disagrees with a working paper about shares, vesting, or exercise status.
- Executed investment documents and later platform adjustments need reconciliation.
- A displayed valuation mark may predate an issuer update, insolvency, or wind-down.
- A proposed total has no supporting document and may instead describe vested shares.

## Verified Workflow

### Quick Reference

Compare quantities and status with dated primary records. Keep acquisition cost, share count,
vested quantity, and valuation marks as separate fields. Explain unresolved differences and
continue researching independent positions when one source is unavailable.

### Source reconciliation

1. Gather available authorized exports, executed agreements, exercise records, and issuer
   communications. A platform snapshot often fills archive gaps, but need not precede all research.
2. Identify the security class, effective date, and meaning of each quantity. An apparent total
   can instead be the vested fraction of a grant. Compare it with the vesting schedule and
   executed records; arithmetic is a clue, not proof.
3. For conversion tables, distinguish converted securities from new cash purchases using the
   agreement's actual definitions. `pdftotext -layout` can help preserve table columns.
4. Compare platform status with dated issuer statements and relevant public records. A platform
   can show an old positive mark after its communications describe a wind-down.
5. Resolve discrepancies from record authority, dates, and transaction definitions instead of
   assigning automatic precedence to one source type. Preserve the source and uncertainty for
   each conclusion.
6. Select direct research or independent assignments according to the number and complexity of
   positions. Match issuer identity carefully when names are similar.

For a requested filing or valuation, identify the applicable basis separately. Platform marks,
round prices, tax records, and acquisition cost are different facts; this reconciliation procedure
does not make them interchangeable or determine the required reporting treatment.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
|---|---|---|---|
| Public research alone | Reconstructed quantities from public financing information | Later account adjustments were absent from public records | Compare available account records and transaction documents. |
| Platform mark alone | Accepted a displayed positive value | A later issuer update described a wind-down | Compare mark dates with issuer events. |
| Combined issuer research | Researched several similarly named entities together | Entity identities became confused | Keep issuer identity and supporting records distinct. |
| Unsupported total | Treated a working-paper figure as total shares | The figure described vesting instead | Compare quantity definitions and grant schedules. |
| Archive absence | Inferred an option was unexercised from a missing document | Platform records showed an exercise | Missing archive evidence does not prove non-occurrence. |

## Results & Parameters

Useful reconciliation fields are issuer identity, security class, source date, grant quantity,
vested quantity, exercised quantity, holdings quantity, acquisition cost, mark date, and source
reference. Keep private exports and account identifiers in their authorized storage location.

The original sessions supplied local evidence that platform exports can reveal missing positions
and that platform marks can lag issuer communications. Personal amounts and case identifiers are
omitted. No new research, valuation, or verification is claimed by this generalized edition.
