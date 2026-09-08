# Multi-Agent-Setup

Two things every multi-agent repo needs, wired once: **one canonical instruction system** that
Claude Code, Codex, and Antigravity all read, and **`codebase-audit`**, a deterministic structural-
health signal your agents run before touching risky code.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![CI](https://github.com/whanksta/Multi-Agent-Setup/actions/workflows/ci.yml/badge.svg)](https://github.com/whanksta/Multi-Agent-Setup/actions/workflows/ci.yml)
[![Use this template](https://img.shields.io/badge/Use%20this%20template-2ea44f?logo=github&logoColor=white)](https://github.com/whanksta/Multi-Agent-Setup/generate)
[![works with](https://img.shields.io/badge/works%20with-Claude%20Code,%20Codex,%20Antigravity-blue)](#compatibility)

**Start here:** from inside your target repo, paste this link into your coding agent and tell it to
set up (or update) the kit:

```text
https://github.com/whanksta/Multi-Agent-Setup
```

The [single adoption prompt](#existing-or-installed-repo-one-prompt) below tells the agent exactly
what to do — **clone this repo for the exact files**, replicate the kit-owned ones, merge only root
`CLAUDE.md`, and run `python3 scripts/docreview.py`. The README and changelog are guidance for
adoption only; the agent reads them but does not copy them into your repo unless you ask.

[Changelog](CHANGELOG.md) | [Quick start](#quick-start) | [What you get](#what-you-get) |
[How it works](#how-it-works) | [Manual install](#manual-install) | [FAQ](#faq)

## Why This Exists

Different coding agents read different instruction files. Claude Code reads `CLAUDE.md`; Codex and
Antigravity read `AGENTS.md`; skills live in different tool-specific folders. If those files are
copied by hand, they drift.

Multi-Agent-Setup makes `CLAUDE.md` the single source of truth, exposes it to other agents through an
`AGENTS.md` symlink, shares skills through a folder symlink, and ships `docreview` to verify and
repair the wiring.

## Two Pillars

This kit ships two core capabilities:

1. **Instruction-file wiring** — `CLAUDE.md` is canonical; `AGENTS.md` and `.agents/skills` are
   symlinks so every agent reads the same bytes; `docreview` verifies and repairs that wiring and
   audits the docs for drift.
2. **`codebase-audit`** — a deterministic, repo-agnostic structural-health signal. It decomposes
   file size and layers in the git-temporal signals (churn, hotspots, temporal coupling) that
   actually predict where defects accrue, so an agent gets the wide quantitative picture before
   it judges what to refactor.

`codebase-audit` is **signal, not a gate** by design: it emits ranked evidence, never a pass/fail
verdict, so it informs judgment instead of blocking work. That is a feature — the agent stays in
control — not a disclaimer.

## Quick Start

Two ways in. For a brand-new repo, use the GitHub template button — no agent needed. For an existing
project (or to update an installed one), paste the single adoption prompt below; it detects which
situation you're in and adapts. Either way you need Git and Python 3.8+ (`docreview.py` alone runs
on 3.7+).

### New repo (template button)

Click **[Use this template](https://github.com/whanksta/Multi-Agent-Setup/generate)**, edit
`CLAUDE.md` with your project's real rules, then run `python3 scripts/docreview.py` and expect
`docreview: PASS`.

The template is a full copy, so it also ships the kit's source-repo artifacts — `tests/`,
`README.md`, `CHANGELOG.md`, `LICENSE`, and `.github/` (CI). Keep or delete them freely; they
are not wiring. When you later update via the one-prompt flow, the shipped root `VERSION` is your
baseline: the agent stamps `.claude/.mas-version` from it on the first update.

### Existing or installed repo (one prompt)

Paste this into your agent from inside the repo you want to set up or update. The same prompt covers
a fresh adoption, a repo that already has other agent files, and an update of an existing install:

```text
Set up (or update) this repo with the Multi-Agent-Setup kit from
https://github.com/whanksta/Multi-Agent-Setup.

1. GET THE EXACT FILES. Clone the source so you have its real bytes — do not retype scripts from a
   web page:
       git clone --depth 1 https://github.com/whanksta/Multi-Agent-Setup /tmp/mas
   Read /tmp/mas/README.md and /tmp/mas/CHANGELOG.md for guidance only. Never copy the source's
   README.md or CHANGELOG.md into my repo unless I explicitly ask.

2. DETERMINE THE SITUATION IMMEDIATELY — run this, do not infer it:
       MARKER=.claude/.mas-version
       [ -f "$MARKER" ] || MARKER=VERSION          # template-button adoptions carry root VERSION
       ADOPTED=$(cat "$MARKER" 2>/dev/null || echo none)
       NEWEST=$(grep -m1 -E '^## [0-9]{4}-[0-9]{2}-[0-9]{2}$' /tmp/mas/CHANGELOG.md | cut -d' ' -f2)
   Act on exactly one outcome:
   - ADOPTED = NEWEST  ->  UP TO DATE: report "already on <NEWEST>, nothing to apply" and STOP —
     skip steps 3-6 entirely.
   - ADOPTED = none    ->  FRESH install (if scripts/docreview.py exists but no marker does, it is
     an unstamped old install — treat it as fresh; step 5 stamps the marker).
   - anything else     ->  UPDATE: apply exactly the CHANGELOG batches dated after ADOPTED, oldest
     first, newest last. Batches at or before ADOPTED are already installed — never re-apply them.
   Separately, if my repo has other instruction files (a real AGENTS.md, .cursorrules, GEMINI.md,
   scattered rule docs)  ->  PRE-CONSOLIDATE: fold their active rules into one canonical CLAUDE.md,
   dedupe, and preserve my conventions; then remove the redundant copies — agent-instruction files
   only (the real AGENTS.md, .cursorrules, GEMINI.md, rule docs whose content you folded in). Never
   delete human-facing docs (README, docs/ handbooks); leave them in place.

3. REPLICATE KIT-OWNED FILES EXACTLY from /tmp/mas (see the Adoption File Policy table for the full
   list + per-file action): scripts/docreview.py, .claude/skills/docreview/,
   .claude/skills/codebase-audit/, and .githooks/pre-commit. Create AGENTS.md as a relative
   symlink to CLAUDE.md and .agents/skills as a folder symlink to .claude/skills. Add the needed
   .gitignore entries (CLAUDE.local.md, .claude/settings.local.json, __pycache__/, *.py[cod],
   *.clobbered-*, .DS_Store) without removing unrelated ones. If I previously patched any
   kit-owned file, diff my copy against the clone first, re-apply my patches after copying, and
   record them so the next update repeats this cleanly.

4. MERGE ONLY ROOT CLAUDE.md — it is my repo's master instruction file. Blend the kit's wiring
   sections with my existing project rules; never overwrite them.

5. STAMP THE VERSION: copy /tmp/mas/VERSION into my repo as .claude/.mas-version so the next update
   knows its baseline.

6. Run python3 scripts/docreview.py from my repo root — the copy just installed, not the /tmp/mas
   clone's script (that one audits the kit itself, not my repo). Confirm it prints docreview: PASS,
   then summarize what changed and any adoption notes from CHANGELOG.md.

Notes: a budget-tightening update can make the newly copied script FAIL before my conformance
edits exist — finish those edits first, then land the kit update + conformance edits as adjacent
commits (or one --no-verify commit for the regime change itself). Work to the end: you have ample
context remaining; do not stop, summarize, or suggest a new session mid-flow.
```

No `git`? Download the source zip instead, then use it as `SRC` anywhere the prompt says `/tmp/mas`:

```bash
curl -L https://github.com/whanksta/Multi-Agent-Setup/archive/refs/heads/main.zip -o /tmp/mas.zip
python3 -m zipfile -e /tmp/mas.zip /tmp
SRC=/tmp/Multi-Agent-Setup-main
```

Then follow steps 2–6, replacing `/tmp/mas` with `$SRC`.

**Zip caveat:** zip extraction stores symlinks as plain text files — `AGENTS.md` becomes a 9-byte
file containing `CLAUDE.md`, and `.agents/skills` likewise. Never copy those two paths from a zip
source; create them as symlinks per the Adoption File Policy (the manual-install `ln -snf` step or
`docreview` itself does this). The GitHub zip also extracts under a wrapper folder named after the
ref (`Multi-Agent-Setup-main` for `main`; a tag zip differs), so check what `$SRC` actually
contains.

### Adoption File Policy

The agent's per-file contract. "Copy exactly" means byte-for-byte from the clone in step 1.

| Source path | Agent action in target repo |
|-------------|-----------------------------|
| `README.md`, `CHANGELOG.md` | Read for guidance and adoption notes only. Do not copy or overwrite target docs unless the user explicitly asks. |
| `scripts/docreview.py` | Copy exactly from the clone. |
| `.claude/skills/docreview/` | Copy exactly into the canonical skill location. |
| `.claude/skills/codebase-audit/` | Copy exactly — it is a core part of the kit, not an optional add-on. |
| `.githooks/pre-commit` | Copy exactly (enable with `git config core.hooksPath .githooks`). |
| `VERSION` | Copy its value into the target as `.claude/.mas-version` to record the adopted version. Do not plant a root `VERSION` in the target. |
| `tests/` | Source-repo regression suite for the scripts. Do not copy during adoption; template-button repos inherit it and may keep or delete it. |
| `.github/` | Source-repo CI workflow for the test suite. Do not copy during adoption; template-button repos inherit it and may keep or delete it. |
| `.gitignore` | Add required entries such as `CLAUDE.local.md`, `*.clobbered-*`, `__pycache__/`, and `*.py[cod]`; preserve unrelated target entries. |
| `CLAUDE.md` | Merge/blend wiring guidance with existing project instructions; never overwrite project rules blindly. |
| `AGENTS.md` | Create as a relative symlink to `CLAUDE.md` after consolidating existing agent rules. |
| `.agents/skills` | Create as a folder symlink to `.claude/skills`; do not copy skill files into the mirror. |

## What You Get

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Canonical shared rulebook. Edit project rules here. |
| `AGENTS.md` | Symlink to `CLAUDE.md` for Codex and Antigravity. |
| `.claude/skills/` | Canonical shared skills directory. |
| `.agents/skills` | Folder symlink to `.claude/skills`. |
| `scripts/docreview.py` | Verifies and repairs wiring; checks instruction-file size budgets in estimated tokens; `debt` reports soft budget debt; `.docreview-ignore` holds local extra ignores. |
| `.githooks/pre-commit` | Optional Git hook running `docreview` (gate) + `codebase-audit --staged` (advisory) before each commit. |
| `.github/workflows/ci.yml` | CI for this source repo: runs the test suite on push and pull request. Inherited by template-button copies; not copied by one-prompt adoption. |
| `.claude/skills/docreview/` | Agent skill for wiring checks and doc-doctrine review. |
| `.claude/skills/codebase-audit/` | Core agent skill + script for structural hotspot/churn signals (advisory, not a gate). |
| `VERSION` | Kit version string; copied into an adopting repo as `.claude/.mas-version`. |
| `CHANGELOG.md` | Source-side update notes for agents to read before adopting changes. |

## How It Works

| Agent | Rules | Skills |
|-------|-------|--------|
| Claude Code | `CLAUDE.md` | `.claude/skills/` |
| Codex | `AGENTS.md -> CLAUDE.md` | `.agents/skills -> .claude/skills` |
| Antigravity | `AGENTS.md -> CLAUDE.md` | `.agents/skills -> .claude/skills` |

`AGENTS.md` is a symlink, not a copy, because Codex and Antigravity read `AGENTS.md` but do not need
a separate rulebook. They read the same bytes Claude Code reads from `CLAUDE.md`.

Skills use the same pattern. Author shared skills once in `.claude/skills/`; Codex and Antigravity
see them through `.agents/skills`.

## Daily Workflow

- Edit shared rules in `CLAUDE.md`, never in `AGENTS.md`.
- Edit shared skills in `.claude/skills/`, never in `.agents/skills`.
- Run `/docreview` after changing instruction files or skills — the doctrine audit runs by
  default. (`python3 scripts/docreview.py` alone checks only wiring + budgets.)
- Add scoped `CLAUDE.md` files only for real folder-specific rules or foot-guns; point to root
  doctrine and keep scoped files small.
- Read [CHANGELOG.md](CHANGELOG.md) before pulling updates from this repo into an installed project.

## Manual Install

Most users should paste the repo link into an agent. If you want to wire the files yourself:

```bash
git clone --depth 1 https://github.com/whanksta/Multi-Agent-Setup /tmp/mas
SRC=/tmp/mas
DST=.

mkdir -p "$DST"/{scripts,.claude/skills}
cp "$SRC"/scripts/docreview.py "$DST"/scripts/
cp -r "$SRC"/.claude/skills/docreview "$DST"/.claude/skills/
cp -r "$SRC"/.claude/skills/codebase-audit "$DST"/.claude/skills/
mkdir -p "$DST"/.githooks
cp "$SRC"/.githooks/pre-commit "$DST"/.githooks/
touch "$DST"/.gitignore                          # add missing entries only; re-runnable
while IFS= read -r l; do
  [ -n "$l" ] && ! grep -qxF "$l" "$DST"/.gitignore && printf '%s\n' "$l" >> "$DST"/.gitignore
done < "$SRC"/.gitignore
cp "$SRC"/VERSION "$DST"/.claude/.mas-version   # record the adopted version

if [ -e "$DST"/CLAUDE.md ]; then
  echo "CLAUDE.md exists; merge the wiring sections from $SRC/CLAUDE.md manually."
else
  cp "$SRC"/CLAUDE.md "$DST"/
fi

ln -snf CLAUDE.md "$DST"/AGENTS.md
python3 "$DST"/scripts/docreview.py   # also creates .agents/skills -> ../.claude/skills
```

For new repos, replace the template conventions in `CLAUDE.md` with your project's real rules. For
existing repos, merge the source `CLAUDE.md` wiring sections into the current project instructions
instead of overwriting them.

## Compatibility

- **Claude Code:** reads `CLAUDE.md` directly.
- **Codex:** reads `AGENTS.md`, which points to `CLAUDE.md`.
- **Antigravity:** reads `AGENTS.md`, which points to `CLAUDE.md`.
- **Cloud sync:** OneDrive, Google Drive, and Dropbox on macOS preserve symlinks; Git stores symlinks
  portably as mode `120000`.
- **Windows:** symlinks require Developer Mode plus `git config core.symlinks true`, or an elevated
  shell. If symlinks check out as plain files, `docreview` will report the problem and repair it
  when the OS permits.
- **Filename case:** `CLAUDE.md` and `AGENTS.md` exactly — Claude Code and Codex match the literal
  names, so a lowercase variant can seem to work on macOS/Windows and silently fails on Linux.
  `docreview` detects wrong-case files by directory entries and renames them automatically
  (`git mv` when the file is tracked, so the index follows the case change).
- **Gemini CLI:** Google ended individual/free, Pro, and Ultra Gemini CLI request serving on
  June 18, 2026, moving those users to Antigravity CLI; enterprise and API-key access differs.
  See Google's
  [transition note](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/).
  This kit targets Antigravity through `AGENTS.md` and no longer ships `GEMINI.md`.

## `docreview`

`docreview` has two jobs:

1. Verify and repair the mechanical wiring:
   `CLAUDE.md`, `AGENTS.md -> CLAUDE.md`, and `.agents/skills -> .claude/skills`.
2. Audit instruction docs for size, scope, drift, broken links, and authoring quality.

Run the mechanical half anytime — the pre-commit hook runs this too:

```bash
python3 scripts/docreview.py   # wiring repair + token budgets only
```

The doctrine audit (job 2) is not scriptable — it is Part 2 of the `docreview` skill, run by an
agent's judgment. A bare `/docreview` means a full doc review; say "wiring only" to skip the
doctrine pass.

The doctrine is aligned with current published practice — Anthropic's 2026 system-prompt cuts
(frontier models need less scaffolding) and empirical study of real instruction files: keep them
short, imperative, free of lint restatement, and limited to what the model can't infer from the
repo.

If an agent clobbers a symlink with a real file, `docreview` backs up the divergent content to a
`*.clobbered-<timestamp>` file before restoring the symlink.

To inventory folders that do not have scoped instruction files, use the report-only `missing`
command. It does not create files or repair symlinks:

```bash
python3 scripts/docreview.py missing
python3 scripts/docreview.py missing --scope repo
python3 scripts/docreview.py missing --scope worktree
python3 scripts/docreview.py missing --scope path --path path/to/subtree
```

To see what each doc actually costs in context, use the `tokens` command. Size budgets are measured
in **estimated tokens, not lines** — a 30-line file of wide table rows can cost 2,000+ tokens, so a
line count hides real bloat. The estimate is `chars / 2.5` over the content that actually loads:
block-level HTML comments are excluded everywhere, and YAML frontmatter everywhere except a
`SKILL.md`, whose `name`/`description` do load via the skill listing.

```bash
python3 scripts/docreview.py tokens                # every doc in scope
python3 scripts/docreview.py tokens CLAUDE.md      # named files
```

Local ignores: extra ignored directory names (generated-output folders, worktree checkouts)
live in a `.docreview-ignore` file at the scope root — the repo root in the default scope — one
name per line, `#` comments (full-line or trailing) allowed; commit it so the whole team shares
it. Customization never forks the script's bytes.

Soft budget debt has a durable artifact — `python3 scripts/docreview.py debt` lists every
WITHIN-SLACK/OVER file with its tokens/budget ratio. Report-only, always exits 0; the `check`
command stays the gate.

The default scope is auto: use the project that owns `scripts/docreview.py`, independent of the
current working directory. Use `--scope worktree` when you explicitly want the current Git worktree,
`--scope repo` / `--scope whole-repo` when you want the project that owns the script, or
`--scope path` for an arbitrary folder. Missing scoped files are informational prompts: add a scoped
`CLAUDE.md` only when that folder has a real folder-specific convention or foot-gun, then run the
normal wiring check.

Requires Python 3.7+ for `docreview.py`; the `codebase-audit` script requires 3.8+ (assignment
expressions).

## `codebase-audit`

`codebase-audit` emits a ranked health digest for source files: decomposed size, biggest symbol,
biggest function, nesting, density, churn, hotspot, and temporal coupling. It uses Git history when
available and falls back to a filesystem scan without Git. It is a thinking aid for agents, not a
linter and not a gate.

Run a full audit from any wired repo:

```bash
python3 .claude/skills/codebase-audit/scripts/audit.py
```

The pre-commit hook runs `audit.py --staged` after `docreview` passes. That staged check is
advisory and must always exit zero; do not add thresholds that block commits.

To verify the bundled script in this source repo, run the stdlib test suite:

```bash
python3 -m unittest discover -s tests
```

## FAQ

### Why a symlink instead of copying into `AGENTS.md`?

Copies drift. A symlink makes `AGENTS.md` read the same content as `CLAUDE.md`, with no sync step.

### Can I keep private local instructions?

Yes. Put machine-local preferences in `CLAUDE.local.md`; it is ignored by Git. Current Claude Code
versions load it automatically; if yours doesn't, add `@./CLAUDE.local.md` to `CLAUDE.md` so it
loads as an explicit import.

### What about rules for one subfolder?

Add a scoped `CLAUDE.md` only when that folder has a real convention or foot-gun not obvious from
the code. Keep must-hold-everywhere rules in the root `CLAUDE.md`.

### Does this survive a machine wipe?

Yes, as long as the repo is pushed to a Git remote. User-profile config such as `~/.claude/` is not
the durable unit; the repo is.

### How does an update know what changed?

On install the agent stamps `.claude/.mas-version` with the kit's `VERSION`. On the next update it
reads that marker and applies only the `CHANGELOG.md` batches dated newer than it, then re-stamps —
so updates are incremental and you can see exactly which version a repo is on. If the marker
already equals the newest batch, the agent reports "up to date" and stops — no update is inferred
or attempted.

## License

[MIT](LICENSE)
