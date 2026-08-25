---
name: validation-workflow
license: BSD-3-Clause
description: When you configure GitHub Actions, use this skill to validate flat Mnemosyne skill files. Before you contribute a skill, use this skill to run checks.
user-invocable: false
---

# Skill Validation Workflow

Use this workflow to validate the Mnemosyne skill corpus. Mnemosyne does not
generate or publish a plugin marketplace.

Write all new or changed active technical prose according to the
[Mnemosyne ASD-STE100 writing policy](../../../../../docs/asd-ste100.md).

## Overview

| Item | Details |
| ------ | --------- |
| Date | 2026-08-25 |
| Objective | Validate flat skill files and the shared parser |
| Outcome | Invalid corpus changes fail before merge |

## When to Use

- Configure CI for the Mnemosyne skill corpus.
- Validate a new or changed flat skill file.
- Check required frontmatter and Markdown sections.
- Before a pull request, run the repository tests.

## Verified Workflow

### Quick Reference

Run the complete local check:

```bash
just check
```

When you investigate a failure, run the two parts separately:

```bash
just validate
just test
```

### 1. Validate Active Skill Files

Run this command:

```bash
uv run python scripts/validate_plugins.py
```

The validator reads flat main skill files in `skills/`. It excludes raw notes
and history files. It checks these requirements:

- Required YAML frontmatter fields.
- Approved categories and field formats.
- Required Markdown sections.
- The Failed Attempts table.
- The Quick Reference heading level.

### 2. Run the Test Suite

Run this command:

```bash
uv run python -m pytest tests/
```

The tests cover the validator, schema, release contract, and shared parser.

### 3. Use the Repository CI Workflows

The required workflow runs structural, test, lint, schema, security, package,
and release-contract checks. The advisory validation workflow runs additional
skill and Python checks. Neither workflow creates a marketplace index.

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| No pull request validation | Accepted invalid skill files | Errors reached the default branch | Before merge, validate the files |
| Manual frontmatter review | Relied only on reviewer inspection | Reviewers missed structural errors | Use the parser and schema checks |
| Optional failures section | Allowed skills without failure evidence | The most reusable diagnostic facts were absent | Require the Failed Attempts section |
| Inline shell validation | Used multiple `grep` checks | The checks missed parser edge cases | Use `validate_plugins.py` |
| Marketplace generation | Treated Mnemosyne as a plugin marketplace | Athena owns plugin distribution | Keep Mnemosyne as the skill corpus |

## Results & Parameters

```yaml
validation:
  target: "skills/*.md"
  excluded_evidence:
    - "skills/*.notes*.md"
    - "skills/*.history*"
  required_frontmatter:
    - name
    - description
    - category
    - date
    - version
  required_sections:
    - "## Overview"
    - "## When to Use"
    - "## Verified Workflow"
    - "## Failed Attempts"
    - "## Results & Parameters"

commands:
  validate: "uv run python scripts/validate_plugins.py"
  test: "uv run python -m pytest tests/"
  complete: "just check"
```

## References

- [Contributor validation](../../../../../CONTRIBUTING.md#validation)
- [Required checks workflow](../../../../../.github/workflows/_required.yml)
- [Advisory validation workflow](../../../../../.github/workflows/validate-plugins.yml)
