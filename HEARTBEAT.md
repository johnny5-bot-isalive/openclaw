# HEARTBEAT

Use the project registry plus the global backlog and Kanban in The Nexus as the execution spine.

## Canonical execution surfaces
- Registry: `/mnt/c/Users/Jaret/Obsidian/The Nexus/40 Agent Nexus/Project Registry.md`
- Backlog: `/mnt/c/Users/Jaret/Obsidian/The Nexus/40 Agent Nexus/Backlog.md`
- Kanban: `/mnt/c/Users/Jaret/Obsidian/The Nexus/40 Agent Nexus/Kanban.md`

## Eligibility rule
- Backlog items may include optional gating fields such as `Not before` (ISO date) and `Trigger` (plain-language condition).
- A backlog item is eligible only when its `Not before` date has arrived and any listed `Trigger` condition is satisfied.
- Ineligible items do not block lower eligible items. Skip downward until the highest-priority eligible item for the current owner is found.

## Johnny execution rule
1. Read the registry, global Kanban, and global Backlog.
2. If there is a Johnny-owned unblocked global `Doing` card, take one real step on it and update the global board immediately.
3. Otherwise, if there is a Johnny-owned unblocked global `Ready` card, start it, do one real step, and update the global board immediately.
4. Otherwise, read the global Backlog, pull the highest-priority eligible Johnny-owned item into the global Kanban as `Ready` or `Doing`, start it, and update both global board files immediately.
5. Once a card is copied from the global Backlog to the global Kanban, delete it from the global Backlog immediately.
6. Any time Johnny changes global board state, reconcile the global Kanban and Backlog in the same turn before replying.
7. Before sending a progress update, re-read enough of the changed files to verify they match the new state.
8. If the registry, Kanban, or Backlog path cannot be read, send a concise blocker update naming the failing path.

## Project dispatch rule
1. After the global control-plane step, read the registry and identify project rows that are active, have local board paths, and are eligible for dispatch now.
2. A project is eligible for dispatch when its cadence calls for action now or there is an explicit dispatch reason from the current heartbeat.
3. For each eligible project, send a short wake to the recorded session or thread with `sessions_send`, telling it to read the local `Project Kanban.md`, then the local `Project Backlog.md`, take one real step if anything actionable exists, reconcile local board state, and report concise progress or a real blocker.
4. When dispatching a real project session, allow a generous wait before calling it a timeout. Use at least 120 seconds unless there is a strong reason to do otherwise. A slow reply is not by itself evidence that the project session failed.
5. Skip project dispatch when any of the following is true: status is `paused` or `archived`, cadence is `manual` and there is no explicit dispatch reason, blocker summary already points to an unchanged external dependency, the project is intentionally waiting on approval or a scheduled trigger, required local files are missing, or the project is already effectively clear.
6. Treat a project as effectively clear when its local `Project Kanban.md` has no actionable `Doing`, `Ready`, or meaningful `Blocked` item and its local backlog has no eligible card. Do not keep re-waking a clear project just because an old cadence still says `every-heartbeat`.
7. If a project should be dispatched but has no recorded session or thread, or its local board paths are missing, report a concrete blocker instead of guessing.
8. If a dispatch times out, do not call routing broken yet. Re-read the local board files first, then check target session history or status on demand. If the wake clearly landed, the target session shows new activity, or the files advanced, treat it as a slow reply or flaky acknowledgment problem, not a delivery failure.
9. Only report routing or visibility as broken when the target session shows no new wake, no new activity, and no local file movement after the follow-up check.
10. If a project-session handoff has not surfaced by the next heartbeat, treat it as a stale handoff immediately, but diagnose before declaring failure. Retry or restart only if the files and session evidence do not already show completed work. Do not emit repeated waiting updates.
11. When a project stays clear across dispatch checks, update the registry cadence away from `every-heartbeat` to a manual or explicitly gated cadence instead of carrying stale fake-active routing state forward.
12. Main should not silently co-write healthy project-local boards except for bootstrap or repair.

## Max parallel rule
1. Spawn Max as a disposable one-shot worker. Use `sessions_spawn` with `runtime: "subagent"`, `agentId: "max"`, `mode: "run"`, `cleanup: "delete"`, and no ACP-only fields.
2. If Max cannot be spawned or the board/files cannot be read, send a concise blocker update.
3. If there is a Max-owned unblocked `Doing` card, he shall take one real step on it and update the card immediately.
4. Otherwise, if there is a Max-owned unblocked `Ready` card, he shall start it, do one real step, and update the card immediately.
5. Otherwise, read the Backlog, pull the highest-priority Max-owned eligible backlog item into the Kanban as `Ready` or `Doing`, delete it from the backlog, he shall start it, and update the board file immediately.
6. Any time Max changes board state, he shall reconcile Backlog and Kanban in the same turn before replying. If a card is pulled, completed, blocked, superseded, split, or renamed, update both board files so they stay consistent.

## Note-search rule
- Prefer QMD first for fuzzy semantic note retrieval across workspace memory and the Obsidian vault.
- Prefer `memory_search` for native runtime recall.
- Prefer `grep`/`read` for exact-text or exact-path lookup.
- On this machine, use CPU-only QMD execution by default.

## Reporting rule
- Heartbeat should produce progress, delegation, or a blocker, not a silent no-op.
- Reply `HEARTBEAT_OK` only if there is truly no actionable Johnny global work, no actionable project dispatch, no actionable Max work, and no blocker to surface.
- If work exists but did not advance, report the blocker or failure reason instead of `HEARTBEAT_OK`.
- Do not report a board change as complete until the relevant global or project-local boards have been reconciled and re-checked.
- If Max or a dispatched project session was spawned and no completion result has surfaced by the next heartbeat, treat that as a stale handoff, not progress.
- Do not report a project-dispatch timeout as a routing blocker until the post-timeout verification check shows no new wake, no new session activity, and no local board or file progress.
- If a timeout occurred but the target project still advanced, report the real progress first. Mention flaky reply delivery only when it is operationally useful.
- On the first stale-handoff detection, stop waiting, diagnose on demand, and then either accept the completed file state, restart the run, continue locally if appropriate, or report a concrete blocker.
- Do not emit repeated waiting heartbeats across multiple turns.
- Otherwise send only a concise progress or blocker update.
