---
name: "approved-plan-mnemosyne-3379-2c3e8171d469"
description: "Use when implementing the approved plan from HomericIntelligence/Mnemosyne#3379."
category: "tooling"
date: "2026-09-08"
version: "1.0.0"
user-invocable: false
verification: "production-host"
tags: [automation, learning, mnemosyne]
---

# Approved implementation plan learning for #3379

## Overview

Use when implementing the approved plan from HomericIntelligence/Mnemosyne#3379.

## When to Use

Use this learning when the same repository workflow, constraint, or failure mode recurs.

## Verified Workflow

### Objective

    Remove the completed ecosystem skill migration utility and its dedicated tests. Keep the current `/learn` and skill-template workflows for new contributions. Do not add a replacement importer or change active guidance.

### Approach

    - Delete the migration utility at `scripts/migrate_ecosystem_skills.py:1-664`. `MIGRATION_STATUS.md:3-11` states that the flat-file migration is complete.
    - Delete the dedicated test module at `tests/test_migrate_ecosystem_skills.py:1-1165`. Its imports and fixtures test only the removed utility.
    - Do not change dependencies. PyYAML remains in use by `scripts/mnemosyne_skill_utils.py:13-37` and `tests/test_merge_queue.py:10-80`.
    - Do not change contributor documentation. `CONTRIBUTING.md:19-40`, `AGENTS.md:179-181`, and `README.md:82-88` already direct contributors to `/learn` or `templates/skill-template.md`.
    - Do not change continuous integration (CI) workflows or other active documentation. A repository-wide search at revision `9cdca47d63aad8be9e07318b5cd634b57a6d8024` found the utility name only in the utility and its dedicated test module.
    - Restore both deleted files together if verification finds an undocumented active consumer. Do not add a compatibility shim or replacement importer.
    - The issue evidence names revision `967f6474bb66cbd8b6a1726acf89e49334172875`. This plan uses the later local checkout revision above. It does not include remote issue comments, labels, or changes after that checkout.

### Implementation Order

    1. Delete `scripts/migrate_ecosystem_skills.py` to satisfy the requirement to retire the completed importer.
    2. Delete `tests/test_migrate_ecosystem_skills.py` to remove tests and fixtures that exist only for the importer.
    3. Search the complete active repository for `migrate_ecosystem_skills` and confirm that no CI workflow, documentation, import, fixture, or command refers to it.
    4. Confirm that contributor guidance still specifies `/learn` and `templates/skill-template.md`.
    5. Run the full repository check.

### Verification

    ```bash
    test ! -e scripts/migrate_ecosystem_skills.py && test ! -e tests/test_migrate_ecosystem_skills.py
    # Acceptance criterion 1: the utility and its dedicated tests are removed.
    ```
    
    ```bash
    rg -n '/learn|templates/skill-template\.md' CONTRIBUTING.md AGENTS.md README.md
    # Acceptance criterion 2: contributor guidance continues to specify /learn or the skill template.
    ```
    
    ```bash
    ! rg -n --hidden --glob '!.git/**' --glob '!build/**' 'migrate_ecosystem_skills(\.py)?' .
    # Acceptance criterion 3: no active CI workflow, documentation, source file, or test refers to the removed utility.
    ```
    
    ```bash
    just check
    # Acceptance criterion 4: repository validation and the full test suite pass.
    ```

### Changes from Review

    _N/A — initial plan_

## Failed Attempts

No failed attempt is asserted beyond the bounded source material above.

## Results & Parameters

- Source repository: `HomericIntelligence/Mnemosyne`
- Issue: `#3379`
- Canonical plan revision: `1`
- Canonical comment database ID: `5579594845`
- Plan fingerprint: `282932125a46d1d39b6c3d10d8bea9c59db1d2de794ae2de1547cbdacda1ec8a`

## Verified On

Prepared by the provider-neutral Mnemosyne host boundary.
