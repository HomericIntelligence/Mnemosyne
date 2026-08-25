# Plugin Standards

Use these standards to create skills in the Mnemosyne skills and session-memory
store. Also use the standards to validate skills.

## Writing Standard

Use ASD-STE100 Simplified Technical English for all active skill prose and all
prose that tools generate for skills. Follow the repository
[ASD-STE100 writing policy](../../docs/asd-ste100.md). Preserve exact commands,
code, configuration, identifiers, paths, and technical literals.

> **Format:** Mnemosyne v2.0.0 uses the **flat-file skill format**.
> Each skill is a single Markdown file at `skills/<name>.md`. There is no
> nested `<name>/SKILL.md`, no per-skill `plugin.json`, and no `.claude-plugin/`
> directory inside each skill.
>
> The only documented exception is
> `plugins/tooling/mnemosyne/`. That directory contains Mnemosyne-side command
> infrastructure and is not a corpus skill. Read `AGENTS.md` for the repository
> structure. Use `templates/skill-template.md` to create a skill.

## Required Structure

```text
skills/
└── <name>.md                  # Single flat skill file (REQUIRED)
```

Optional sibling files alongside `<name>.md`:

- `<name>.notes.md` or `<name>.notes-<topic>.md`: Session notes that validation excludes.
- `<name>.history*`: Historical revisions that validation excludes.

## Skill Metadata

Put the YAML frontmatter at the start of `skills/<name>.md`.

| Field | Required | Description |
| ------- | ---------- | ------------- |
| `name` | Yes | Lowercase kebab-case identifier (matches the filename stem) |
| `description` | Yes | Specific trigger conditions |
| `version` | Yes | Semantic version such as `1.0.0` |
| `date` | Yes | Last-updated date (YYYY-MM-DD) |
| `category` | Yes | One of the approved categories below |
| `user-invocable` | Yes | For an internal skill or subskill, use `false` |
| `tags` | No | YAML list of searchable keywords |

Do not add a repository-specific `source` field.

## Skill File Requirements

### YAML Frontmatter (Required)

```yaml
---
name: skill-name
description: "Specific trigger conditions"
category: category-name
version: "1.0.0"
date: YYYY-MM-DD
user-invocable: false
tags:
  - keyword-1
  - keyword-2
---
```

### Required Sections

1. **Overview table**: Give the date, objective, and outcome.
2. **When to Use**: Give specific trigger conditions.
3. **Verified Workflow**: Give successful steps and a Quick Reference subsection.
4. **Failed Attempts**: Use the required four-column table.
5. **Results & Parameters**: Give configurations and expected outputs.

The repository policy recommends a title and References section. The validator
does not require them.

## Approved Categories

| Category | Description |
| ---------- | ------------- |
| `training` | ML training experiments |
| `evaluation` | Model evaluation |
| `optimization` | Performance tuning |
| `debugging` | Bug investigation |
| `architecture` | Design decisions |
| `tooling` | Automation tools |
| `ci-cd` | Pipeline configs |
| `testing` | Test strategies |
| `documentation` | Knowledge and technical documents |

## Validation and Review Rules

1. Store the skill at `skills/<name>.md`.
2. Delimit valid YAML frontmatter with `---` lines.
3. Include all required frontmatter fields.
4. Include the description field. The validator confirms that it is not empty.
5. Use one approved category.
6. Use `YYYY-MM-DD` for the date.
7. Include all required Markdown sections.
8. Use the required Failed Attempts columns.
9. Use a level-three Quick Reference heading.

Authors and reviewers must confirm that each description has specific trigger
conditions.

## Quality Guidelines

### Good Description

```text
"When you run vLLM on separate GPUs, use this skill for GRPO training.
When vllm_skip_weight_sync errors or OpenAI API parsing issues occur, use
this skill again. The team verified it on gemma-3-12b-it."
```

### Bad Description

```text
"Training experiments"  # Too vague, no trigger conditions
```

### Good Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| External inference | Used inline vLLM | The process exhausted GPU memory | Use an external server |
| Large batch | Used `batch_size=16` | The gradients overflowed | Use `batch_size=4` |

### Bad Failed Attempts

| Attempt | What Was Tried | Why It Failed | Lesson Learned |
| --------- | ---------------- | --------------- | ---------------- |
| Unknown | It did not work | Unknown | Try again |

## Search Command Standards

Exclude hidden directories from all `grep` and `find` commands in skills. This
rule prevents searches in `.pixi/`, `.git/`, `.cache/`, and other hidden
directories.

### Required Pattern

```bash
# Correct - excludes all directories starting with .
grep -rn "pattern" --include="*.ext" --exclude-dir='.*' .

# Multiple file types
grep -rn "FIXME" --include="*.mojo" --include="*.py" --exclude-dir='.*' .

# With Perl regex
grep -oP "FIXME\(#\K\d+" --include="*.mojo" --exclude-dir='.*' -r . | sort -u
```

### Common Mistake

```bash
# WRONG - searches .pixi/, .git/, .cache/, etc.
grep -rn "FIXME" --include="*.mojo" .

# CORRECT - excludes hidden directories
grep -rn "FIXME" --include="*.mojo" --exclude-dir='.*' .
```

### Why This Matters

- `.pixi/` contains many dependency files with their own TODOs and FIXMEs.
- `.git/` contains repository metadata.
- Hidden directories can add false positives to search results.
- Searches take more time when they examine hidden directories.
