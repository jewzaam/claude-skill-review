---
name: review
description: This skill should be used when the user asks to review, assess, audit, or evaluate a codebase, project, or implementation. Trigger phrases include "review the code", "assess the codebase", "audit the implementation", "evaluate code quality", "review this project".
allowed-tools: Agent, Read, Glob, Grep, Write, Edit
argument-hint: "[path-to-review] [--focus area1,area2]"
---

# Review Skill

## Purpose

Perform a comprehensive expert-level review of a codebase by spinning up parallel review agents across multiple dimensions. Produce a single consolidated review document.

## Constraints

- **Read-only analysis.** Never modify source code or tests.
- **No program execution.** Never install dependencies, run the program, or execute language runtimes directly (no `python`, `node`, `go run`, etc.).
- **No package management.** Never run `pip`, `npm`, `cargo`, etc.
- **If a check requires a tool not present**, note it in the review as a recommendation — do not attempt to install or build it.

## Process

### 1. Determine Scope

- If an argument is provided, use it as the root path to review.
- If no argument, use the current working directory.
- Use Glob and Read to understand the project structure.
- Identify the language, framework, build system, and test framework.

### 2. Spin Up All Review Agents in Parallel

Launch **all five** agents simultaneously using the Agent tool. Each agent produces findings as a structured list.

#### Agent 1: Build & Checks
Run available `make` check targets **sequentially** via Bash and report results. The Bash calls go through normal user permission prompts. Do NOT run `install`, `build`, `run`, `deploy`, or any target that installs or executes the program.

Safe targets to attempt (skip if they don't exist):
- `make format` (check mode / dry-run if available)
- `make lint`
- `make typecheck`
- `make test` or `make test-unit`
- `make coverage`

Report pass/fail and relevant error output for each target. If a target fails due to missing dependencies, report that — do not install them.

#### Agent 2: Architecture & Design
Read-only (Read, Glob, Grep). Assess:
- Project structure and organization (files in the right places, logical separation)
- Module boundaries and coupling (are dependencies between modules appropriate?)
- Data model design (are dataclasses/models well-defined?)
- Configuration management (hardcoded values, environment handling)
- Design patterns used (appropriateness, consistency)

#### Agent 3: Implementation Quality
Read-only (Read, Glob, Grep). Assess:
- Code correctness (logic errors, off-by-one, race conditions)
- Error handling (missing error paths, swallowed exceptions, bare excepts)
- Type safety (missing annotations, incorrect types, unsafe casts)
- Security (path traversal, injection, credential handling)
- Resource management (file handles, connections, cleanup)
- Edge cases (empty inputs, None handling, boundary conditions)
- Keyword-only args with `*` separator (if project convention requires it)

#### Agent 4: Test Quality & Coverage
Read-only (Read, Glob, Grep). Assess:
- Test plan alignment (do tests match any documented test plan?)
- Test isolation (proper use of fixtures, no shared state, no network calls)
- Assertion quality (meaningful assertions, not just "no exception")
- Edge case coverage (error paths, empty inputs, boundary conditions)
- Mock usage (appropriate mocking, not over-mocking)
- Missing test scenarios (what isn't tested that should be?)
- Fixture design (reusable, minimal, well-named)

#### Agent 5: Maintainability & Standards
Read-only (Read, Glob, Grep). Assess:
- Naming conventions (consistent, descriptive, not redundant)
- Code duplication (DRY violations, copy-paste patterns)
- Documentation (docstrings present where needed, accurate, not excessive)
- Import organization (grouped, sorted, no unused)
- Function complexity (too long, too many parameters, deeply nested)
- Consistency (similar patterns handled the same way throughout)
- Build system (Makefile/pyproject.toml correctness, dependency declarations)

### 3. Consolidate Review

After all agents complete, produce a single review document written to `Review-<project-name>.md` at the project root. If a review file already exists, overwrite it.

#### Review Document Structure

```markdown
# Code Review: <project-name>

## TL;DR
<3-5 sentence executive summary with overall assessment>

## Build & Check Results

| Target | Status | Notes |
|--------|--------|-------|
| format | ✅/❌/⚠️ | ... |
| lint   | ✅/❌/⚠️ | ... |
| ...    | ...    | ... |

## Findings

### 🔴 Critical
<Issues that must be fixed — bugs, security issues, data loss risks>

### 🟡 Important
<Issues that should be fixed — error handling gaps, design problems, missing tests>

### 🟢 Suggestions
<Nice-to-haves — style improvements, minor optimizations, documentation>

### ✅ Strengths
<What the codebase does well — good patterns, solid design choices>

## Detailed Analysis

### Architecture & Design
<Consolidated findings from Agent 2>

### Implementation Quality
<Consolidated findings from Agent 3>

### Test Quality & Coverage
<Consolidated findings from Agent 4>

### Maintainability & Standards
<Consolidated findings from Agent 5>

## Recommendations
<Prioritized list of actionable next steps>
```

### 4. Present Summary

After writing the review document, present the TL;DR and critical/important findings directly to the user. Reference the review document for full details.

## Agent Prompt Template

Each read-only review agent should receive a prompt structured as:

```
Review the project at <root-path> focusing on <review-area>.

Read all relevant source files. Use Glob to find files and Grep to search for patterns.
Do NOT run any commands. Do NOT modify any files. Read-only analysis only.

Project context:
- Language: <detected>
- Build system: <detected>
- Test framework: <detected>

Report findings as a structured list with:
- Severity: critical / important / suggestion / strength
- File and line reference (file.py:42)
- Description of the issue
- Why it matters
- Suggested fix (if applicable)
```

## Critical Rules

- **NEVER modify source code or tests** — this is a review, not a fix
- **NEVER install dependencies** — if make targets fail due to missing deps, report it
- **NEVER run the program** — no `python -m`, `node`, `go run`, etc.
- **NEVER run pip, npm, cargo, etc.** — no package management
- **Read-only agents (2-5) use Read, Glob, Grep only** — no Bash
- **Build agent (1) runs only make check targets** — no install, build, run, deploy
- **All findings need file:line references** — no vague complaints
- **Severity must be justified** — explain why something is critical vs. suggestion
- **Acknowledge strengths** — a good review recognizes what works well
