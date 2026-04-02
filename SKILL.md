---
name: review
description: Perform a comprehensive expert-level codebase review by spinning up parallel review agents across multiple dimensions. This skill is explicitly user-invoked only — use it when the user directly asks to review, assess, audit, or evaluate a codebase with phrases like "review the code", "assess the codebase", "audit the implementation", "evaluate code quality", or "review this project". Never trigger automatically.
disable-model-invocation: true
argument-hint: "[path-to-review] [--focus area1,area2]"
---

# Review Skill

## Purpose

Perform a comprehensive expert-level review of a codebase by spinning up parallel review agents across multiple dimensions. Produce a single consolidated review document, then validate it with an independent agent.

## Constraints

- **Read-only analysis.** Never modify source code or tests.
- **No program execution.** Never install dependencies, run the program, or execute language runtimes directly (no `python`, `node`, `go run`, etc.).
- **No package management.** Never run `pip`, `npm`, `cargo`, etc.
- **Output is a single Review markdown file.** The only file this skill creates or overwrites is `Review-<project-name>.md` at the project root.
- **If a check requires a tool not present**, note it in the review as a recommendation — do not attempt to install or build it.

## Process

### 1. Determine Scope & Context

- If an argument is provided, use it as the root path to review.
- If no argument, use the current working directory.
- Use Glob and Read to understand the project structure.
- Identify the language, framework, build system, and test framework.

**Standards detection:** Read `.git/config` and check the origin remote URL. If the remote is owned by GitHub user `jewzaam` or GitLab user `nmalik`, this is a user-owned repo and agents should check against the coding standards in `~/source/standards/`. Pass the relevant standards context to each agent (see agent prompts below). If the repo is not user-owned, agents should follow the project's own conventions and skip the standards check.

### 2. Launch All Review Agents in Parallel

Launch **all five** agents simultaneously in a single message using the Agent tool. Each agent produces findings as a structured list.

Use the `model` parameter on each Agent call to control speed/accuracy tradeoffs:
- **Agent 1 (Build & Checks):** `model: "haiku"` — runs commands and reports output; speed matters more than analytical depth.
- **Agents 2–5 (analytical):** `model: "sonnet"` — good balance of speed and analytical quality.

Each agent prompt should include: "Maximize parallel tool calls — when you need to read multiple files or search for multiple patterns, issue all independent Read/Glob/Grep calls in the same message."

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

If this is a user-owned repo, also read the relevant standards from `~/source/standards/` (particularly `common/` and any language-specific `project-structure.md`) and check compliance.

#### Agent 3: Implementation Quality
Read-only (Read, Glob, Grep). Assess:
- Code correctness (logic errors, off-by-one, race conditions)
- Error handling (missing error paths, swallowed exceptions, bare excepts)
- Type safety (missing annotations, incorrect types, unsafe casts)
- Security (path traversal, injection, credential handling)
- Resource management (file handles, connections, cleanup)
- Edge cases (empty inputs, None handling, boundary conditions)

If this is a user-owned repo, also read the relevant language style standards from `~/source/standards/` (e.g., `python/style.md`, `cli/conventions.md`) and check compliance.

#### Agent 4: Test Quality & Coverage
Read-only (Read, Glob, Grep). Assess:
- Test plan alignment (do tests match any documented test plan?)
- Test isolation (proper use of fixtures, no shared state, no network calls)
- Assertion quality (meaningful assertions, not just "no exception")
- Edge case coverage (error paths, empty inputs, boundary conditions)
- Mock usage (appropriate mocking, not over-mocking)
- Missing test scenarios (what isn't tested that should be?)
- Fixture design (reusable, minimal, well-named)

If this is a user-owned repo, also read the relevant testing standards from `~/source/standards/` (e.g., `python/testing.md`, `cli/testing.md`) and check compliance.

#### Agent 5: Maintainability & Standards
Read-only (Read, Glob, Grep). Assess:
- Naming conventions (consistent, descriptive, not redundant)
- Code duplication (DRY violations, copy-paste patterns)
- Documentation (docstrings present where needed, accurate, not excessive)
- Import organization (grouped, sorted, no unused)
- Function complexity (too long, too many parameters, deeply nested)
- Consistency (similar patterns handled the same way throughout)
- Build system (Makefile/pyproject.toml correctness, dependency declarations)

If this is a user-owned repo, also read the relevant standards from `~/source/standards/` (particularly `common/naming.md`, `build/makefile.md`, `common/readme-format.md`) and check compliance. Flag any divergences between the project and the standards.

### 3. Consolidate Review

After all agents complete, synthesize their findings into a single review document. Deduplicate overlapping findings, resolve severity disagreements (take the higher severity when in doubt), and organize by priority.

Write the document to `Review-<project-name>.md` at the project root. If a review file already exists, overwrite it.

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

### Critical
<Issues that must be fixed — bugs, security issues, data loss risks>

### Important
<Issues that should be fixed — error handling gaps, design problems, missing tests>

### Suggestions
<Nice-to-haves — style improvements, minor optimizations, documentation>

### Strengths
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

## Standards Compliance
<If user-owned repo: summary of standards check results. If not user-owned: omit this section.>

## Recommendations
<Prioritized list of actionable next steps>
```

### 4. Validate Review

After writing the review document, spawn an independent validation agent (`model: "sonnet"`) that:

1. Reads the review document
2. Spot-checks a sample of findings by reading the referenced source files
3. Verifies that file:line references are accurate
4. Checks that severity ratings are justified (critical issues are actually critical, not inflated)
5. Flags any findings that appear speculative or unsupported by the code

The validation agent appends a brief validation summary to the end of the review document:

```markdown
## Review Validation
<Summary of validation checks performed and any corrections made>
```

If the validation agent finds inaccuracies, correct them in the review document before presenting to the user.

### 5. Present Summary

After validation, present the TL;DR and critical/important findings directly to the user. Reference the review document for full details.

## Agent Prompt Template

Each read-only review agent should receive a prompt structured as:

```
Review the project at <root-path> focusing on <review-area>.

Read all relevant source files. Use Glob to find files and Grep to search for patterns.
Maximize parallel tool calls — issue all independent Read/Glob/Grep calls in the same message.
Do NOT run any commands. Do NOT modify any files. Read-only analysis only.

Project context:
- Language: <detected>
- Build system: <detected>
- Test framework: <detected>
<if user-owned repo>
- Standards: This is a user-owned repo. Read the relevant standards from ~/source/standards/ for your review area and check compliance.
</if>

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
- **Only write Review-<project-name>.md** — never create or modify any other file
