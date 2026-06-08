# MultiAgentSetup

> **One canonical rulebook that every AI coding agent reads.** Keep a single source of truth for
> your repo's rules across Claude Code, Codex, and Antigravity — and have it survive cloud sync,
> self-heal when an agent breaks the wiring, and audit its own docs.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Use this template](https://img.shields.io/badge/Use%20this%20template-2ea44f?logo=github&logoColor=white)](https://github.com/whanksta/MultiAgentSetup/generate)
[![works with](https://img.shields.io/badge/works%20with-Claude%20Code,%20Codex,%20Antigravity-blue)](#how-it-works)

Different AI coding agents read different instruction files — `CLAUDE.md`, `AGENTS.md`, and more.
Maintain them by hand and they drift; the rules start to disagree and agents pick a side at random.
**MultiAgentSetup** makes `CLAUDE.md` the one canonical file and wires every other agent's file back
to it, so you edit shared rules in exactly one place.

It's a tiny, drop-in bundle — click **Use this template** or copy it into any repo and you're set.

## Features

- **Single source of truth** — `CLAUDE.md` holds every shared rule; the other agents read the same bytes.
- **Zero duplication** — `AGENTS.md` is a symlink, not a copy, so it can never drift out of sync.
- **Survives cloud sync** — works inside OneDrive / Google Drive / Dropbox; git preserves the symlink (mode `120000`).
- **Self-healing** — `docreview` detects and repairs a clobbered symlink, backing up any diverging content first.
- **Doc-quality audit** — the bundled `docreview` skill checks size budgets, scope, drift, broken links, and authoring quality.
- **Agent-agnostic** — Claude Code (CLI + desktop + web + IDE), Codex (CLI + desktop), and Antigravity (CLI + desktop) covered today.

## Quick start

### Start a new project

Click **[Use this template](https://github.com/whanksta/MultiAgentSetup/generate)** → you get a
fresh repo with the wiring already in place and no inherited history. Then edit `CLAUDE.md` with your
project's rules.

### Add it to an existing repo

Fastest — from inside your repo, paste this to Claude Code (or any coding agent):

> Set up multi-agent instruction files like https://github.com/whanksta/MultiAgentSetup. Make
> CLAUDE.md the canonical rulebook (fold any existing AGENTS.md / .cursorrules content into it),
> replace AGENTS.md with a symlink to CLAUDE.md, add scripts/docreview.sh, the
> `.claude/skills/docreview` skill, and the `.gitignore` entries from that repo, then run
> `bash scripts/docreview.sh` and confirm it prints PASS.

Prefer to wire it up yourself? See [Manual install](#manual-install).

## How it works

**Claude Code is the primary agent, so `CLAUDE.md` is canonical** — it holds all shared rules.
Every other agent reads it through `AGENTS.md`.

| Agent | Reads | How |
|-------|-------|-----|
| Claude Code (CLI + desktop + web + IDE) — primary | `CLAUDE.md` | native |
| Codex (CLI + desktop) | `AGENTS.md` | symlink → `CLAUDE.md` |
| Antigravity (CLI + desktop) | `AGENTS.md` | symlink → `CLAUDE.md` |

`AGENTS.md` is the cross-tool standard both Codex and Antigravity read, but neither resolves an
`@import`. So `AGENTS.md` is a **symlink** to `CLAUDE.md` — they read the canonical bytes directly,
with zero duplication. Claude owns `CLAUDE.md` natively; Claude-only rules live in `.claude/rules/`.

> **No Gemini?** Google retired Gemini CLI on 2026-06-18, replacing it with Antigravity (which reads
> `AGENTS.md`). Google's agent is covered by the symlink — a separate `GEMINI.md` is no longer needed.

### What's in the bundle

```
CLAUDE.md                  canonical rules — every agent reads this (edit per project)
AGENTS.md → CLAUDE.md      symlink: Codex + Antigravity read the rules through it
scripts/docreview.sh       verify + auto-repair the wiring (agents, hooks, and CI all run it)
.claude/skills/docreview/  the /docreview skill: wiring check + doc-doctrine audit
  reference/doctrine.md      CLAUDE.md rubric, 9 audit axes, size budgets, fix-classes
  reference/skill-axes.md    rubric for reviewing SKILL.md files
.gitignore                 ignores CLAUDE.local.md + clobbered-symlink backups
```

### Cloud sync & symlinks

- OneDrive / Google Drive on macOS **preserve and sync symlinks** — the "OneDrive mangles symlinks" claim is false.
- Git stores symlinks portably (mode `120000`), so clones reconstruct them.
- **Windows:** symlinks need Developer Mode + `git config core.symlinks true`, or `AGENTS.md` checks
  out as a text file containing "CLAUDE.md". `docreview` repairs it.

### The one fragility → `docreview`

An **atomic save** (write-temp-then-rename) can replace the `AGENTS.md` symlink with a regular file,
and edits to `CLAUDE.md` stop propagating. `scripts/docreview.sh` detects it and re-links — backing
up any diverging content to `AGENTS.md.clobbered-<ts>` first, so nothing is lost. It also recreates
the symlink if `AGENTS.md` goes missing entirely.

`docreview` does two jobs: **(1) wiring** (the script, runnable by every agent and any hook/CI) and
**(2) a doc-doctrine audit** — size budgets, scope placement, drift, broken links, and
`CLAUDE.md` / `SKILL.md` authoring quality.

> **Rule of the road:** never write to `AGENTS.md`; edit `CLAUDE.md`; run `/docreview` (or
> `bash scripts/docreview.sh`) after touching any instruction file.

## Manual install

```bash
SRC=path/to/MultiAgentSetup; DST=.
mkdir -p "$DST"/{scripts,.claude/skills}
cp "$SRC"/CLAUDE.md "$DST"/                          # then replace CLAUDE.md's rules with yours
cp "$SRC"/scripts/docreview.sh "$DST"/scripts/
cp -r "$SRC"/.claude/skills/docreview "$DST"/.claude/skills/
cat "$SRC"/.gitignore >> "$DST"/.gitignore          # or merge by hand
ln -snf CLAUDE.md "$DST"/AGENTS.md
bash "$DST"/scripts/docreview.sh                     # expect: docreview: PASS
```

For an agent that can't see this repo's files, paste the full [Bootstrap Prompt](#bootstrap-prompt) instead.

## FAQ

**Why a symlink instead of copying the rules into `AGENTS.md`?**
A copy drifts the moment either file is edited. A symlink makes `AGENTS.md` *be* `CLAUDE.md` — one
set of bytes, no sync step, nothing to forget.

**Does this survive a machine wipe?**
Keep the repo on a GitHub remote. User-profile config (`~/.claude/`) is *not* migrated by a wipe —
the durable unit is always the repo. Carry the setup forward by templating/cloning it or pasting the
Bootstrap Prompt into the new repo.

**What about rules for a single subfolder?**
Add a `CLAUDE.md` to that folder *only* when it has a foot-gun not obvious from its code — point to
the root, don't restate it. `docreview` audits scoped files for exactly this (and flags ones that
don't earn their place).

## Bootstrap Prompt

<details>
<summary>Paste into an agent from inside the target repo (for when it can't see this repo's files).</summary>

```
Set up this repo for multi-agent instruction files, with Claude Code as the primary agent and
CLAUDE.md as the single canonical rulebook the other agents point at. Do all of the following:

1. CLAUDE.md (REAL, canonical): keep it if present; else create it with a short project
   description + a "Canonical instructions file" section stating CLAUDE.md is canonical (edited
   here), AGENTS.md is a symlink to it, .claude/rules/ is Claude-only, never write to AGENTS.md,
   run /docreview after edits — plus a "Scoped CLAUDE.md files" rule: add a folder-level CLAUDE.md
   only when that folder has a foot-gun not obvious from its code, point to root, keep it <=80 lines.
   If shared rules currently live in AGENTS.md / .cursorrules / elsewhere, consolidate into CLAUDE.md first.
2. AGENTS.md: delete any existing file, then  ln -snf CLAUDE.md AGENTS.md
3. scripts/docreview.sh: create the verify/auto-repair script that enforces this topology
   (CLAUDE.md real canonical; AGENTS.md symlink→CLAUDE.md, creating it if missing and re-linking +
   backing up a clobbered diverging AGENTS.md to AGENTS.md.clobbered-<ts>; no circular @./AGENTS.md
   in CLAUDE.md). chmod +x it.
4. .claude/skills/docreview/SKILL.md: a "docreview" skill that runs bash scripts/docreview.sh,
   reports the result, handles AGENTS.md.clobbered-* backups (summarize the diff, ask before
   folding in), and re-runs to confirm PASS.
5. .gitignore: add CLAUDE.local.md and AGENTS.md.clobbered-*.
6. Run bash scripts/docreview.sh, confirm "docreview: PASS", then summarize and remind me to edit
   shared rules only in CLAUDE.md.

Context: Codex (CLI + desktop) + Antigravity (CLI + desktop) read AGENTS.md but can't auto-@import,
which is why AGENTS.md is a symlink (they read CLAUDE.md's bytes directly). Claude Code reads
CLAUDE.md natively. The only fragility is an atomic-save turning the symlink into a regular file —
docreview repairs that. OneDrive/Google Drive on macOS preserve symlinks; git stores them mode
120000; Windows needs Developer Mode + core.symlinks=true.
```

</details>

## License

[MIT](LICENSE) — do whatever; no warranty.
