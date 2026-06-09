#!/usr/bin/env bash
# docreview.sh — verify & auto-repair the agent instruction-file wiring.
#
# Topology this enforces:
#   CLAUDE.md  = real canonical file (all shared rules)
#   AGENTS.md  = symlink -> CLAUDE.md   (Codex + Antigravity read rules through it)
#   .claude/rules/ = Claude-only rules
#   .claude/skills/ = canonical skills; each non-Claude agent's skills dir is a
#       symlink to it so skills auto-replicate from Claude with zero drift. Codex
#       and Antigravity both read .agents/skills -> ../.claude/skills. Add another
#       agent's skills dir via SKILL_MIRRORS.
#
# Safe to run anytime. Auto-fixes the AGENTS.md symlink and skill mirrors; never
# silently discards content (a clobbered AGENTS.md or diverging skill copy is
# backed up before repair).
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

# 4. Skill mirrors: each non-Claude agent's skills dir is a symlink to .claude/skills,
#    so every skill auto-replicates from Claude with zero drift (one symlink, like
#    AGENTS.md). Add an agent: append its skills dir (relative to repo root, parent
#    must exist or be creatable) to SKILL_MIRRORS.
SKILL_CANON=".claude/skills"
# Codex and Antigravity both read project skills from .agents/skills (-> ../.claude/skills).
# Add another agent by appending its skills dir (relative to repo root) here.
SKILL_MIRRORS=(".agents/skills")

if [[ -d "$SKILL_CANON" && ! -L "$SKILL_CANON" ]]; then
  for mirror in "${SKILL_MIRRORS[@]}"; do
    parent="$(dirname "$mirror")"
    # ../ prefix to climb from the mirror's parent dir back to repo root.
    up=""; IFS='/' read -ra _segs <<< "$parent"; for _ in "${_segs[@]}"; do up="../$up"; done
    want="${up}${SKILL_CANON}"
    if [[ -L "$mirror" ]]; then
      if [[ "$(readlink "$mirror")" == "$want" ]]; then
        echo "  ok    $mirror -> $want"
      else
        ln -snf "$want" "$mirror"; echo "  FIX   re-linked $mirror -> $want"; status=1
      fi
    elif [[ -e "$mirror" ]]; then
      # A real dir/file where the folder symlink belongs. Back up only if it holds a
      # real (non-symlink) skill that would be lost; a dir of symlinks is safe to drop.
      real_skill=""
      if [[ -d "$mirror" ]]; then
        for entry in "$mirror"/*/; do
          [[ -d "$entry" && ! -L "${entry%/}" ]] && { real_skill=1; break; }
        done
      fi
      if [[ -n "$real_skill" ]]; then
        backup="$mirror.clobbered-$ts"; cp -R "$mirror" "$backup"
        echo "  WARN  $mirror held real skill copies — backed up to $backup before replacing with symlink."; status=1
      elif [[ -d "$mirror" ]]; then
        echo "  WARN  $mirror was a dir of symlinks/empty — replacing with a single folder symlink."; status=1
      else
        echo "  WARN  $mirror was a regular file (dereferenced symlink) — replacing with a folder symlink."; status=1
      fi
      rm -rf "$mirror"; mkdir -p "$parent"; ln -snf "$want" "$mirror"
    else
      mkdir -p "$parent"; ln -snf "$want" "$mirror"; echo "  FIX   created $mirror -> $want"; status=1
    fi
  done
fi

if [[ $status -eq 0 ]]; then
  echo "docreview: PASS — instruction-file wiring is compliant."
else
  echo "docreview: repaired/flagged issues above. Re-run to confirm PASS."
fi
exit $status
