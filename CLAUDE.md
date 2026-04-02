# claude-skill-review

This repo contains a single Claude Code skill (`SKILL.md`) that performs parallel multi-agent codebase reviews.

## Repo structure

- `SKILL.md` — the skill definition (frontmatter + instructions)
- `LICENSE` — GPL-3.0
- `README.md` — user-facing documentation

## Working in this repo

- `SKILL.md` is the only functional file. All changes to the skill go here.
- The skill is markdown-only — no code, no dependencies, no build system.
- Review output files (`Review-*.md`) are generated in target projects, not in this repo.
- Follow the skill's own conventions: phased analysis, confidence scoring, severity prefixes (C/I/S).
