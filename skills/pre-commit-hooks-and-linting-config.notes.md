# Pre-commit Hooks and Linting Configuration — Case Notes

These notes retain repository-specific evidence from version 2.6.0. The complete
v2.6.0 retrievable file is archived once in the
[history file](./pre-commit-hooks-and-linting-config.history).

## Case Index

| Case | Source | Status | Retained lesson |
| --- | --- | --- | --- |
| Consolidated lint corpus | [Archived 53-skill cross-project corpus](./pre-commit-hooks-and-linting-config.history) | verified-ci overall | Pre-commit is the common local/CI entry point |
| Ruff format false green | Hephaestus [PR #707](https://github.com/HomericIntelligence/Hephaestus/pull/707) / [PR #913](https://github.com/HomericIntelligence/Hephaestus/pull/913) | verified-ci | `ruff check` and `ruff format` are separate gates |
| Dual lint/pre-commit red | Hephaestus [PR #1058](https://github.com/HomericIntelligence/Hephaestus/pull/1058), [issue #814](https://github.com/HomericIntelligence/Hephaestus/issues/814) | verified-local | One formatter drift can fail two jobs |
| TOML and locked Ruff parity | [Archived Inference Service PR #157 evidence](./pre-commit-hooks-and-linting-config.history) | verified-ci | Parse TOML and pin Ruff hook to lockfile version |
| Full PR-diff scope | [Odyssey PR #5453](https://github.com/HomericIntelligence/Odyssey/pull/5453) | verified-ci | Per-file checks missed delegated Mojo files; run from merge base |
| Cross-editor baseline | [Scylla PR #1556](https://github.com/HomericIntelligence/Scylla/pull/1556), audit S13 | verified-ci | Add a root `.editorconfig` with file-specific whitespace rules |
| Review scope for forced churn | Hephaestus [PR #1019](https://github.com/HomericIntelligence/Hephaestus/pull/1019), [issue #1017](https://github.com/HomericIntelligence/Hephaestus/issues/1017), review on [PR #1015](https://github.com/HomericIntelligence/Hephaestus/pull/1015) | verified-ci | Tool-required formatting is not unrelated scope creep |
| Commit-message stage | [Mnemosyne closed PR #2353](https://github.com/HomericIntelligence/Mnemosyne/pull/2353) | verified-ci | Install and invoke `commit-msg`; `--all-files` does not cover it |
| Bandit target ownership | [Telemachy issue #157](https://github.com/HomericIntelligence/Telemachy/issues/157) | verified-local | Directory scan plus INI requires `pass_filenames: false` |
| Pixi policy checker | Hephaestus [issue #1550](https://github.com/HomericIntelligence/Hephaestus/issues/1550) / [PR #1586](https://github.com/HomericIntelligence/Hephaestus/pull/1586) | verified-precommit | Anchor task regexes, ignore comments, and wire before claiming enforcement |
| Hook abort mistaken for signing failure | [Archived Hephaestus session evidence](./pre-commit-hooks-and-linting-config.history) | verified-precommit | Prove `HEAD` advanced before debugging the displayed parent signature |
| No-skip required gate | [Odyssey PR #5584](https://github.com/HomericIntelligence/Odyssey/pull/5584) | verified-ci | Advisory `SKIP=mojo-format` passed while a separate required fail-fast step failed; exact no-skip run went green after formatting |
| Duplicate markdownlint job planning | [Hephaestus issue #1199](https://github.com/HomericIntelligence/Hephaestus/issues/1199) | partially verified planning only | Check required contexts, new file scope, and docs before deletion; implementation was pending at capture |
| mypy sees untracked staged-work companion | Hephaestus [PR #670](https://github.com/HomericIntelligence/Hephaestus/pull/670), [issue #615](https://github.com/HomericIntelligence/Hephaestus/issues/615) / [issue #616](https://github.com/HomericIntelligence/Hephaestus/issues/616) | verified-ci | Keep multi-commit work outside the tree until its implementation commit exists |
| Stray prompt artifact | [Hephaestus PR #657](https://github.com/HomericIntelligence/Hephaestus/pull/657) | verified-ci | Remove accidental prompt files and add a narrow ignore |

## Project-Specific Parameters

- Inference Service PR #157 aligned `ruff-pre-commit` with locked Ruff `v0.15.17`.
  The version is case evidence, not a current universal recommendation.
- ProjectTelemachy issue #157 used Bandit's `.bandit` targets with recursive scan
  and `pass_filenames: false`; the trigger regex still limited when it ran.
- ProjectHephaestus issue #1550 / PR #1586 distinguished a task value beginning
  with `pip-audit` from the dependency key/value `pip-audit = ">=2.7,<3"`, and
  removed documentation-comment matches before counting `--ignore-vuln` flags.
- ProjectOdyssey PR #5584 required `pixi run mojo format <files>` followed by the
  full no-skip pre-commit suite; fixing only the first fail-fast files risked a
  second round.

## Configuration Fragments Retained as Cases

Use generated-file exclusion, not lint-only per-file ignores, when Ruff formatting
must also skip a file:

```toml
[tool.ruff]
line-length = 100
target-version = "py310"
exclude = ["package/_version.py"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "D102", "D107"]
```

A minimal cross-editor contract:

```ini
root = true

[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[Makefile]
indent_style = tab
```

Tool thresholds remain repository decisions. An observed Bandit configuration
used medium-or-higher findings to suppress low-noise B404/B603/B607 without
disabling security scanning. Every ignore still requires a reason.

## Semantic Audit for v3.0.0

The compaction retained all material triggers, flags, and failure modes from
v2.6.0:

- exact hook revisions; Pixi environment selection; TOML parsing; Ruff check/
  format separation; mypy explicit package bases; full-diff and all-file scope;
- hook-stage installation, `commit-msg` invocation, generated-lock staging,
  directory scanner `pass_filenames: false`, Bandit severity, pip-audit regex and
  comment scoping, exclusion load-bearing checks, and required-context review;
- formatter mutation, `SKIP=` false greens, system executable shadowing,
  untracked-file visibility, aborted commits masquerading as signature failures,
  and markdownlint MD060's incomplete auto-fix;
- named failed approaches, no-suppression policy, copy-ready configuration, and
  explicit verification boundaries.

Repeated hook/reference blocks, long transcripts, exact one-off paths, and
duplicate examples moved here or remain in history. The partially verified
ProjectHephaestus #1199 planning case remains explicitly unverified for
implementation; no evidence was upgraded.
