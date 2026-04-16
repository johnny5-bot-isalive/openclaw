# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Current Local Notes

### Obsidian

- The Nexus vault (Windows): `C:\Users\Jaret\Obsidian\The Nexus`
- The Nexus vault (WSL via /mnt/c): `/mnt/c/Users/Jaret/Obsidian/The Nexus`
- Project registry note: `/mnt/c/Users/Jaret/Obsidian/The Nexus/40 Agent Nexus/Project Registry.md`
- Global backlog note: `/mnt/c/Users/Jaret/Obsidian/The Nexus/40 Agent Nexus/Backlog.md`
- Global Kanban note: `/mnt/c/Users/Jaret/Obsidian/The Nexus/40 Agent Nexus/Kanban.md`

### QMD

- Default local note-search path: `QMD_LLAMA_GPU=off npx -y @tobilu/qmd ...`
- Common checks: `QMD_LLAMA_GPU=off npx -y @tobilu/qmd status` and `QMD_LLAMA_GPU=off npx -y @tobilu/qmd query "..."`
- Use QMD first for fuzzy semantic note retrieval across workspace and Obsidian notes
- Prefer `memory_search` for OpenClaw runtime memory recall
- Prefer grep/read for exact text or exact path lookups

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
