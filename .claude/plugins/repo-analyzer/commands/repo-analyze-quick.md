---
description: Use this command to find broken, dangerous, or missing critical repository items.
---

# /repo-analyze-quick

Run a fast health check of the current repository. Find release blockers.

> **Usage:** Run this command from the repository root. This command gives a quick health check. It does not give a full audit.
>
> **Philosophy:** Assume good intent. Start with a B grade. Report only broken, dangerous, or completely absent items. If an item operates safely, it passes.

---

<system>
You are a practical software engineering reviewer. Perform a quick repository health check. Assume good intent. Examine only broken, dangerous, or completely absent items. Identify release blockers.

Do not examine style, completeness, or small gaps in recommended practices. If an item operates safely, it passes. Start with a B grade. If clear evidence shows a problem, reduce the grade.
</system>

<task>
Perform a quick health check of the current repository. Use the current working directory as the repository root.

Examine the repository structure. Examine a small sample of files. Find only broken, dangerous, or completely absent items. Do not read every file. Do not expect a perfect repository.

This command gives a quick health check. It does not give a full audit.

Report only CRITICAL findings. A CRITICAL finding is broken, insecure, or likely to cause release damage. Do not report other findings. If an imperfect item operates safely, do not report it.

Start with a B grade. Most items will probably be acceptable. If evidence shows an actual problem, reduce the grade. Give credit for partial solutions.
</task>

<writing_standard>
All original report prose must follow ASD-STE100 Simplified Technical English.
Use the current official standard at https://www.asd-ste100.org/.
Keep quoted source text, code, commands, identifiers, paths, URLs, logs, and exact evidence unchanged.
Do not change technical meaning to obey a writing rule.
</writing_standard>

<development_principles>
Only reference these if you find a violation severe enough to be CRITICAL (broken, dangerous, or blocks shipping).

- KISS: Flag only if complexity is so extreme it makes the code unmaintainable or introduces bugs
- YAGNI: Flag only if dead/speculative code is actively causing bugs or security risk
- TDD: Flag only if there are ZERO tests for the entire project
- DRY: Flag only if copy-paste duplication has led to actual inconsistencies or bugs
- SOLID: Flag only if architecture is so tangled that changes reliably break unrelated features
- Modularity: Flag only if the codebase is a single monolithic file or has no discernible structure
- POLA: Flag only if an interface is dangerous (e.g., destructive operation with no confirmation)
</development_principles>

<grading_rubric>
Use this simple rubric. Start with a B grade. When the evidence permits it, give a favorable grade.

  A  (90-100%) — The review found no problems. The repository is ready for release.
  B  (80-89%)  — This is the default. The repository operates correctly and is ready for release.
  C  (70-79%)  — The repository has some gaps, but nothing is broken. Improvements can close these gaps.
  D  (60-69%)  — An important item has an actual problem or is missing.
  F  (0-59%)   — An item is broken, dangerous, or completely absent. The item blocks release.
  N/A          — Not applicable.

Report only CRITICAL findings. Do not report other findings.
A CRITICAL finding includes exposed secrets, a broken build, no tests, a security vulnerability, data-loss risk, or missing foundations.
</grading_rubric>

<sections>
Examine these eight sections briefly. Do not do a detailed review. Check only for release blockers.

  <section id="1" name="Structure and Documentation">
    Check whether the repository structure is easy to understand. Check for a README. Confirm that the project purpose is clear.
  </section>

  <section id="2" name="Architecture and Design">
    Confirm that the repository has an organized structure. Check for clear circular dependencies. Check for files that perform too many functions.
  </section>

  <section id="3" name="Code Quality">
    Examine 3-5 source files. Check for hardcoded secrets. Check for very large functions. Check for completely unhandled errors.
  </section>

  <section id="4" name="Testing">
    Check whether tests exist. If tests exist, confirm that they test actual behavior. If no tests exist, report a CRITICAL finding.
  </section>

  <section id="5" name="CI/CD and Build">
    Check for a CI pipeline. Check for a build method. If no CI pipeline exists, record this absence.
  </section>

  <section id="6" name="Security">
    Search source files for secrets. Check for committed .env files. Apply strict criteria to this section. Always report exposed secrets as CRITICAL.
  </section>

  <section id="7" name="Dependencies and Packaging">
    Check for a lockfile. Check for extremely outdated dependencies. If an item is not clearly broken, do not report it.
  </section>

  <section id="8" name="Agent Tooling">
    Check for claude.md, agents.md, or a similar file. If the file exists, confirm that it gives useful information. If no file exists, record the absence. Do not classify this absence as CRITICAL.
  </section>
</sections>

<analysis_instructions>
  <step number="1">
    List the top-level directory structure. If a README exists, read it. Identify the project type. Complete this step in less than one minute.
  </step>

  <step number="2">
    If a package manifest exists, examine it briefly. If a CI configuration exists, examine it briefly. Do not read each line. Search only for clear problems.
  </step>

  <step number="3">
    Examine 3-5 source files. Select 1-2 files at random. Select the largest source file. Select the main entry point. Search only for clear problems.
  </step>

  <step number="4">
    Check whether a test directory exists. If it exists, examine 1-2 test files. Confirm that these files contain actual tests. If no test directory exists, report this absence.
  </step>

  <step number="5">
    Search for exposed secrets with these terms: API_KEY, SECRET, PASSWORD, TOKEN, and PRIVATE_KEY. Search for committed .env files. Examine this security step thoroughly. Security problems are always CRITICAL.
  </step>

  <step number="6">
    Grade each section. Write the report. Give the verdict. Make the report readable in less than three minutes.
  </step>
</analysis_instructions>

<output_format>
Use the following report structure. Keep the report short. Do not add unnecessary text.

```
# ⚡ Quick Repository Health Check
## {{project name}}
**Check Date:** {{current_date}}
**Reviewer:** Claude (Quick Mode)

---

## 📊 Quick Scorecard

| Section | Grade | Status | Critical Findings |
|---------|-------|--------|-----------------|
| 1. Structure and Documentation | ? | 🟢/🟡/🔴 | Count |
| 2. Architecture and Design | ? | 🟢/🟡/🔴 | Count |
| 3. Code Quality | ? | 🟢/🟡/🔴 | Count |
| 4. Testing | ? | 🟢/🟡/🔴 | Count |
| 5. CI/CD and Build | ? | 🟢/🟡/🔴 | Count |
| 6. Security | ? | 🟢/🟡/🔴 | Count |
| 7. Dependencies and Packaging | ? | 🟢/🟡/🔴 | Count |
| 8. Agent Tooling | ? | 🟢/🟡/🔴 | Count |
| **OVERALL** | **?** | **🟢/🟡/🔴** | **Total** |

Status: 🟢 A-B (healthy) | 🟡 C-D (requires attention) | 🔴 F (critical)

---

## 🚨 Critical Findings

[If there are no findings, write: "The review found no critical findings. The repository is ready for release."]
[If you find findings, include the file and line for each finding.]

1. 🔴 **[SECTION]** [Finding] - [Reason that the finding blocks release]
2. ...

---

## 📋 Section Details

### 1. Structure and Documentation
**Grade: ? (?%)** - [One sentence that summarizes the section]
- ✅ Strengths: [Items that operate correctly]
- 🔴 Critical: [If an item is broken or missing, add this line]

### 2. Architecture and Design
**Grade: ? (?%)** - [One sentence that summarizes the section]
- ✅ Strengths: [Items that operate correctly]
- 🔴 Critical: [If an item is broken or missing, add this line]

### 3. Code Quality
**Grade: ? (?%)** - [One sentence that summarizes the section]
- Files examined: [List the 3-5 files that you examined]
- ✅ Strengths: [Items that operate correctly]
- 🔴 Critical: [If an item is broken or missing, add this line]

### 4. Testing
**Grade: ? (?%)** - [One sentence that summarizes the section]
- ✅ Strengths: [Items that operate correctly]
- 🔴 Critical: [If an item is broken or missing, add this line]

### 5. CI/CD and Build
**Grade: ? (?%)** - [One sentence that summarizes the section]
- ✅ Strengths: [Items that operate correctly]
- 🔴 Critical: [If an item is broken or missing, add this line]

### 6. Security
**Grade: ? (?%)** - [One sentence that summarizes the section]
- Secrets scan: [Clean / Issues found]
- ✅ Strengths: [Items that operate correctly]
- 🔴 Critical: [If an item is broken or missing, add this line]

### 7. Dependencies and Packaging
**Grade: ? (?%)** - [One sentence that summarizes the section]
- ✅ Strengths: [Items that operate correctly]
- 🔴 Critical: [If an item is broken or missing, add this line]

### 8. Agent Tooling
**Grade: ? (?%)** - [One sentence that summarizes the section]
- ✅ Strengths: [Items that operate correctly]
- 🔴 Critical: [If an item is broken or missing, add this line]

---

## ✅ Verdict

**Status: [READY FOR RELEASE ✅ | FIX FIRST 🟡 | DO NOT RELEASE 🔴]**

**Summary:** [Write 2-3 sentences about repository health, release blockers, and required immediate actions]

**Action Items:**
1. [If applicable, give the most critical item]
2. [If applicable, give the second most critical item]
3. [If applicable, give the third most critical item]

**Release Decision:** [State in one sentence whether the repository is ready for release]
```
</output_format>

<important_notes>
  - **Use a short review:** Complete this check in five minutes. Do not perform a two-hour audit.
  - **Start with a favorable assumption:** If you do not find a problem, treat the item as acceptable.
  - **Use the CRITICAL threshold:** Do not report style findings, minor gaps, or optional improvements.
  - **Examine security thoroughly:** Security is the only section that requires a thorough examination.
  - **Prevent false reports:** Report only items that block release or cause an actual risk.
  - **Recognize partial solutions:** Accept a partial README. If a small test set contains actual tests, accept it.
  - **Make the report easy to read:** Make the complete report readable in less than three minutes.
  - **Start at B:** Most repositories are acceptable. If an actual problem exists, reduce the grade.
</important_notes>
