# MultiAgentSetup

One canonical instruction system for Claude Code, Codex, and Antigravity.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Use this template](https://img.shields.io/badge/Use%20this%20template-2ea44f?logo=github&logoColor=white)](https://github.com/whanksta/MultiAgentSetup/generate)
[![works with](https://img.shields.io/badge/works%20with-Claude%20Code,%20Codex,%20Antigravity-blue)](#compatibility)

**Start here:** copy this repo link into your coding agent and let it handle everything:

```text
https://github.com/whanksta/MultiAgentSetup
```

From inside your target repo, tell the agent to read this repo, preserve your existing project
rules, adopt the multi-agent wiring, and run `python3 scripts/docreview.py`.

[Changelog](CHANGELOG.md) | [Bootstrap prompt](#bootstrap-prompt) | [Manual install](#manual-install)

## Why This Exists

Different coding agents read different instruction files. Claude Code reads `CLAUDE.md`; Codex and
Antigravity read `AGENTS.md`; skills live in different tool-specific folders. If those files are
copied by hand, they drift.

MultiAgentSetup makes `CLAUDE.md` the single source of truth, exposes it to other agents through an
`AGENTS.md` symlink, shares skills through a folder symlink, and ships `docreview` to verify and
repair the wiring.

## Quick Start

### New Repo

Click **[Use this template](https://github.com/whanksta/MultiAgentSetup/generate)**, then edit
`CLAUDE.md` with your project's real rules and run:

```bash
python3 scripts/docreview.py
```

Expect `docreview: PASS`.

### Existing Repo

Paste this into your agent from inside the repo you want to set up:

```text
Incorporate the multi-agent instruction-file wiring from
https://github.com/whanksta/MultiAgentSetup into THIS repo. Add it around my existing rules; do not
replace my project conventions.

First, pre-consolidate: read all existing instruction files such as AGENTS.md, .cursorrules,
GEMINI.md, and scattered rule docs. Fold their active rules into one canonical CLAUDE.md,
deduplicating and preserving my project's conventions.

Then wire one source of truth: replace AGENTS.md with a symlink to CLAUDE.md; keep shared skills in
.claude/skills; let docreview create .agents/skills as a folder symlink to .claude/skills; add
scripts/docreview.py and the needed .gitignore entries.

Finally, run python3 scripts/docreview.py and confirm it prints docreview: PASS.
```

### Existing Install

Paste this into your agent from inside a repo that already uses MultiAgentSetup:

```text
Pull the latest guidance from https://github.com/whanksta/MultiAgentSetup and update THIS repo's
multi-agent setup. Treat the repo link as the only source of truth: read README.md and CHANGELOG.md,
adopt relevant shared-kit changes to scripts/docreview.py, .claude/skills/docreview/, .gitignore,
and wiring docs, but preserve this repo's project-specific CLAUDE.md content.

Keep AGENTS.md as a symlink to CLAUDE.md, keep .agents/skills as a symlink to .claude/skills, then
run python3 scripts/docreview.py and confirm it prints docreview: PASS. Summarize what changed and
any adoption notes from CHANGELOG.md.
```

## What You Get

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Canonical shared rulebook. Edit project rules here. |
| `AGENTS.md` | Symlink to `CLAUDE.md` for Codex and Antigravity. |
| `.claude/skills/` | Canonical shared skills directory. |
| `.agents/skills` | Folder symlink to `.claude/skills`. |
| `scripts/docreview.py` | Verifies and repairs wiring; checks instruction-file size budgets. |
| `.claude/skills/docreview/` | Agent skill for wiring checks and doc-doctrine review. |
| `CHANGELOG.md` | Update notes for agents adopting changes from this repo link. |

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
- Run `/docreview` or `python3 scripts/docreview.py` after changing instruction files or skills.
- Add scoped `CLAUDE.md` files only for real folder-specific rules or foot-guns; point to root
  doctrine and keep scoped files small.
- Read [CHANGELOG.md](CHANGELOG.md) before pulling updates from this repo into an installed project.

## Manual Install

Most users should paste the repo link into an agent. If you want to wire the files yourself:

```bash
SRC=path/to/MultiAgentSetup
DST=.

mkdir -p "$DST"/{scripts,.claude/skills}
cp "$SRC"/CLAUDE.md "$DST"/
cp "$SRC"/scripts/docreview.py "$DST"/scripts/
cp -r "$SRC"/.claude/skills/docreview "$DST"/.claude/skills/
cat "$SRC"/.gitignore >> "$DST"/.gitignore
ln -snf CLAUDE.md "$DST"/AGENTS.md
python3 "$DST"/scripts/docreview.py
```

After copying, replace the template conventions in `CLAUDE.md` with your project's real rules.

## Compatibility

- **Claude Code:** reads `CLAUDE.md` directly.
- **Codex:** reads `AGENTS.md`, which points to `CLAUDE.md`.
- **Antigravity:** reads `AGENTS.md`, which points to `CLAUDE.md`.
- **Cloud sync:** OneDrive, Google Drive, and Dropbox on macOS preserve symlinks; Git stores symlinks
  portably as mode `120000`.
- **Windows:** symlinks require Developer Mode plus `git config core.symlinks true`, or an elevated
  shell. If symlinks check out as plain files, `docreview` will report the problem and repair it
  when the OS permits.
- **Gemini CLI:** Google announced that individual/free, Pro, and Ultra Gemini CLI request serving
  ends on June 18, 2026, with those users moving to Antigravity CLI; enterprise and API-key access
  differs. See Google's
  [transition note](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/).
  This kit targets Antigravity through `AGENTS.md` and no longer ships `GEMINI.md`.

## `docreview`

`docreview` has two jobs:

1. Verify and repair the mechanical wiring:
   `CLAUDE.md`, `AGENTS.md -> CLAUDE.md`, and `.agents/skills -> .claude/skills`.
2. Audit instruction docs for size, scope, drift, broken links, and authoring quality.

Run it anytime:

```bash
python3 scripts/docreview.py
```

If an agent clobbers a symlink with a real file, `docreview` backs up the divergent content to a
`*.clobbered-<timestamp>` file before restoring the symlink.

## FAQ

### Why a symlink instead of copying into `AGENTS.md`?

Copies drift. A symlink makes `AGENTS.md` read the same content as `CLAUDE.md`, with no sync step.

### Can I keep private local instructions?

Yes. Put machine-local preferences in `CLAUDE.local.md`; it is ignored by Git.

### What about rules for one subfolder?

Add a scoped `CLAUDE.md` only when that folder has a real convention or foot-gun not obvious from
the code. Keep must-hold-everywhere rules in the root `CLAUDE.md`.

### Does this survive a machine wipe?

Yes, as long as the repo is pushed to a Git remote. User-profile config such as `~/.claude/` is not
the durable unit; the repo is.

## Bootstrap Prompt

Use this longer prompt only when the target agent cannot inspect this repo directly.

<details>
<summary>Full fallback prompt</summary>

```text
Set up this repo for multi-agent instruction files, with Claude Code as the primary agent and
CLAUDE.md as the single canonical rulebook the other agents point at.

Do all of the following:

1. CLAUDE.md: keep it if present, preserving all existing rules and adding the wiring around them.
   If it does not exist, create it with a short project description, a "Canonical instructions file"
   section, scoped CLAUDE.md guidance, and the project's real conventions.

2. Pre-consolidate first: read all existing instruction files, including AGENTS.md, .cursorrules,
   GEMINI.md, and scattered rule docs. Fold all active rules into CLAUDE.md, deduplicate them, and
   preserve the project's conventions. Once consolidated, remove redundant copies so CLAUDE.md is
   the single source of truth.

3. AGENTS.md: delete any existing file after consolidation, then create a relative symlink pointing
   to CLAUDE.md.

4. scripts/docreview.py: create the verify/auto-repair script that enforces this topology:
   CLAUDE.md is real and canonical; AGENTS.md is a symlink to CLAUDE.md; .agents/skills is a folder
   symlink to .claude/skills; circular @./AGENTS.md imports are rejected; clobbered divergent files
   are backed up as *.clobbered-<timestamp>.

5. .claude/skills/docreview/: add the canonical docreview skill. Do not copy it into other agents'
   directories; .agents/skills must be a symlink to .claude/skills.

6. .gitignore: add CLAUDE.local.md and *.clobbered-*.

7. Run python3 scripts/docreview.py, confirm docreview: PASS, and remind me to edit shared rules and
   skills only in their canonical homes: CLAUDE.md and .claude/skills/.
```

</details>

## License

[MIT](LICENSE)
