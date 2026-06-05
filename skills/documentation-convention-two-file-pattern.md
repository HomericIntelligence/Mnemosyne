---
name: documentation-convention-two-file-pattern
description: 'Document undocumented conventions using README section + source-code intent comment with cross-references. Use when fixing NITPICK-level doc gaps for features that affect user experience (pip install, API behavior, config structure).'
category: documentation
date: 2026-06-05
version: 1.0.0
user-invocable: true
verification: verified-ci
tags:
  - documentation
  - convention
  - readme
  - source-code-intent
  - cross-reference
  - user-experience
---

# Documentation Convention: Two-File Pattern

## Overview

| Field | Value |
| ------- | ------- |
| Date | 2026-06-05 |
| Category | documentation |
| Objective | Document undocumented conventions affecting user experience using README + source intent comment pattern |
| Verification | verified-ci (issue #786) |
| Theme | NITPICK-level doc gaps for features with user impact (pip install extras, API behavior, config structure) |

## When to Use

Use this skill when:

1. **Identifying undocumented conventions**: A feature exists but its behavior/intent is not documented
2. **User-impacting features**: The convention affects how users interact with the software (e.g., `pip install` extras, config behavior, API contracts)
3. **NITPICK-level doc gap**: The feature works correctly; only its documentation is missing
4. **Affecting multiple files**: The convention spans configuration, documentation, and implementation

**Example triggers**:
- `[all]` pip extra excludes `[dev]` (not documented; users need to know this for dependency isolation)
- Configuration section behavior (e.g., how sections interact or override each other)
- API contracts (e.g., function behavior that differs from similar functions)
- Dependency resolution rules (e.g., what gets installed with certain flags)

## Verified Workflow

### Phase 1: Identify the Convention

1. **Find the source code** implementing the convention
   - Look for comments, logic branches, or config parsing
   - Note the exact lines and file path
2. **Trace the user impact**
   - How does this convention affect users?
   - Which docs are missing this context?
   - Are there confusing behaviors without the explanation?

### Phase 2: Add README Documentation

1. **Locate the target README section**
   - Find the section covering the related feature (e.g., Installation, Configuration, API)
   - If no section exists, create one with a clear heading
2. **Write user-facing explanation**
   - Plain language (no code jargon unless necessary)
   - Include concrete examples showing the convention in action
   - Explain the *why* (rationale/design decision)
3. **Add an anchor comment** (markdown HTML comment)
   - Use kebab-case anchor name: `<!-- convention-name -->`
   - Place directly above the section heading or at the start of the explanation

**Example README section** (from issue #786):

```markdown
## Dependency Extras

### All Extras vs Dev Extras

<!-- extras-all-excludes-dev -->

The `[all]` extras group excludes development dependencies (`[dev]`). This is intentional:

- **`[all]`**: Installs all production-ready extras (data processing, ML, API clients, etc.)
  ```bash
  pip install hephaestus[all]
  ```

- **`[dev]`**: Installs development-only tools (testing, linting, documentation)
  ```bash
  pip install hephaestus[dev]
  ```

Users who need both production and development tools should install explicitly:
```bash
pip install hephaestus[all,dev]
```

**Rationale**: This separation allows production deployments to use `[all]` without pulling in large testing frameworks, linters, and doc tools. Development environments can opt in to `[dev]` separately.
```

### Phase 3: Add Source Code Intent Comment

1. **Locate the exact code** implementing the convention
   - Find the configuration, logic, or validation code
   - Note the line numbers
2. **Add an intent comment** at the implementation
   - Format: `# <Descriptive summary> — See <README-anchor>`
   - Reference the README section using the anchor name
   - Keep it concise (1-2 lines)

**Example source comment** (from issue #786, `pyproject.toml`):

```toml
[project.optional-dependencies]
# The [all] group excludes [dev] intentionally — see extras-all-excludes-dev in README
all = [
    "requests>=2.28.0",
    "pydantic>=2.0.0",
    # ... more deps
]

dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",
    # ... more dev tools
]
```

**Example source comment** (from issue #786, `hephaestus/config/loader.py`):

```python
def load_config(path: str, ...) -> ConfigDict:
    """Load configuration from file.
    
    See extras-all-excludes-dev in README for convention documentation.
    """
```

### Phase 4: Verify Cross-References

1. **Check anchor formatting**
   - Markdown anchors use `<!-- kebab-case-name -->`
   - Source comments reference the anchor name (no angle brackets or dashes)
   - Example: README anchor `<!-- extras-all-excludes-dev -->` → comment references `extras-all-excludes-dev`

2. **Verify bidirectional linking**
   - README section includes the anchor comment
   - Source code comments reference the README anchor
   - Both names match exactly

3. **Test the documentation**
   - Build docs locally: `pixi run docs build` (if applicable)
   - Verify links resolve (no broken anchors)
   - Read the documentation as a new user to check clarity

### Quick Reference

#### README Anchor Template

```markdown
<!-- convention-kebab-name -->

## Feature Name

[Plain-language explanation]

**Example**:
[Code block showing the convention]

**Rationale**: [Why this design choice]
```

#### Source Comment Template

```python
# [Descriptive summary] — See <convention-kebab-name> in README
# or
"""[Docstring] — See <convention-kebab-name> in README."""
```

#### Validation Checklist

- [ ] Convention identified and understood (what user behavior does it control?)
- [ ] README section created/updated with user-facing explanation
- [ ] Anchor comment added to README: `<!-- convention-name -->`
- [ ] Source code intent comment added referencing README anchor
- [ ] Anchor names match exactly (kebab-case in both places)
- [ ] Documentation explains *why* (rationale/design decision)
- [ ] Examples provided showing the convention in action
- [ ] Documentation builds without errors
- [ ] New user would understand the convention without source code review

## Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | --------------- |
| N/A | Two-file pattern worked first time | Straightforward approach | Pattern is effective for convention documentation |

## Results & Parameters

### Line Anchors

- **README markdown anchors**: Use HTML comments in kebab-case: `<!-- convention-name -->`
- **Source code comments**: Reference the anchor by name (no angle brackets)
- **Anchor naming**: Must be consistent between README and source comments

### Cross-Reference Format

- **README → Code**: Implicit via anchor location (section explains the code)
- **Code → README**: Explicit via comment: `"See <anchor-name> in README"`
- **Anchor paths**: Use relative references (assume same repo for now)

### Documentation Pattern

1. **README section**: User-facing explanation with examples and rationale
2. **Anchor comment**: Above the section explaining the convention
3. **Source comment**: At implementation, referencing the README anchor
4. **Bidirectional**: Both files aware of the convention, linked by name

## References

- **Origin**: Resolved issue #786 (ProjectHephaestus) — documenting pip extras behavior
- **Related skills**: `documentation-workflow-meta-patterns`, `doc-issue-readme`
- **Standards**: ProjectHephaestus CLAUDE.md documentation rules
- **Verification workflow**: Issue #786, commit `e3ab245`

## Implementation Notes

### When Adding a New Convention

1. Identify the convention by reading code and understanding user impact
2. Add a clear README section (not a subsection of an unrelated topic)
3. Place the HTML anchor comment directly above the heading
4. Add source code intent comment at the implementation location
5. Use consistent kebab-case naming for the anchor
6. Document the rationale (design decision, not just what happens)

### Handling Multiple Conventions

If a feature spans multiple sections:
- Create separate README sections for each distinct convention
- Each section gets its own anchor and intent comment
- Source code can reference multiple anchors if needed
- Keep each convention explanation independent

### Documentation Maintenance

- Review source code comments when making implementation changes
- Update README if the convention changes
- Keep anchor names stable (renaming breaks all references)
- Verify links in documentation builds

