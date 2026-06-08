#!/usr/bin/env bash
# docreview.sh — verify & auto-repair the agent instruction-file wiring.
#
# Topology this enforces:
#   CLAUDE.md  = real canonical file (all shared rules)
#   AGENTS.md  = symlink -> CLAUDE.md   (Codex + Antigravity read rules through it)
#   .claude/rules/ = Claude-only rules
#
# Safe to run anytime. Auto-fixes the AGENTS.md symlink; never silently discards
# content (a clobbered AGENTS.md with diverging rules is backed up before repair).
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

status=0
ts="$(date +%Y%m%d-%H%M%S)"
echo "docreview: checking agent instruction files in $ROOT"

# 1. CLAUDE.md must exist and be a real (non-symlink) file.
if [[ ! -e CLAUDE.md ]]; then
  echo "  FAIL  CLAUDE.md (canonical) is missing — cannot continue."
  exit 1
elif [[ -L CLAUDE.md ]]; then
  echo "  FAIL  CLAUDE.md is a symlink but must be the real canonical file."
  status=1
else
  echo "  ok    CLAUDE.md is the real canonical file."
fi

# 2. AGENTS.md must be a symlink -> CLAUDE.md.
relink_agents() { ln -snf CLAUDE.md AGENTS.md && echo "  FIX   (re)created AGENTS.md -> CLAUDE.md symlink."; }
if [[ -L AGENTS.md ]]; then
  target="$(readlink AGENTS.md)"
  if [[ "$target" == "CLAUDE.md" ]]; then
    echo "  ok    AGENTS.md -> CLAUDE.md"
  else
    echo "  WARN  AGENTS.md points to '$target' (expected CLAUDE.md) — repairing."
    relink_agents; status=1
  fi
elif [[ -e AGENTS.md ]]; then
  # Regular file where a symlink belongs — clobbered by an atomic-save.
  if diff -q AGENTS.md CLAUDE.md >/dev/null 2>&1; then
    echo "  WARN  AGENTS.md is a regular file identical to CLAUDE.md (dereferenced copy) — replacing with symlink."
    rm -f AGENTS.md; relink_agents; status=1
  else
    backup="AGENTS.md.clobbered-$ts"
    cp AGENTS.md "$backup"
    echo "  WARN  AGENTS.md is a regular file that DIFFERS from CLAUDE.md."
    echo "        An agent likely wrote rules here. Backed up to: $backup"
    echo "        Review it, fold any wanted changes into CLAUDE.md, then re-run."
    rm -f AGENTS.md; relink_agents; status=1
  fi
else
  echo "  WARN  AGENTS.md missing — creating symlink."
  relink_agents; status=1
fi

# 3. Canonical must not import the symlink (would be circular).
if grep -q '^@\./AGENTS\.md' CLAUDE.md 2>/dev/null; then
  echo "  WARN  CLAUDE.md imports @./AGENTS.md — circular (AGENTS.md is a symlink to CLAUDE.md). Remove that line."
  status=1
fi

if [[ $status -eq 0 ]]; then
  echo "docreview: PASS — instruction-file wiring is compliant."
else
  echo "docreview: repaired/flagged issues above. Re-run to confirm PASS."
fi
exit $status
