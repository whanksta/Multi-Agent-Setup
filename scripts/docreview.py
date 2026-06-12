#!/usr/bin/env python3
"""Verify and repair multi-agent instruction-file wiring and budgets."""

from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Topology this enforces:
#   CLAUDE.md = real canonical file (all shared rules)
#   AGENTS.md = symlink -> CLAUDE.md (Codex + Antigravity read rules through it)
#   .claude/rules/ = Claude-only rules
#   .claude/skills/ = canonical skills
#   .agents/skills = symlink -> .claude/skills
#   [subfolder]/AGENTS.md = symlink -> CLAUDE.md in the same subfolder
#
# Safe to run anytime. Auto-fixes symlinks and backs up diverging content to
# *.clobbered-<timestamp> before repair.

BUDGET_ROOT_CLAUDE = 200
BUDGET_SCOPED_CLAUDE = 80
BUDGET_RULES_FILE = 80

IGNORED_DIRS = {
    ".agents",
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


def relative(path: Path, root_dir: Path) -> Path:
    """Return path relative to repo root for stable human output."""
    return path.relative_to(root_dir)


def count_non_blank_lines(file_path: Path) -> int:
    """Count non-blank lines in a file."""
    try:
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError as exc:
        print(f"  ERROR Reading {file_path}: {exc}")
        return 0

    return sum(1 for line in lines if line.strip())


def iter_scoped_claude_files(root_dir: Path):
    """Yield non-root CLAUDE.md files, skipping generated/dependency dirs."""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRS)

        path = Path(dirpath)
        if path == root_dir:
            continue

        if "CLAUDE.md" in filenames:
            yield path / "CLAUDE.md"


def path_contents_match(path1: Path, path2: Path) -> bool:
    """Return whether two files exist and have identical bytes."""
    try:
        return path1.exists() and path2.exists() and path1.read_bytes() == path2.read_bytes()
    except OSError:
        return False


def remove_existing_path(path: Path) -> None:
    """Remove a file, link, or real directory before creating a symlink."""
    if not os.path.lexists(path):
        return

    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def safe_symlink(target: str, link_path: Path, *, target_is_directory: bool = False) -> bool:
    """Create a symlink with helpful Windows diagnostics."""
    remove_existing_path(link_path)

    try:
        os.symlink(target, link_path, target_is_directory=target_is_directory)
    except OSError as exc:
        print(f"  FAIL  Failed to create symlink {link_path} -> {target}: {exc}")
        if sys.platform == "win32":
            print(
                "        [Windows Tip] Creating symlinks on Windows requires "
                "Developer Mode enabled"
            )
            print("        or running the shell as Administrator. Configure Git with:")
            print("        git config --global core.symlinks true")
        return False

    return True


def check_agents_symlink(
    claude_path: Path,
    agents_path: Path,
    root_dir: Path,
    timestamp: str,
) -> int:
    """Check and repair one AGENTS.md -> CLAUDE.md symlink."""
    rel_agents = relative(agents_path, root_dir)

    if agents_path.is_symlink():
        target = os.readlink(agents_path)
        if target == "CLAUDE.md":
            print(f"  ok    {rel_agents} -> CLAUDE.md")
            return 0

        print(
            f"  WARN  {rel_agents} points to {target!r} "
            "(expected CLAUDE.md) - repairing."
        )
        if safe_symlink("CLAUDE.md", agents_path):
            print(f"  FIX   (re)created {rel_agents} symlink.")
            return 0
        return 1

    if agents_path.exists():
        if path_contents_match(claude_path, agents_path):
            print(
                f"  WARN  {rel_agents} is a regular file identical to "
                "CLAUDE.md - replacing with symlink."
            )
            if safe_symlink("CLAUDE.md", agents_path):
                print("  FIX   Replaced with symlink.")
                return 0
            return 1

        backup = agents_path.parent / f"AGENTS.md.clobbered-{timestamp}"
        shutil.copy2(agents_path, backup)
        print(f"  WARN  {rel_agents} is a regular file that DIFFERS from CLAUDE.md.")
        print(
            "        An agent likely wrote rules here. Backed up to: "
            f"{relative(backup, root_dir)}"
        )
        print(
            f"        Review it, fold wanted changes into CLAUDE.md, then delete "
            f"{relative(backup, root_dir)}"
        )
        if safe_symlink("CLAUDE.md", agents_path):
            print("  FIX   Restored symlink.")
            return 0
        return 1

    print(f"  WARN  {rel_agents} missing - creating symlink.")
    if safe_symlink("CLAUDE.md", agents_path):
        print("  FIX   Created symlink.")
        return 0
    return 1


def has_real_skill_dirs(mirror: Path) -> bool:
    """Return whether a mirror dir contains real copied skill directories."""
    if not mirror.is_dir():
        return False

    return any(entry.is_dir() and not entry.is_symlink() for entry in mirror.iterdir())


def check_skill_mirror(root_dir: Path, timestamp: str) -> int:
    """Check and repair .agents/skills -> .claude/skills."""
    status = 0
    skill_canon = root_dir / ".claude" / "skills"
    mirror = root_dir / ".agents" / "skills"
    want = "../.claude/skills"

    if not skill_canon.exists() or skill_canon.is_symlink():
        return status

    mirror.parent.mkdir(parents=True, exist_ok=True)
    rel_mirror = relative(mirror, root_dir)

    if mirror.is_symlink():
        target = os.readlink(mirror)
        if target == want:
            print(f"  ok    {rel_mirror} -> {want}")
            return status

        print(
            f"  WARN  {rel_mirror} points to {target!r} "
            f"(expected {want}) - repairing."
        )
        if safe_symlink(want, mirror, target_is_directory=True):
            print(f"  FIX   Re-linked {rel_mirror} -> {want}")
        else:
            status = 1
        return status

    if mirror.exists():
        if has_real_skill_dirs(mirror):
            backup = mirror.parent / f"skills.clobbered-{timestamp}"
            shutil.copytree(mirror, backup)
            print(
                f"  WARN  {rel_mirror} held real skill copies - backed up to "
                f"{relative(backup, root_dir)} before replacing with symlink."
            )
        else:
            print(
                f"  WARN  {rel_mirror} was empty, symlink-only, or a non-directory "
                "path - replacing with symlink."
            )

    if safe_symlink(want, mirror, target_is_directory=True):
        print(f"  FIX   Created {rel_mirror} -> {want}")
    else:
        status = 1

    return status


def audit_wiring(root_dir: Path, timestamp: str) -> int:
    """Part 1: Audit and repair instruction file wiring."""
    status = 0
    root_claude = root_dir / "CLAUDE.md"

    if not root_claude.exists():
        print("  FAIL  CLAUDE.md (canonical) is missing - cannot continue.")
        sys.exit(1)

    if root_claude.is_symlink():
        print("  FAIL  CLAUDE.md is a symlink but must be the real canonical file.")
        status = 1
    else:
        print("  ok    CLAUDE.md is the real canonical file.")

    status |= check_agents_symlink(
        root_claude,
        root_dir / "AGENTS.md",
        root_dir,
        timestamp,
    )

    for scoped_claude in iter_scoped_claude_files(root_dir):
        status |= check_agents_symlink(
            scoped_claude,
            scoped_claude.with_name("AGENTS.md"),
            root_dir,
            timestamp,
        )

    try:
        canonical_lines = root_claude.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError as exc:
        print(f"  ERROR Checking circular imports in CLAUDE.md: {exc}")
        status = 1
    else:
        if any(line.startswith("@./AGENTS.md") for line in canonical_lines):
            print(
                "  WARN  CLAUDE.md imports @./AGENTS.md - circular "
                "(AGENTS.md is a symlink). Remove that line."
            )
            status = 1

    status |= check_skill_mirror(root_dir, timestamp)
    return status


def print_budget_verdict(
    label: str,
    rel_path: Path | str,
    line_count: int,
    budget: int,
) -> int:
    """Print one budget verdict and return a non-zero status for hard failures."""
    prefix = f"  {{level:<5}} [{label}] {rel_path} count: {line_count} (budget <= {budget})"

    if line_count <= budget:
        print(prefix.format(level="ok") + " - PASS")
        return 0

    if line_count < budget * 1.5:
        print(prefix.format(level="WARN") + " - WITHIN-SLACK")
        return 0

    print(prefix.format(level="FAIL") + " - OVER")
    return 1


def audit_budgets(root_dir: Path) -> int:
    """Part 2: Audit non-blank line counts against size budgets."""
    status = 0
    print("\ndocreview: checking size budgets (non-blank lines)")

    root_claude = root_dir / "CLAUDE.md"
    status |= print_budget_verdict(
        "Root",
        root_claude.name,
        count_non_blank_lines(root_claude),
        BUDGET_ROOT_CLAUDE,
    )

    for scoped_claude in iter_scoped_claude_files(root_dir):
        status |= print_budget_verdict(
            "Scoped",
            relative(scoped_claude, root_dir),
            count_non_blank_lines(scoped_claude),
            BUDGET_SCOPED_CLAUDE,
        )

    rules_dir = root_dir / ".claude" / "rules"
    if rules_dir.is_dir():
        for rules_file in sorted(rules_dir.glob("*.md")):
            status |= print_budget_verdict(
                "Rule",
                relative(rules_file, root_dir),
                count_non_blank_lines(rules_file),
                BUDGET_RULES_FILE,
            )

    return status


def main() -> None:
    """Run docreview from the repo root."""
    root_dir = Path(__file__).resolve().parent.parent
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    print(f"docreview: checking agent instruction files in {root_dir}")

    overall_status = audit_wiring(root_dir, timestamp) | audit_budgets(root_dir)

    print("\n------------------------------------------------")
    if overall_status == 0:
        print("docreview: PASS - instruction-file wiring and budgets are compliant.")
    else:
        print("docreview: FAIL/WARN - repaired issues or exceeded budgets. Re-run to confirm PASS.")

    sys.exit(overall_status)


if __name__ == "__main__":
    main()
