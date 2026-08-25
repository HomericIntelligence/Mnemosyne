# Contributing to Mnemosyne

This guide explains how to contribute skills to Mnemosyne. It also gives the
quality requirements and the pull request process.

## Table of Contents

- [How to Contribute a Skill](#how-to-contribute-a-skill)
- [Skill Structure](#skill-structure)
- [Quality Standards](#quality-standards)
- [Categories](#categories)
- [Branch and Commit Conventions](#branch-and-commit-conventions)
- [Pull Request Process](#pull-request-process)
- [Validation](#validation)
- [Code Style](#code-style)
- [Cross-Repository Compatibility](#cross-repository-compatibility)
- [Releasing](#releasing)

## How to Contribute a Skill

### Option 1: Automatic via `/learn` (Recommended)

Athena owns the `/learn` workflow. Mnemosyne does not copy its skill
instructions.

1. Install Athena through the coding harness plugin mechanism.
2. After a session contains verified knowledge, run `/learn`.
3. Follow the installed Athena skill.
4. Review the pull request.
5. Merge the pull request.

### Option 2: Manual Creation

1. Copy `templates/skill-template.md`.
2. Save as `skills/<name>.md` (lowercase, kebab-case).
3. Complete the YAML frontmatter. See [Skill Structure](#skill-structure).
4. Complete all required Markdown sections.
5. You can create `skills/<name>.notes.md` for raw session details.
6. Create a pull request. Follow the
   [branch conventions](#branch-and-commit-conventions).

## Skill Structure

Each skill is a flat Markdown file in `skills/`. Each file has YAML
frontmatter.

```text
skills/<name>.md             # Main skill file with YAML frontmatter + markdown content
skills/<name>.notes.md       # (Optional) Additional context from development session
skills/<name>.history        # Version/provenance archive for /learn writes
```

Keep each retrievable main skill at or below 30,000 bytes. Put reusable triggers,
decision rules, and short failure patterns in the main skill. Keep no more than
three examples that cover different decisions. Before an amendment replaces the
main skill, archive its complete prior content in `.history`.

Put raw session details and project-specific paths in `.notes.md`. Also put long
examples, command transcripts, and verification reports in `.notes.md`. Put
prior versions, change summaries, provenance, and version-control narratives in
`.history`. In the frontmatter, keep only the current `version` identifier.
Athena excludes both companion types from normal retrieval.

### Required YAML Frontmatter

```yaml
---
name: skill-name-here
description: "When a specific condition occurs, use this skill. When another condition occurs, use it again."
category: training
date: 2026-03-24
version: "1.0.0"
user-invocable: false
tags: [optional, searchable, keywords]
---
```

| Field | Description |
| ------- | ------------- |
| `name` | Lowercase, kebab-case identifier |
| `description` | Trigger conditions with specific use cases |
| `category` | One of the 9 approved categories (see below) |
| `date` | Creation date (YYYY-MM-DD) |
| `version` | Semantic version such as `1.0.0` |
| `user-invocable` | Set to `false` for internal/sub-skills |
| `tags` | (Optional) Searchable keywords array |

### Required Markdown Sections

Each skill must contain these sections:

1. **Overview table** -- Date, objective, outcome.
2. **When to Use** -- Specific trigger conditions.
3. **Verified Workflow** -- Give the steps that worked. Include a Quick
   Reference subsection.
4. **Failed Attempts table (REQUIRED)** -- Include these columns: Attempt, What
   Was Tried, Why It Failed, and Lesson Learned.
5. **Results & Parameters** -- Give configurations that users can copy and use.
   Give the expected outputs.

### Filename Convention

```
<topic>-<subtopic>-<short-4-word-summary>.md
```

Use lowercase kebab-case. For example:

- `mojo-parametric-dtype-migration.md`
- `docker-pixi-isolation.md`
- `batch-subprocess-signal-hang.md`

## Quality Standards

1. **Specific descriptions**: Include trigger conditions. Do not use vague
   summaries. State when to use the skill.
2. **Failures required**: Record each method that did not work. Explain why it
   did not work. The Failed Attempts table is mandatory.
3. **Ready to use**: Parameters, configurations, and commands must work when
   users copy them.
4. **No duplication**: Link to external documents. Do not copy their content.
   If a skill overlaps an existing skill, extend the existing skill.
5. **Bounded retrieval**: Keep `skills/<name>.md` at or below 30,000 bytes.
   Keep concise reusable guidance in the main skill. Keep no more than three
   examples that cover different decisions. Put session evidence in the notes
   file. Put prior versions and version-control records in the history file.

## Categories

| Category | Description |
| ---------- | ------------- |
| `training` | ML training experiments and hyperparameters |
| `evaluation` | Model evaluation and metrics |
| `optimization` | Performance tuning and speedups |
| `debugging` | Bug investigation and fixes |
| `architecture` | Design decisions and patterns |
| `tooling` | Automation and developer tools |
| `ci-cd` | Pipeline configurations and CI fixes |
| `testing` | Test strategies and patterns |
| `documentation` | Paper writing, academic reviews, knowledge docs |

## Branch and Commit Conventions

### Branch Naming

- **Skills (automatic)**: `skill/<name>`, such as `skill/mojo-parametric-dtype-migration`
- **Fixes**: `fix/<issue-number>-<short-description>`, such as `fix/913-contributing-changelog`
- **Features**: `feat/<short-description>`.

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <short description>

[optional body]

[optional footer]
```

Use these common types:

- `feat:` -- New skill or feature
- `fix:` -- Bug fix or correction
- `docs:` -- Documentation changes
- `chore:` -- Maintenance tasks

For example:

```
feat: add mojo-parametric-dtype-migration skill
fix: resolve skill validation issues and missing frontmatter fields
docs: update migration status - 100% complete
```

## Pull Request Process

1. Create a branch following the naming conventions above.
2. Make the required changes.
3. Before you push, run local validation. See [Validation](#validation).
4. Push your branch.
5. Create a pull request.
6. Let CI validate these requirements:
   - YAML frontmatter has required fields.
   - All required markdown sections are present.
   - Failed Attempts section exists.
   - The description field is present.
   - Category is valid.
7. Confirm that the description has specific trigger conditions.
8. After CI passes and reviewers approve the pull request, maintainers can
   merge it.

### Merge queue readiness

The required-check workflow supports GitHub merge groups. Odysseus owns the
separate queue-activation operation. Read
[`docs/ci/merge-queue.md`](docs/ci/merge-queue.md) for the policy and trigger
boundaries. It also gives the post-merge evidence for issue #3115. Auto-merge
does not prove that a pull request entered the queue.

## Validation

CI validates all pull requests. Before you submit a pull request, run local
validation:

```bash
python3 scripts/validate_plugins.py
```

The validator does these checks:

- Confirms the required frontmatter fields
- Confirms all required Markdown sections
- Confirms the Failed Attempts table
- Confirms the description field
- Confirms one of the nine approved categories
- Enforces the 30,000-byte main skill limit
- Excludes notes and history files.

Authors and reviewers must confirm that each description has specific trigger
conditions.

## Code Style

### Technical prose

All active technical prose must follow the
[ASD-STE100 writing policy](docs/asd-ste100.md). Use short sentences and active
voice. Do not use contractions or semicolons. Preserve commands, identifiers,
facts, legal text, and quoted text.

### Markdown

- Use ATX-style headers (`#`, `##`, `###`).
- Use fenced code blocks with language identifiers, such as ` ```bash` and ` ```yaml`.
- Use tables for structured data (overview, failed attempts, verified-on).
- Keep lines readable. There is no strict line-length limit.

### YAML Frontmatter

- Use lowercase kebab-case for the `name` field.
- Quote string values that contain special characters.
- Use arrays for `tags`.

### General Principles

This project follows these development principles:

- **KISS**: Keep it simple. Do not add complexity when a simpler solution works.
- **YAGNI**: Do not add features until they are required.
- **DRY**: Do not duplicate functionality, data structures, or algorithms.
- **POLA**: Create intuitive and predictable interfaces.

## Cross-Repository Compatibility

Write skills that can work in multiple repositories:

1. **No `source:` in frontmatter** -- Do not include repository-specific source
   fields.
2. **Use placeholders** -- Replace hardcoded paths with `<project-root>`,
   `<test-path>`, and `<package-manager>`.
3. **Add a "Verified On" section** -- Record where you validated the skill:
   ```markdown
   ## Verified On

   | Project | Context | Details |
   |---------|---------|---------|
   | ProjectName | PR #XXX context | [notes.md](./skill-name.notes.md) |
   ```
4. **Move specifics to companions** -- Put project-specific commands, paths,
   transcripts, and verification details in `.notes.md`. Put version and
   provenance records in `.history`.
5. **Generic workflows** -- Write workflows that users can adapt to each
   repository structure.

## Releasing

Maintainers release the skill corpus as a tagged snapshot. `pyproject.toml`
`[project].version` is the single source of truth.

1. Bump the version in `pyproject.toml`.
2. Add a matching `## [X.Y.Z] - YYYY-MM-DD` entry at the top of `CHANGELOG.md`.
3. Merge the pull request. The `release` CI check runs
   `scripts/validate_release_contract.py` in dry-run mode on every pull request
   and every push to `main`.
4. Create the `vX.Y.Z` tag.
5. Push the tag. `.github/workflows/release.yml` validates the contract against
   the tag.
6. The workflow publishes a GitHub Release. The release contains the corpus
   snapshot and the changelog entry.
