# MultiAgentSetup

One canonical instruction system for Claude Code, Codex, and Antigravity.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Use this template](https://img.shields.io/badge/Use%20this%20template-2ea44f?logo=github&logoColor=white)](https://github.com/whanksta/Multi-Agent-Setup/generate)
[![works with](https://img.shields.io/badge/works%20with-Claude%20Code,%20Codex,%20Antigravity-blue)](#compatibility)

**Start here:** copy this repo link into your coding agent and let it handle everything:

```text
https://github.com/whanksta/Multi-Agent-Setup
```

From inside your target repo, tell the agent to read this repo's README and changelog, identify what
changed from the target repo's current setup, adopt the kit-owned files, merge only the root
`CLAUDE.md` with existing project instructions, and run `python3 scripts/docreview.py`.

[Changelog](CHANGELOG.md) | [Bootstrap prompt](#bootstrap-prompt) | [Manual install](#manual-install)

## Why This Exists

Different coding agents read different instruction files. Claude Code reads `CLAUDE.md`; Codex and
Antigravity read `AGENTS.md`; skills live in different tool-specific folders. If those files are
copied by hand, they drift.

MultiAgentSetup makes `CLAUDE.md` the single source of truth, exposes it to other agents through an
`AGENTS.md` symlink, shares skills through a folder symlink, and ships `docreview` to verify and
repair the wiring.

## Quick Start

### Adoption Protocol

Whether this is a first install or an update, the agent should always start by reading `README.md`
and [CHANGELOG.md](CHANGELOG.md) from this repo link.

- **New setup:** replicate kit-owned files and symlinks exactly from this repo, then customize only
  root `CLAUDE.md` for the target project.
- **Existing setup:** compare this repo against the target repo's current implementation, identify
  changes from the changelog, and replicate kit-owned files exactly.
- **Only exception:** root `CLAUDE.md` is the target project's master instruction file. Preserve and
  blend existing project instructions there instead of overwriting it.
- **Project files:** add required `.gitignore` entries without removing unrelated project entries.

### New Repo

Click **[Use this template](https://github.com/whanksta/Multi-Agent-Setup/generate)**, then edit
`CLAUDE.md` with your project's real rules and run:

```bash
python3 scripts/docreview.py
```

Expect `docreview: PASS`.

### Existing Repo

Paste this into your agent from inside the repo you want to set up:

```text
Incorporate the multi-agent instruction-file wiring from
https://github.com/whanksta/Multi-Agent-Setup into THIS repo. Treat that repo link as the only
source of truth: read README.md and CHANGELOG.md before editing.

First, pre-consolidate: read all existing instruction files such as AGENTS.md, .cursorrules,
GEMINI.md, and scattered rule docs. Fold their active rules into one canonical CLAUDE.md,
deduplicating and preserving my project's conventions. CLAUDE.md is the only file that should blend
the kit with existing project-specific instructions.

Then wire one source of truth: replicate kit-owned files exactly from Multi-Agent-Setup, including
scripts/docreview.py, .claude/skills/docreview/, .githooks/pre-commit, AGENTS.md as a symlink to
CLAUDE.md, and .agents/skills as a folder symlink to .claude/skills. Add the needed .gitignore
entries without removing unrelated project entries.

Finally, run python3 scripts/docreview.py and confirm it prints docreview: PASS.
```

### Existing Install

Paste this into your agent from inside a repo that already uses MultiAgentSetup:

```text
Pull the latest guidance from https://github.com/whanksta/Multi-Agent-Setup and update THIS repo's
multi-agent setup. Treat the repo link as the only source of truth: read README.md and CHANGELOG.md,
compare the target repo's current implementation against the source repo, and identify the changes
to adopt.

Replicate kit-owned files exactly: scripts/docreview.py, .claude/skills/docreview/,
.githooks/pre-commit, AGENTS.md as a symlink to CLAUDE.md, and .agents/skills as a symlink to
.claude/skills. Add required .gitignore entries without removing unrelated project entries.

Only merge/blend root CLAUDE.md, because it is the target repo's master instruction file and may
already contain project-specific rules. Then run python3 scripts/docreview.py and confirm it prints
docreview: PASS. Summarize what changed and any adoption notes from CHANGELOG.md.
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
SRC=path/to/Multi-Agent-Setup
DST=.

mkdir -p "$DST"/{scripts,.claude/skills}
cp "$SRC"/scripts/docreview.py "$DST"/scripts/
cp -r "$SRC"/.claude/skills/docreview "$DST"/.claude/skills/
mkdir -p "$DST"/.githooks
cp "$SRC"/.githooks/pre-commit "$DST"/.githooks/
cat "$SRC"/.gitignore >> "$DST"/.gitignore

if [ -e "$DST"/CLAUDE.md ]; then
  echo "CLAUDE.md exists; merge the wiring sections from $SRC/CLAUDE.md manually."
else
  cp "$SRC"/CLAUDE.md "$DST"/
fi

ln -snf CLAUDE.md "$DST"/AGENTS.md
python3 "$DST"/scripts/docreview.py
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

Requires Python 3.7+.

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

First read README.md and CHANGELOG.md from https://github.com/whanksta/Multi-Agent-Setup. If this is
a new setup, replicate kit-owned files exactly. If this repo already has MultiAgentSetup, compare
the current implementation against the source repo and identify the changelog changes to adopt.

Do all of the following:

1. CLAUDE.md: keep it if present, preserving all existing rules and adding the wiring around them.
   If it does not exist, create it with a short project description, a "Canonical instructions file"
   section, scoped CLAUDE.md guidance, and the project's real conventions. This is the only file
   where source-repo content should be blended with existing project-specific instructions.

2. Pre-consolidate first: read all existing instruction files, including AGENTS.md, .cursorrules,
   GEMINI.md, and scattered rule docs. Fold all active rules into CLAUDE.md, deduplicate them, and
   preserve the project's conventions. Once consolidated, remove redundant copies so CLAUDE.md is
   the single source of truth.

3. AGENTS.md: delete any existing file after consolidation, then create a relative symlink pointing
   to CLAUDE.md.

4. scripts/docreview.py: replicate the source repo's script exactly. It enforces this topology:
   CLAUDE.md is real and canonical; AGENTS.md is a symlink to CLAUDE.md; .agents/skills is a folder
   symlink to .claude/skills; circular @./AGENTS.md imports are rejected; clobbered divergent files
   are backed up as *.clobbered-<timestamp>.

5. .claude/skills/docreview/: replicate the source repo's canonical docreview skill exactly. Do not
   copy it into other agents' directories; .agents/skills must be a symlink to .claude/skills.

6. .githooks/pre-commit: replicate the source repo's hook exactly. .gitignore: add
   CLAUDE.local.md and *.clobbered-* without removing unrelated project entries.

7. Run python3 scripts/docreview.py, confirm docreview: PASS, and remind me to edit shared rules and
   skills only in their canonical homes: CLAUDE.md and .claude/skills/.
```

</details>

## License

[MIT](LICENSE)
