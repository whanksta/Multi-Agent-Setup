from __future__ import annotations

import importlib.util
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

            gaps = list(docreview.iter_instruction_file_gaps(root))

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

    def test_missing_command_defaults_to_current_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "subdir").mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)

            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "missing"],
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


if __name__ == "__main__":
    unittest.main()
