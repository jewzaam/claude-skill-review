---
name: review
description: Perform a multi-agent codebase review by spinning up parallel review agents across multiple dimensions. Use when the user asks to review, assess, audit, or evaluate a codebase or project.
disable-model-invocation: true
argument-hint: "[path-to-review]"
---

# Review Skill

## Purpose

Perform a multi-agent review of a codebase by spinning up parallel review agents across multiple dimensions. Produce a single consolidated review document, then validate it with an independent agent.

## Constraints

- **Read-only analysis.** Never modify source code or tests.
- **No program execution.** Never install dependencies, run the program, or execute language runtimes directly (no `python`, `node`, `go run`, etc.).
- **No package management.** Never run `pip`, `npm`, `cargo`, etc.
- **Output is two Review markdown files** at the project root: `Review-<project-name>.md` (actionable findings) and `Review-<project-name>-supplementary.md` (detailed analysis, strengths, standards). If the user provides constrained context (a PR number, specific area, topic), append a slug (max 12 chars, lowercase, hyphens) to both filenames: `Review-<project-name>-<slug>.md` and `Review-<project-name>-<slug>-supplementary.md`.
- **If a check requires a tool not present**, note it in the review as a recommendation — do not attempt to install or build it.

## Process

### 1. Determine Scope & Context

- If an argument is provided, use it as the root path to review.
- If no argument, use the current working directory.
- Use Glob and Read to understand the project structure.
- Identify the language, framework, build system, and test framework.

**Standards detection:** Read `.git/config` and check the origin remote URL. If the remote is owned by GitHub user `jewzaam` or GitLab user `nmalik`, this is a user-owned repo and agents should check against the coding standards in `~/source/standards/`. Pass the relevant standards context to each agent (see agent prompts below). If the repo is not user-owned, agents should follow the project's own conventions and skip the standards check.

**Allowlist discovery:** Call `mcp__allowlist__get_allowed_permissions` once to discover which commands are pre-approved. Include the allowed commands in each agent's prompt so agents know what they can run without blocking on user approval.

### 2. Launch All Review Agents in Parallel

Launch **all five** agents simultaneously in a single message using the Agent tool. Each agent produces findings as a structured list.

Use the `model` parameter on each Agent call to control speed/accuracy tradeoffs:
- **Agent 1 (Build & Checks):** `model: "haiku"` — runs commands and reports output; speed matters more than analytical depth.
- **Agents 2–5 (analytical):** `model: "sonnet"` — good balance of speed and analytical quality.

Each agent prompt should include: "Maximize parallel tool calls — when you need to read multiple files or search for multiple patterns, issue all independent Read/Glob/Grep calls in the same message."

#### Confidence & Filtering Rules

All agents (2–5) must self-score each finding's confidence:
- **High (>80%):** Clear issue with concrete evidence in the code. Report it.
- **Medium (60–80%):** Plausible issue but requires assumptions. Report only if severity is critical or important.
- **Low (<60%):** Speculative or theoretical. Drop it — do not include in output.

**Hard exclusions — do not report these regardless of confidence:**
- Style issues already enforced by project linters or formatters (check for config files like `.flake8`, `pyproject.toml [tool.ruff]`, `.eslintrc`, etc.)
- Missing tests for trivial code (getters, setters, simple data classes, constants)
- Architecture concerns in `scripts/`, one-off utilities, or exploratory code
- Suggestions that repeat what a make target already checks (e.g., don't flag import ordering if `make lint` covers it)
- Missing docstrings on internal/private functions
- Generic best-practice advice not grounded in a specific code location

#### Agent 1: Build & Checks
Run available `make` check targets **sequentially** via Bash and report results. Prefer commands from the provided allowlist to avoid blocking on user approval prompts. Do NOT run `install`, `build`, `run`, `deploy`, or any target that installs or executes the program.

Safe targets to attempt (skip if they don't exist):
- `make format` (check mode / dry-run if available)
- `make lint`
- `make typecheck`
- `make test` or `make test-unit`
- `make coverage`

Report pass/fail and relevant error output for each target. If a target fails due to missing dependencies, report that — do not install them.

**Output guidelines:** Summarize failures concisely — report the error type and affected files, not full stack traces. Users can rerun targets for full output. For missing-dependency failures, state which dependency is missing and move on.

#### Agent 2: Architecture & Design
Read-only (Read, Glob, Grep). Two phases:

**Phase 1 — Establish baseline patterns:** Before assessing issues, identify the project's established architectural patterns: directory layout conventions, module boundary style, how config is handled, what design patterns are already in use. Document these briefly.

**Phase 2 — Assess against baseline:** Evaluate whether the codebase follows its own patterns consistently. Flag deviations from the project's own conventions, not abstract ideals.

Assessment areas:
- Project structure and organization (files in the right places, logical separation)
- Module boundaries and coupling (are dependencies between modules appropriate?)
- Data model design (are dataclasses/models well-defined?)
- Configuration management (hardcoded values, environment handling)
- Design patterns used (appropriateness, consistency)

If this is a user-owned repo, also read the relevant standards from `~/source/standards/` (particularly `common/` and any language-specific `project-structure.md`) and check compliance.

#### Agent 3: Implementation Quality
Read-only (Read, Glob, Grep). Two phases:

**Phase 1 — Establish baseline patterns:** Before assessing issues, identify the project's established patterns for error handling, type usage, input validation, and resource management. Note how the codebase typically handles these concerns.

**Phase 2 — Assess against baseline:** Evaluate whether the codebase follows its own patterns consistently. Flag deviations and gaps relative to the project's own conventions.

Assessment areas:
- Code correctness (logic errors, off-by-one, race conditions)
- Error handling (missing error paths, swallowed exceptions, bare excepts)
- Type safety (missing annotations, incorrect types, unsafe casts)
- Security (path traversal, injection, credential handling)
- Resource management (file handles, connections, cleanup)
- Edge cases (empty inputs, None handling, boundary conditions)

If this is a user-owned repo, also read the relevant language style standards from `~/source/standards/` (e.g., `python/style.md`, `cli/conventions.md`) and check compliance.

#### Agent 4: Test Quality & Coverage
Read-only (Read, Glob, Grep). Two phases:

**Phase 1 — Establish baseline patterns:** Before assessing issues, identify the project's established testing patterns: test framework, fixture conventions, mocking approach, assertion style, and directory structure. Note what the project's tests typically look like.

**Phase 2 — Assess against baseline:** Evaluate whether tests follow the project's own patterns consistently. Flag deviations and gaps relative to established conventions.

Assessment areas:
- Test plan alignment (do tests match any documented test plan?)
- Test isolation (proper use of fixtures, no shared state, no network calls)
- Assertion quality (meaningful assertions, not just "no exception")
- Edge case coverage (error paths, empty inputs, boundary conditions)
- Mock usage (appropriate mocking, not over-mocking)
- Missing test scenarios (what isn't tested that should be?)
- Fixture design (reusable, minimal, well-named)

If this is a user-owned repo, also read the relevant testing standards from `~/source/standards/` (e.g., `python/testing.md`, `cli/testing.md`) and check compliance.

#### Agent 5: Maintainability & Standards
Read-only (Read, Glob, Grep). Two phases:

**Phase 1 — Establish baseline patterns:** Before assessing issues, identify the project's established conventions for naming, imports, documentation, and build configuration. Note the project's own style.

**Phase 2 — Assess against baseline:** Evaluate whether the codebase follows its own patterns consistently. Flag internal inconsistencies, not deviations from external style guides.

Assessment areas:
- Naming conventions (consistent, descriptive, not redundant)
- Code duplication (DRY violations, copy-paste patterns)
- Documentation (docstrings present where needed, accurate, not excessive)
- Import organization (grouped, sorted, no unused)
- Function complexity (too long, too many parameters, deeply nested)
- Consistency (similar patterns handled the same way throughout)
- Build system (Makefile/pyproject.toml correctness, dependency declarations)

If this is a user-owned repo, also read the relevant standards from `~/source/standards/` (particularly `common/naming.md`, `build/makefile.md`, `common/readme-format.md`) and check compliance. Flag any divergences between the project and the standards.

### 3. Consolidate Review

After all agents complete, synthesize their findings into a single review document. Deduplicate overlapping findings and organize by priority.

**Deduplication rules:**
- When two agents flag the same code location, keep the finding from the agent whose review area is the better fit (e.g., a security issue flagged by both Agent 3 and Agent 5 stays under Implementation Quality).
- When agents disagree on severity, take the higher severity.
- When merging, preserve the most specific file:line reference and the most actionable suggested fix.

Write two documents at the project root. If review files already exist, overwrite them. If the user provided constrained context, derive a slug (max 12 chars, lowercase, hyphens) and append it to the filenames.

#### Filename examples

| Context | Main file | Supplementary file |
|---------|-----------|-------------------|
| No context | `Review-myapp.md` | `Review-myapp-supplementary.md` |
| `/review PR 565` | `Review-myapp-pr-565.md` | `Review-myapp-pr-565-supplementary.md` |
| `/review audit module` | `Review-myapp-audit-module.md` | `Review-myapp-audit-module-supplementary.md` |

#### Main document: `Review-<project-name>[-<slug>].md`

Actionable content only — what needs to change and what to do next.

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
<Issues that must be fixed — bugs, security issues, data loss risks.
 Number each finding with a C prefix: C0, C1, C2, etc.
 If none: "No critical issues identified.">

### Important
<Issues that should be fixed — error handling gaps, design problems, missing tests.
 Number each finding with an I prefix: I0, I1, I2, etc.
 If none: "No important issues identified.">

### Suggestions
<Nice-to-haves — style improvements, minor optimizations, documentation.
 Number each finding with an S prefix: S0, S1, S2, etc.
 If none: "No suggestions.">

## Recommendations
<Prioritized list of actionable next steps>
```

#### Supplementary document: `Review-<project-name>[-<slug>]-supplementary.md`

Context, analysis, and reference material that supports the main findings.

```markdown
# Code Review (Supplementary): <project-name>

## Strengths
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
```

### 4. Validate Review

After writing the review document, spawn **parallel** validation subagents (`model: "sonnet"`) — one per severity category that has findings. Each validation subagent prompt must include the project context (language, framework, build system) so it can judge whether findings are reasonable for this type of project.

#### Validation subagent: Critical findings
- Read the review document and extract all Critical findings
- For **every** Critical finding, read the referenced source file and line
- Challenge each finding: Is the issue real? Is the severity justified? Is the file:line reference accurate?
- Return a list of findings that survived validation and any that should be downgraded or removed, with reasoning

#### Validation subagent: Important findings
- Same process as Critical, but for all Important findings
- For **every** Important finding, read the referenced source and challenge it
- Return validated findings and any that should be downgraded or removed

#### Validation subagent: Suggestions
- Read the review document and extract all Suggestions
- Spot-check a sample (at least 50%) by reading the referenced source
- Remove any that are speculative, already covered by linters, or not grounded in specific code
- Return the filtered list

After all validation subagents complete, update the review document:
- Remove findings that failed validation
- Adjust severity for findings that were downgraded
- Append a validation summary:

```markdown
## Review Validation
<Number of findings validated, removed, and downgraded, with brief reasoning for any changes>
```

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
- Allowed commands: <allowlist from mcp__allowlist__get_allowed_permissions>
<if user-owned repo>
- Standards: This is a user-owned repo. Read the relevant standards from ~/source/standards/ for your review area and check compliance.
</if>

METHODOLOGY — work in two phases:

Phase 1 — Establish baseline patterns:
Before looking for issues, read enough code to understand the project's established
patterns for your review area. Document these briefly at the top of your output.
This grounds your review in the project's own conventions, not abstract ideals.

Phase 2 — Assess against baseline:
Evaluate whether the codebase follows its own patterns consistently. Flag deviations,
gaps, and concrete issues relative to established conventions.

CONFIDENCE SCORING — self-score every finding:
- High (>80%): Clear issue with concrete evidence. Report it.
- Medium (60-80%): Plausible but requires assumptions. Report only if critical/important.
- Low (<60%): Speculative. Drop it entirely.

HARD EXCLUSIONS — never report these:
- Style issues already enforced by project linters/formatters
- Missing tests for trivial code (getters, setters, simple data classes)
- Architecture concerns in scripts/ or one-off utilities
- Issues already caught by make targets
- Missing docstrings on internal/private functions
- Generic best-practice advice not grounded in a specific code location

PROHIBITED ACTIONS:
- Do NOT write or execute ad hoc tests. If a test is missing, report it as a finding.
- Do NOT pipe code to a runtime (no `echo "..." | python`, no `python -c`, etc.).
- Do NOT attempt to verify findings by executing code. Static analysis only.
- If something needs runtime verification, recommend it as a next step in the review.

Report findings as a structured list with:
- Severity: critical / important / suggestion / strength
- Confidence: high / medium
- File and line reference (file.py:42)
- Description of the issue
- Why it matters (grounded in the project's own patterns where possible)
- Suggested fix (if applicable)
```

## Critical Rules

- **NEVER modify source code or tests** — this is a review, not a fix
- **NEVER install dependencies** — if make targets fail due to missing deps, report it
- **NEVER run the program** — no `python -m`, `node`, `go run`, etc.
- **NEVER run pip, npm, cargo, etc.** — no package management
- **NEVER write or execute ad hoc tests** — if a test is missing, report it as a finding. Do not write a test to prove it is missing. Do not execute code to verify a gap — that is what the missing test is for
- **NEVER pipe code to a runtime** — no `echo "..." | python`, no `python -c "..."`, no equivalent in any language
- **Read-only agents (2-5) use Read, Glob, Grep only** — no Bash
- **Build agent (1) runs only make check targets** — no install, build, run, deploy
- **Prefer allowlisted commands** — agents receive the allowlist as context. Stick to pre-approved commands to avoid blocking the review on user approval prompts. The goal is a hands-off review that runs without user intervention
- **All findings need file:line references** — no vague complaints
- **Severity must be justified** — explain why something is critical vs. suggestion
- **Acknowledge strengths** — a good review recognizes what works well
- **Only write Review-<project-name>[-<slug>].md and its supplementary file** — never create or modify any other file
- **Review is observation, not action** — the review identifies findings and gaps for other agents or the user to act on later. Do not attempt to fix, verify, or validate issues beyond reading source code. If something needs verification beyond static analysis, recommend it as a next step in the review
