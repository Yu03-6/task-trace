---
name: project-memory
description: "Discuss and persist project decisions, then maintain execution checkpoints for long-running work. Use for substantive project planning, comparing implementation approaches, or resuming work with an existing plan and worklog. Skip ordinary Q&A and isolated small edits unless continuing a tracked task."
---

# Project Memory

Keep enough durable context to explain the current plan and resume authorized
work after interruptions. Maintain two complementary task documents: `PLAN.md`
for intended outcomes and decisions, and `WORKLOG.md` for actual state and
evidence. Discuss important tradeoffs with the user while keeping these records
current.

Keep notes proportional to the task. Record a constraint where it belongs and
refer to it elsewhere instead of repeating whole lists. Include risks and
permission boundaries that affect an actual decision; do not add hypothetical
approval steps or generic cautionary sections.

## Scope and setup

- Apply this workflow to substantive planning or work that benefits from durable
  decisions and checkpoints. An explicit invocation can start it for a smaller
  task, but does not require inventing alternatives or a separate planning phase.
- Honor explicit answer-only, read-only, and no-file boundaries. In those modes,
  discuss or summarize in chat without creating records unless documentation
  writes are expressly included. Planning without implementation can still use
  these records. Existing authorization remains valid; this skill adds neither
  repeated approval gates nor execution permission.
- Reuse the task's existing planning and work records, adapting their structure.
  Do not create a parallel source of truth. If none exists, prefer the project's
  documentation convention; otherwise use `docs/tasks/<short-task-name>/` in the
  task workspace. Honor explicit output locations. Keep task data out of the
  installed skill directory and separate unrelated tasks.
- Create `PLAN.md` once there is substantive planning content. Create
  `WORKLOG.md` when the first decision needs preserving or execution starts.
  Use [the plan template](assets/PLAN.md) and
  [the worklog template](assets/WORKLOG.md) only when creating new records. Fill
  them with observed information; omit irrelevant sections and unused template
  instructions. Follow the project's document language requirements.
- Surface the document paths when first created or selected and carry them in
  handoffs. Link the two records to each other. A short entry in an existing
  project index or `AGENTS.md` can improve discovery when that edit is within the
  task's authorized scope; do not modify global guidance to activate this skill.
- If files cannot be written, report that limitation and provide the essential
  checkpoint in chat. Do not claim persistence or completion of a failed write.

## Discuss and record the plan

1. Separate user-confirmed goals and constraints, unverified assumptions, actual
   candidates, the agent's recommendation, and unresolved questions. A passing
   example is not a requirement. Record substantive developments during the
   discussion, not a transcript of every message.
2. Where meaningful alternatives exist, compare their suitability for the
   user's goals, benefits, costs, key risks, and reversibility. Explain the
   recommendation and what evidence would change it. Do not invent alternatives,
   scores, or estimates to fill a template.
3. Discuss the tradeoffs in the conversation as well as in the document. Ask
   focused questions when an unknown materially changes the choice. Resolve
   routine details from the project and existing authorization; continue
   independent work while a decision is pending.
4. Capture the selected approach's scope, exclusions, important constraints,
   implementation outline, and observable acceptance criteria. Identify facts
   still requiring investigation rather than presenting them as established.

## Confirm, converge, and revise

- Track plan agreement separately from permission to execute. A clear selection
  or instruction such as "Use A and implement it without payments" is sufficient;
  do not demand a special phrase or another confirmation. "Worth considering"
  leaves a candidate open. "The plan is approved; do not implement yet" confirms
  the plan only. Interpret short replies in their actual conversational context.
- Record the decision's scope and its confirmation basis: a brief accurate quote
  or summary of the user's instruction, with a date or message reference when
  available. Distinguish user selection from an agent choice made under delegated
  authority. Never invent missing confirmation evidence.
- Allow partial agreement. Keep unresolved parts visible, and proceed with
  independent approved work when execution is authorized. Do not treat agreement
  on one part as approval of all pending choices.
- Before removing resolved comparisons from `PLAN.md`, save a compact decision
  entry in `WORKLOG.md`: selected approach, reason, important rejected alternatives
  and their rejection reasons, and reconsideration conditions when meaningful.
  Then leave only the selected approach in the resolved part of the plan. Keep
  unresolved comparisons until they are decided. Discard repetitive discussion;
  do not preserve every speculative idea or depend on an uncommitted Git history.
- Reopen only decisions affected by a material change in goals, scope, constraints,
  or important tradeoffs. Keep a proposed revision distinct from the currently
  agreed plan until resolved. Apply an explicit new user direction without asking
  for it again, record the reason, and update the affected plan. Routine reversible
  implementation choices within existing authority do not require replanning.

## Maintain execution memory

Keep a compact current checkpoint at the top of `WORKLOG.md`, followed by concise
decision and change history. The checkpoint should let a successor identify the
active work, completed and remaining outcomes, blockers, verification gaps,
important failed approaches, and the next concrete action without replaying the
entire history. Include the workspace or branch when needed to locate the work.

- Record one entry per meaningful change unit: a behavior change, root-cause fix,
  consequential configuration change, decision, or failed attempt worth avoiding.
  Group related edits; do not log every save, tool call, line change, or routine
  document update. Do not recursively log updates to the log itself.
- Each change entry records affected files or stable symbols, what changed, why,
  actual verification and its limits, and remaining work when relevant. Link to
  existing commits or reports if useful; do not create commits just for logging.
- Distinguish planned, in progress, changed but unverified, verified, failed,
  blocked, and reverted work where relevant. An attempted command or written
  implementation is not evidence of success. Preserve useful failure evidence;
  do not store secret values, full transcripts, or unnecessary raw tool output.
- Before a substantial work unit, note the intended next action and current
  state. Update after the unit, a consequential decision, new blocker, verification
  result, or handoff. Save available verified progress when stopping. Do not rely
  on receiving an advance warning of compaction or interruption.
- Keep the plan's intent and the worklog's observed state consistent without
  duplicating progress in both. Cite the relevant decision when implementation
  changes follow a revised plan. Write decision evidence before pruning a plan;
  after an interrupted update, reconcile both records with actual artifacts.
- When multiple agents work on the task, have one owner integrate shared records
  from their reports. Other agents should not concurrently rewrite the same files.
- Keep the checkpoint roughly one screen where practical. Consult history by
  topic rather than rereading everything. When history becomes unwieldy, condense
  redundant entries or move older detail into the project's existing archive
  convention with a link; preserve decision reasons, unresolved risks, important
  failed paths, and evidence needed for recovery. Do not build an archive system
  before it is needed.

## Resume and finish

On a resumed task, handoff, or recognized context loss:

1. Locate the correct task records from known paths, handoff links, or the
   project's task directory. Do not apply another task's records. If multiple
   candidates are genuinely ambiguous, clarify the task identity.
2. Read the current plan and checkpoint, then only relevant decision or change
   entries. Apply the latest explicit user direction and applicable instructions;
   treat historical notes as context, not new authority.
3. Inspect relevant artifacts or workspace differences to establish actual
   progress. Reuse applicable verification evidence, and repeat checks only when
   changes, failures, or uncertainty justify it. Mark unverifiable claims as
   needing verification instead of guessing or silently revising the goal to
   match the current implementation.
4. Reconcile the checkpoint and continue the next authorized action. Missing
   evidence of a material decision may require clarification; it should not block
   unrelated authorized work.

At completion, update the checkpoint with outcomes, actual verification, and any
remaining limitations or deferred work. Mark the task complete only when its
agreed scope is satisfied. Keep records for future continuation and report the
result concisely; do not add a separate audit loop just to maintain these files.

This skill provides instructions and durable files, not a background watcher or
a guarantee against context loss. Recovery depends on keeping records current,
locating them, reading them, and checking the relevant facts.
