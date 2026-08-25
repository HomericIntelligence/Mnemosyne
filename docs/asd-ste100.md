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

Do not rewrite these content types only to change their style:

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

## Writing Rules

Use the official standard as the primary source. During each writing and review
task, use this checklist:

1. Use one approved term for each concept.
2. Use approved words and project technical terms.
3. Use American English. Do not use slang or unnecessary jargon.
4. Use active voice. If the actor is unknown in descriptive text, you can use
   passive voice.
5. Put one instruction in each sentence. Use the imperative form.
6. Put a necessary condition before the instruction.
7. Limit an instruction sentence to 20 words.
8. Limit a descriptive sentence to 25 words.
9. Give each paragraph one topic. Use no more than six sentences.
10. Do not use contractions, semicolons, or Latin abbreviations.
11. When complex text is hard to read, use a vertical list.
12. Use inclusive language and unambiguous pronouns.

These items are a review aid. They do not replace the official standard or its
controlled dictionary.

Use the official copy of the standard. Do not store the standard, its
dictionary, or ASD logos in this repository. Do not redistribute these items.

## Approved Project Terms

ASD-STE100 permits approved technical terms. Mnemosyne uses these established
terms where they are necessary:

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
