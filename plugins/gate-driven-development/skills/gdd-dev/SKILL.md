---
name: gdd-dev
description: "Use when the user invokes /gdd-dev <task> or asks to start a formal GDD workflow in Codex."
version: 0.1.0
---

# GDD Dev Entry Point for Codex

This skill is the Codex-compatible entry point for the Claude Code slash command `commands/gdd-dev.md`.

## When to Use

Use this skill when the user writes any of the following:

- `/gdd-dev <task>`
- `gdd-dev: <task>`
- `GDDで <task>`
- A direct request to start the formal gate-driven-development workflow

## Instructions

1. Treat the user's text after `/gdd-dev` or `gdd-dev:` as `$ARGUMENTS`.
2. Read `../gdd-using-skills/SKILL.md` first and follow its routing rules.
3. Read `../../commands/gdd-dev.md` as the command contract source. Adapt Claude Code-specific tool names to Codex tools.
4. If running setup is appropriate, run `scripts/setup-gdd-loop.sh` from the plugin root with `$ARGUMENTS`. In Codex, resolve the plugin root from this skill path instead of relying on `${CLAUDE_PLUGIN_ROOT}` being set.
5. Continue through `gdd-brainstorming` for formal workflow start/resume. Do not switch to generic planning mode.
6. If the command contract and a GDD skill conflict, prefer the more specific GDD skill/reference named by the command contract.

## Codex Notes

- Claude Code loads `commands/gdd-dev.md` as a native slash command. Codex may not expose plugin `commands/` as slash commands, so this skill provides the same discoverable entrypoint.
- If the host UI captures `/gdd-dev` before it reaches the assistant, use `gdd-dev: <task>` as the equivalent user-facing trigger.
