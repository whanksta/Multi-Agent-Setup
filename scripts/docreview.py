#!/usr/bin/env python3
"""Verify and repair multi-agent instruction-file wiring and budgets."""

from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

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

# Budgets are in ESTIMATED TOKENS, not lines. Lines were a broken proxy: one
# 1,800-char table row counted as 1, so a ~6,600-token file could report PASS.
# Line counts are still printed, but only as an advisory readout.
#
# CHARS_PER_TOKEN is measured, not assumed. The widely-quoted "~3.5 English
# chars per token" predates the Claude 4.7+ tokenizer and understates dense
# markdown by ~40%. Measured against this repo's own docs as the delta in
# reported input tokens between two otherwise-identical `claude -p` runs:
#   CLAUDE.md 2.58 | doctrine.md 2.52 | SKILL.md 2.52 | README.md 2.42
# 2.5 is the working constant for agent-instruction markdown. Re-derive it the
# same way if the tokenizer changes; `docreview.py tokens` reports the estimate.
CHARS_PER_TOKEN = 2.5

BUDGET_ROOT_TOKENS = 2500
BUDGET_UMBRELLA_TOKENS = 1800
BUDGET_SCOPED_TOKENS = 1000
BUDGET_RULES_TOKENS = 1000

# A fence is 3+ backticks or tildes; the closer must be at least as long as the
# opener (CommonMark), or a ``` inside a ```` block would close it early and
# expose its contents to comment-stripping.
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")

# A leading `---` only opens YAML frontmatter if the block actually looks like
# YAML. Without this, a doc whose first line is a `---` horizontal rule loses
# everything up to the next `---` - silent under-counting, the dangerous
# direction for a budget gate.
YAML_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:")

# An @-import of AGENTS.md in any common shape - bare, ./, /, indented, or a
# list item - is circular: AGENTS.md is a symlink back to CLAUDE.md itself.
CIRCULAR_IMPORT_RE = re.compile(r"^\s*(?:[-*+]\s*)?@\.?/?AGENTS\.md\b")

# CHANGELOG batch headings the adoption flow compares against .claude/.mas-version.
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

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

# Local customization lives in <scope root>/.docreview-ignore so adopters
# never patch this script: a patch dies on the next byte-exact copy. One
# directory name per line (matched at any depth, like IGNORED_DIRS);
# blank lines and #-comments (full-line or trailing) are skipped.


class InstructionFileGap(NamedTuple):
    """Instruction files missing from one directory in a report scope."""

    relative_dir: Path
    missing_claude: bool
    missing_agents: bool


def relative(path: Path, root_dir: Path) -> Path:
    """Return path relative to repo root for stable human output."""
    return path.relative_to(root_dir)


class DocSize(NamedTuple):
    """What a doc actually costs once it reaches the context window."""

    tokens: int
    lines: int


def frontmatter_end(lines: list[str]) -> int:
    """Return the index just past a real YAML frontmatter block, else 0."""
    if not lines or lines[0].rstrip() != "---":
        return 0

    for close in range(1, len(lines)):
        if lines[close].rstrip() != "---":
            continue
        block = [line for line in lines[1:close] if line.strip()]
        if block and any(YAML_KEY_RE.match(line) for line in block):
            return close + 1
        return 0

    return 0


def strip_unloaded(text: str, *, drop_frontmatter: bool = True) -> str:
    """Drop the parts of an instruction file that never reach the context window.

    Claude Code strips YAML frontmatter and block-level HTML comments before
    injecting a memory file, and preserves comments inside fenced code blocks.
    Measured empirically: 7,200 chars inside `<!-- -->` cost 0 tokens while the
    same text uncommented cost 2,101, and a 10,100-char frontmatter block cost
    nothing beyond run-to-run noise. Measuring the raw file would charge a doc
    for bytes it never pays for.
    """
    lines = text.splitlines()
    start = frontmatter_end(lines) if drop_frontmatter else 0

    kept: list[str] = []
    fence: tuple[str, int] | None = None
    in_comment = False
    # Lines swallowed by a comment so far. If the comment never closes, the
    # construct is malformed markdown and the content is charged, not dropped -
    # under-counting is the dangerous direction for a budget gate.
    pending: list[str] = []

    for raw_line in lines[start:]:
        line = raw_line

        if in_comment:
            _, closed, tail = line.partition("-->")
            if not closed:
                pending.append(raw_line)
                continue
            pending.clear()
            in_comment = False
            line = tail

        # Comment syntax is literal inside a code fence, so only peel comments
        # when we are outside one.
        if fence is None:
            while line.strip().startswith("<!--"):
                _, closed, tail = line.partition("-->")
                if not closed:
                    in_comment = True
                    pending.append(raw_line)
                    break
                line = tail
            if in_comment:
                continue
            if raw_line.strip() and not line.strip():
                continue  # the line held nothing but comments

        match = FENCE_RE.match(line.strip())

        if fence is not None:
            kept.append(line)
            # A closer must be bare fence chars (CommonMark forbids trailing
            # text on closers); "``` trailing" is not a close.
            if (
                match
                and line.strip() == match.group()
                and match.group()[0] == fence[0]
                and len(match.group()) >= fence[1]
            ):
                fence = None
            continue

        if match:
            fence = (match.group()[0], len(match.group()))

        kept.append(line)

    if in_comment:
        kept.extend(pending)

    return "\n".join(kept)


def measure(file_path: Path) -> DocSize | None:
    """Estimate the context cost of one doc, ignoring content that never loads.

    Returns None when the file cannot be read: a doc the gate cannot measure
    must fail the gate, never pass it as a zero-cost file.
    """
    try:
        raw = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        print(f"  ERROR Reading {file_path}: {exc}")
        return None

    # A skill's frontmatter is the one kind that DOES load: `name` +
    # `description` sit in the always-present skill listing. Charge for it.
    loaded = strip_unloaded(raw, drop_frontmatter=file_path.name != "SKILL.md")
    return DocSize(
        math.ceil(len(loaded) / CHARS_PER_TOKEN),
        sum(1 for line in loaded.splitlines() if line.strip()),
    )


def walk_reporting_errors(root_dir: Path, scan_errors: list[str]):
    """os.walk that records unreadable directories instead of skipping them.

    os.walk's default is to silently step past an OSError, so a locked subtree
    reads as coverage it never had. Callers decide how loudly to fail.
    """

    def record(error: OSError) -> None:
        scan_errors.append(str(error.filename or error))

    yield from os.walk(root_dir, onerror=record)


# Loaded once per scope root per run; a `check` run walks via several
# iterators and must not re-read the file (or re-print its warnings).
_EXTRA_IGNORES_CACHE: dict = {}


def load_extra_ignores(root_dir: Path) -> set:
    """Return directory names from <scope root>/.docreview-ignore, else empty.

    One name per line, matched at any depth like IGNORED_DIRS; blank lines and
    #-comments (full-line or trailing) are skipped. A mis-parsed entry would
    under-ignore - the dangerous direction for a gate - so gitignore-style
    trailing slashes and a leading BOM are normalized, path-shaped entries WARN
    and are dropped, and an unreadable file WARNs and keeps built-ins only.
    """
    cache_key = str(root_dir.resolve())
    if cache_key in _EXTRA_IGNORES_CACHE:
        return _EXTRA_IGNORES_CACHE[cache_key]

    names: set = set()
    ignore_file = root_dir / ".docreview-ignore"
    if os.path.lexists(ignore_file):
        try:
            lines = ignore_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError as exc:
            print(f"  WARN  Could not read {ignore_file}: {exc} - extra ignores NOT loaded.")
        else:
            for raw in lines:
                name = raw.split("#", 1)[0].strip().strip("/").lstrip("\ufeff").strip()
                if not name:
                    continue
                if "/" in name or "\\" in name:
                    print(
                        f"  WARN  .docreview-ignore entry {name!r} is a path, not a "
                        "directory name - skipped."
                    )
                    continue
                names.add(name)

    _EXTRA_IGNORES_CACHE[cache_key] = names
    return names


def iter_scoped_claude_files(root_dir: Path, scan_errors: list[str]):
    """Yield non-root CLAUDE.md files, skipping generated/dependency dirs."""
    ignored = IGNORED_DIRS | load_extra_ignores(root_dir)
    for dirpath, dirnames, filenames in walk_reporting_errors(root_dir, scan_errors):
        dirnames[:] = sorted(name for name in dirnames if name not in ignored)

        path = Path(dirpath)
        if path == root_dir:
            continue

        if "CLAUDE.md" in filenames:
            yield path / "CLAUDE.md"


def find_case_variants(filenames: list[str]) -> list[str]:
    """Return mis-cased CLAUDE.md/AGENTS.md entries within one directory listing.

    Claude Code reads `CLAUDE.md` and Codex reads `AGENTS.md` exactly - the
    AGENTS.md spec says so outright - but OS path lookups fold case on macOS
    and Windows default filesystems. Only real directory entries tell the
    truth, so variant detection compares those, never exists()-style checks.
    """
    canonical = {"CLAUDE.md", "AGENTS.md"}
    return sorted(
        name
        for name in filenames
        if name.lower() in {"claude.md", "agents.md"} and name not in canonical
    )


def iter_case_variants(root_dir: Path, scan_errors: list[str]):
    """Yield (relative_dir, filename) for every mis-cased instruction file in scope."""
    ignored = IGNORED_DIRS | load_extra_ignores(root_dir)
    for dirpath, dirnames, filenames in walk_reporting_errors(root_dir, scan_errors):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in ignored and not (Path(dirpath) / name).is_symlink()
        )

        path = Path(dirpath)
        for variant in find_case_variants(filenames):
            rel_dir = Path(".") if path == root_dir else relative(path, root_dir)
            yield rel_dir, variant


def iter_instruction_file_gaps(root_dir: Path, scan_errors: list[str]):
    """Yield directories in scope that lack CLAUDE.md and/or AGENTS.md.

    Membership is tested against os.walk's directory entries, which preserve
    case everywhere - an os.path.lexists lookup would fold case on macOS and
    Windows and count claude.md as CLAUDE.md.
    """
    ignored = IGNORED_DIRS | load_extra_ignores(root_dir)
    for dirpath, dirnames, filenames in walk_reporting_errors(root_dir, scan_errors):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in ignored and not (Path(dirpath) / name).is_symlink()
        )

        path = Path(dirpath)
        missing_claude = "CLAUDE.md" not in filenames
        missing_agents = "AGENTS.md" not in filenames

        if missing_claude or missing_agents:
            relative_dir = Path(".") if path == root_dir else relative(path, root_dir)
            yield InstructionFileGap(relative_dir, missing_claude, missing_agents)


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
            if not path_contents_match(claude_path, agents_path):
                print(
                    f"  FAIL  {rel_agents} points to CLAUDE.md, but the link "
                    "does not read the same bytes as CLAUDE.md."
                )
                return 1
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


def path_has_contents(path: Path) -> bool:
    """Return whether a real path has content worth backing up."""
    if path.is_dir():
        return any(path.iterdir())

    return os.path.lexists(path)


def backup_existing_path(path: Path, backup: Path) -> None:
    """Back up a real file or directory before replacing it with a symlink."""
    if path.is_dir() and not path.is_symlink():
        shutil.copytree(path, backup, symlinks=True)
    else:
        shutil.copy2(path, backup)


def check_skill_mirror(root_dir: Path, timestamp: str) -> int:
    """Check and repair .agents/skills -> .claude/skills."""
    status = 0
    skill_canon = root_dir / ".claude" / "skills"
    mirror = root_dir / ".agents" / "skills"
    want = "../.claude/skills"

    if not skill_canon.exists():
        print("  WARN  .claude/skills does not exist - nothing to mirror.")
        return status
    if skill_canon.is_symlink():
        print("  WARN  .claude/skills is itself a symlink - mirror check skipped.")
        return status
    if not skill_canon.is_dir():
        print("  FAIL  .claude/skills must be a real directory before mirroring.")
        return 1

    mirror.parent.mkdir(parents=True, exist_ok=True)
    rel_mirror = relative(mirror, root_dir)

    if mirror.is_symlink():
        target = os.readlink(mirror)
        if target == want:
            if not mirror.is_dir():
                print(
                    f"  FAIL  {rel_mirror} points to {want}, but the link "
                    "does not resolve to a directory."
                )
                return 1
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
        if path_has_contents(mirror):
            backup = mirror.parent / f"skills.clobbered-{timestamp}"
            backup_existing_path(mirror, backup)
            print(
                f"  WARN  {rel_mirror} held real content - backed up to "
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

    # Wrong-case variants fail before any repair: path lookups fold case on
    # macOS/Windows, so a claude.md/agents.md variant can satisfy the checks
    # below while no agent on a case-sensitive filesystem ever reads it.
    case_scan_errors: list[str] = []
    case_variants = list(iter_case_variants(root_dir, case_scan_errors))
    for scan_error in case_scan_errors:
        print(f"  FAIL  Could not scan {scan_error} - filename case there is UNCHECKED.")
        status = 1
    if case_variants:
        for rel_dir, name in case_variants:
            where = (rel_dir / name).as_posix()
            print(
                f"  FAIL  {where} - wrong case. Claude Code reads CLAUDE.md and "
                "Codex reads AGENTS.md, exactly; rename (git mv) and re-run."
            )
        sys.exit(1)

    if root_claude.is_symlink():
        print("  FAIL  CLAUDE.md is a symlink but must be the real canonical file.")
        status = 1
    elif not root_claude.is_file():
        print("  FAIL  CLAUDE.md must be a regular file.")
        status = 1
    else:
        print("  ok    CLAUDE.md is the real canonical file.")

    status |= check_agents_symlink(
        root_claude,
        root_dir / "AGENTS.md",
        root_dir,
        timestamp,
    )

    scan_errors: list[str] = []
    for scoped_claude in iter_scoped_claude_files(root_dir, scan_errors):
        status |= check_agents_symlink(
            scoped_claude,
            scoped_claude.with_name("AGENTS.md"),
            root_dir,
            timestamp,
        )

    for scan_error in scan_errors:
        print(f"  FAIL  Could not scan {scan_error} - wiring there is UNCHECKED.")
        status = 1

    try:
        canonical_lines = root_claude.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError as exc:
        print(f"  ERROR Checking circular imports in CLAUDE.md: {exc}")
        status = 1
    else:
        if any(CIRCULAR_IMPORT_RE.match(line) for line in canonical_lines):
            print(
                "  WARN  CLAUDE.md imports AGENTS.md - circular "
                "(AGENTS.md is a symlink). Remove that line."
            )
            status = 1

    status |= check_skill_mirror(root_dir, timestamp)
    status |= audit_version_stamp(root_dir)
    return status


def classify_budget_verdict(size: DocSize, budget: int) -> str:
    """Return PASS / WITHIN-SLACK / OVER for one measured doc."""
    if size.tokens <= budget:
        return "PASS"
    if size.tokens < budget * 1.5:
        return "WITHIN-SLACK"
    return "OVER"


def print_budget_verdict(
    label: str,
    rel_path: Path | str,
    size: DocSize,
    budget: int,
) -> int:
    """Print one budget verdict and return a non-zero status for hard failures."""
    prefix = (
        f"  {{level:<5}} [{label}] {rel_path} ~{size.tokens} tok "
        f"(budget <= {budget}, {size.lines} non-blank lines)"
    )

    verdict = classify_budget_verdict(size, budget)
    if verdict == "PASS":
        print(prefix.format(level="ok") + " - PASS")
        return 0

    if verdict == "WITHIN-SLACK":
        print(prefix.format(level="WARN") + " - WITHIN-SLACK")
        return 0

    print(prefix.format(level="FAIL") + " - OVER")
    return 1


def budget_verdict(label: str, rel_path: Path | str, file_path: Path, budget: int) -> int:
    """Measure one doc and print its budget verdict.

    An unreadable doc fails loudly instead of passing as a zero-cost file -
    one ERROR line followed by a PASS derived from a measurement of nothing.
    """
    size = measure(file_path)
    if size is None:
        print(f"  FAIL  [{label}] {rel_path} could not be read - budget UNCHECKED.")
        return 1
    return print_budget_verdict(label, rel_path, size, budget)


def is_umbrella(scoped_claude: Path, all_scoped: list[Path]) -> bool:
    """Return whether this scoped CLAUDE.md tops a subtree holding further ones."""
    parent = scoped_claude.parent
    return any(other != scoped_claude and parent in other.parents for other in all_scoped)


def audit_version_stamp(root_dir: Path) -> int:
    """Check VERSION against the newest dated CHANGELOG batch.

    The adoption flow stamps VERSION into a target as `.claude/.mas-version`,
    then applies only the CHANGELOG batches dated newer than that marker. If the
    two drift, adopters silently skip an update and nothing surfaces it. Only
    the kit's source repo has both files; elsewhere this is a no-op.
    """
    version_file = root_dir / "VERSION"
    changelog = root_dir / "CHANGELOG.md"
    if not (version_file.is_file() and changelog.is_file()):
        return 0

    try:
        version = version_file.read_text(encoding="utf-8", errors="ignore").strip()
        entries = changelog.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError as exc:
        print(f"  ERROR Reading VERSION/CHANGELOG.md: {exc}")
        return 1

    newest = next(
        (
            line[len("## ") :].strip()
            for line in entries
            if line.startswith("## ") and DATE_RE.match(line[len("## ") :].strip())
        ),
        None,
    )
    if newest is None:
        print("  WARN  CHANGELOG.md has no dated '## YYYY-MM-DD' batch to check VERSION against.")
        return 0

    if version == newest:
        print(f"  ok    VERSION {version} matches the newest CHANGELOG batch.")
        return 0

    print(
        f"  FAIL  VERSION is {version!r} but the newest CHANGELOG batch is {newest!r}. "
        "Adopters compare .claude/.mas-version against these headings, so a "
        "mismatch silently skips an update."
    )
    return 1


def iter_budget_targets(root_dir: Path, scan_errors: list[str]):
    """Yield (label, rel_path, file_path, budget) for every always-loaded doc.

    Single discovery order shared by the check gate and the debt report so the
    two can never disagree about what is in scope.
    """
    root_claude = root_dir / "CLAUDE.md"
    yield ("Root", root_claude.name, root_claude, BUDGET_ROOT_TOKENS)

    scoped_files = list(iter_scoped_claude_files(root_dir, scan_errors))
    for scoped_claude in scoped_files:
        umbrella = is_umbrella(scoped_claude, scoped_files)
        yield (
            "Umbrella" if umbrella else "Scoped",
            relative(scoped_claude, root_dir),
            scoped_claude,
            BUDGET_UMBRELLA_TOKENS if umbrella else BUDGET_SCOPED_TOKENS,
        )

    rules_dir = root_dir / ".claude" / "rules"
    if rules_dir.is_dir():
        for rules_file in sorted(rules_dir.rglob("*.md")):
            yield ("Rule", relative(rules_file, root_dir), rules_file, BUDGET_RULES_TOKENS)


def audit_budgets(root_dir: Path) -> int:
    """Part 2: Audit estimated token cost against size budgets."""
    status = 0
    print("\ndocreview: checking size budgets (estimated tokens; lines advisory)")

    scan_errors: list[str] = []
    for label, rel_path, file_path, budget in iter_budget_targets(root_dir, scan_errors):
        status |= budget_verdict(label, rel_path, file_path, budget)
    for scan_error in scan_errors:
        print(f"  FAIL  Could not scan {scan_error} - budgets there are UNCHECKED.")
        status = 1

    return status


def print_debt_report(root_dir: Path) -> int:
    """List files carrying budget debt (WITHIN-SLACK or OVER) with ratios.

    Report-only, always exits 0 - the `check` command stays the gate. WITHIN-SLACK
    flags printed nothing durable between runs; this is the artifact the next
    pass (or CI) picks up.
    """
    print(f"docreview: budget debt report for {root_dir}")

    scan_errors: list[str] = []
    found_debt = False
    for label, rel_path, file_path, budget in iter_budget_targets(root_dir, scan_errors):
        size = measure(file_path)
        if size is None:
            print(f"  ERROR [{label}] {rel_path} could not be read - debt UNKNOWN.")
            found_debt = True
            continue

        verdict = classify_budget_verdict(size, budget)
        if verdict == "PASS":
            continue

        ratio = size.tokens / budget
        print(
            f"  [{label}] {rel_path} ~{size.tokens} tok (budget <= {budget}) "
            f"{ratio:.2f}x - {verdict}"
        )
        found_debt = True

    for scan_error in scan_errors:
        print(f"  WARN  Could not scan {scan_error} - debt there is UNKNOWN.")
        found_debt = True

    if not found_debt:
        print("  ok    no WITHIN-SLACK or OVER files - no budget debt")
    print("  note  WITHIN-SLACK = over budget but < 1.5x (soft debt); OVER = the gate fails it.")
    return 0


def repo_root_from_script() -> Path:
    """Return the repo root that owns this script."""
    return Path(__file__).resolve().parent.parent


def git_worktree_root(cwd: Path) -> Path:
    """Return the Git worktree root for cwd."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"cannot run git to resolve the worktree root: {exc}") from exc
    if result.returncode != 0:
        raise ValueError(f"{cwd} is not inside a Git worktree")

    return Path(result.stdout.strip()).resolve()


def resolve_scope_root(scope: str, custom_path: str | None, cwd: Path) -> Path:
    """Resolve a user-selected scope root."""
    if scope == "auto":
        return repo_root_from_script()

    if scope in {"repo", "whole-repo"}:
        return repo_root_from_script()

    if scope in {"worktree", "work-tree"}:
        return git_worktree_root(cwd)

    if scope == "path":
        if not custom_path:
            raise ValueError("--scope path requires --path")
        custom_root = Path(custom_path).expanduser().resolve()
        if not custom_root.is_dir():
            # A missing root must fail loudly: os.walk over nothing looks
            # like full coverage, so a silent pass would certify air.
            raise ValueError(f"scope path is not an existing directory: {custom_path}")
        return custom_root

    raise ValueError(f"Unsupported scope: {scope}")


def print_missing_instruction_report(root_dir: Path) -> int:
    """Print directories missing CLAUDE.md and/or AGENTS.md, plus wrong-case variants."""
    print(f"docreview: reporting instruction-file coverage in {root_dir}")

    scan_errors: list[str] = []
    gaps = list(iter_instruction_file_gaps(root_dir, scan_errors))
    variants = list(iter_case_variants(root_dir, scan_errors))
    for scan_error in scan_errors:
        print(f"  WARN  Could not scan {scan_error} - coverage there is UNKNOWN.")
    if not gaps and not variants and not scan_errors:
        print("  ok    every directory in scope has correctly-cased CLAUDE.md and AGENTS.md")
        return 0

    for gap in gaps:
        missing = []
        if gap.missing_claude:
            missing.append("CLAUDE.md")
        if gap.missing_agents:
            missing.append("AGENTS.md")
        print(f"  info  {gap.relative_dir.as_posix()} missing {', '.join(missing)}")

    for rel_dir, name in variants:
        where = (rel_dir / name).as_posix()
        print(f"  info  {where} - wrong case; no agent reads it. Rename (git mv) to the exact name.")

    print(
        "  note  Missing CLAUDE.md entries are prompts to consider scoped files "
        "only when folder-specific rules warrant them."
    )
    return 0


def iter_markdown_docs(root_dir: Path, scan_errors: list[str]):
    """Yield repo-owned Markdown docs, skipping symlink mirrors and vendored dirs."""
    ignored = IGNORED_DIRS | load_extra_ignores(root_dir)
    for dirpath, dirnames, filenames in walk_reporting_errors(root_dir, scan_errors):
        dirnames[:] = sorted(
            name
            for name in dirnames
            if name not in ignored and not (Path(dirpath) / name).is_symlink()
        )

        path = Path(dirpath)
        for name in sorted(filenames):
            if not name.endswith(".md"):
                continue
            # AGENTS.md is a symlink to CLAUDE.md - counting it double-counts.
            if name == "AGENTS.md" or (path / name).is_symlink():
                continue
            yield path / name


def print_token_report(root_dir: Path, paths: list[str]) -> int:
    """Print estimated token cost for named docs, or every doc in scope."""
    scan_errors: list[str] = []
    if paths:
        targets = [Path(p).expanduser() for p in paths]
    else:
        targets = list(iter_markdown_docs(root_dir, scan_errors))
        print(f"docreview: estimating context cost of Markdown docs in {root_dir}")

    status = 0
    for scan_error in scan_errors:
        print(f"  WARN  Could not scan {scan_error} - docs there are not measured.")
        status = 1
    for target in targets:
        if not target.is_file():
            print(f"  ERROR {target} is not a readable file")
            status = 1
            continue

        size = measure(target)
        if size is None:
            status = 1
            continue
        try:
            label = relative(target.resolve(), root_dir).as_posix()
        except ValueError:
            label = str(target)
        print(f"  {label:<60} ~{size.tokens:>6} tok  {size.lines:>5} non-blank lines")

    print(f"  note  ~tok is chars/{CHARS_PER_TOKEN} over content that actually loads:")
    print("        block-level HTML comments are excluded everywhere, and YAML")
    print("        frontmatter everywhere except SKILL.md (whose description loads).")
    return status


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Verify/repair agent instruction wiring or report missing scoped files."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("check", "missing", "tokens", "debt"),
        default="check",
        help=(
            "check repairs wiring and budgets; missing reports directories without "
            "both files; tokens reports estimated context cost per doc; debt lists "
            "WITHIN-SLACK/OVER files with ratios (report-only)"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="files to measure with the tokens command; defaults to every doc in scope",
    )
    parser.add_argument(
        "--scope",
        choices=("auto", "repo", "whole-repo", "worktree", "work-tree", "path"),
        default="auto",
        help=(
            "scope root for the selected command; defaults to the project "
            "that owns this script"
        ),
    )
    parser.add_argument(
        "--path",
        help="custom scope root when --scope path is used",
    )
    return parser


def main() -> None:
    """Run docreview for the selected command and scope."""
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        root_dir = resolve_scope_root(args.scope, args.path, Path.cwd())
    except ValueError as exc:
        print(f"docreview: FAIL - {exc}", file=sys.stderr)
        sys.exit(2)

    if args.command == "missing":
        sys.exit(print_missing_instruction_report(root_dir))

    if args.command == "tokens":
        sys.exit(print_token_report(root_dir, args.paths))

    if args.command == "debt":
        sys.exit(print_debt_report(root_dir))

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
