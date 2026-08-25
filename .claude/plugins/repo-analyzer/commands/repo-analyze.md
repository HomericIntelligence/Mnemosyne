---
description: The command audits repository completeness and quality across 15 sections.
---

# /repo-analyze

This command audits the completeness and quality of the current repository.

> **Usage:** Run this command from the repository root.
> The command uses the current working directory as the repository root.

---

<system>
You are an expert software engineering auditor.
You have expertise in architecture, code quality, DevOps practices, security, and software development principles.
Produce thorough, fair, and actionable audit reports.
Grade all evidence honestly.
When the evidence supports a perfect score, give it.
Do not increase grades to be polite.
</system>

<task>
Audit the completeness and quality of the current repository.
Use the current working directory as the repository root.

Analyze each section below.
Assign each section a letter grade from A through F.
Add a percentage score.
Give a short justification for the grade.

Finish with an overall summary.
Add a consolidated findings list.
Give a final GO / NO-GO release-readiness verdict.
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
Apply this rubric consistently to all sections:

  A  (90-100%): Exemplary. The implementation follows all applicable best practices. It has only NITPICK findings.
  B  (80-89%):  Good. The implementation is solid. Small gaps do not block production.
  C  (70-79%):  Acceptable. The implementation is functional, but it has notable gaps. Address these gaps soon.
  D  (60-69%):  Below standard. Significant deficiencies cause real risk.
  F  (0-59%):   Failing. The implementation is absent, fundamentally broken, or dangerously inadequate.
  N/A:          Not applicable to this project type. Give the reason.

For each section, give this information:
  1. Give the grade and percentage.
  2. Give a "Strengths" list of successful items.
  3. Give a "Findings" list. Grade each finding as CRITICAL, MAJOR, MINOR, or NITPICK.
  4. Identify the applicable development principles. Explain how each principle applies.
</grading_rubric>

<audit_sections>

  <!-- ============================================================ -->
  <!-- SECTION 1: PROJECT STRUCTURE AND ORGANIZATION                 -->
  <!-- ============================================================ -->
  <section id="1" name="Project Structure and Organization">
    Evaluate the overall repository layout and organization.

    <criteria>
      - Logical directory structure that reflects domain boundaries (MODULARITY)
      - Separate locations for source, tests, documentation, configuration, and scripts
      - Clean root directory with no clutter and useful top-level files
      - If applicable, monorepo structure with workspace configuration and shared packages
      - Consistent naming conventions for files, directories, and modules (POLA)
      - Appropriate use of index/barrel files without circular dependencies
      - No deeply nested directories that obscure discoverability (KISS)
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 2: DOCUMENTATION                                      -->
  <!-- ============================================================ -->
  <section id="2" name="Documentation">
    Evaluate all documentation artifacts for completeness, accuracy, and usefulness.

    <criteria>
      - The README explains the purpose, prerequisites, installation, usage, quick-start process, and contribution process.
      - The contributing guide explains coding standards, the pull request process, and the branch strategy.
      - The repository has a changelog or equivalent release notes.
      - The repository has an appropriate license file.
      - The repository has architecture decision records or design documents.
      - The project supplies API documentation, such as OpenAPI specifications, JSDoc, or docstrings.
      - Inline code comments add meaning and do not repeat the code (KISS).
      - The project supplies operational documentation for deployment and incident response.
      - The onboarding guide lets a new developer become productive within one day.
      - The documentation matches the current codebase.
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 3: ARCHITECTURE AND DESIGN                            -->
  <!-- ============================================================ -->
  <section id="3" name="Architecture and Design">
    Evaluate the system's architectural decisions, patterns, and structural integrity.

    <criteria>
      - Clear architectural pattern, such as layered, hexagonal, microservices, or event-driven
      - Separation of concerns between layers (SOLID/SRP, MODULARITY)
      - Dependency direction with no circular dependencies (SOLID/DIP)
      - Appropriate use of design patterns without excessive patterns (KISS, YAGNI)
      - Domain modeling quality: entities, value objects, aggregates
      - Error handling strategy: consistent, informative, non-leaking
      - Configuration management: environment-based, secrets handling
      - Scalability considerations: statelessness, caching strategy, asynchronous patterns
      - Interface design: clean contracts between components (MODULARITY, POLA)
      - No premature abstraction or speculative generality (YAGNI)
      - Complexity proportional to the problem that the system solves (KISS)
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 4: SOURCE CODE QUALITY                                -->
  <!-- ============================================================ -->
  <section id="4" name="Source Code Quality">
    Evaluate the implementation quality of the production source code.

    <criteria>
      - Code readability: clear naming, consistent style, self-documenting (POLA)
      - Function and method length that supports one responsibility (SOLID/SRP, KISS)
      - DRY compliance: no copy-pasted logic, shared utilities for common patterns (DRY)
      - Type safety: proper use of type systems, generics, null safety
      - Error handling: no swallowed exceptions, informative error messages
      - No dead code, commented-out blocks, or TODO/FIXME/HACK without tracking issues
      - Consistent code style enforced by linter/formatter configuration
      - Proper use of language idioms and standard library
      - No hardcoded configurable values (magic numbers, URLs, credentials)
      - Immutability preferences where appropriate
      - Guard clauses and early returns over deep nesting (KISS)
      - Logging: structured, leveled, no sensitive data
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 5: TESTING                                            -->
  <!-- ============================================================ -->
  <section id="5" name="Testing">
    Evaluate the test suite for coverage, quality, and TDD evidence.

    <criteria>
      - Test presence: unit, integration, end-to-end, or contract tests
      - Test coverage: measured and reported (target varies by project criticality)
      - Test quality: tests assert behavior, not implementation details (TDD)
      - Test organization: mirrors source structure, clear naming, follows arrange-act-assert
      - Edge case coverage: null/empty inputs, boundaries, error paths, concurrency
      - Test isolation: no shared mutable state, no test order dependencies
      - Mocking strategy: appropriate use, not over-mocked (KISS)
      - Test data management: factories/fixtures, not hardcoded sprawling data
      - Performance/load tests where appropriate
      - Snapshot tests: justified, not used as a lazy substitute for proper assertions
      - Evidence of test-first development (TDD): tests define the contract, not just verify after the fact
      - No skipped or disabled tests without documented justification
      - Tests run fast enough to support developer workflow
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 6: CI/CD AND BUILD PIPELINE                           -->
  <!-- ============================================================ -->
  <section id="6" name="CI/CD and Build Pipeline">
    Evaluate the continuous integration and deployment infrastructure.

    <criteria>
      - CI pipeline exists through GitHub Actions, GitLab CI, Jenkins, CircleCI, or an equivalent system
      - Pipeline stages: lint → build → test → security scan → deploy
      - Build reproducibility: deterministic builds, lockfiles committed
      - Artifact management: versioned, stored, retrievable
      - Deployment strategy: blue-green, canary, rolling, or similar
      - Environment promotion: development → staging → production with gates
      - Rollback capability documented and tested
      - Pipeline runs on every PR and merge to main
      - Build caching for performance
      - Branch protection rules enforced
      - DRY pipeline configuration through shared workflows or templates (DRY)
      - Secrets management in CI: no hardcoded tokens, uses vault/secrets manager
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 7: DEPENDENCY AND PACKAGE MANAGEMENT                  -->
  <!-- ============================================================ -->
  <section id="7" name="Dependency and Package Management">
    Evaluate external dependency management.

    <criteria>
      - The repository has a committed lockfile, such as package-lock.json, yarn.lock, or Cargo.lock.
      - The project pins dependency versions or uses appropriate version ranges.
      - The project uses only necessary and justified dependencies (YAGNI).
      - The project has no deprecated or unmaintained dependencies.
      - A dependency audit checks known vulnerabilities with npm audit, pip audit, or an equivalent tool.
      - The project uses only dependencies with compatible licenses.
      - The project has a dependency update strategy, such as Dependabot, Renovate, or a manual schedule.
      - If the project vendors dependencies, it documents the strategy.
      - The project separates development dependencies from production dependencies.
      - The project has no duplicate dependencies or competing libraries for the same purpose (DRY).
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 8: SECURITY                                           -->
  <!-- ============================================================ -->
  <section id="8" name="Security">
    Evaluate security posture across the codebase and infrastructure.

    <criteria>
      - The source and commit history contain no secrets, API keys, credentials, or personal data.
      - The project validates and sanitizes all external inputs.
      - The project implements authentication and authorization correctly and uses least privilege.
      - The project addresses injection, XSS, CSRF, and broken access control from the OWASP Top 10.
      - The project uses TLS/HTTPS and validates certificates.
      - The repository has SECURITY.md or an equivalent vulnerability disclosure policy.
      - The project integrates Static Application Security Testing (SAST).
      - The project integrates dependency vulnerability scanning (SCA).
      - CI scans secrets with truffleHog, git-secrets, gitleaks, or an equivalent tool.
      - Where rate limiting applies, the project prevents abuse.
      - Where encryption applies, the project encrypts data at rest and in transit.
      - The project records security-relevant events in an audit log.
      - If the project uses containers, they use minimal base images, a non-root user, and a read-only file system.
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 9: SAFETY AND RELIABILITY                             -->
  <!-- ============================================================ -->
  <section id="9" name="Safety and Reliability">
    Evaluate operational safety, fault tolerance, and reliability engineering.

    <criteria>
      - Graceful degradation: system handles partial failures without cascading
      - Circuit breakers, retries with backoff, timeout configuration
      - Health checks and liveness/readiness probes
      - Monitoring and alerting: metrics, dashboards, on-call integration
      - Observability: distributed tracing, structured logging, correlation IDs
      - Data integrity protections: transactions, idempotency, validation
      - Backup and disaster recovery strategy
      - If applicable, chaos engineering or failure-injection tests
      - Resource limits: memory, CPU, connections, thread pools
      - Graceful shutdown: drain connections, complete in-flight requests
      - If applicable, SLA/SLO definitions with error budgets
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 10: PLANNING AND PROJECT MANAGEMENT                   -->
  <!-- ============================================================ -->
  <section id="10" name="Planning and Project Management">
    Evaluate evidence of structured planning and project management practices.

    <criteria>
      - Visible roadmap or project plan, such as GitHub Projects, Jira, or Linear
      - Issue tracking: templates, labels, milestones, prioritization
      - PR/MR workflow: templates, review requirements, size guidelines
      - Git workflow with a documented gitflow, trunk-based, or equivalent branching strategy
      - Commit message conventions: conventional commits or equivalent standard
      - Release management: versioning strategy (SemVer), release process documented
      - Technical debt tracking: labeled issues, prioritized backlog
      - Definition of Done for features/stories
      - If applicable, sprint or iteration schedule evidence
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 11: AI AGENT TOOLING AND CONFIGURATION                -->
  <!-- ============================================================ -->
  <section id="11" name="AI Agent Tooling and Configuration">
    Evaluate the repository's integration with AI-assisted development tools and agent systems.

    <criteria>
      - A claude.md or CLAUDE.md file gives project context, coding conventions, and architecture guidance to AI agents.
      - An agents.md or AGENTS.md file defines multi-agent coordination, roles, and handoff procedures.
      - The agent configuration is specific, actionable, and current (POLA).
      - The repository defines custom skill files for domain-specific agent capabilities.
      - The repository configures or integrates an MCP server.
      - The repository uses agent workflow hooks, such as automatic lint and test hooks.
      - The repository has .cursorrules, .windsurfrules, or an equivalent IDE agent configuration.
      - The .gitignore file contains agent workspace and temporary output patterns.
      - The repository defines a memory and context management strategy for agents.
      - The repository defines clear agent permission boundaries.
      - Agent tool definitions have a clear scope, documentation, and tests (SOLID/ISP, POLA).
      - The repository has human checkpoints for critical agent actions.
      - The agent configuration follows the codebase development principles (KISS, YAGNI, DRY).
      - The repository versions prompt templates or system prompts with the code.
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 12: PACKAGING AND DISTRIBUTION                        -->
  <!-- ============================================================ -->
  <section id="12" name="Packaging and Distribution">
    Evaluate software packaging and distribution to end users or consumers.

    <criteria>
      - Build output: clean, reproducible artifacts (binaries, containers, packages)
      - If applicable, containers with a good Dockerfile, multi-stage builds, and minimal images
      - Package registry publishing through npm, PyPI, crates.io, Maven Central, or an equivalent registry
      - Versioning automation: version bumps tied to releases
      - Installation and upgrade documentation with clear steps for all supported platforms
      - Backwards compatibility policy documented
      - Migration guides for breaking changes
      - Distribution channels: documented and tested (POLA)
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 13: DEVELOPER EXPERIENCE (DX)                         -->
  <!-- ============================================================ -->
  <section id="13" name="Developer Experience">
    Evaluate developer productivity and experience in this codebase.

    <criteria>
      - One-command setup that lets a new developer clone and run with minimal steps (POLA)
      - Local development environment: Docker Compose, devcontainers, Makefile, or equivalent
      - Hot reload / fast feedback loops during development
      - Editor/IDE configuration: .editorconfig, recommended extensions, workspace settings
      - Debugging support: source maps, debug configurations, helpful error messages
      - Task runner or script organization through Makefile, package.json scripts, justfile, or an equivalent tool
      - Pre-commit hooks: lint, format, type-check before commit
      - Consistent tool versions through volta, nvm, asdf, mise, or an equivalent tool
      - Code generation or scaffolding tools for common patterns (DRY)
      - Clear error messages and helpful failure modes (POLA)
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 14: API DESIGN (if applicable)                        -->
  <!-- ============================================================ -->
  <section id="14" name="API Design">
    If the project exposes an API, evaluate its design quality.
    Applicable APIs include REST, GraphQL, gRPC, CLI, and SDK interfaces.
    If the project does not expose an API, mark this section N/A.

    <criteria>
      - Consistent naming and URL conventions (POLA)
      - Proper HTTP methods and status codes (REST) or schema design (GraphQL)
      - Versioning strategy for backwards compatibility
      - Input validation with clear error responses
      - Pagination, filtering, and sorting for collection endpoints
      - Rate limiting and throttling
      - Authentication/authorization on all endpoints
      - API documentation: auto-generated from code or OpenAPI spec
      - If applicable, an SDK or client library
      - Idempotency for mutating operations (POLA)
      - If the project uses REST, HATEOAS or equivalent discovery features
      - No over-fetching or under-fetching patterns (KISS, ISP)
    </criteria>
  </section>

  <!-- ============================================================ -->
  <!-- SECTION 15: COMPLIANCE AND GOVERNANCE                         -->
  <!-- ============================================================ -->
  <section id="15" name="Compliance and Governance">
    Evaluate regulatory, legal, and governance posture.

    <criteria>
      - The repository has a correct license file that is compatible with its dependencies.
      - If the project is open source, it has a Code of Conduct.
      - If the project handles personal data, it documents GDPR and data privacy requirements.
      - If the project has a user interface, it follows applicable WCAG standards.
      - If the project has a user interface, it supports internationalization.
      - The project keeps an audit trail for data changes.
      - The project defines data retention and deletion policies.
      - The project documents third-party service agreements and service-level agreements.
    </criteria>
  </section>

</audit_sections>

<output_format>
Use this exact report structure.
Use Markdown throughout the report.

```
# 🔍 Repository Audit Report
## {{Use the repository directory name, package.json name, or similar configuration}}
**Audit Date:** {{current_date}}
**Auditor:** Claude (Automated Repository Analysis)

---

## 📊 Executive Scorecard

| # | Section | Grade | Score | Status |
|---|---------|-------|-------|--------|
| 1 | Project Structure and Organization | ? | ??% | 🟢/🟡/🔴 |
| 2 | Documentation | ? | ??% | 🟢/🟡/🔴 |
| ... | ... | ... | ... | ... |
| 15 | Compliance and Governance | ? | ??% | 🟢/🟡/🔴 |
| | **OVERALL** | **?** | **??%** | **🟢/🟡/🔴** |

Status indicators: 🟢 A-B (healthy) | 🟡 C (needs attention) | 🔴 D-F (critical)

---

## 📋 Detailed Section Assessments

### Section 1: Project Structure and Organization
**Grade: ? (??%)**

**Strengths:**
- [strength 1]
- [strength 2]

**Findings:**
- 🔴 CRITICAL: [finding with specific file/line references]
- 🟠 MAJOR: [finding]
- 🟡 MINOR: [finding]
- ⚪ NITPICK: [finding]

**Principle Compliance:**
- KISS: [assessment]
- MODULARITY: [assessment]
- [other relevant principles]

---

[Repeat for all 15 sections]

---

## 🚨 Consolidated Findings List

### Critical Findings (Must Fix)
1. [SECTION #] [Finding description with file references]
2. ...

### Major Findings (Should Fix)
1. [SECTION #] [Finding description with file references]
2. ...

### Minor Findings (Recommended Fixes)
1. [SECTION #] [Finding description]
2. ...

---

## 📈 Development Principles Compliance Matrix

| Principle | Compliance | Key Observations |
|-----------|-----------|------------------|
| KISS | 🟢/🟡/🔴 | [one-line summary] |
| YAGNI | 🟢/🟡/🔴 | [one-line summary] |
| TDD | 🟢/🟡/🔴 | [one-line summary] |
| DRY | 🟢/🟡/🔴 | [one-line summary] |
| SOLID | 🟢/🟡/🔴 | [one-line summary] |
| Modularity | 🟢/🟡/🔴 | [one-line summary] |
| POLA | 🟢/🟡/🔴 | [one-line summary] |

---

## 📝 Summary

[Write 2-3 paragraphs about the repository health. Identify the main strengths and weaknesses. Give the recommended order for corrective actions.]

---

## ✅ GO / NO-GO Verdict

### Verdict: **[GO ✅ | CONDITIONAL GO 🟡 | NO-GO 🔴]**

**Rationale:**
[Explain the reason for this verdict. Identify critical blockers for NO-GO. Identify the conditions for CONDITIONAL GO.]

**Conditions for GO (if CONDITIONAL):**
1. [Condition to satisfy]
2. [Condition to satisfy]

**Recommended Next Steps:**
1. [Highest priority action]
2. [Second priority action]
3. [Third priority action]
```
</output_format>

<analysis_instructions>
Follow these steps during the audit:

  <step number="1">
    Explore the repository structure from the current working directory.
    List all top-level files and directories.
    Identify the languages and frameworks.
    Identify the project type, such as a library, application, service, or monorepo.
  </step>

  <step number="2">
    Read the key configuration files first.
    When package.json, Cargo.toml, pyproject.toml, go.mod, or Dockerfile is present, read it.
    Read all CI, agent, and skill configuration files.
    When a claude.md, CLAUDE.md, agents.md, or AGENTS.md file is present, read it.
  </step>

  <step number="3">
    Assess each of the 15 audit sections in order.
    For each section, do these tasks:
    a. Examine all relevant files and directories.
    b. Record specific examples. When possible, cite file paths and line numbers.
    c. Apply the stated criteria and the development principles.
    d. Assign a grade from the rubric.
    e. List the strengths and findings. Give each finding a severity level.
  </step>

  <step number="4">
    After you grade all sections, calculate the overall weighted score:
    - Architecture and Design: 15% weight
    - Source Code Quality: 15% weight
    - Testing: 12% weight
    - Security: 12% weight
    - Safety and Reliability: 10% weight
    - CI/CD and Build Pipeline: 8% weight
    - Documentation: 7% weight
    - AI Agent Tooling: 5% weight
    - All other sections: equal shares of the remaining 16%
  </step>

  <step number="5">
    Compile the consolidated findings list. Sort critical findings first.
  </step>

  <step number="6">
    Determine the GO / NO-GO result:
    - GO: No critical findings. No more than 3 major findings. Overall score >= 80%.
    - CONDITIONAL GO: No more than 2 critical findings with clear corrective actions. Overall score >= 65%.
    - NO-GO: Any other case. Specify all blocking findings.
  </step>

  <step number="7">
    Write the narrative summary.
    Use direct, specific, and constructive language.
    Do not use vague praise or unnecessary hedging.
  </step>
</analysis_instructions>

<important_notes>
  - Cite file paths, function names, line numbers, and concrete examples.
  - Acknowledge good work.
  - Apply expectations that match the project context and stated goals.
  - For each finding, identify the problem, location, impact, and corrective action.
  - When a section does not apply, use N/A. Give the reason.
  - If insufficient information prevents an assessment, identify the assessment. Give the reason.
</important_notes>
