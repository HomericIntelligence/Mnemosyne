# ASD-STE100 Writing Policy

## Requirement

Mnemosyne-authored technical prose must follow the current issue of
[ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/).
This repository uses Issue 9, dated 15 January 2025, as its review baseline.

This policy is a writing requirement. It is not a statement of ASD approval,
certification, or endorsement.

## Scope

Apply this policy to these content types:

- All retrievable main skill files in `skills/`
- Agent instructions and generated skill content
- Contributor guides, templates, procedures, and public technical documents
- New prose and prose that an author changes or republishes
- Agent summaries of older skill content.

When you change existing active skill prose, review it. Do not state that a
human reviewed unchanged legacy prose against ASD-STE100.

## Protected Content

For a style-only change, do not rewrite these content types:

- The documented software-development principles
- Code, commands, configuration syntax, and schema syntax
- Identifiers, file paths, URLs, keys, and exact error messages
- Proper names, product names, and approved project terms
- Verbatim quotations, logs, output, and research evidence
- Legal text, licenses, release history, raw notes, and history files.

Human-facing description values are active prose. This rule includes
description values in frontmatter, manifests, configuration, and schemas.

Preserve technical meaning. If a style change can alter the meaning, keep the
original text. Record the reason for the exception.

## Repository Review Procedure

Use the official copy of the standard as the primary source. Request a copy
from the official download page. Keep that copy outside this repository.

Before you publish a change, use the procedure that matches its scope.

For a corpus-wide style change, complete these actions:

1. Review every active prose surface in the complete tracked-path inventory.
2. Check changed descriptions, comments, labels, help text, and Markdown prose.
3. For a style-only change, keep code, commands, configuration, identifiers, URLs, quotations, and evidence unchanged.
4. Preserve technical meaning and protected historical or legal content.
5. Run repository validation and the applicable tests.
6. Ask a human reviewer to check the technical English.

For another change, review new, changed, or republished active prose. Apply the
protected-content rules when the change is style-only.

The inventory includes active skills, active guidance Markdown, and human-facing
prose in mixed tracked files. It excludes notes, history, legal records, and
generated lock data from style-only changes.

The repository does not store or redistribute the standard, its rules, its
dictionary, or its logo. Automated checks cannot certify natural-language
conformance.

## Established Repository Terms

Use these established project terms when they are necessary. Their use does
not imply ASD approval:

| Term | Meaning |
| ------- | ------- |
| Mnemosyne | The skills and session-memory store |
| Athena | The plugin that supplies `/advise` and `/learn` |
| HomericIntelligence | The project ecosystem and GitHub organization |
| skill | A reusable knowledge file with instructions and evidence |
| frontmatter | The YAML metadata at the start of a skill file |
| Markdown and YAML | Repository file formats |
| Git and GitHub | Version-control and collaboration systems |
| pull request (PR) | The required review unit for a repository change |
| continuous integration (CI) | Automated repository checks |

Code identifiers, command names, API names, and project names are also approved
technical terms when the context requires them.

## Review

For each new or changed technical document, complete these steps:

1. Compare the prose with the current official ASD-STE100 issue.
2. Confirm that protected content did not change only for style.
3. Confirm that each instruction preserves its technical meaning.
4. Run the repository validation and Markdown checks.
5. Ask a human reviewer to examine the controlled English.

Automated checks can find some risks. They cannot prove full natural-language
conformance.

## Official References

- [ASD-STE100 official website](https://www.asd-ste100.org/)
- [Official downloads](https://www.asd-ste100.org/STE_downloads.html)
- [Official frequently asked questions](https://www.asd-ste100.org/STE_faq.html)
