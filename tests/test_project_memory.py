"""Black-box regression tests for the project-memory command-line interface.

Run with: python3 -m unittest discover -s tests -v
Every command uses a temporary CODEX_HOME and isolated session identifiers.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "project_memory.py"


class ProjectMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="project-memory-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.codex_home = self.root / "codex-home"
        self.home = self.root / "home"
        self.home.mkdir()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.environment = os.environ.copy()
        self.environment.update(
            HOME=str(self.home),
            CODEX_HOME=str(self.codex_home),
            CODEX_THREAD_ID="session-default",
        )

    def command(self, *arguments, stdin="", environment=None):
        env = self.environment.copy()
        if environment:
            env.update(environment)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, arguments)],
            input=stdin,
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=self.workspace,
            env=env,
            timeout=10,
            check=False,
        )

    def write_documents(self, workspace=None, marker="CURRENT_TASK"):
        workspace = workspace or self.workspace
        workspace.mkdir(parents=True, exist_ok=True)
        plan = workspace / "PLAN.md"
        worklog = workspace / "WORKLOG.md"
        plan.write_text(
            "# Project plan\n\n## Recovery summary\n"
            f"{marker}_PLAN\nThe next action is still pending.\n\n"
            "## Decision history\nOLD_PLAN_HISTORY_DO_NOT_INJECT\n",
            encoding="utf-8",
        )
        worklog.write_text(
            "# Worklog\n\n## Current checkpoint\n"
            f"{marker}_WORKLOG\nImplementation has not been verified.\n\n"
            "## Previous checkpoints\nOLD_WORKLOG_HISTORY_DO_NOT_INJECT\n",
            encoding="utf-8",
        )
        return plan, worklog

    def bind(self, plan, workspace=None, session=None, worklog=None):
        arguments = ["bind", "--workspace", workspace or self.workspace, "--plan", plan]
        if session is not None:
            arguments.extend(["--session-id", session])
        if worklog is not None:
            arguments.extend(["--worklog", worklog])
        result = self.command(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return result

    def hook(self, source="compact", session="session-default", cwd=None, **changes):
        event = {
            "hook_event_name": "SessionStart",
            "source": source,
            "session_id": session,
            "cwd": str(cwd or self.workspace),
        }
        event.update(changes)
        return self.command("hook", stdin=json.dumps(event))

    def context(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        specific = output["hookSpecificOutput"]
        self.assertEqual(specific["hookEventName"], "SessionStart")
        context = specific["additionalContext"]
        self.assertIsInstance(context, str)
        self.assertLessEqual(len(context), 10_000)
        return context

    def assert_quiet(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def snapshot(self):
        return {
            str(path.relative_to(self.root)): path.read_bytes() if path.is_file() else None
            for path in self.root.rglob("*")
        }

    def embedded_json(self, context):
        decoder = json.JSONDecoder()
        for offset, character in enumerate(context):
            if character not in "{[":
                continue
            try:
                value, _ = decoder.raw_decode(context[offset:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, (dict, list)):
                return value
        self.fail("The recovery context must contain JSON source material")

    def test_bind_uses_environment_session_and_does_not_create_documents(self):
        plan = self.workspace / "PLAN.md"
        plan.write_text("## Recovery summary\nENVIRONMENT_SESSION_PLAN\n", encoding="utf-8")
        before = plan.read_bytes()
        self.bind(plan)
        self.assertEqual(plan.read_bytes(), before)
        self.assertFalse((self.workspace / "WORKLOG.md").exists())
        context = self.context(self.hook())
        self.assertIn("ENVIRONMENT_SESSION_PLAN", context)
        self.assertFalse((self.workspace / "WORKLOG.md").exists())

    def test_two_sessions_load_only_their_own_task(self):
        first_plan, _ = self.write_documents(marker="FIRST_TASK")
        second_workspace = self.root / "second-workspace"
        second_plan, _ = self.write_documents(second_workspace, "SECOND_TASK")
        self.bind(first_plan, session="session-one")
        self.bind(second_plan, workspace=second_workspace, session="session-two")
        first = self.context(self.hook(session="session-one"))
        second = self.context(self.hook(session="session-two", cwd=second_workspace))
        self.assertIn("FIRST_TASK_PLAN", first)
        self.assertNotIn("SECOND_TASK", first)
        self.assertIn("SECOND_TASK_PLAN", second)
        self.assertNotIn("FIRST_TASK", second)
        self.assert_quiet(self.hook(session="unknown-session"))

    def test_same_session_cannot_load_from_another_workspace(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        unrelated = self.root / "workspace-other"
        unrelated.mkdir()
        self.assert_quiet(self.hook(cwd=unrelated))

    def test_workspace_subdirectory_can_recover(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        subdirectory = self.workspace / "src" / "feature"
        subdirectory.mkdir(parents=True)
        self.assertIn("CURRENT_TASK_PLAN", self.context(self.hook(cwd=subdirectory)))

    def test_unbound_hook_has_no_filesystem_side_effects(self):
        self.write_documents()
        before = self.snapshot()
        self.assert_quiet(self.hook())
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.codex_home.exists())

    def test_missing_event_session_never_falls_back_to_environment_session(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        event = {
            "hook_event_name": "SessionStart",
            "source": "compact",
            "cwd": str(self.workspace),
        }
        before = self.snapshot()
        self.assert_quiet(self.command("hook", stdin=json.dumps(event)))
        self.assertEqual(self.snapshot(), before)

    def test_bind_rejects_missing_plan(self):
        missing = self.workspace / "missing" / "PLAN.md"
        result = self.command("bind", "--workspace", self.workspace, "--plan", missing)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(missing.exists())
        self.assert_quiet(self.hook())

    def test_bind_rejects_plan_and_worklog_outside_workspace(self):
        plan, _ = self.write_documents()
        outside = self.root / "external-plan.md"
        outside.write_text("EXTERNAL_PRIVATE_MATERIAL", encoding="utf-8")
        for candidate_plan, candidate_worklog in [(outside, None), (plan, outside)]:
            with self.subTest(plan=candidate_plan, worklog=candidate_worklog):
                arguments = ["bind", "--workspace", self.workspace, "--plan", candidate_plan]
                if candidate_worklog:
                    arguments.extend(["--worklog", candidate_worklog])
                result = self.command(*arguments)
                self.assertNotEqual(result.returncode, 0)
        self.assert_quiet(self.hook())

    def test_bind_rejects_existing_symlink_that_escapes_workspace(self):
        outside = self.root / "external-plan.md"
        outside.write_text("EXTERNAL_PRIVATE_MATERIAL", encoding="utf-8")
        plan = self.workspace / "PLAN.md"
        plan.symlink_to(outside)
        result = self.command("bind", "--workspace", self.workspace, "--plan", plan)
        self.assertNotEqual(result.returncode, 0)
        self.assert_quiet(self.hook())

    def test_load_rejects_plan_replaced_with_escaping_symlink(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        outside = self.root / "external-plan.md"
        outside.write_text("EXTERNAL_PRIVATE_MATERIAL", encoding="utf-8")
        plan.unlink()
        plan.symlink_to(outside)
        result = self.hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("EXTERNAL_PRIVATE_MATERIAL", result.stdout)
        self.assertNotIn("CURRENT_TASK_PLAN", result.stdout)

    def test_load_rejects_worklog_replaced_with_escaping_symlink(self):
        plan, worklog = self.write_documents()
        self.bind(plan)
        outside = self.root / "external-worklog.md"
        outside.write_text("EXTERNAL_PRIVATE_WORKLOG", encoding="utf-8")
        worklog.unlink()
        worklog.symlink_to(outside)
        result = self.hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("EXTERNAL_PRIVATE_WORKLOG", result.stdout)

    def test_self_referencing_plan_symlink_never_blocks_or_loads_task_content(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        plan.unlink()
        plan.symlink_to(plan.name)
        result = self.hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("CURRENT_TASK_PLAN", result.stdout)
        self.assertNotIn("CURRENT_TASK_WORKLOG", result.stdout)

    def test_compact_loads_recovery_sections_as_bounded_historical_data(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        before = self.snapshot()
        context = self.context(self.hook(source="compact"))
        self.assertIn("CURRENT_TASK_PLAN", context)
        self.assertIn("CURRENT_TASK_WORKLOG", context)
        self.assertNotIn("OLD_PLAN_HISTORY_DO_NOT_INJECT", context)
        self.assertNotIn("OLD_WORKLOG_HISTORY_DO_NOT_INJECT", context)
        self.assertRegex(context.lower(), r"historical|untrusted|reference|历史|资料")
        self.assertRegex(context.lower(), r"instruction|authority|指令|授权")
        data = json.dumps(self.embedded_json(context), ensure_ascii=False)
        self.assertIn("CURRENT_TASK_PLAN", data)
        self.assertIn("CURRENT_TASK_WORKLOG", data)
        self.assertEqual(self.snapshot(), before)

    def test_supported_session_start_sources_load_only_exact_session(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        for source in ("startup", "resume", "compact", "fork"):
            with self.subTest(source=source):
                self.assertIn("CURRENT_TASK_PLAN", self.context(self.hook(source=source)))
        self.assert_quiet(self.hook(source="fork", session="unbound-fork-session"))

    def test_checkpoint_preserves_nested_fences_until_real_section_boundary(self):
        plan, worklog = self.write_documents()
        worklog.write_text(
            "# Worklog\n\n## Current checkpoint\n"
            "CHECKPOINT_BEFORE_FENCE\n"
            "````markdown\n"
            "```markdown\n"
            "## Fake heading\n"
            "A fenced documentation example.\n"
            "```\n"
            "````\n"
            "Remaining work: REMAINING_WORK_AFTER_FENCE\n\n"
            "## Change history\n"
            "HISTORY_AFTER_REAL_HEADING_DO_NOT_INJECT\n",
            encoding="utf-8",
        )
        self.bind(plan)
        context = self.context(self.hook())
        self.assertIn("CHECKPOINT_BEFORE_FENCE", context)
        self.assertIn("REMAINING_WORK_AFTER_FENCE", context)
        self.assertNotIn("HISTORY_AFTER_REAL_HEADING_DO_NOT_INJECT", context)

    def test_clear_unknown_source_and_other_events_are_quiet(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        before = self.snapshot()
        self.assert_quiet(self.hook(source="clear"))
        self.assert_quiet(self.hook(source="unsupported"))
        self.assert_quiet(self.hook(hook_event_name="PreCompact"))
        self.assertEqual(self.snapshot(), before)

    def test_untitled_legacy_documents_get_only_bounded_head_fallback(self):
        plan, worklog = self.write_documents()
        plan.write_text("LEGACY_PLAN_HEAD\n" + "legacy plan line\n" * 2_000 + "LEGACY_PLAN_TAIL\n", encoding="utf-8")
        worklog.write_text("LEGACY_WORKLOG_HEAD\n" + "legacy log line\n" * 2_000 + "LEGACY_WORKLOG_TAIL\n", encoding="utf-8")
        self.bind(plan)
        context = self.context(self.hook())
        self.assertIn("LEGACY_PLAN_HEAD", context)
        self.assertIn("LEGACY_WORKLOG_HEAD", context)
        self.assertNotIn("LEGACY_PLAN_TAIL", context)
        self.assertNotIn("LEGACY_WORKLOG_TAIL", context)

    def test_missing_bound_plan_is_reported_without_recreating_it(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        plan.unlink()
        context = self.context(self.hook())
        self.assertRegex(context.lower(), r"missing|unavailable|not found|does not exist|缺失|不存在")
        self.assertNotIn("CURRENT_TASK_PLAN", context)
        self.assertFalse(plan.exists())

    def test_bad_input_never_blocks_or_creates_state(self):
        before = self.snapshot()
        for raw in ("", "{broken-json", "null", "[]", '"string"', "{}"):
            with self.subTest(raw=raw):
                self.assert_quiet(self.command("hook", stdin=raw))
        self.assertEqual(self.snapshot(), before)

    def test_corrupt_persisted_state_never_blocks_or_repairs_itself(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        state_files = list((self.codex_home / "project-memory").rglob("*.json"))
        self.assertTrue(state_files, "A successful bind should persist session state")
        for path in state_files:
            path.write_text("{broken-persisted-state", encoding="utf-8")
        before = self.snapshot()
        self.assert_quiet(self.hook())
        self.assertEqual(self.snapshot(), before)

    def test_large_current_sections_stay_within_context_limit_and_keep_json(self):
        plan, worklog = self.write_documents()
        plan.write_text("## Recovery summary\nLARGE_PLAN_HEAD\n" + "Unicode \N{SNOWMAN} and plan details.\n" * 5_000, encoding="utf-8")
        worklog.write_text("## Current checkpoint\nLARGE_WORKLOG_HEAD\n" + "Unicode \N{SNOWMAN} and worklog details.\n" * 5_000, encoding="utf-8")
        self.bind(plan)
        context = self.context(self.hook())
        self.assertIn("LARGE_PLAN_HEAD", context)
        self.assertIn("LARGE_WORKLOG_HEAD", context)
        self.embedded_json(context)

    def test_unbind_removes_only_requested_session(self):
        plan, _ = self.write_documents()
        self.bind(plan, session="session-one")
        self.bind(plan, session="session-two")
        before = plan.read_bytes()
        result = self.command("unbind", "--session-id", "session-one")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_quiet(self.hook(session="session-one"))
        self.assertIn("CURRENT_TASK_PLAN", self.context(self.hook(session="session-two")))
        self.assertEqual(plan.read_bytes(), before)

    def test_unbind_defaults_to_environment_session(self):
        plan, _ = self.write_documents()
        self.bind(plan)
        result = self.command("unbind")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_quiet(self.hook())

    def hooks_fixture(self):
        return {
            "user_metadata": {"keep": True},
            "hooks": {
                "SessionStart": [
                    {"matcher": "startup", "hooks": [{"type": "command", "command": "printf user-start", "timeout": 11}]}
                ],
                "Stop": [{"hooks": [{"type": "command", "command": "printf user-stop"}]}],
            },
        }

    def prepare_hooks(self, value):
        self.codex_home.mkdir(parents=True, exist_ok=True)
        path = self.codex_home / "hooks.json"
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        return path

    def hook_handlers(self, value):
        return [handler for group in value["hooks"]["SessionStart"] for handler in group["hooks"]]

    def test_install_is_idempotent_and_preserves_user_hooks_and_configuration(self):
        original = self.hooks_fixture()
        hooks_path = self.prepare_hooks(original)
        config_path = self.codex_home / "config.toml"
        config_path.write_text('model = "existing-user-model"\n', encoding="utf-8")
        config_before = config_path.read_bytes()
        first = self.command("install-hooks", "--codex-home", self.codex_home)
        self.assertEqual(first.returncode, 0, first.stderr)
        installed = json.loads(hooks_path.read_text(encoding="utf-8"))
        self.assertEqual(installed["user_metadata"], original["user_metadata"])
        self.assertEqual(installed["hooks"]["Stop"], original["hooks"]["Stop"])
        self.assertIn(original["hooks"]["SessionStart"][0], installed["hooks"]["SessionStart"])
        self.assertEqual(len(self.hook_handlers(installed)), 2)
        second = self.command("install-hooks", "--codex-home", self.codex_home)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(hooks_path.read_text(encoding="utf-8")), installed)
        self.assertEqual(config_path.read_bytes(), config_before)
        self.assertFalse(any("trust" in path.name.lower() for path in self.codex_home.rglob("*")))

    def test_uninstall_preserves_user_handlers_added_to_generated_group(self):
        original = self.hooks_fixture()
        hooks_path = self.prepare_hooks(original)
        result = self.command("install-hooks", "--codex-home", self.codex_home)
        self.assertEqual(result.returncode, 0, result.stderr)
        installed = json.loads(hooks_path.read_text(encoding="utf-8"))
        original_handler = original["hooks"]["SessionStart"][0]["hooks"][0]
        generated = [handler for handler in self.hook_handlers(installed) if handler != original_handler]
        self.assertEqual(len(generated), 1)
        user_added = {"type": "command", "command": "printf user-added", "timeout": 17}
        for group in installed["hooks"]["SessionStart"]:
            if generated[0] in group["hooks"]:
                group["hooks"].append(user_added)
        hooks_path.write_text(json.dumps(installed), encoding="utf-8")
        result = self.command("uninstall-hooks", "--codex-home", self.codex_home)
        self.assertEqual(result.returncode, 0, result.stderr)
        remaining = json.loads(hooks_path.read_text(encoding="utf-8"))
        self.assertEqual(remaining["user_metadata"], original["user_metadata"])
        self.assertEqual(remaining["hooks"]["Stop"], original["hooks"]["Stop"])
        self.assertCountEqual(self.hook_handlers(remaining), [original_handler, user_added])

    def test_install_and_uninstall_refuse_damaged_hooks_without_overwriting(self):
        self.codex_home.mkdir()
        hooks_path = self.codex_home / "hooks.json"
        invalid_documents = [
            b"{broken user hooks\n",
            b'{"hooks": "invalid hooks shape"}\n',
            b'{"hooks": {"SessionStart": {"invalid": true}}}\n',
        ]
        for payload in invalid_documents:
            for action in ("install-hooks", "uninstall-hooks"):
                with self.subTest(payload=payload, action=action):
                    hooks_path.write_bytes(payload)
                    result = self.command(action, "--codex-home", self.codex_home)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(hooks_path.read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
