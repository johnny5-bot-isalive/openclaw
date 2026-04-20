# PROJECT.md - Project Session Runbook

Load this file only when the current conversation clearly belongs to an active project.

## Project startup

1. Read that project's `Project Brief.md` if it exists.
2. Read that project's `Project Kanban.md` first, then `Project Backlog.md`, if they exist.
3. Treat the project's local boards as the primary execution surface for project-local detail.
4. Use the global backlog and global Kanban as the cross-project control plane, not as a replacement for project-local boards.
5. Read any exact rule, architecture note, or control-plane file explicitly named by the active card or required by the work.
6. If a reusable rule looks durable beyond one project, prefer the relevant narrow shared startup surface under `40 Agent Nexus/Operating Rules and Playbooks/` instead of assuming the project folder is the long-term home.
7. When the exact file is already known, read it directly before using memory recall, QMD, or inference from logs.
8. When creating or rewriting backlog cards, make them fresh-agent legible: plain outcome title, clear next action, and enough references for a new agent to act without guesswork.
9. Default repetitive low-risk grunt work to Max when practical, but keep external-source research, prompt-injection-sensitive review, and high-judgment synthesis with Johnny unless there is a clear reason to delegate otherwise.

## Load discipline

- Do not scan broad folders by default when a narrow startup surface or exact named file already exists.
- If the work is research-heavy, load the Research playbook through its `_index.md`.
- If the work is about shared memory-system behavior, load the Memory playbook through its `_index.md`.
- Keep project state in project-local boards and notes, not only in chat history.
