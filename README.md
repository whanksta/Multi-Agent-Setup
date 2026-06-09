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

## Why run all three?

The agents aren't interchangeable — each trades speed against quality differently, and that's the
whole point:

- **Claude Code** — the strongest reasoning of the three, but the slowest. Reach for it on the hard,
  ambiguous, high-stakes work.
- **Codex** — almost as capable, and much faster. The everyday workhorse for fast, high-quality iteration.
- **Antigravity** — blazing fast, lighter on judgment. Great for quick, well-scoped changes and
  high-volume grunt work.

Point all three at **one shared rulebook** and they complement instead of compete: hand each task to
whichever fits the speed/quality tradeoff of the moment, and because every agent reads the same
`CLAUDE.md` and the same skills, the output stays consistent no matter who did it. That symbiosis
needs a single source of truth — which is what this kit enforces.

## Features

- **Single source of truth** — `CLAUDE.md` holds every shared rule; the other agents read the same bytes.
- **Zero duplication** — `AGENTS.md` is a symlink, not a copy, so it can never drift out of sync.
- **Skills shared too** — Claude's `.claude/skills/` is folder-symlinked into the `.agents/skills` dir Codex & Antigravity read, so a skill authored once auto-replicates to every agent.
- **Survives cloud sync** — works inside OneDrive / Google Drive / Dropbox; git preserves the symlink (mode `120000`).
- **Self-healing** — `docreview` detects and repairs a clobbered symlink, backing up any diverging content first.
- **Doc-quality audit** — the bundled `docreview` skill checks size budgets, scope, drift, broken links, and authoring quality.
- **Agent-agnostic** — Claude Code (CLI + desktop + web + IDE), Codex (CLI + desktop), and Antigravity (CLI + desktop) covered today.

## Quick start

### Start a new project

The clean case — nothing to consolidate. Click
**[Use this template](https://github.com/whanksta/MultiAgentSetup/generate)** → you get a fresh repo
with the wiring already in place and no inherited history. Then edit `CLAUDE.md` with your project's
rules and run `python3 scripts/docreview.py` to confirm `PASS`.

### Add it to an existing repo

More work than a new project: existing repos have usually **sprawled** — rules scattered across
`AGENTS.md`, `.cursorrules`, a stray `GEMINI.md`, loose notes, often disagreeing. So this is a
**clean + consolidate** pass: collapse them into one canonical `CLAUDE.md`, wire every agent to it,
and keep *your* rules (never the template's examples). Paste this to any agent from inside your repo:

> Incorporate the multi-agent instruction-file wiring from
> https://github.com/whanksta/MultiAgentSetup into THIS repo — **add it, don't replace anything I
> already have.** First **pre-consolidate**: read all existing instruction files (like AGENTS.md, .cursorrules,
> and scattered rule docs), extract and fold all their active rules into a single canonical **CLAUDE.md**
> (de-duplicating and keeping all my project's conventions, never swapping them for the template's examples).
> Doing this first ensures no rules are lost before files are replaced with symlinks.
> Then **wire to one source of truth**: delete the old AGENTS.md file and replace it with a symlink to
> CLAUDE.md; keep my canonical skills in .claude/skills/ and let docreview folder-symlink .agents/skills
> (read by Codex and Antigravity) to it — **symlink, never copy**; add scripts/docreview.py and the
> .gitignore entries. Finally run `python3 scripts/docreview.py` and confirm it prints `PASS`.

Prefer to wire it up yourself? See [Manual install](#manual-install).

## How it works

**Claude Code is the primary agent, so `CLAUDE.md` is canonical** — it holds all shared rules.
Every other agent reads it through `AGENTS.md`.

| Agent | Rules | Skills |
|-------|-------|--------|
| Claude Code (CLI + desktop + web + IDE) — primary | `CLAUDE.md` (native) | `.claude/skills/` (native, canonical) |
| Codex (CLI + desktop) | `AGENTS.md` → `CLAUDE.md` | `.agents/skills/` → `.claude/skills/` |
| Antigravity (CLI + desktop) | `AGENTS.md` → `CLAUDE.md` | `.agents/skills/` → `.claude/skills/` |

`AGENTS.md` is the cross-tool standard both Codex and Antigravity read, but neither resolves an
`@import`. So `AGENTS.md` is a **symlink** to `CLAUDE.md` — they read the canonical bytes directly,
with zero duplication. Claude owns `CLAUDE.md` natively; Claude-only rules live in `.claude/rules/`.

**Skills ride the same rails.** Claude's skills live in `.claude/skills/` (canonical); Codex and
Antigravity read them from `.agents/skills/`, a **folder symlink** to it — author a skill once and it
auto-replicates to every agent, no copy step. `docreview` maintains the link like it does `AGENTS.md`.

> **No Gemini?** Google retired Gemini CLI on 2026-06-18, replacing it with Antigravity (which reads
> `AGENTS.md`). Google's agent is covered by the symlink — a separate `GEMINI.md` is no longer needed.

### What's in the bundle

```
CLAUDE.md                  canonical rules — every agent reads this (edit per project)
AGENTS.md → CLAUDE.md      symlink: Codex + Antigravity read the rules through it
scripts/docreview.py       verify + auto-repair the wiring (agents, hooks, and CI all run it)
.claude/skills/docreview/  the /docreview skill: wiring check + doc-doctrine audit (canonical)
  reference/doctrine.md      CLAUDE.md rubric, 9 audit axes, size budgets, fix-classes
  reference/skill-axes.md    rubric for reviewing SKILL.md files
.agents/skills → .claude/skills   symlink: Codex + Antigravity read Claude's skills through it
.gitignore                 ignores CLAUDE.local.md + clobbered backups
```

### Cloud sync & symlinks

- OneDrive / Google Drive on macOS **preserve and sync symlinks** — the "OneDrive mangles symlinks" claim is false.
- Git stores symlinks portably (mode `120000`), so clones reconstruct them.
- **Windows:** symlinks need Developer Mode + `git config core.symlinks true`, or `AGENTS.md` **and**
  `.agents/skills` check out as plain files containing their target path. `docreview` repairs both.

### The one fragility → `docreview`

An **atomic save** (write-temp-then-rename) can turn either symlink — `AGENTS.md` or `.agents/skills`
— into a regular file, and edits to `CLAUDE.md` (or a skill) stop propagating. `scripts/docreview.py`
detects either case and re-links — backing up any diverging content to a `*.clobbered-<ts>` copy
first, so nothing is lost. It also recreates a symlink that has gone missing entirely.

`docreview` does two jobs: **(1) wiring** (the script, runnable by every agent and any hook/CI) and
**(2) a doc-doctrine audit** — size budgets, scope placement, drift, broken links, and
`CLAUDE.md` / `SKILL.md` authoring quality.

> **Rule of the road:** never write to `AGENTS.md`; edit `CLAUDE.md`; run `/docreview` (or
> `python3 scripts/docreview.py`) after touching any instruction file.

## Manual install

```bash
SRC=path/to/MultiAgentSetup; DST=.
mkdir -p "$DST"/{scripts,.claude/skills}
cp "$SRC"/CLAUDE.md "$DST"/                          # then replace CLAUDE.md's rules with yours
cp "$SRC"/scripts/docreview.py "$DST"/scripts/
cp -r "$SRC"/.claude/skills/docreview "$DST"/.claude/skills/   # canonical skill
cat "$SRC"/.gitignore >> "$DST"/.gitignore          # or merge by hand
ln -snf CLAUDE.md "$DST"/AGENTS.md                   # rules symlink
python3 "$DST"/scripts/docreview.py                  # mints skill mirrors (.agents/skills…); expect: docreview: PASS
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

1. CLAUDE.md (REAL, canonical): keep it if present — preserve all existing rules and add the wiring
   around them, never overwrite the project's own conventions; else create it with a short project
   description + a "Canonical instructions file" section stating CLAUDE.md is canonical (edited
   here), AGENTS.md is a symlink to it, .claude/rules/ is Claude-only, never write to AGENTS.md,
   run /docreview after edits — plus a "Scoped CLAUDE.md files" rule: add a folder-level CLAUDE.md
   only when that folder has a foot-gun not obvious from its code, point to root, keep it <=80 lines.
   **Pre-consolidate first:** Read all existing instruction files (including AGENTS.md, .cursorrules,
   GEMINI.md, etc.) and fold all active rules into CLAUDE.md. Doing this first ensures no rules are
   lost. Once consolidated, remove the redundant copies so only CLAUDE.md remains as the single source of truth.
2. AGENTS.md: delete any existing file, then create a relative symlink pointing to CLAUDE.md (so the
   script will just see a compliant setup and maintain it).
3. scripts/docreview.py: create the verify/auto-repair script that enforces this topology
   (CLAUDE.md real canonical; AGENTS.md symlink→CLAUDE.md, creating it if missing and re-linking +
   backing up a clobbered diverging AGENTS.md to AGENTS.md.clobbered-<ts>; no circular @./AGENTS.md
   in CLAUDE.md; and the skills mirror .agents/skills (read by Codex + Antigravity) as a folder
   symlink to .claude/skills, re-linking if missing/wrong and backing up real copies). chmod +x it.
4. .claude/skills/docreview/SKILL.md: a canonical "docreview" skill that runs python3
   scripts/docreview.py, reports the result, handles AGENTS.md.clobbered-* backups (summarize the
   diff, ask before folding in), and re-runs to confirm PASS. Do NOT copy the skill into other agents'
   dirs — docreview.py folder-symlinks .agents/skills -> .claude/skills so Codex and Antigravity
   read the same canonical skill.
5. .gitignore: add CLAUDE.local.md and AGENTS.md.clobbered-* (also covers skill-mirror backups).
6. Run python3 scripts/docreview.py, confirm "docreview: PASS", then summarize and remind me to edit
   shared rules and skills only in their canonical home (CLAUDE.md / .claude/skills/).

Context: Codex (CLI + desktop) + Antigravity (CLI + desktop) read AGENTS.md but can't auto-@import,
which is why AGENTS.md is a symlink (they read CLAUDE.md's bytes directly). Claude Code reads
CLAUDE.md natively. Skills work the same way: Claude's .claude/skills/ is canonical and is
folder-symlinked into .agents/skills (read by Codex and Antigravity), so a skill is authored once and
read by all three. The only fragility is an atomic-save turning a symlink into a regular file —
docreview repairs that. OneDrive/Google Drive on macOS preserve symlinks; git stores them mode
120000; Windows needs Developer Mode + core.symlinks=true.
```

</details>

## License

[MIT](LICENSE) — do whatever; no warranty.
