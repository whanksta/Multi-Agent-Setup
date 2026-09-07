from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "docreview.py"


def load_docreview_module():
    spec = importlib.util.spec_from_file_location("docreview", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MissingInstructionFileReportTests(unittest.TestCase):
    def test_check_command_defaults_to_script_root_from_other_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            agents_path = root / "AGENTS.md"
            agents_is_symlink = agents_path.is_symlink()
            agents_target = os.readlink(agents_path) if agents_is_symlink else None

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertIn(
            f"docreview: checking agent instruction files in {root.resolve()}",
            result.stdout,
        )
        self.assertTrue(agents_is_symlink)
        self.assertEqual(agents_target, "CLAUDE.md")

    def test_check_command_fails_when_claude_is_not_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").mkdir()
            (root / "AGENTS.md").symlink_to("CLAUDE.md")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("CLAUDE.md must be a regular file", result.stdout)
        self.assertNotIn("docreview: PASS", result.stdout)

    def test_check_command_fails_when_skill_mirror_target_is_not_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")
            (root / "AGENTS.md").symlink_to("CLAUDE.md")
            (root / ".claude").mkdir()
            (root / ".claude" / "skills").write_text("not a directory\n", encoding="utf-8")
            (root / ".agents").mkdir()
            (root / ".agents" / "skills").symlink_to("../.claude/skills")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(".claude/skills must be a real directory", result.stdout)
        self.assertNotIn("docreview: PASS", result.stdout)

    def test_reports_every_directory_missing_instruction_files(self) -> None:
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")
            (root / "AGENTS.md").symlink_to("CLAUDE.md")
            (root / "src").mkdir()
            (root / "docs").mkdir()
            (root / "docs" / "CLAUDE.md").write_text("docs\n", encoding="utf-8")
            (root / "tools").mkdir()
            (root / "tools" / "AGENTS.md").symlink_to("CLAUDE.md")
            (root / ".git").mkdir()
            (root / ".git" / "hooks").mkdir()

            gaps = list(docreview.iter_instruction_file_gaps(root, []))

        self.assertEqual(
            [
                (gap.relative_dir.as_posix(), gap.missing_claude, gap.missing_agents)
                for gap in gaps
            ],
            [
                ("docs", False, True),
                ("src", True, True),
                ("tools", True, False),
            ],
        )

    def test_docreview_ignore_file_extends_ignored_dirs(self) -> None:
        """Local customization must extend the walkers without patching the script."""
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")
            # Trailing slash (gitignore muscle memory), a leading BOM, trailing
            # comments, blanks, and a path-shaped entry that must warn+skip.
            (root / ".docreview-ignore").write_text(
                "# generated output\n"
                "\n"
                "generated/\n"
                "\ufeffbomdir\n"
                "worktrees/  # agent checkouts\n"
                "src/pkg  # path-shaped, never matches a dir name\n",
                encoding="utf-8",
            )
            generated = root / "generated"
            generated.mkdir()
            (generated / "CLAUDE.md").write_text("stale artifact\n", encoding="utf-8")
            (root / "src").mkdir()

            extra = docreview.load_extra_ignores(root)
            gaps = list(docreview.iter_instruction_file_gaps(root, []))
            docs = list(docreview.iter_markdown_docs(root, []))
            scoped = list(docreview.iter_scoped_claude_files(root, []))

        self.assertEqual(extra, {"generated", "bomdir", "worktrees"})
        gap_dirs = [gap.relative_dir.as_posix() for gap in gaps]
        self.assertIn("src", gap_dirs)
        self.assertNotIn("generated", gap_dirs)
        self.assertIn("CLAUDE.md", [path.name for path in docs])
        self.assertFalse(any("generated" in path.parts for path in docs))
        self.assertFalse(any("generated" in path.parts for path in scoped))

    def test_case_variant_detection_compares_directory_entries(self) -> None:
        """Variant detection must be dirent-based, never an exists()-style lookup.

        macOS/Windows default filesystems fold case in path lookups, so
        claude.md would satisfy a CLAUDE.md exists() check while no
        case-sensitive agent reads it. os.walk's filenames preserve case.
        """
        docreview = load_docreview_module()

        self.assertEqual(
            docreview.find_case_variants(["CLAUDE.md", "AGENTS.md", "readme.md"]),
            [],
        )
        self.assertEqual(
            docreview.find_case_variants(["claude.md", "Agents.md", "CLAUDE.local.md"]),
            ["Agents.md", "claude.md"],
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")
            (root / "agents.md").write_text("wrong case\n", encoding="utf-8")

            variants = list(docreview.iter_case_variants(root, []))

        self.assertEqual(
            [(rel.as_posix(), name) for _dir, rel, name in variants],
            [(".", "agents.md")],
        )

    def test_missing_command_reports_wrong_case_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")
            (root / "agents.md").write_text("wrong case\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "missing",
                    "--scope",
                    "path",
                    "--path",
                    str(root),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("agents.md - wrong case; no agent reads it", result.stdout)
        self.assertNotIn("every directory in scope has", result.stdout)

    def test_check_command_repairs_wrong_case_instruction_files(self) -> None:
        """A lowercase agents.md is renamed (not warned about) even on case-folding FS."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")
            (root / "agents.md").write_text("wrong case\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            # Dirent-based assertions: a case-folded exists() lookup would find
            # the new AGENTS.md through the fold and mask a surviving variant.
            entries = os.listdir(root)
            agents_is_symlink = (root / "AGENTS.md").is_symlink()
            variant_gone = "agents.md" not in entries
            canonical_present = "AGENTS.md" in entries

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("renamed agents.md -> AGENTS.md", result.stdout)
        self.assertTrue(variant_gone)
        self.assertTrue(canonical_present)
        self.assertTrue(agents_is_symlink)
        self.assertIn("docreview: PASS", result.stdout)

    def test_check_uses_git_mv_for_tracked_wrong_case_files(self) -> None:
        """A tracked variant must move via git mv - a plain rename is a silent
        no-op for the index on case-insensitive filesystems, and the next
        case-sensitive clone would resurrect the wrong name."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "claude.md").write_text("root\n", encoding="utf-8")

            for args in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "t@example.com"],
                ["git", "config", "user.name", "t"],
                ["git", "add", "claude.md"],
                ["git", "commit", "-qm", "init"],
            ):
                subprocess.run(args, cwd=root, check=True)

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            listed = subprocess.run(
                ["git", "ls-files"],
                cwd=root,
                text=True,
                capture_output=True,
                check=True,
            ).stdout.split()

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("claude.md -> CLAUDE.md (git mv", result.stdout)
        self.assertIn("CLAUDE.md", listed)
        self.assertNotIn("claude.md", listed)
        self.assertIn("docreview: PASS", result.stdout)

    def test_missing_command_honors_custom_path_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scope = root / "pkg"
            scope.mkdir()
            (scope / "src").mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "missing",
                    "--scope",
                    "path",
                    "--path",
                    str(scope),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertIn(
            f"docreview: reporting instruction-file coverage in {scope.resolve()}",
            result.stdout,
        )
        self.assertIn("  info  . missing CLAUDE.md, AGENTS.md", result.stdout)
        self.assertIn("  info  src missing CLAUDE.md, AGENTS.md", result.stdout)
        self.assertIn(
            "Missing CLAUDE.md entries are prompts to consider scoped files only "
            "when folder-specific rules warrant them.",
            result.stdout,
        )

    def test_missing_command_rejects_bad_scope_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            as_file = root / "notes.md"
            as_file.write_text("not a directory\n", encoding="utf-8")

            for bad_path in (str(root / "does-not-exist"), str(as_file)):
                with self.subTest(bad_path=bad_path):
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(SCRIPT_PATH),
                            "missing",
                            "--scope",
                            "path",
                            "--path",
                            bad_path,
                        ],
                        cwd=root,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
                    self.assertIn("scope path is not an existing directory", result.stderr)
                    self.assertNotIn("every directory in scope has", result.stdout)

    def test_check_command_fails_when_a_scoped_claude_is_unreadable(self) -> None:
        if not hasattr(os, "chmod"):
            self.skipTest("chmod unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")
            (root / "AGENTS.md").symlink_to("CLAUDE.md")
            scoped = root / "pkg" / "CLAUDE.md"
            scoped.parent.mkdir()
            scoped.write_text("x" * 20_000, encoding="utf-8")
            (root / "pkg" / "AGENTS.md").symlink_to("CLAUDE.md")
            scoped.chmod(0)

            try:
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
            finally:
                scoped.chmod(0o644)

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("could not be read - budget UNCHECKED", result.stdout)
        self.assertNotIn("docreview: PASS", result.stdout)

    def test_missing_command_warns_on_unscannable_directory(self) -> None:
        if not hasattr(os, "chmod"):
            self.skipTest("chmod unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")
            (root / "AGENTS.md").symlink_to("CLAUDE.md")
            locked = root / "locked"
            locked.mkdir()
            (locked / "CLAUDE.md").write_text("never seen\n", encoding="utf-8")
            locked.chmod(0)

            try:
                result = subprocess.run(
                    [sys.executable, str(script_path), "missing"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
            finally:
                locked.chmod(0o755)

        self.assertIn("coverage there is UNKNOWN", result.stdout)
        self.assertNotIn("every directory in scope has", result.stdout)

    def test_check_command_fails_on_circular_import_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").write_text("rules\n\n- @AGENTS.md\n", encoding="utf-8")
            (root / "AGENTS.md").symlink_to("CLAUDE.md")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("circular", result.stdout)

    def test_worktree_scope_without_git_binary_exits_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty_bin = Path(tmp) / "bin"
            empty_bin.mkdir()
            env = dict(os.environ)
            env["PATH"] = str(empty_bin)

            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "missing", "--scope", "worktree"],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
        self.assertIn("cannot run git", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_command_honors_current_git_worktree_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "subdir").mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)

            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "missing", "--scope", "worktree"],
                cwd=root / "subdir",
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertIn(
            f"docreview: reporting instruction-file coverage in {root.resolve()}",
            result.stdout,
        )


class VersionStampTests(unittest.TestCase):
    def _repo(self, tmp: str, version: str, heading: str) -> Path:
        root = Path(tmp)
        (root / "VERSION").write_text(version + "\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text(
            f"# Changelog\n\nintro prose\n\n## {heading}\n\n### Fixed\n\n- thing\n",
            encoding="utf-8",
        )
        return root

    def test_matching_version_and_newest_batch_passes(self) -> None:
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp, "2026-08-03", "2026-08-03")
            self.assertEqual(docreview.audit_version_stamp(root), 0)

    def test_drifted_version_fails(self) -> None:
        """A mismatch silently skips an update for every adopter."""
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp, "2026-06-16", "2026-08-03")
            self.assertEqual(docreview.audit_version_stamp(root), 1)

    def test_no_op_in_an_adopting_repo(self) -> None:
        """Adopters get neither VERSION nor CHANGELOG.md - must not fail there."""
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(docreview.audit_version_stamp(Path(tmp)), 0)

    def test_undated_heading_is_skipped_not_failed(self) -> None:
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp, "2026-08-03", "Unreleased")
            self.assertEqual(docreview.audit_version_stamp(root), 0)

    def test_this_repo_is_in_sync(self) -> None:
        docreview = load_docreview_module()

        self.assertEqual(docreview.audit_version_stamp(REPO_ROOT), 0)


class SizeMeasurementTests(unittest.TestCase):
    def test_unclosed_html_comment_is_charged_not_dropped(self) -> None:
        docreview = load_docreview_module()

        loaded = docreview.strip_unloaded(
            "BODY ONE\n<!-- never closed\nBODY TWO\nBODY THREE\n"
        )
        self.assertIn("BODY ONE", loaded)
        self.assertIn("BODY TWO", loaded)
        self.assertIn("BODY THREE", loaded)

        closed = docreview.strip_unloaded("BODY ONE\n<!-- closed -->\nBODY TWO\n")
        self.assertNotIn("closed", closed)
        self.assertIn("BODY TWO", closed)

    def test_fence_line_with_trailing_text_does_not_close_the_fence(self) -> None:
        docreview = load_docreview_module()

        loaded = docreview.strip_unloaded(
            "\n".join(
                [
                    "```python",
                    "code line",
                    "``` trailing",
                    "<!-- secret -->",
                    "```",
                    "after",
                    "",
                ]
            )
        )
        # The ```-with-trailing-text line is an opener, not a closer, so the
        # comment inside the fence is literal content and must be charged.
        self.assertIn("<!-- secret -->", loaded)
        self.assertIn("after", loaded)

    def test_long_lines_are_charged_for_their_real_cost(self) -> None:
        """The bug this replaced: one huge line counted as 1 and passed."""
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            dense = Path(tmp) / "CLAUDE.md"
            dense.write_text("| a | " + "x" * 12000 + " |\n", encoding="utf-8")

            size = docreview.measure(dense)

        self.assertEqual(size.lines, 1)
        self.assertGreater(size.tokens, docreview.BUDGET_ROOT_TOKENS)

    def test_block_html_comments_and_frontmatter_are_not_charged(self) -> None:
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp) / "plain.md"
            plain.write_text("# Rules\n\n- Use 2-space indent.\n", encoding="utf-8")

            padded = Path(tmp) / "padded.md"
            padded.write_text(
                "---\npaths:\n  - 'src/**/*.ts'\n---\n"
                "# Rules\n\n- Use 2-space indent.\n\n"
                "<!--\n" + "maintainer note padding\n" * 200 + "-->\n",
                encoding="utf-8",
            )

            plain_size = docreview.measure(plain)
            padded_size = docreview.measure(padded)
            raw_padded_tokens = len(padded.read_text(encoding="utf-8")) / docreview.CHARS_PER_TOKEN

        # The frontmatter and the 200-line comment block cost nothing; only a
        # stray blank line survives stripping, so allow a token of slack.
        self.assertLessEqual(padded_size.tokens - plain_size.tokens, 1)
        self.assertEqual(padded_size.lines, plain_size.lines)
        self.assertGreater(raw_padded_tokens, plain_size.tokens * 50)

    def test_comments_inside_code_fences_still_count(self) -> None:
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            fenced = Path(tmp) / "fenced.md"
            fenced.write_text(
                "# Example\n\n```html\n<!-- this ships to the reader -->\n```\n",
                encoding="utf-8",
            )

            size = docreview.measure(fenced)
            kept = docreview.strip_unloaded(fenced.read_text(encoding="utf-8"))

        self.assertIn("this ships to the reader", kept)
        self.assertGreater(size.tokens, 0)

    def test_leading_horizontal_rule_is_not_mistaken_for_frontmatter(self) -> None:
        """A `---` hrule on line 1 must not swallow content up to the next `---`."""
        docreview = load_docreview_module()

        kept = docreview.strip_unloaded("---\n# Title\nBODY ONE\n---\nBODY TWO\n")

        self.assertIn("BODY ONE", kept)
        self.assertIn("BODY TWO", kept)

    def test_real_yaml_frontmatter_is_still_dropped(self) -> None:
        docreview = load_docreview_module()

        kept = docreview.strip_unloaded("---\npaths:\n  - 'src/**/*.ts'\n---\nBODY\n")

        self.assertEqual(kept, "BODY")

    def test_longer_fence_is_not_closed_by_a_shorter_one(self) -> None:
        """A ``` inside a ```` block must not expose it to comment-stripping."""
        docreview = load_docreview_module()

        kept = docreview.strip_unloaded("````\n```\n<!-- inside -->\n```\n````\nAFTER\n")

        self.assertIn("<!-- inside -->", kept)
        self.assertIn("AFTER", kept)

    def test_skill_frontmatter_is_charged(self) -> None:
        """A skill's name/description sit in the always-loaded skill listing."""
        docreview = load_docreview_module()

        body = "---\nname: demo\ndescription: " + "d" * 500 + "\n---\n\n# Demo\n\n- rule\n"

        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "SKILL.md"
            skill.write_text(body, encoding="utf-8")
            rule = Path(tmp) / "rule.md"
            rule.write_text(body, encoding="utf-8")

            self.assertGreater(docreview.measure(skill).tokens, 200)
            self.assertLess(docreview.measure(rule).tokens, 20)

    def test_estimate_tracks_the_real_tokenizer(self) -> None:
        """Pins the estimator to observed truth, not to a rule of thumb.

        `tests/fixtures/calibration.md` really costs 362 tokens on Opus 5,
        measured as the delta in reported input tokens between two otherwise
        identical `claude -p` runs. The estimator reads ~400: it errs high on
        prose-heavy samples, which is the safe direction for a budget gate.
        If this fails, the tokenizer moved - re-measure and update both numbers.
        """
        docreview = load_docreview_module()

        size = docreview.measure(REPO_ROOT / "tests" / "fixtures" / "calibration.md")

        self.assertAlmostEqual(size.tokens, 362, delta=round(362 * 0.15))

    def test_over_budget_file_fails_the_check_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").write_text("x" * 40000 + "\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("[Root] CLAUDE.md", result.stdout)
        self.assertIn("- OVER", result.stdout)
        self.assertNotIn("docreview: PASS", result.stdout)

    def test_debt_command_lists_within_slack_and_exits_zero(self) -> None:
        """debt is the durable artifact for soft flags - report-only, exit 0."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            # 8,000 chars / 2.5 = 3,200 tokens: over the 2,500 root budget,
            # under the 1.5x hard line - exactly the WITHIN-SLACK band.
            (root / "CLAUDE.md").write_text("x" * 8_000 + "\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(script_path), "debt"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("[Root] CLAUDE.md", result.stdout)
        self.assertIn("WITHIN-SLACK", result.stdout)
        self.assertIn("1.28x", result.stdout)
        self.assertNotIn("- PASS", result.stdout)

    def test_debt_command_exits_zero_even_on_over_files(self) -> None:
        """debt reports OVER debt but stays report-only - check is the gate."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").write_text("x" * 50_000 + "\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(script_path), "debt"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("OVER", result.stdout)
        self.assertIn("8.00x", result.stdout)

    def test_umbrella_claude_md_gets_the_wider_budget(self) -> None:
        docreview = load_docreview_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pkg" / "api").mkdir(parents=True)
            umbrella = root / "pkg" / "CLAUDE.md"
            leaf = root / "pkg" / "api" / "CLAUDE.md"
            for path in (umbrella, leaf):
                path.write_text("rules\n", encoding="utf-8")

            scoped = [umbrella, leaf]

            self.assertTrue(docreview.is_umbrella(umbrella, scoped))
            self.assertFalse(docreview.is_umbrella(leaf, scoped))

    def test_rules_are_discovered_in_subdirectories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "scripts" / "docreview.py"
            script_path.parent.mkdir()
            shutil.copy2(SCRIPT_PATH, script_path)
            (root / "CLAUDE.md").write_text("root\n", encoding="utf-8")
            nested = root / ".claude" / "rules" / "backend"
            nested.mkdir(parents=True)
            (nested / "testing.md").write_text("- run pytest\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn(".claude/rules/backend/testing.md", result.stdout)

    def test_tokens_command_reports_named_files(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "tokens", str(REPO_ROOT / "CLAUDE.md")],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("CLAUDE.md", result.stdout)
        # "non-blank lines" only appears in a real measurement row, never in
        # the note lines - asserting "tok" alone would pass on the notes too.
        self.assertIn("non-blank lines", result.stdout)

    def test_tokens_command_skips_the_agents_symlink(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "tokens"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertNotIn("AGENTS.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
