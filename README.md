# Skills

[![skills.sh](https://skills.sh/ganidhu/skills)](https://skills.sh/ganidhu/skills)

Agent skills I actually use — motion, filmmaking, and product work.

Each skill is a folder with a `SKILL.md` plus optional scripts. Compatible with the [Agent Skills](https://agentskills.io) spec and installable through [skills.sh](https://skills.sh).

## Install

**Any agent (Claude Code, Codex, Cursor, Grok, OpenCode, …)**

```bash
npx skills add ganidhu/skills
```

Pick the skills you want, and which agents to install them on.

**One skill only**

```bash
npx skills add ganidhu/skills --skill reverse-animate
```

**Claude Code plugin**

```
/plugin marketplace add ganidhu/skills
/plugin install ganidhu-skills@ganidhu-skills
```

## Skills

| Skill | What it does |
| --- | --- |
| [reverse-animate](./skills/reverse-animate) | Screen recording → GSAP / CSS / Framer Motion, with optical-flow timing and a render-back fidelity score |

## Creating a skill

A skill is a folder under `skills/` with YAML frontmatter:

```markdown
---
name: my-skill
description: What it does and when to use it
---

# My Skill

Instructions the agent follows when this skill is active.
```

`name` and `description` are required. Put helper code in `scripts/` and long reference in `references/`.

## License

MIT. See [LICENSE](./LICENSE). Individual skills may also ship a `LICENSE.txt`.
