# Project Memory

English | [简体中文](README.zh-CN.md)

A Codex skill for discussing project decisions, keeping a clear plan, and
maintaining enough execution context to resume long-running work.

The skill captures why an approach was chosen, what actually changed, what was
verified, and what to do next. It keeps planning and execution records in the
project workspace and follows the user's existing scope and authorization.

## When to use it

- Planning a project or comparing approaches with meaningful tradeoffs.
- Carrying an agreed plan through several stages of implementation.
- Resuming a task after an interruption, handoff, or context compaction.

Ordinary questions and isolated small edits do not require this workflow unless
they continue a tracked task or the user explicitly invokes the skill.

## Two complementary documents

| Document | Purpose | Contents |
| --- | --- | --- |
| `PLAN.md` | Intended outcomes and decisions | Goals, constraints, assumptions, options under discussion, selected approach, confirmation basis, and acceptance criteria. |
| `WORKLOG.md` | Actual state and evidence | A current checkpoint, decision reasons, meaningful changes, affected files, verification results, remaining work, and the next authorized action. |

The skill reuses existing project records. When new records are needed, it follows
the project's documentation convention, defaulting to
`docs/tasks/<short-task-name>/`. The [plan](assets/PLAN.md) and
[worklog](assets/WORKLOG.md) templates are starting points; irrelevant sections
are omitted. Task data belongs in the project workspace, not this skill's
installation directory.

## How it works

1. **Discuss the choice.** Separate confirmed requirements, assumptions,
   candidates, and recommendations. Explain important tradeoffs and ask questions
   that can change the decision.
2. **Record agreement.** Preserve what the user selected and its scope. Partial
   agreement stays partial; agreeing to a plan does not automatically authorize
   implementation.
3. **Converge the plan.** Move the essential reasons for rejecting alternatives
   into the worklog before removing resolved comparisons from the plan. Keep
   unresolved choices visible.
4. **Track meaningful changes.** Record what changed, where, why, and the actual
   verification result. Group related edits instead of logging every save or
   tool call, and keep the current checkpoint up to date.
5. **Resume from evidence.** Read the plan and checkpoint, inspect relevant
   files or workspace differences, resolve stale claims, and continue authorized
   work. At completion, record outcomes and remaining limitations.

## Install

With Git installed, clone this repository into a user-level Codex skill directory:

```sh
mkdir -p ~/.agents/skills
git clone https://github.com/Yu03-6/project-memory.git ~/.agents/skills/project-memory
```

If your environment already uses another supported skill directory, use that
location instead. Keep one discoverable copy; do not overwrite an existing
`project-memory` directory. Codex detects skill changes automatically; restart
Codex if the skill does not appear. See the official
[skill documentation](https://learn.chatgpt.com/docs/build-skills) for discovery
and configuration details.

The skill contains Markdown instructions and templates. It has no additional
runtime dependencies or background service.

## Use

Automatic matching is enabled in [agents/openai.yaml](agents/openai.yaml).
Codex can select the skill when the task matches its description. You can also
invoke it explicitly:

**Plan without implementing**

```text
Use $project-memory to compare approaches for our internal knowledge base.
Discuss the tradeoffs and record the plan, but do not implement it yet.
```

**Confirm a choice and start work**

```text
Use $project-memory. Choose approach A, exclude payments, and implement the
agreed scope. Keep the execution checkpoint and meaningful changes current.
```

**Resume a task**

```text
Use $project-memory to resume the task in docs/tasks/internal-knowledge-base/.
Read the plan and checkpoint, check the actual workspace, and finish the
remaining work within the previously authorized scope.
```

Requests can be written in English or Chinese. Task documents follow the
project's language requirements. Explicit chat-only, read-only, or no-file
instructions take precedence over automatic documentation.

## Repository contents

- [SKILL.md](SKILL.md): workflow, decision handling, and recovery instructions.
- [agents/openai.yaml](agents/openai.yaml): display metadata and invocation policy.
- [assets/PLAN.md](assets/PLAN.md): planning template.
- [assets/WORKLOG.md](assets/WORKLOG.md): checkpoint and history template.

## Practical limits

Automatic matching is a model decision, so it is not guaranteed on every request.
The skill does not monitor files in the background or guarantee lossless memory.
Recovery depends on keeping records current, locating them, reading them, and
checking relevant facts. A log entry is not proof that a change or test succeeded.
