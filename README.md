# claude-skill-review

A Claude Code skill that performs multi-agent reviews of an entire codebase — not a branch diff or PR review, but a full assessment of the whole repo.

## Overview

This skill launches five parallel agents to review a codebase simultaneously:

- **Build & Checks** — runs available `make` check targets and reports results
- **Architecture & Design** — evaluates project structure, module boundaries, and design patterns
- **Implementation Quality** — checks correctness, error handling, type safety, and security
- **Test Quality & Coverage** — assesses test isolation, assertion quality, and missing scenarios
- **Maintainability & Standards** — reviews naming, duplication, complexity, and consistency

Each agent establishes the project's own patterns first, then assesses against that baseline — findings are grounded in the project's conventions, not abstract ideals. Findings are filtered by confidence scoring and validated by independent subagents before inclusion.

Output is a single `Review-<project-name>.md` file with prioritized findings (C0, I0, S0 prefixed for easy reference), strengths, and actionable recommendations.

## Dependencies

This skill requires the **feature-dev** Claude Code plugin. Analytical agents (2–5) use `subagent_type: "feature-dev:code-reviewer"` to structurally restrict their available tools to read-only operations (Glob, Grep, Read, etc.) — Bash, Write, and Edit are physically unavailable, not just discouraged by prompt. This is the primary mechanism that enforces the skill's read-only guarantee for code analysis.

Without the plugin installed, agents 2–5 will fail to launch.

The feature-dev plugin is an official Anthropic plugin. Requires Claude Code v2.0 or later (the `/plugin` command is built-in). To install it:

```
/plugin install feature-dev@claude-plugins-official
```

## Installation

Clone the repo into your Claude Code skills directory:

```bash
cd ~/.claude/skills/
git clone git@github.com:jewzaam/claude-skill-review.git review
```

## Usage

Invoke the skill in Claude Code:

```
/review
/review /path/to/project
/review focus on error handling and test coverage
/review just the src/api/ directory, I'm worried about input validation
```

With no arguments, it reviews the entire codebase across all dimensions. Any text after `/review` is passed to the agents as additional context, so you can guide what they pay attention to — but all five agents still run regardless.

The skill is read-only — it never modifies source code, installs dependencies, or runs the program.

## Standards reference

For user-owned repos, the skill also checks against coding standards from `~/source/standards/` if that directory exists. Ownership is determined automatically: the skill compares the origin remote's owner against your authenticated GitHub user (`gh api user --jq '.login'`). If they match and `~/source/standards/` exists, the standards are applied.

The [jewzaam/standards](https://github.com/jewzaam/standards/) repo provides a set of language and project conventions designed for use with this skill. Contributions are welcome — if you have standards that would benefit the broader community, open a PR. To use it, clone it to `~/source/standards/`.

