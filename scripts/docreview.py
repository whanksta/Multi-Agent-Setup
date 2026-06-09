#!/usr/bin/env python3
# docreview.py — verify & auto-repair the agent instruction-file wiring and budgets.
#
# Topology this enforces:
#   CLAUDE.md  = real canonical file (all shared rules)
#   AGENTS.md  = symlink -> CLAUDE.md   (Codex + Antigravity read rules through it)
#   .claude/rules/ = Claude-only rules
#   .claude/skills/ = canonical skills; each non-Claude agent's skills dir is a
#       symlink to it so skills auto-replicate from Claude with zero drift.
#   [subfolder]/AGENTS.md = symlink -> CLAUDE.md in the same subfolder (scoped rules)
#
# Safe to run anytime. Auto-fixes symlinks; backs up diverging content to
# *.clobbered-<ts> before repair.

import os
import sys
import pathlib
import datetime
import shutil

# Size budgets
BUDGET_ROOT_CLAUDE = 200
BUDGET_SCOPED_CLAUDE = 80
BUDGET_RULES_FILE = 80

def get_non_blank_lines(file_path):
    """Count non-blank lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.strip() for line in f]
            return [line for line in lines if line]
    except Exception as e:
        print(f"  ERROR Reading {file_path}: {e}")
        return []

def safe_symlink(target, link_path, target_is_directory=False):
    """Create a symlink, catching OS errors with helpful messages (especially on Windows)."""
    # Delete existing file/link if any
    if os.path.lexists(link_path):
        if os.path.isdir(link_path) and not os.path.islink(link_path):
            shutil.rmtree(link_path)
        else:
            os.remove(link_path)
            
    try:
        os.symlink(target, link_path, target_is_directory=target_is_directory)
        return True
    except OSError as e:
        print(f"  FAIL  Failed to create symlink {link_path} -> {target}: {e}")
        if sys.platform == 'win32':
            print("        [Windows Tip] Creating symlinks on Windows requires Developer Mode enabled")
            print("        or running the shell as Administrator. You can also configure Git via:")
            print("        git config --global core.symlinks true")
        return False

def check_file_identical(path1, path2):
    """Check if two files have identical content."""
    try:
        if not os.path.exists(path1) or not os.path.exists(path2):
            return False
        with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
            return f1.read() == f2.read()
    except Exception:
        return False

def audit_wiring(root_dir, ts):
    """Part 1: Audit and repair instruction file wiring."""
    status = 0
    
    # 1. Root CLAUDE.md must exist and be a real file.
    root_claude = root_dir / "CLAUDE.md"
    if not root_claude.exists():
        print("  FAIL  CLAUDE.md (canonical) is missing — cannot continue.")
        sys.exit(1)
    elif root_claude.is_symlink():
        print("  FAIL  CLAUDE.md is a symlink but must be the real canonical file.")
        status = 1
    else:
        print("  ok    CLAUDE.md is the real canonical file.")

    # Helper function to check/heal an AGENTS.md symlink in a given directory
    def check_agents_symlink(claude_path, agents_path):
        nonlocal status
        if agents_path.is_symlink():
            target = os.readlink(agents_path)
            if target == "CLAUDE.md":
                print(f"  ok    {agents_path.relative_to(root_dir)} -> CLAUDE.md")
            else:
                print(f"  WARN  {agents_path.relative_to(root_dir)} points to '{target}' (expected CLAUDE.md) — repairing.")
                if safe_symlink("CLAUDE.md", agents_path):
                    print(f"  FIX   (re)created {agents_path.relative_to(root_dir)} symlink.")
                else:
                    status = 1
        elif agents_path.exists():
            # Regular file where a symlink belongs (dereferenced or diverged)
            if check_file_identical(claude_path, agents_path):
                print(f"  WARN  {agents_path.relative_to(root_dir)} is a regular file identical to CLAUDE.md — replacing with symlink.")
                if safe_symlink("CLAUDE.md", agents_path):
                    print(f"  FIX   Replaced with symlink.")
                else:
                    status = 1
            else:
                backup = agents_path.parent / f"AGENTS.md.clobbered-{ts}"
                shutil.copy2(agents_path, backup)
                print(f"  WARN  {agents_path.relative_to(root_dir)} is a regular file that DIFFERS from CLAUDE.md.")
                print(f"        An agent likely wrote rules here. Backed up to: {backup.relative_to(root_dir)}")
                print(f"        Review it, fold any wanted changes into CLAUDE.md, then delete {backup.relative_to(root_dir)}")
                if safe_symlink("CLAUDE.md", agents_path):
                    print(f"  FIX   Restored symlink.")
                else:
                    status = 1
        else:
            print(f"  WARN  {agents_path.relative_to(root_dir)} missing — creating symlink.")
            if safe_symlink("CLAUDE.md", agents_path):
                print(f"  FIX   Created symlink.")
            else:
                status = 1

    # 2. Root AGENTS.md must be a symlink -> CLAUDE.md
    root_agents = root_dir / "AGENTS.md"
    check_agents_symlink(root_claude, root_agents)

    # 3. Find scoped CLAUDE.md files and ensure corresponding AGENTS.md exists as relative symlinks
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prune search to avoid scanning dependency and system directories
        dirnames[:] = [d for d in dirnames if d not in ('.git', 'node_modules', 'venv', '.venv', '__pycache__', 'build', 'dist', '.agents')]
        path = pathlib.Path(dirpath)
        if path == root_dir:
            continue
            
        if "CLAUDE.md" in filenames:
            sub_claude = path / "CLAUDE.md"
            sub_agents = path / "AGENTS.md"
            check_agents_symlink(sub_claude, sub_agents)

    # 4. Canonical must not import the symlink (would be circular)
    try:
        with open(root_claude, 'r', encoding='utf-8', errors='ignore') as f:
            if any(line.startswith('@./AGENTS.md') for line in f):
                print("  WARN  CLAUDE.md imports @./AGENTS.md — circular (AGENTS.md is a symlink). Remove that line.")
                status = 1
    except Exception as e:
        print(f"  ERROR Checking circular imports in CLAUDE.md: {e}")
        status = 1

    # 5. Skill mirrors check
    skill_canon = root_dir / ".claude" / "skills"
    skill_mirrors = [root_dir / ".agents" / "skills"]

    if skill_canon.exists() and not skill_canon.is_symlink():
        for mirror in skill_mirrors:
            parent = mirror.parent
            # Relative path up from mirror's parent to the root, then to skill_canon
            # e.g., for .agents/skills, parent is .agents. We climb up 1 level: ../.claude/skills
            want = "../.claude/skills"
            
            if mirror.is_symlink():
                target = os.readlink(mirror)
                if target == want:
                    print(f"  ok    {mirror.relative_to(root_dir)} -> {want}")
                else:
                    print(f"  WARN  {mirror.relative_to(root_dir)} points to '{target}' (expected {want}) — repairing.")
                    if safe_symlink(want, mirror, target_is_directory=True):
                        print(f"  FIX   Re-linked {mirror.relative_to(root_dir)} -> {want}")
                    else:
                        status = 1
            elif mirror.exists():
                # Check if it has real files that would be clobbered
                has_real_files = False
                if mirror.is_dir():
                    for entry in mirror.iterdir():
                        if entry.is_dir() and not entry.is_symlink():
                            has_real_files = True
                            break
                if has_real_files:
                    backup = mirror.parent / f"skills.clobbered-{ts}"
                    shutil.copytree(mirror, backup)
                    print(f"  WARN  {mirror.relative_to(root_dir)} held real skill copies — backed up to {backup.relative_to(root_dir)} before replacing with symlink.")
                else:
                    print(f"  WARN  {mirror.relative_to(root_dir)} was a directory of symlinks/empty — replacing with symlink.")
                
                if safe_symlink(want, mirror, target_is_directory=True):
                    print(f"  FIX   Created folder symlink {mirror.relative_to(root_dir)} -> {want}")
                else:
                    status = 1
            else:
                parent.mkdir(parents=True, exist_ok=True)
                if safe_symlink(want, mirror, target_is_directory=True):
                    print(f"  FIX   Created {mirror.relative_to(root_dir)} -> {want}")
                else:
                    status = 1
                    
    return status

def audit_budgets(root_dir):
    """Part 2: Audit non-blank line counts against size budgets."""
    status = 0
    print("\ndocreview: checking size budgets (non-blank lines)")
    
    # 1. Check root CLAUDE.md
    root_claude = root_dir / "CLAUDE.md"
    root_lines = len(get_non_blank_lines(root_claude))
    
    if root_lines <= BUDGET_ROOT_CLAUDE:
        print(f"  ok    [Root] {root_claude.name} count: {root_lines} (budget <= {BUDGET_ROOT_CLAUDE}) — PASS")
    elif root_lines < BUDGET_ROOT_CLAUDE * 1.5:
        print(f"  WARN  [Root] {root_claude.name} count: {root_lines} (budget <= {BUDGET_ROOT_CLAUDE}) — WITHIN-SLACK")
    else:
        print(f"  FAIL  [Root] {root_claude.name} count: {root_lines} (budget <= {BUDGET_ROOT_CLAUDE}) — OVER")
        status = 1

    # 2. Check scoped CLAUDE.md files
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ('.git', 'node_modules', 'venv', '.venv', '__pycache__', 'build', 'dist', '.agents')]
        path = pathlib.Path(dirpath)
        if path == root_dir:
            continue
            
        if "CLAUDE.md" in filenames:
            sub_claude = path / "CLAUDE.md"
            sub_lines = len(get_non_blank_lines(sub_claude))
            rel_path = sub_claude.relative_to(root_dir)
            if sub_lines <= BUDGET_SCOPED_CLAUDE:
                print(f"  ok    [Scoped] {rel_path} count: {sub_lines} (budget <= {BUDGET_SCOPED_CLAUDE}) — PASS")
            elif sub_lines < BUDGET_SCOPED_CLAUDE * 1.5:
                print(f"  WARN  [Scoped] {rel_path} count: {sub_lines} (budget <= {BUDGET_SCOPED_CLAUDE}) — WITHIN-SLACK")
            else:
                print(f"  FAIL  [Scoped] {rel_path} count: {sub_lines} (budget <= {BUDGET_SCOPED_CLAUDE}) — OVER")
                status = 1

    # 3. Check Claude rules files (.claude/rules/*.md)
    rules_dir = root_dir / ".claude" / "rules"
    if rules_dir.is_dir():
        for file in rules_dir.glob("*.md"):
            rules_lines = len(get_non_blank_lines(file))
            rel_path = file.relative_to(root_dir)
            if rules_lines <= BUDGET_RULES_FILE:
                print(f"  ok    [Rule] {rel_path} count: {rules_lines} (budget <= {BUDGET_RULES_FILE}) — PASS")
            elif rules_lines < BUDGET_RULES_FILE * 1.5:
                print(f"  WARN  [Rule] {rel_path} count: {rules_lines} (budget <= {BUDGET_RULES_FILE}) — WITHIN-SLACK")
            else:
                print(f"  FAIL  [Rule] {rel_path} count: {rules_lines} (budget <= {BUDGET_RULES_FILE}) — OVER")
                status = 1

    return status

def main():
    script_dir = pathlib.Path(__file__).resolve().parent
    root_dir = script_dir.parent
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    
    print(f"docreview: checking agent instruction files in {root_dir}")
    
    wiring_status = audit_wiring(root_dir, ts)
    budget_status = audit_budgets(root_dir)
    
    overall_status = wiring_status | budget_status
    
    print("\n------------------------------------------------")
    if overall_status == 0:
        print("docreview: PASS — instruction-file wiring and budgets are compliant.")
    else:
        print("docreview: FAIL/WARN — repaired issues or exceeded budgets. Re-run to confirm PASS.")
        
    sys.exit(overall_status)

if __name__ == "__main__":
    main()
