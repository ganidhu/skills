# Skills repo

Public catalog of Ganidhu's agent skills. Canonical install copy for this Mac is still `~/.claude/skills/<name>` (symlink into this repo). This tree is what `npx skills add ganidhu/skills` and the Claude plugin marketplace read.

Layout:

- `skills/<name>/SKILL.md` — required
- `skills/<name>/scripts/` — optional
- `.claude-plugin/` — marketplace + plugin manifests

Do not dump third-party harness skills here. Those live in `ganidhu/claude-skills` (`~/.claude/skills`).
