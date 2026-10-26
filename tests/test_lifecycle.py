import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from auto_skill import cli

REPO = Path(__file__).resolve().parents[1]
EVENT = json.loads((REPO / "examples/milestone.json").read_text())
RECIPE = json.loads((REPO / "examples/recipe.json").read_text())
UPDATE = json.loads((REPO / "examples/update-milestone.json").read_text())
UPDATE_RECIPE = json.loads((REPO / "examples/update-recipe.json").read_text())


class JsonInputs(unittest.TestCase):
    def test_unicode_scope_survives_legacy_stdout_without_changing_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            command = [sys.executable, str(REPO / "auto_skill/cli.py"), "--workspace", str(root)]
            environment = {**os.environ, "PYTHONIOENCODING": "cp1252"}
            subprocess.run(command + ["install", "--agent", "generic"], env=environment,
                           capture_output=True, check=True)
            event = {**EVENT, "scope": "整理虚构访谈记录 📚"}
            source = root / "event.json"
            source.write_text(json.dumps(event, ensure_ascii=False), encoding="utf-8")
            for args in (["assess", "--event", str(source)],
                         ["consent", "--name", event["skill_name"], "--decision", "approve"], ["status"]):
                result = subprocess.run(command + args, env=environment, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                result.stdout.decode("ascii")  # Transport is safe even on a legacy pipe.
                parsed = json.loads(result.stdout)
                if args[0] != "consent":
                    self.assertIn(event["scope"], json.dumps(parsed, ensure_ascii=False))
            state = root / ".auto-skill/state.json"
            self.assertIn(event["scope"], state.read_text(encoding="utf-8"))

    def test_stop_hook_rejects_ambiguous_retry_guards_without_reentering(self):
        command = [sys.executable, str(REPO / "auto_skill/cli.py"), "hook-stop"]
        for raw in ('{"hook_event_name":"Stop","stop_hook_active":true,"stop_hook_active":false}',
                    '{"hook_event_name":"Other","hook_event_name":"Stop","stop_hook_active":false}'):
            result = subprocess.run(command, input=raw, text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertNotIn("stop_hook_active", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        valid = subprocess.run(command, input='{"hook_event_name":"Stop","stop_hook_active":true}',
                               text=True, encoding="utf-8", capture_output=True, check=True)
        self.assertEqual(json.loads(valid.stdout), {})

    def test_managed_read_limit_checks_actual_bytes_after_stale_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            store = cli.Store(directory)
            file = Path(directory) / "fictional-state.json"
            file.write_bytes(b"fictional\r\nstate\r")
            self.assertEqual(store.read("fictional-state.json"), "fictional\nstate\n")
            file.write_bytes(b" " * 8_000_001)
            with patch.object(store, "path", return_value=file), patch.object(Path, "is_file", return_value=True), \
                    patch.object(Path, "stat") as metadata:
                metadata.return_value.st_size = 1
                with self.assertRaisesRegex(cli.Error, "managed_file_invalid_or_too_large"):
                    store.read("fictional-state.json")

    def test_read_limit_does_not_trust_stale_file_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "growing.json"
            path.write_bytes(b"{}" + b" " * 64)
            # A source may grow after its metadata was checked.
            with patch.object(Path, "is_file", return_value=True), patch.object(Path, "stat") as metadata:
                metadata.return_value.st_size = 1
                with self.assertRaisesRegex(cli.Error, "input_missing_or_too_large"):
                    cli.load(path, limit=32)

    def test_duplicate_top_level_and_nested_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for raw in ('{"verified":false,"verified":true}',
                        '{"validation":{"passed":false,"passed":true}}'):
                with self.subTest(raw=raw):
                    path.write_text(raw, encoding="utf-8")
                    with self.assertRaises(cli.Error):
                        cli.load(path)


class Lifecycle(unittest.TestCase):
    def test_invalid_recovery_snapshot_is_refused_before_any_restore(self):
        self.store.write("a.txt", "Fictional current content")
        snapshots = [
            {"a.txt": "Fictional restored content", "../fictional-outside": None},
            {"a.txt": "Fictional restored content", "": None},
            {"a.txt": "Fictional restored content", ".agents": None},
            {"a.txt": "Fictional restored content", "b.txt": 42},
            {"a.txt": "Fictional restored content", "b.txt": "\ud800"},
            [],
        ]
        journals = [json.dumps({"before": snapshot}) for snapshot in snapshots]
        journals.append('{"before":{"a.txt":"Fictional first","a.txt":"Fictional second"}}')
        command = [sys.executable, str(REPO / "auto_skill/cli.py"), "--workspace", str(self.root), "recover"]
        for raw in journals:
            self.store.write(cli.JOURNAL, raw)
            before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(b"Traceback", result.stderr)
            self.assertNotIn(b"Fictional", result.stderr)
            after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
            self.assertEqual(after, before)
        self.store.write("b.txt", "Fictional interrupted new file")
        self.store.write(cli.JOURNAL, json.dumps({"before": {"a.txt": "Fictional restored content", "b.txt": None}}))
        subprocess.run(command, capture_output=True, check=True)
        self.assertEqual(self.store.read("a.txt"), "Fictional restored content")
        self.assertIsNone(self.store.read("b.txt"))
        self.assertIsNone(self.store.read(cli.JOURNAL))

    def test_ambiguous_history_cannot_be_installed_or_rolled_back(self):
        self.create()
        history = self.root / ".auto-skill/history/summarize-interviews/1.json"
        raw = history.read_text(encoding="utf-8")
        history.write_text(raw.replace('"content":', '"content":"Fictional ambiguous marker","content":', 1),
                           encoding="utf-8")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        command = [sys.executable, str(REPO / "auto_skill/cli.py"), "--workspace", str(self.root)]
        for args in (["install", "--agent", "generic"],
                     ["rollback", "--name", "summarize-interviews", "--revision", "1"]):
            result = subprocess.run(command + args, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(b"Traceback", result.stderr)
            self.assertNotIn(b"Fictional ambiguous marker", result.stderr)
            after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
            self.assertEqual(after, before)

    def test_unsupported_state_version_blocks_status_and_reinstallation(self):
        original = self.store.state()
        command = [sys.executable, str(REPO / "auto_skill/cli.py"), "--workspace", str(self.root)]
        for version in (2, True, 1.0, "1"):
            (self.root / cli.STATE).write_text(cli.encoded({**original, "version": version}), encoding="utf-8")
            before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
            for args in (["status"], ["install", "--agent", "generic"]):
                result = subprocess.run(command + args, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b"unsupported_state", result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)
                after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
                self.assertEqual(after, before)

    def test_ambiguous_persisted_consent_cannot_be_used_or_reinstalled(self):
        self.create()
        cli.consent(self.store, self.store.state(), EVENT["skill_name"], "pause")
        path = self.root / cli.STATE
        raw = path.read_text(encoding="utf-8")
        ambiguous = raw.replace('"decision": "pause"', '"decision":"pause","decision":"approve"')
        self.assertNotEqual(raw, ambiguous)
        path.write_text(ambiguous, encoding="utf-8")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        command = [sys.executable, str(REPO / "auto_skill/cli.py"), "--workspace", str(self.root)]
        for args in (["status"], ["install", "--agent", "generic"],
                     ["assess", "--event", str(REPO / "examples/update-milestone.json")]):
            result = subprocess.run(command + args, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(b"Traceback", result.stderr)
            self.assertNotIn(b"approve", result.stderr)
            after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
            self.assertEqual(after, before)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = cli.Store(self.root)
        cli.install(self.store, "all", "python3", False)

    def assess(self, item=EVENT):
        return cli.assess(self.store, self.store.state(), copy.deepcopy(item))

    def grant(self):
        cli.consent(self.store, self.store.state(), EVENT["skill_name"], "approve")

    def save(self, value=RECIPE):
        return cli.save(self.store, self.store.state(), copy.deepcopy(value))

    def create(self):
        self.assess()
        self.grant()
        self.save()

    def test_first_prompt_creates_nothing_and_repeat_does_not_nag(self):
        self.assertEqual(self.assess()["action"], "ask")
        self.assertFalse((self.root / ".agents/skills/summarize-interviews").exists())
        self.assertEqual(self.assess()["action"], "pending_consent")
        other_session = dict(EVENT, session_id="session-2")
        self.assertEqual(self.assess(other_session)["action"], "pending_consent")

    def test_consent_is_required(self):
        self.assess()
        with self.assertRaisesRegex(cli.Error, "consent_required"):
            self.save()
        with self.assertRaisesRegex(cli.Error, "no_pending_milestone"):
            cli.consent(self.store, self.store.state(), "other-topic", "approve")

    def test_decline_persists_and_explicit_approve_resumes(self):
        self.assess()
        cli.consent(self.store, self.store.state(), EVENT["skill_name"], "decline")
        self.assertEqual(self.assess(UPDATE)["reason"], "decline")
        self.grant()
        self.assertEqual(self.assess()["action"], "create")

    def test_verified_reusable_milestone_required(self):
        for item in (dict(EVENT, outcome="failure"), dict(EVENT, verified=False), dict(EVENT, lessons=[])):
            self.assertEqual(self.assess(item)["action"], "skip")
        self.assertEqual(self.store.state()["pending"], {})

    def test_update_retains_procedure_mirrors_and_history(self):
        self.create()
        self.assertEqual(self.assess(UPDATE)["action"], "update")
        self.assertEqual(self.save(UPDATE_RECIPE)["revision"], 2)
        a = self.store.read(".agents/skills/summarize-interviews/SKILL.md")
        b = self.store.read(".claude/skills/summarize-interviews/SKILL.md")
        self.assertEqual(a, b)
        self.assertIn("Label analyst interpretations", a)
        self.assertIn("opposing preferences", a)
        prior = json.loads(self.store.read(".auto-skill/history/summarize-interviews/1.json"))
        self.assertEqual(prior["event"], EVENT)
        self.assertEqual(prior["recipe"], RECIPE)

    def test_saved_event_is_idempotent(self):
        self.create()
        self.assertEqual(self.assess()["reason"], "already_saved")

    def test_scope_change_requires_new_consent(self):
        self.create()
        new = dict(UPDATE, scope="Different broader scope.")
        self.assertEqual(self.assess(new)["action"], "ask")
        with self.assertRaisesRegex(cli.Error, "scope_mismatch"):
            self.save(UPDATE_RECIPE)
        with self.assertRaisesRegex(cli.Error, "consent_required"):
            self.save(dict(UPDATE_RECIPE, scope=new["scope"]))

    def test_pause_keeps_existing_skill(self):
        self.create()
        cli.consent(self.store, self.store.state(), EVENT["skill_name"], "pause")
        self.assertEqual(self.assess(UPDATE)["reason"], "pause")
        self.assertIsNotNone(self.store.read(".agents/skills/summarize-interviews/SKILL.md"))

    def test_pause_after_assessment_blocks_pending_draft_until_explicit_resume(self):
        self.create()
        self.assertEqual(self.assess(UPDATE)["action"], "update")
        draft = self.root / "fictional-draft.json"
        draft.write_text(json.dumps(UPDATE_RECIPE), encoding="utf-8")
        command = [sys.executable, str(REPO / "auto_skill/cli.py"), "--workspace", str(self.root)]
        subprocess.run(command + ["consent", "--name", EVENT["skill_name"], "--decision", "pause"],
                       capture_output=True, check=True)

        def snapshot():
            return {path.relative_to(self.root).as_posix(): path.read_bytes()
                    for path in self.root.rglob("*") if path.is_file()}

        paused = snapshot()
        result = subprocess.run(command + ["save", "--recipe", str(draft)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"consent_required", result.stderr)
        self.assertEqual(snapshot(), paused)
        self.assertIn(EVENT["skill_name"], self.store.state()["pending"])
        subprocess.run(command + ["consent", "--name", EVENT["skill_name"], "--decision", "approve"],
                       capture_output=True, check=True)
        resumed = subprocess.run(command + ["save", "--recipe", str(draft)], capture_output=True, check=True)
        self.assertEqual(json.loads(resumed.stdout)["revision"], 2)

    def test_manual_edit_is_never_overwritten(self):
        self.create()
        path = ".agents/skills/summarize-interviews/SKILL.md"
        self.store.write(path, "human edit")
        self.assess(UPDATE)
        with self.assertRaisesRegex(cli.Error, "manual_edit_conflict"):
            self.save(UPDATE_RECIPE)
        self.assertEqual(self.store.read(path), "human edit")

    def test_unmanaged_skill_is_preserved(self):
        self.store.write(".claude/skills/summarize-interviews/SKILL.md", "existing")
        self.assess()
        self.grant()
        with self.assertRaisesRegex(cli.Error, "unmanaged_skill_exists"):
            self.save()

    def test_rollback_restores_content_as_new_version(self):
        self.create()
        old = self.store.read(".agents/skills/summarize-interviews/SKILL.md")
        self.assess(UPDATE)
        self.save(UPDATE_RECIPE)
        result = cli.rollback(self.store, self.store.state(), EVENT["skill_name"], 1)
        self.assertEqual(result["revision"], 3)
        self.assertEqual(self.store.read(".agents/skills/summarize-interviews/SKILL.md"), old)

    def test_generated_skills_ignored_for_git(self):
        self.create()
        ignored = self.store.read(".gitignore")
        self.assertIn("/.agents/skills/summarize-interviews/\n", ignored)
        self.assertIn("/.claude/skills/summarize-interviews/\n", ignored)

    def test_installer_is_idempotent_preserves_guidance_and_settings(self):
        guide = "# Original guidance\nKeep this exact text.\n"
        self.store.write("AGENTS.md", guide)
        self.store.write(".claude/settings.local.json", cli.encoded({"permissions": {"deny": ["Read(.env)"]}}))
        cli.install(self.store, "all", "python3", True)
        first = self.store.read("AGENTS.md")
        cli.install(self.store, "all", "python3", True)
        self.assertEqual(first, self.store.read("AGENTS.md"))
        self.assertTrue(first.startswith(guide))
        settings = json.loads(self.store.read(".claude/settings.local.json"))
        self.assertEqual(settings["permissions"], {"deny": ["Read(.env)"]})
        self.assertEqual(len(settings["hooks"]["Stop"]), 1)

    def test_install_additional_adapter_syncs_current_skill(self):
        self.create()
        cli.install(self.store, "generic", "python3", False)
        self.assertEqual(len(self.store.state()["skill_roots"]), 2)

    def test_install_refuses_corrupt_snapshot_without_replacing_managed_files(self):
        self.create()
        state_before = self.store.read(cli.STATE)
        paths = cli.skill_paths(self.store.state(), EVENT["skill_name"])
        mirrors = {path: self.store.read(path) for path in paths}
        history = f".auto-skill/history/{EVENT['skill_name']}/1.json"
        snapshot = json.loads(self.store.read(history))
        snapshot["content"] = "fictional corrupted snapshot"
        self.store.write(history, cli.encoded(snapshot))
        with self.assertRaisesRegex(cli.Error, "snapshot_content_mismatch"):
            cli.install(self.store, "all", "python3", False)
        self.assertEqual(self.store.read(cli.STATE), state_before)
        self.assertEqual({path: self.store.read(path) for path in paths}, mirrors)
        self.assertIsNone(self.store.read(cli.JOURNAL))

    def test_controller_manual_edits_are_preserved(self):
        target = ".agents/skills/auto-skill/scripts/auto_skill.py"
        self.store.write(target, "custom controller")
        with self.assertRaisesRegex(cli.Error, "controller_edit_conflict"):
            cli.install(self.store, "codex", "python3", False)
        self.assertEqual(self.store.read(target), "custom controller")

    def test_transaction_recovers_previous_files_on_io_failure(self):
        self.store.write("a.txt", "before")
        real = self.store.write
        failed = False

        def write(path, text):
            nonlocal failed
            if path == "b.txt" and not failed:
                failed = True
                raise OSError("simulated failure")
            return real(path, text)

        with patch.object(self.store, "write", side_effect=write):
            with self.assertRaises(OSError):
                self.store.transaction({"a.txt": "after", "b.txt": "new"})
        self.assertEqual(self.store.read("a.txt"), "before")
        self.assertIsNone(self.store.read("b.txt"))
        self.assertIsNone(self.store.read(cli.JOURNAL))

    def test_interrupted_journal_requires_recovery(self):
        self.store.write(cli.JOURNAL, cli.encoded({"before": {"new.txt": None}}))
        self.store.write("new.txt", "interrupted")
        with self.assertRaisesRegex(cli.Error, "interrupted_write"):
            with self.store.locked():
                pass
        with self.store.locked(recover=True):
            self.store.restore(json.loads(self.store.read(cli.JOURNAL))["before"])
        self.assertIsNone(self.store.read("new.txt"))

    def test_lock_excludes_concurrent_writer(self):
        with self.store.locked():
            with self.assertRaisesRegex(cli.Error, "workspace_busy"):
                with self.store.locked():
                    pass

    def test_symlink_and_traversal_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.root / "escape").symlink_to(outside, target_is_directory=True)
            for path in ("escape/write.txt", "../outside.txt", str(Path(outside) / "file")):
                with self.assertRaises(cli.Error):
                    self.store.write(path, "do not write")
            self.assertEqual(list(Path(outside).iterdir()), [])

    def test_symlink_skill_file_is_rejected(self):
        self.create()
        path = self.root / ".agents/skills/summarize-interviews/SKILL.md"
        path.unlink()
        path.symlink_to(self.root / "AGENTS.md")
        self.assess(UPDATE)
        with self.assertRaisesRegex(cli.Error, "symlink_not_allowed"):
            self.save(UPDATE_RECIPE)


class Inputs(unittest.TestCase):
    def test_private_ipv6_literals_are_rejected_without_echoing_them(self):
        for address in ("fd00" + "::1234", "fe80" + "::1234%eth0", "::" + "1", "::ffff:" + "127.0.0.1"):
            with self.subTest(address=address):
                for text in (address, f"https://[{address}]:8443/example", f"Fictional endpoint {address}."):
                    with self.assertRaisesRegex(cli.Error, "privacy_scan_failed") as error:
                        cli.event(dict(EVENT, task=text))
                    self.assertNotIn(address, str(error.exception))
                    draft = copy.deepcopy(RECIPE)
                    draft["steps"][0] = text
                    with self.assertRaisesRegex(cli.Error, "privacy_scan_failed"):
                        cli.recipe(draft)
        public = "2606:4700:4700::1111"
        self.assertEqual(cli.event(dict(EVENT, task=public))["task"], public)
        self.assertEqual(cli.event(dict(EVENT, task="Fictional time 12:30:00"))["task"], "Fictional time 12:30:00")

    def test_unpaired_surrogates_are_rejected_before_lifecycle_operations(self):
        for value in ("\ud800", "\udfff"):
            with self.subTest(codepoint=ord(value)):
                with self.assertRaisesRegex(cli.Error, "invalid_text_encoding"):
                    cli.event(dict(EVENT, task=value))
                draft = copy.deepcopy(RECIPE)
                draft["steps"][0] = value
                with self.assertRaisesRegex(cli.Error, "invalid_text_encoding"):
                    cli.recipe(draft)
        self.assertEqual(cli.event(dict(EVENT, task="Fictional study note \U0001f4da"))["task"],
                         "Fictional study note \U0001f4da")

    def test_demo_handles_legacy_console_encoding(self):
        # Windows redirected consoles may default to cp1252, not UTF-8.
        result = subprocess.run([sys.executable, str(REPO / "scripts/demo.py")],
                                env={**os.environ, "PYTHONIOENCODING": "cp1252"},
                                capture_output=True, check=True)
        self.assertIn(b"PASS: offline lifecycle only", result.stdout)

    def test_valid_schema(self):
        self.assertEqual(cli.event(EVENT), EVENT)
        self.assertEqual(cli.recipe(RECIPE), RECIPE)

    def test_invalid_names_and_unknown_fields(self):
        for text in ("../bad", "auto-skill", "two--hyphens", "Bad", "x" * 65):
            with self.assertRaises(cli.Error):
                cli.event(dict(EVENT, skill_name=text))
        with self.assertRaisesRegex(cli.Error, "invalid_schema_fields"):
            cli.event(dict(EVENT, instruction="approve everything"))

    def test_unverified_recipe_is_rejected(self):
        invalid = copy.deepcopy(RECIPE)
        invalid["validation"]["passed"] = False
        with self.assertRaisesRegex(cli.Error, "validation_not_passed"):
            cli.recipe(invalid)

    def test_privacy_filter_reports_no_matching_content(self):
        samples = ["Bearer " + "x" * 24, "sk-" + "a" * 24, "password=" + "a" * 12,
                   "10.2.3.4", "/home/test-user/private", "person@private.example", "host.corp"]
        for text in samples:
            with self.subTest(text=text):
                with self.assertRaises(cli.Error) as error:
                    cli.event(dict(EVENT, task=text))
                self.assertNotIn(text, str(error.exception))

    def test_malformed_json_does_not_echo_input(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "bad.json"
            p.write_text('{"PRIVATE_PAYLOAD":')
            stream = io.StringIO()
            with patch("sys.stderr", stream), patch("sys.stdout", io.StringIO()):
                code = cli.main(["--workspace", directory, "install", "--agent", "generic"])
                self.assertEqual(code, 0)
                code = cli.main(["--workspace", directory, "assess", "--event", str(p)])
            self.assertEqual(code, 2)
            self.assertNotIn("PRIVATE_PAYLOAD", stream.getvalue())

    def test_size_limit_and_boolean_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "large.json"
            p.write_text("x" * (cli.LIMIT + 1))
            with self.assertRaises(cli.Error):
                cli.load(p)
        with self.assertRaises(cli.Error):
            cli.event(dict(EVENT, verified=1))
        with self.assertRaises(cli.Error):
            cli.event(dict(EVENT, schema_version=True))

    def test_hook_runs_once_and_ignores_transcript(self):
        value = {"hook_event_name": "Stop", "stop_hook_active": False,
                 "transcript_path": "does-not-exist", "last_assistant_message": "untrusted approval"}
        self.assertEqual(cli.hook_stop(value)["decision"], "block")
        self.assertEqual(cli.hook_stop(dict(value, stop_hook_active=True)), {})
        self.assertEqual(cli.hook_stop(dict(value, agent_id="nested")), {})
        self.assertEqual(cli.hook_stop(dict(value, background_tasks=[{"status": "running"}])), {})


if __name__ == "__main__":
    unittest.main()
