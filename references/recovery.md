# Automatic recovery

The skill manages decisions and evidence. The optional Python loader only
locates and reads task records; it never decides that a task is approved or
complete. It uses the standard library and requires Python 3.8 or later.

## Install the host integration

Run the installer from the skill's stable installed location, not a temporary
checkout. For an installation in `~/.agents/skills/task-trace`:

```sh
python3 ~/.agents/skills/task-trace/scripts/task_trace.py install-hooks
```

Use the actual installed path when the environment uses another skill directory.
The installer adds one `SessionStart` handler to `${CODEX_HOME:-~/.codex}/hooks.json`.
It preserves unrelated handlers, makes a backup of existing configuration before
its first change, and does nothing on an identical repeat installation. An
existing different Task Trace handler must be reviewed rather than silently
replaced. It does not edit `config.toml` or any hook trust settings.

Codex requires review and trust of the exact hook definition before it runs.
Installing the skill alone does not register or trust hooks. Open `/hooks` in the
Codex CLI to review and trust the definition; do not bypass trust or write approval state on the user's
behalf. Existing inline, project, or plugin hooks also run: register this loader
in one location only. Host policy may disable hooks.

The installer currently supports macOS/Linux command quoting. The loader itself
uses Python's portable filesystem APIs; Windows host registration is not verified.

To remove only the generated handler:

```sh
python3 ~/.agents/skills/task-trace/scripts/task_trace.py uninstall-hooks
```

The task documents and session bindings are preserved. `--codex-home PATH` lets
the installer target a specific host configuration directory; task binding and
loading use the runtime's `CODEX_HOME` environment variable.

## Migrate from Project Memory

Before updating or moving an old installation, run its existing
`scripts/project_memory.py uninstall-hooks` command to remove the old handler.
Then use the renamed `task-trace` skill directory and `scripts/task_trace.py`
script, and run `install-hooks` from that stable installed path. Review and
trust the new exact definition in the Codex CLI's `/hooks` before it can run.

To retain existing bindings, move `${CODEX_HOME:-~/.codex}/project-memory/bindings/`
to `${CODEX_HOME:-~/.codex}/task-trace/bindings/`. If the destination already exists,
inspect and reconcile its bindings before proceeding; do not overwrite it.
Task documents do not need to be renamed. Without migrating bindings, bind the
intended task again with the new script.

## Bind the task after selecting its records

When maintaining records is authorized, bind the current session after the plan
exists. Replace the example paths with the actual workspace and records:

```sh
python3 ~/.agents/skills/task-trace/scripts/task_trace.py bind \
  --workspace /path/to/project \
  --plan docs/tasks/account-sync/PLAN.md \
  --worklog docs/tasks/account-sync/WORKLOG.md
```

The command uses `CODEX_THREAD_ID`. If that variable is unavailable, pass a known
`--session-id` from the host; never guess it from the newest transcript or a file
modification time. If the ID cannot be established, use manual recovery and
report that automatic binding is unavailable. A worklog may be absent during
early planning; it is loaded once it exists. Existing nonstandard filenames can
be supplied, so the workflow does not need to rename project documents.

Bindings live in `${CODEX_HOME:-~/.codex}/task-trace/bindings/`, one JSON file
per session. They contain version metadata, session identity, and workspace and
document paths, not document contents. Rebinding the
same session deliberately switches its task. Other sessions retain their own
bindings. Do not bind or unbind during a read-only task unless those bookkeeping
writes were already authorized.

When a conversation moves to an unrelated task, remove or replace its binding:

```sh
python3 ~/.agents/skills/task-trace/scripts/task_trace.py unbind
```

Keep completed task documents. A completed checkpoint can remain bound for a
follow-up, but it is historical context, not a request to continue working.

## What reloads

On `SessionStart` with source `startup`, `resume`, `compact`, or `fork`, the hook
uses the exact supplied session ID and checks that the current directory is
inside its bound workspace. A new or forked session with no binding returns no
context and creates nothing. `clear` is deliberately excluded. No project-wide
search or most-recent-task heuristic is used.

The hook reads `## Recovery summary` from the plan and `## Current checkpoint`
from the worklog. Each excerpt is bounded; the combined context is limited to
10,000 characters. Without those headings, it uses a bounded file-start excerpt
and identifies the fallback. Older records remain usable without rewriting them.
Long history stays in the files for targeted reads. JSON-quoted historical data
is accompanied by an instruction to preserve current scope and verify facts.

The agent must reconcile the loaded records with the latest request and relevant
artifacts. Loading a next step does not authorize executing it, and recorded
success does not establish that checks really passed. Missing records are
reported as missing. Invalid input, broken bindings, or unsafe paths produce no
task data; the hook returns success so recovery failures cannot trap a turn.
They do not satisfy an outstanding requirement to save requested documents.

No `Stop`, `PreToolUse`, or `PreCompact` handlers are installed. Save checkpoints
after meaningful progress during normal work; do not wait for a last-chance hook.
The loader neither summarizes transcripts nor writes task records.

## Verification and references

Run the isolated behavioral checks from the repository root:

```sh
python3 -m unittest discover -s tests -v
```

Tests of the loader and configuration merger are distinct from a live host
lifecycle test. Report which actually ran; hook trust and host support must be
verified before claiming automatic reload is active.

- [Codex hooks: lifecycle events, configuration, and trust](https://learn.chatgpt.com/docs/hooks)
- [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills)
