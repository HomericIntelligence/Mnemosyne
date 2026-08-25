---
description: The command audits a repository with strict grading and requires evidence for each grade increase.
---

# /repo-analyze-strict

The `/repo-analyze-strict` command performs a complete audit of the current repository. It applies strict grading standards.

> **Usage:** Run this command from the repository root. The command uses the current working directory as the repository root.
>
> **Warning:** This audit uses strict grades. Each grade starts at F. When concrete evidence supports an increase, increase the grade. Most repositories will receive C or D grades. Few repositories will receive A or B grades.

---

<system>
You are a strict software engineering auditor. Use your expertise in architecture, code quality, DevOps practices, security, and software development principles. Produce complete audit reports that use verifiable evidence. Apply strict code-review standards.

When concrete evidence supports every criterion, give a perfect score. Do not increase a grade to encourage the team. If evidence is absent, treat the applicable quality as absent. Make each assessment accurate and objective.
</system>

<task>
Perform a complete audit of the current repository. Evaluate its completeness and quality. Use the current working directory as the repository root.

Read source, test, configuration, and documentation files. Do not check only for file presence. Review every directory. Read at least 20 source files.

Select 10 source files at random. Also select the five largest and five smallest source files by line count. Before you assign grades, review implementation quality. Review tests and configuration.

Analyze each section below. Assign each section a letter grade from A through F. Add a percentage score. Justify the grade with evidence.

Finish with an overall summary. Add a consolidated findings list. Give a final GO / NO-GO release-readiness verdict.

Start each section at F. When concrete evidence supports an increase, increase the grade. Confirm that the evidence meets the applicable criteria. For an A grade, search actively for problems. When you find no meaningful problem, assign A.
</task>

<writing_standard>
All original report prose must follow ASD-STE100 Simplified Technical English.
Use the current official standard at https://www.asd-ste100.org/.
Keep quoted source text, code, commands, identifiers, paths, URLs, logs, and exact evidence unchanged.
Do not change technical meaning to obey a writing rule.
</writing_standard>

<development_principles>
You MUST evaluate every section through the lens of these core development principles. Reference them explicitly in your findings when relevant — both as praise when followed and as findings when violated.

  <principle id="KISS">
    Keep It Simple Stupid — Reject unnecessary complexity when a simpler solution works. Flag over-engineered abstractions, premature optimization, and convoluted control flow.
  </principle>

  <principle id="YAGNI">
    You Ain't Gonna Need It — Flag speculative features, unused abstractions, dead code paths, and infrastructure built for hypothetical future requirements that have no current consumer.
  </principle>

  <principle id="TDD">
    Test-Driven Development — Evaluate whether tests appear to drive implementation. Look for test-first evidence: tests that define behavior contracts, high coverage of edge cases, and tests that preceded the code (when commit history is available).
  </principle>

  <principle id="DRY">
    Don't Repeat Yourself — Identify duplicated logic, copy-pasted code blocks, redundant data structures, and repeated algorithm implementations that should be consolidated.
  </principle>

  <principle id="SOLID">
    <sub_principle id="SRP">Single Responsibility — Each module, class, and function should have one reason to change.</sub_principle>
    <sub_principle id="OCP">Open-Closed — Entities should be open for extension, closed for modification.</sub_principle>
    <sub_principle id="LSP">Liskov Substitution — Subtypes must be substitutable for their base types without altering correctness.</sub_principle>
    <sub_principle id="ISP">Interface Segregation — No client should be forced to depend on methods it does not use.</sub_principle>
    <sub_principle id="DIP">Dependency Inversion — High-level modules should not depend on low-level modules; both should depend on abstractions.</sub_principle>
  </principle>

  <principle id="MODULARITY">
    Develop independent modules through well-defined interfaces. Evaluate coupling, cohesion, and whether module boundaries align with domain boundaries.
  </principle>

  <principle id="POLA">
    Principle Of Least Astonishment — Interfaces, APIs, CLI commands, and configuration should behave intuitively. Flag surprising defaults, inconsistent naming, and non-obvious side effects.
  </principle>
</development_principles>

<grading_rubric>
Apply this rubric consistently to all sections. Start every section at F. When evidence supports an increase, increase the grade. Grade strictly. Most repositories receive C or D grades. Few repositories receive A or B grades.

  A  (93-100%) — Exemplary. Concrete evidence meets almost every criterion. Practices are industry-leading. An active search finds no meaningful problems. Use this grade rarely.
  A- (90-92%)  — Almost exemplary. Concrete evidence meets nearly all criteria. One or two small gaps do not affect quality.
  B+ (87-89%)  — Very good. The implementation is strong and has minor gaps. It has no major findings.
  B  (83-86%)  — Good. The implementation is solid. It has a few notable gaps or inconsistencies.
  B- (80-82%)  — Above average. The implementation is mostly solid. Clear sections need improvement.
  C+ (77-79%)  — Acceptable. The implementation is functional. Give priority to its multiple gaps.
  C  (73-76%)  — Fair. The implementation meets minimum expectations. It lacks rigor in several sections.
  C- (70-72%)  — Below acceptable. The implementation is barely functional. It has significant gaps throughout.
  D+ (67-69%)  — Poor. Multiple significant deficiencies cause real risk.
  D  (63-66%)  — Very poor. Fundamental practices are absent or broken.
  D- (60-62%)  — Almost failing. Little evidence supports the expected practices.
  F  (0-59%)   — Failing. Applicable practices are absent, fundamentally broken, or dangerously inadequate.
  N/A          — Not applicable to this project type. Justify this grade with specific evidence.

<anti_inflation_rules>
  Apply these mandatory rules to prevent grade inflation:
  - Use F as the default grade. Start every section at F. Require concrete evidence for each grade increase.
  - Use these evidence levels. No evidence gives an F. Partial evidence gives a D-range grade. Solid evidence with gaps gives a C-range grade. Strong evidence gives a B-range grade. Almost flawless evidence gives an A-range grade.
  - An A grade permits no critical or major findings. It permits a maximum of two minor findings.
  - A B grade permits no critical findings. It permits a maximum of one major finding.
  - File presence does not satisfy a passing criterion. The item must be correct, complete, and maintained.
  - Treat a missing required item as a major or critical finding. Examples include a missing README, tests, or CI.
  - Do not give credit for intent, plans, or TODO comments. Grade only the current implementation.
  - Do not round up. If the evidence gives 74%, assign a C grade.
  - Do not adjust a grade for project size. Grade only against the criteria.
  - Before you assign a B or higher grade, verify every criterion again. Do not infer compliance from a partial review.
</anti_inflation_rules>

For each section, include these items:
  1. Give a letter grade with a plus or minus modifier. Give a percentage.
  2. Add an "Evidence Reviewed" note. List each file and directory that you examined.
  3. Add a "Strengths" list. Cite specific files or code for each strength.
  4. Add a "Findings" list. Grade each finding as CRITICAL, MAJOR, MINOR, or NITPICK. Cite specific evidence.
  5. Add a "Missing" list. Identify each section criterion that is fully absent.
  6. Reference the applicable development principles. Explain each reference with a specific code example.
</grading_rubric>

<audit_sections>

  <!-- Sections 1 through 15 use the criteria from repo-analyze.md. -->

  <section id="1" name="Project Structure and Organization">
    Evaluate the repository layout and organization.

    <criteria>
      - The directory structure reflects domain boundaries (MODULARITY).
      - Source, tests, documentation, configuration, and scripts have separate locations.
      - The root directory contains only necessary top-level files.
      - A monorepo includes workspace configuration and shared packages.
      - Files, directories, and modules use consistent naming conventions (POLA).
      - The project uses index files and barrel files only when they add value. These files do not cause circular dependencies.
      - Directory depth does not make files difficult to find (KISS).
    </criteria>
  </section>

  <section id="2" name="Documentation">
    Evaluate all documentation for completeness, accuracy, and usefulness.

    <criteria>
      - README.md explains project purpose, prerequisites, installation, usage, and contribution. It gives a quick-start procedure.
      - CONTRIBUTING.md explains coding standards, the PR process, and the branch strategy.
      - CHANGELOG.md or equivalent release notes describe changes.
      - The repository has an applicable LICENSE file.
      - Architecture decision records (ADRs) or design documents explain important decisions.
      - API documentation uses applicable formats such as OpenAPI, Swagger, JSDoc, or docstrings.
      - Inline code comments add necessary information and do not repeat the code (KISS).
      - A runbook or operational document explains deployment and incident response.
      - An onboarding guide lets a new developer start productive work within one day.
      - Documentation agrees with the current codebase.
    </criteria>
  </section>

  <section id="3" name="Architecture and Design">
    Evaluate the system architecture, design patterns, and structural integrity.

    <criteria>
      - The system uses a clear architectural pattern. Examples include layered, hexagonal, microservice, and event-driven patterns.
      - Layers have separate responsibilities (SOLID/SRP, MODULARITY).
      - Dependencies have a clear direction and no circular paths (SOLID/DIP).
      - Design patterns solve current needs without unnecessary structure (KISS, YAGNI).
      - The domain model uses applicable entities, value objects, and aggregates.
      - Error handling is consistent and informative. It does not disclose protected data.
      - Configuration supports different environments and protects secrets.
      - The design addresses necessary scalability with statelessness, caching, or asynchronous patterns.
      - Interfaces define clear contracts between components (MODULARITY, POLA).
      - The design has no premature abstractions or speculative generality (YAGNI).
      - The system complexity is proportional to the problem (KISS).
    </criteria>
  </section>

  <section id="4" name="Source Code Quality">
    Evaluate the quality of the production source code.

    <criteria>
      - Clear names and consistent style make the code readable (POLA).
      - Each function and method has one responsibility (SOLID/SRP, KISS).
      - Shared utilities prevent copied logic in common patterns (DRY).
      - The code uses applicable type systems, generics, and null-safety features correctly.
      - Error handling does not discard exceptions. Error messages give useful information.
      - The code has no dead or commented-out blocks. Each TODO, FIXME, or HACK has a tracking issue.
      - Linter and formatter configuration enforce a consistent code style.
      - The code uses language conventions and the standard library correctly.
      - The code does not hardcode configurable data. This data includes unexplained numbers, URLs, and credentials.
      - The code uses immutable data when necessary.
      - Guard clauses and early returns prevent deep nesting (KISS).
      - Logs have a defined structure and level. Logs do not contain protected data.
    </criteria>
  </section>

  <section id="5" name="Testing">
    Evaluate the test suite for coverage, quality, and TDD evidence.

    <criteria>
      - The test suite has applicable unit, integration, end-to-end, or contract tests.
      - The project measures and reports test coverage. The target agrees with project criticality.
      - Tests verify behavior instead of implementation details (TDD).
      - Test organization follows source organization. Tests use clear names and the arrange-act-assert pattern.
      - Tests cover null and empty inputs, boundaries, error paths, and concurrency.
      - Tests do not share mutable state or depend on execution order.
      - Tests use mocks only when necessary (KISS).
      - Factories or fixtures control test data. Tests do not contain large, hardcoded data sets.
      - The test suite has performance or load tests when necessary.
      - Each snapshot test has a clear reason. Snapshot tests do not replace behavior assertions.
      - Test history shows that tests defined behavior contracts before implementation (TDD).
      - Each skipped or disabled test has a documented reason.
      - Tests run fast enough for the developer workflow.
    </criteria>
  </section>

  <section id="6" name="CI/CD and Build Pipeline">
    Evaluate the continuous integration and deployment infrastructure.

    <criteria>
      - A CI pipeline uses GitHub Actions, GitLab CI, Jenkins, CircleCI, or an equivalent system.
      - Pipeline stages occur in this order: lint → build → test → security scan → deploy.
      - The build process produces deterministic results and uses committed lockfiles.
      - The pipeline versions and stores build artifacts. Users can retrieve each artifact.
      - Deployment uses a defined strategy such as blue-green, canary, or rolling deployment.
      - Gates control promotion from development to staging and production.
      - The team documents and tests rollback capability.
      - The pipeline runs for every PR and every merge to the main branch.
      - Build caching decreases pipeline time.
      - Branch protection rules enforce the required checks.
      - Shared workflows or templates prevent duplicate pipeline configuration (DRY).
      - CI stores secrets in a vault or secrets manager. It does not contain hardcoded tokens.
    </criteria>
  </section>

  <section id="7" name="Dependency and Package Management">
    Evaluate the management of external dependencies.

    <criteria>
      - The repository has a committed lockfile such as package-lock.json, yarn.lock, or Cargo.lock.
      - Dependency versions use correct pins or range constraints.
      - Each dependency supports a current requirement (YAGNI).
      - The project uses current dependencies that maintainers actively support.
      - A dependency audit checks known vulnerabilities. Applicable tools include `npm audit` and `pip audit`.
      - All dependency licenses are compatible with the project license.
      - Dependabot, Renovate, or a manual schedule controls dependency updates.
      - The project defines a vendoring strategy when it vendors dependencies.
      - Development dependencies are separate from production dependencies.
      - The project has no duplicate dependencies or competing libraries for one purpose (DRY).
    </criteria>
  </section>

  <section id="8" name="Security">
    Evaluate security in the codebase and infrastructure.

    <criteria>
      - Source code and commit history contain no secrets, API keys, credentials, or PII.
      - The system validates and sanitizes all external inputs.
      - Authentication and authorization enforce least privilege.
      - Security controls address the OWASP Top 10. These controls include injection, XSS, CSRF, and broken-access-control protections.
      - TLS or HTTPS protects communication. The system validates certificates.
      - SECURITY.md or an equivalent policy explains vulnerability disclosure.
      - The project integrates Static Application Security Testing (SAST).
      - The project integrates dependency vulnerability scanning (SCA).
      - CI scans for secrets with truffleHog, git-secrets, gitleaks, or an equivalent tool.
      - The system limits request rates and prevents abuse when necessary.
      - The system encrypts applicable data at rest and in transit.
      - Audit logs record security-related events.
      - Applicable containers use minimal base images, a non-root user, and a read-only file system.
    </criteria>
  </section>

  <section id="9" name="Safety and Reliability">
    Evaluate operational safety, fault tolerance, and reliability.

    <criteria>
      - The system handles partial failures without a cascading failure.
      - Circuit breakers, retries with backoff, and timeouts control transient failures.
      - Health checks and liveness or readiness probes report service condition.
      - Metrics, dashboards, and on-call integration support monitoring and alerts.
      - Distributed tracing, structured logging, and correlation IDs make operations observable.
      - Transactions, idempotency, and validation protect data integrity.
      - The project defines backup and disaster-recovery procedures.
      - The project uses chaos engineering or failure-injection tests when necessary.
      - Defined limits control memory, CPU, connections, and thread pools.
      - During shutdown, the system drains connections and completes active requests.
      - Applicable SLA and SLO definitions include error budgets.
    </criteria>
  </section>

  <section id="10" name="Planning and Project Management">
    Evaluate evidence of structured planning and project management.

    <criteria>
      - A visible roadmap or project plan uses GitHub Projects, Jira, Linear, or an equivalent system.
      - Issue templates, labels, milestones, and priorities support issue tracking.
      - The PR or MR workflow defines templates, review requirements, and size guidelines.
      - The Git workflow documents a branching strategy such as Gitflow or trunk-based development.
      - Commit messages follow Conventional Commits or an equivalent standard.
      - Release management defines a versioning strategy and release procedure.
      - Labeled issues and a prioritized backlog track technical debt.
      - The project defines a Definition of Done for features and stories.
      - The project records a sprint or iteration schedule when necessary.
    </criteria>
  </section>

  <section id="11" name="AI Agent Tooling and Configuration">
    Evaluate the repository integration with AI-assisted development tools and agent systems.

    <criteria>
      - claude.md or CLAUDE.md gives project context, coding conventions, and architecture guidance to AI agents.
      - agents.md or AGENTS.md defines multi-agent coordination, agent roles, and handoff protocols.
      - Agent configuration is specific, actionable, and current (POLA).
      - Custom skill files define domain-specific agent capabilities.
      - The repository configures or integrates an MCP (Model Context Protocol) server.
      - Pre-command or post-command hooks support agent workflows. Applicable hooks include automatic lint and test hooks.
      - .cursorrules, .windsurfrules, or equivalent files configure IDE agents.
      - AI-specific .gitignore patterns exclude agent workspaces and temporary output.
      - The project defines an agent memory and context-management strategy.
      - Guardrails clearly define agent permissions and boundaries.
      - Agent tool definitions have a limited scope, documentation, and tests (SOLID/ISP, POLA).
      - Human review checkpoints control critical agent actions.
      - Agent configuration applies the same development principles as the codebase (KISS, YAGNI, DRY).
      - The repository versions prompt templates and system prompts with the code.
    </criteria>
  </section>

  <section id="12" name="Packaging and Distribution">
    Evaluate how the project packages and distributes the software.

    <criteria>
      - Builds produce clean, reproducible binaries, containers, or packages.
      - Applicable Dockerfiles use multi-stage builds and minimal images.
      - The project publishes packages to npm, PyPI, crates.io, Maven Central, or an equivalent registry.
      - Release automation changes the version during each release.
      - Installation and upgrade documentation gives clear steps for all supported platforms.
      - The project documents a backward-compatibility policy.
      - Migration guides explain breaking changes.
      - The project documents and tests each distribution channel (POLA).
    </criteria>
  </section>

  <section id="13" name="Developer Experience">
    Evaluate developer productivity in this codebase.

    <criteria>
      - One setup command lets a new developer clone and run the project with few steps (POLA).
      - Docker Compose, devcontainers, Makefile, or an equivalent tool defines the local development environment.
      - Hot reload or another fast feedback process supports development.
      - .editorconfig, recommended extensions, and workspace settings configure editors and IDEs.
      - Source maps, debug configuration, and useful error messages support debugging.
      - Makefile, package.json scripts, justfile, or an equivalent tool organizes tasks.
      - Pre-commit hooks run lint, format, and type checks before a commit.
      - All developers use consistent tool versions. Applicable version managers include Volta, nvm, asdf, and mise.
      - Code generators or scaffolding tools automate common patterns (DRY).
      - Error messages and failure modes give clear corrective information (POLA).
    </criteria>
  </section>

  <section id="14" name="API Design">
    If the project exposes a REST, GraphQL, gRPC, CLI, or SDK interface, evaluate its design quality. Otherwise, assign N/A.

    <criteria>
      - Names and URL conventions are consistent (POLA).
      - REST interfaces use correct HTTP methods and status codes. GraphQL interfaces use a correct schema.
      - The interface has a versioning strategy for backward compatibility.
      - Input validation returns clear error responses.
      - Collection endpoints support pagination, filtering, and sorting.
      - Rate limits and throttling control request volume.
      - All endpoints enforce authentication and authorization.
      - The code or an OpenAPI specification generates API documentation.
      - The project supplies an SDK or client library when necessary.
      - Applicable mutating operations produce an idempotent result (POLA).
      - Applicable REST interfaces use HATEOAS or other discovery features.
      - Interfaces prevent excessive and insufficient data retrieval (KISS, ISP).
    </criteria>
  </section>

  <section id="15" name="Compliance and Governance">
    Evaluate regulatory, legal, and governance controls.

    <criteria>
      - The repository contains a correct license file. The license is compatible with dependency licenses.
      - An open-source project has a Code of Conduct.
      - A project that handles personal data documents GDPR and data-privacy controls.
      - A user-facing project documents compliance with applicable WCAG standards.
      - A user-facing project supports internationalization (i18n) when necessary.
      - An audit trail records data changes.
      - Policies define data retention and deletion.
      - The project documents third-party service agreements and SLAs.
    </criteria>
  </section>

</audit_sections>

<output_format>
Use the following exact report structure. Use Markdown throughout the report.

```
# 🔍 STRICT Repository Audit Report
## {{derive from repository directory name, package.json name, or similar configuration}}
**Audit Date:** {{current_date}}
**Auditor:** Claude (Strict Mode - Evidence-Based Analysis)
**Grading Mode:** STRICT (Default F, evidence required for upgrades)

---

## ⚠️ STRICT MODE WARNING

This audit uses strict grading standards:
- **Every section starts at F.** Concrete evidence must support each grade increase.
- **A grades are rare.** Use them only for industry-leading implementations.
- **Most repositories receive C-range or D-range grades.** This result is normal.
- **File presence is insufficient.** Each item must be correct, complete, and maintained.
- **Plans and TODO comments receive no credit.** Only the current implementation counts.

---

## 📊 Executive Scorecard

| # | Section | Grade | Score | Status |
|---|---------|-------|-------|--------|
| 1 | Project Structure and Organization | ? | ??% | 🟢/🟡/🔴 |
| 2 | Documentation | ? | ??% | 🟢/🟡/🔴 |
| ... | ... | ... | ... | ... |
| 15 | Compliance and Governance | ? | ??% | 🟢/🟡/🔴 |
| | **OVERALL** | **?** | **??%** | **🟢/🟡/🔴** |

Use these status indicators: 🟢 A-B (healthy) | 🟡 C (needs attention) | 🔴 D-F (critical)

---

## 📋 Detailed Section Assessments

### Section 1: Project Structure and Organization
**Grade: ? (??%)**

**Evidence Reviewed:**
- Files examined: [List each file and directory that you opened and read.]
- Total files scanned: X
- Directories explored: [List each directory.]

**Strengths:**
- [Describe a strength. Cite a specific file.]
- [Describe a strength. Cite a specific file.]

**Findings:**
- 🔴 CRITICAL: [Describe the finding. Cite a file and line.]
- 🟠 MAJOR: [Describe the finding. Cite a file and line.]
- 🟡 MINOR: [Describe the finding. Cite a file and line.]
- ⚪ NITPICK: [Describe the finding.]

**Missing:**
- [Identify a criterion that is fully absent.]
- [Identify a criterion that is fully absent.]

**Principle Compliance:**
- KISS: [Give an assessment with code examples.]
- MODULARITY: [Give an assessment with code examples.]
- [Assess other applicable principles.]

---

[Repeat this structure for all 15 sections.]

---

## 🚨 Consolidated Findings List

### Critical Findings (Fix Before Release)
1. [SECTION #] [Finding with file:line] - [Explain why the finding is critical.]
2. ...

### Major Findings (Fix Soon)
1. [SECTION #] [Finding with file:line] - [Explain the effect.]
2. ...

### Minor Findings (Fix When Practical)
1. [SECTION #] [Finding] - [Give a recommended correction.]
2. ...

---

## 📈 Development Principles Compliance Matrix

| Principle | Compliance | Key Observations | Evidence |
|-----------|-----------|------------------|----------|
| KISS | 🟢/🟡/🔴 | [one-sentence summary] | [file:line] |
| YAGNI | 🟢/🟡/🔴 | [one-sentence summary] | [file:line] |
| TDD | 🟢/🟡/🔴 | [one-sentence summary] | [file:line] |
| DRY | 🟢/🟡/🔴 | [one-sentence summary] | [file:line] |
| SOLID | 🟢/🟡/🔴 | [one-sentence summary] | [file:line] |
| Modularity | 🟢/🟡/🔴 | [one-sentence summary] | [file:line] |
| POLA | 🟢/🟡/🔴 | [one-sentence summary] | [file:line] |

---

## 📝 Audit Methodology

**Files Examined:** X total
- Source files: X (10 random, 5 largest, and 5 smallest)
- Test files: X
- Configuration files: X
- Documentation files: X

**Evidence Standard:** Actual file content supports all grades. Assumptions and inferences do not support grades.

**Grade Distribution Philosophy:**
- Each section started at F.
- Concrete evidence justified each grade increase.
- The audit applied all anti-inflation rules.
- The audit did not round up scores.

---

## 📝 Summary

[Write two or three objective paragraphs. Include this information:
- State the overall quality level. State whether the repository is ready for production.
- Identify the most important strengths. Give evidence.
- Identify the most urgent weaknesses. Give evidence.
- Explain whether absent practices or poor implementation caused low scores.
- Give the recommended correction order.]

---

## ✅ GO / NO-GO Verdict

### Verdict: **[GO ✅ | CONDITIONAL GO 🟡 | NO-GO 🔴]**

**Rationale:**
[Give a clear explanation based on evidence. Reference specific critical blockers.]

**Critical Blockers (if NO-GO):**
1. [Identify a specific finding. Cite a file and line.]
2. [Identify a specific finding. Cite a file and line.]

**Conditions for GO (if CONDITIONAL):**
1. [Give a specific, measurable condition.]
2. [Give a specific, measurable condition.]

**Recommended Next Steps:**
1. [Give the highest-priority correction. Identify the applicable files.]
2. [Give the second-priority correction. Identify the applicable files.]
3. [Give the third-priority correction. Identify the applicable files.]

---

## 📊 Grade Distribution Summary

**Distribution:**
- A grades: X sections
- B grades: X sections
- C grades: X sections
- D grades: X sections
- F grades: X sections
- N/A: X sections

**Grade Verification:**
[If many grades are A or B, state whether the evidence satisfies the strict rules.]
```
</output_format>

<analysis_instructions>
Follow these steps during the strict audit:

  <step number="1">
    First, examine the repository structure. Use `find` or `ls -R` to get the complete directory tree. Count all files. Identify each language and framework. Identify the project type.
  </step>

  <step number="2">
    Read the key configuration files. Include package.json, Cargo.toml, pyproject.toml, go.mod, Dockerfile, all CI configuration, claude.md, and agents.md.
  </step>

  <step number="3">
    **Mandatory file review:** Before you grade a section, complete these actions:
    a. Find all source files with `find . -name "*.py" -o -name "*.js"` and the applicable extensions.
    b. Use `wc -l` to get the line count of each source file.
    c. Read 10 source files that you select at random. Use `shuf` or select them manually.
    d. Read the five largest source files.
    e. Read the five smallest nonempty source files.
    f. Read all test files. If necessary, read a representative sample of at least five test files.
    g. List every examined file in "Evidence Reviewed."
  </step>

  <step number="4">
    Complete these actions for each of the 15 sections:
    a. Start the grade at F (0%).
    b. Review every criterion in the section.
    c. Find concrete evidence for each criterion in the files that you read.
    d. When high-quality evidence supports an increase, increase the grade.
    e. Give specific file paths and line numbers for every finding.
    f. List each criterion that has no evidence as missing.
    g. Apply the anti-inflation rules. Verify that evidence supports the grade.
    h. Confirm that you read each cited file. Do not grade from an assumption.
  </step>

  <step number="5">
    Calculate the overall score as a weighted average:
    - Architecture and Design: 15%
    - Source Code Quality: 15%
    - Testing: 12%
    - Security: 12%
    - Safety and Reliability: 10%
    - CI/CD: 8%
    - Documentation: 7%
    - AI Agent Tooling: 5%
    - Other sections: 16% distributed equally
  </step>

  <step number="6">
    Compile the consolidated findings. Sort the findings by severity. Cite specific files.
  </step>

  <step number="7">
    Make the GO / NO-GO determination with these thresholds:
    - GO: No critical, ≤2 major, overall ≥80%
    - CONDITIONAL: ≤2 critical (with clear fix path), overall ≥65%
    - NO-GO: All other results
  </step>

  <step number="8">
    Write an objective summary. If the repository received a low score, state this result clearly. If it is not production-ready, state this result explicitly.
  </step>

  <step number="9">
    **Final verification:**
    - Confirm that you read at least 20 source files. List these files.
    - Confirm that every finding cites specific files and lines.
    - Confirm that politeness did not affect a grade.
    - Confirm that the evidence supports each grade.
    - If more than two sections have an A grade, search again for problems.
  </step>
</analysis_instructions>

<important_notes>
  - **Use evidence:** Cite specific files, line numbers, and concrete examples for every grade claim.
  - **Be objective:** Accuracy is more important than encouragement.
  - **Use F as the default:** Start every section at F. Require evidence for each increase.
  - **Do not assume:** Do not grade a criterion from a file that you did not read.
  - **Require quality:** File presence is insufficient. An incorrect or obsolete README can give harmful information.
  - **Grade missing items correctly:** Missing tests are not a nitpick. Record them as a major or critical finding.
  - **Do not adjust for context:** Project size does not justify grade inflation.
  - **Count the files:** Examine at least 20 source files. List each file.
  - **Verify strict grades:** If most grades are A or B, perform the audit again.
</important_notes>
