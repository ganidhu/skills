# Contributing

New skills go in `skills/<name>/` with a `SKILL.md` that has `name` and `description` in the YAML frontmatter.

Then:

1. Add the folder path to `.claude-plugin/plugin.json` under `skills`
2. List it in the README table
3. Keep scripts next to the skill, not at the repo root

Install locally while iterating:

```bash
npx skills add ./ --skill <name> -g -y
```
