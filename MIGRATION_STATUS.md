# Mnemosyne Flat File Migration - Complete

> Current status: the migration record is complete. Mnemosyne is a skill corpus
> and session-memory store, not a plugin marketplace. See the [ASD-STE100
> writing policy](docs/asd-ste100.md) for current repository requirements.

## Summary

Mnemosyne stores skills as flat files in the `skills/` directory. Athena owns
the `/advise` and `/learn` commands that read and write this corpus.

## Current File Structure

```text
skills/<name>.md           # Main skill file with YAML frontmatter and Markdown
skills/<name>.notes.md     # Optional session context
skills/<name>.history      # Version and provenance archive
```

Each main skill file must contain the required YAML frontmatter and Markdown
sections. Use `scripts/validate_plugins.py` to check the corpus.

## Current Metadata Format

```yaml
---
name: skill-name
description: "Specific use case description"
category: training
date: 2026-03-19
version: "1.0.0"
user-invocable: false
tags: []
---
```

## Current Guidance

- Keep one main skill file for each skill.
- Keep optional session context in a `.notes.md` companion.
- Keep version and provenance data in a `.history` companion.
- Use the repository validation commands before you open a pull request.

## Related Files

- `AGENTS.md` — repository contract and skill standards
- `CONTRIBUTING.md` — contributor workflow
- `templates/skill-template.md` — skill file template
- `scripts/validate_plugins.py` — corpus validation
