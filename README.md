# Task Trace

English | [简体中文](README.zh-CN.md)

A Codex skill that connects project decisions, meaningful changes, verification,
and completion evidence. It keeps enough durable context to resume authorized
work after an interruption, handoff, or context compaction.

An optional loader can return the bound task's plan summary and checkpoint at
session start. The agent still checks the latest request and actual artifacts.

## When to use it

- Planning a project or comparing approaches with meaningful tradeoffs.
- Carrying an agreed plan through several stages of implementation.
- Resuming a task with existing decisions, execution records, and unfinished work.

Ordinary questions and isolated small edits do not require this workflow unless
they continue a tracked task or the user explicitly invokes the skill.

## Two complementary documents

| Document | Purpose | Contents |
| --- | --- | --- |
| `PLAN.md` | Intended outcomes and decisions | Scope, selected approach, confirmation basis, acceptance criteria, and a brief recovery summary. |
| `WORKLOG.md` | Actual state and evidence | Current checkpoint, decision reasons, meaningful changes, verification results, required command and subtask results, and completion basis. |

Reuse existing project records. When new records are needed, follow the project's
documentation convention, defaulting to `docs/tasks/<short-task-name>/`.
The [plan](assets/PLAN.md) and [worklog](assets/WORKLOG.md) templates are starting
points; existing documents do not need reinitialization or mandatory migration.
Task data stays in the project workspace, outside the skill installation.

Choose documents by purpose. A worklog links to design specifications and
specialized verification matrices; it does not replace them. Engineering records
remain with the project unless the user selects another destination. Using this
skill does not authorize creating or moving records to Pages.

Review, answer-only, and monitoring requests do not write records by default.
Existing explicit authorization to write documentation still applies. Read-only
and no-file boundaries also apply to session binding changes.

## How it works

1. **Discuss and select.** Separate user-confirmed goals, assumptions, actual
   alternatives, and agent recommendations. Record the selected approach and
   its scope; agreement on a plan and permission to implement stay distinct.
2. **Preserve the reason.** Save essential decision reasons before removing
   resolved comparisons. When new evidence changes a key tradeoff, reopen only
   the affected decision and preserve unaffected agreements.
3. **Connect changes to evidence.** For each meaningful change, record its goal,
   decision, or necessary consequence of authorized work, then the affected
   files and actual verification result. Group related edits instead of saves.
4. **Recover actual state.** Read the plan summary and checkpoint, distinguish
   confirmed instructions from suggestions and observations, and inspect relevant
   artifacts. An old pending item or next-action note is not new authorization.
5. **Complete against the scope.** Collect required command and subtask results
   and resolve necessary verification. Once the scope is delivered, update the
   checkpoint once and report the result without adding optional work or loops.

## Install the skill

With Git installed, clone this repository into a user-level Codex skill directory:

```sh
mkdir -p ~/.agents/skills
git clone https://github.com/Yu03-6/task-trace.git ~/.agents/skills/task-trace
```

If your environment uses another supported skill directory, keep that location.
Keep one discoverable copy and do not overwrite an existing directory. Codex
detects skill changes automatically; restart if it does not appear. See the
[official skill documentation](https://learn.chatgpt.com/docs/build-skills).

The document workflow has no additional runtime dependency. Optional automatic
recovery requires Python 3.8 or later and uses only the standard library.
Installing the skill does not register or activate its recovery hook.

When upgrading from Project Memory, follow the
[rename migration steps](references/recovery.md#migrate-from-project-memory)
before moving the old installation.

## Use

[Automatic matching](agents/openai.yaml) is enabled, and you can invoke the skill
explicitly. Requests may be in English or Chinese; records follow the project's
language requirements.

**Plan without implementing**

```text
Use $task-trace to compare our account synchronization approaches.
You may save the plan and worklog, but do not implement the approach yet.
```

**Select and implement**

```text
Use $task-trace. Choose approach A and implement account synchronization,
excluding payments. Preserve the decision reasons and verification evidence.
```

**Resume**

```text
Use $task-trace to resume docs/tasks/account-sync/. Read the plan and
checkpoint, check the actual workspace, and finish the authorized scope.
```

## Optional automatic recovery

Run the installer from the stable installed skill path on a supported host:

```sh
python3 ~/.agents/skills/task-trace/scripts/task_trace.py install-hooks
```

This registers a `SessionStart` handler in the host's `hooks.json`, preserves
unrelated handlers, and backs up existing configuration before its first change.
It does not change trust settings. In the Codex CLI, open `/hooks` to review and
trust the exact definition before it can run; never bypass or automatically grant
trust. Host policy can disable hooks. The installer supports macOS/Linux;
Windows host registration is not verified.

After selecting task records and authorizing their maintenance, bind the session.
The plan must already exist. Replace these paths with the actual workspace and
records, using the installed script's actual location:

```sh
python3 ~/.agents/skills/task-trace/scripts/task_trace.py bind \
  --workspace /path/to/project \
  --plan docs/tasks/account-sync/PLAN.md \
  --worklog docs/tasks/account-sync/WORKLOG.md
```

Binding uses `CODEX_THREAD_ID`, or an explicit known `--session-id` when needed.
Never infer the session from the newest transcript. Record paths may be absolute
or relative to the bound workspace and must stay inside it. Existing document
names can be used. Bindings live under the host's Codex home, separate from task
records. Rebinding deliberately selects another task for that session.

Use `unbind` when leaving a task, or `uninstall-hooks` to remove the registered
handler; both preserve task documents. See [the recovery reference](references/recovery.md)
for configuration locations, removal commands, and manual fallback behavior.

## What reloads and what does not

- The hook accepts `startup`, `resume`, `compact`, and `fork` session-start events.
  `clear` is excluded. It installs no `Stop` hook and cannot force continuation.
- It uses the event's exact session ID and checks that the current directory is
  inside the bound workspace. An unbound session or workspace mismatch supplies
  no context. A new fork has no inherited binding; no recent-task guessing occurs.
- It reads bounded excerpts of `## Recovery summary` and `## Current checkpoint`.
  Missing headings use a labeled, bounded file-start excerpt. Relevant history
  remains available for targeted reads; existing records need no rewrite.
- Reloading is read-only. Missing records are identified; invalid input or broken
  bindings fail without blocking the turn. The loader neither writes records nor
  summarizes transcripts. Loaded history supplies context, not execution authority.

Without a registered, trusted hook, use the same manual recovery workflow:
locate the correct task documents, read relevant context, check actual artifacts,
and continue only within the current authorization.

## Repository contents

- [SKILL.md](SKILL.md): decision, evidence, recovery, and completion workflow.
- [agents/openai.yaml](agents/openai.yaml): display metadata and invocation policy.
- [assets/PLAN.md](assets/PLAN.md) and [assets/WORKLOG.md](assets/WORKLOG.md): new-record templates.
- [scripts/task_trace.py](scripts/task_trace.py): binding and optional hook integration.
- [references/recovery.md](references/recovery.md): setup, behavior, and verification details.
- [tests/](tests/): isolated loader and configuration checks.

## Practical limits

Automatic skill matching is a model decision. Recovery depends on current records
and checking relevant facts; a written success claim is not verification evidence.
The repository's isolated tests do not establish live activation on an installed
host. Each host must support, register, and trust the hook before automatic reload
is active. This skill provides no background watcher or guarantee against context
loss, and loading a completed checkpoint does not request more work.
