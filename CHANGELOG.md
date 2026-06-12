# Changelog

This file is for agents as much as humans. When a user pastes the repo link into an agent later,
the agent should read this file to understand what changed and what the target repo should adopt.

This repo uses the GitHub repo link as the delivery channel, so dated sections represent update
batches available once committed.

Historical entries were reconstructed from Git history through `7b20a84`.

## 2026-06-12

### Changed

- Clarified the repo-link adoption protocol: agents must always read `README.md` and
  `CHANGELOG.md`, then identify what changed from the target repo's current implementation before
  installing or updating.
- Made exact replication the default for kit-owned files and symlinks, including
  `scripts/docreview.py`, `.claude/skills/docreview/`, `.githooks/pre-commit`, `AGENTS.md`, and
  `.agents/skills`.
- Modernized `scripts/docreview.py` into a cleaner source-template style: sorted imports,
  pathlib-first helpers, typed functions, shared ignore-directory constants, and wrapped diagnostics
  while preserving the same wiring and budget checks.
- Added Python bytecode cache ignores to `.gitignore` for `__pycache__/` and `*.py[cod]`.
- Made `.agents/skills` repair back up any real non-empty content before replacing it with the
  canonical folder symlink.
- Updated the pre-commit hook to fail if `docreview.py` repairs the worktree, so repairs can be
  staged and committed explicitly.
- Clarified the `docreview` skill workflow: run `python3 scripts/docreview.py` first to normalize
  wiring, choose either full or scoped doctrine review, then run the Python script again as the final
  mechanical check.
- Broadened full `docreview` scope to every repo-owned Markdown doc exactly once while excluding
  symlink mirrors such as `AGENTS.md` and `.agents/skills`.
- Updated manual install instructions so existing repos never overwrite root `CLAUDE.md`.
- Documented that `docreview.py` requires Python 3.7+ while keeping the modern source style.
- Clarified the one merge/blend exception: root `CLAUDE.md` is the target repo's master instruction
  file, so existing project-specific instructions must be preserved and blended instead of
  overwritten.
- Updated README links and prompts to use the canonical moved repo URL:
  `https://github.com/whanksta/Multi-Agent-Setup`.

### Adoption Notes

- For new installs, replicate kit-owned files exactly and customize only root `CLAUDE.md`.
- For existing installs, compare against the current source repo and changelog before editing; copy
  kit-owned files exactly, merge only root `CLAUDE.md`, and preserve unrelated project `.gitignore`
  entries.
- Replace `scripts/docreview.py` from the source repo exactly, even when the target repo's older
  version is functionally similar; this carries the canonical script style forward.

## 2026-06-11

### Added

- Added this changelog as the update notes carried by the repo link itself.
- Added README guidance for the link-only workflow: users can paste
  `https://github.com/whanksta/Multi-Agent-Setup` into an agent for both first install and later
  updates.
- Added an "Update an installed repo" agent prompt that tells future agents to read this README and
  changelog before adopting changes.
- Added `.githooks/pre-commit`, which runs `python3 scripts/docreview.py` before commits when a
  clone enables it with `git config core.hooksPath .githooks`.

### Changed

- Updated the root `CLAUDE.md` template with the optional pre-commit hook setup command, a stronger
  cross-agent review convention, and a clearer scoped-file budget rule.
- Reworked README into a more standard open-source layout: concise intro, quick start, install and
  update prompts, file map, compatibility notes, `docreview` usage, FAQ, and a collapsible fallback
  bootstrap prompt.
- Updated README's Gemini/Antigravity compatibility note to describe the June 18, 2026 transition
  as an upcoming service change for affected Gemini CLI users, not a past event.
- Tightened the `docreview` skill so Part 1 explicitly includes size-budget verdicts, Part 2 reuses
  those counts, the default audit scope includes `CLAUDE.local.md`, and static skill review now
  covers axes 1-12.
- Expanded doc doctrine from 9 to 10 audit axes by adding a Completeness check, clarified command
  verification as part of doctrine-vs-reality, improved shell-safe verification commands, and added
  `[propose-script]` for deterministic repeated work that should become a helper script.
- Expanded the skill-authoring rubric with command execution checks and script-worthy procedure
  detection, while clarifying trigger precision and skill-body voice rules.

### Fixed

- Standardized the local override filename as `CLAUDE.local.md` in `docreview` docs.

### Adoption Notes

- For new installs, follow the README quick start and preserve the target repo's existing project
  rules while wiring `AGENTS.md` and `.agents/skills` as symlinks.
- For updates to an existing install, compare this repo's shared kit files with the target repo:
  `scripts/docreview.py`, `.claude/skills/docreview/`, `.gitignore`, `.githooks/`, README guidance,
  root `CLAUDE.md` wiring guidance, and any wiring docs. Adopt relevant kit changes without
  overwriting project-specific `CLAUDE.md` content.
- To use the new pre-commit hook in an installed repo, copy `.githooks/pre-commit` and run
  `git config core.hooksPath .githooks` once per clone.
- After any install or update, run `python3 scripts/docreview.py` from the target repo and confirm it
  prints `docreview: PASS`.

## 2026-06-09

### Changed

- Migrated the mechanical wiring audit from `scripts/docreview.sh` to `scripts/docreview.py`
  (`7b20a84`).
- Updated README/bootstrap guidance and the `docreview` skill to call
  `python3 scripts/docreview.py`.

### Added

- Added recursive checks for scoped `CLAUDE.md` / `AGENTS.md` pairs.
- Added non-blank-line size budget checks: root `CLAUDE.md` <= 200 lines, scoped `CLAUDE.md` files
  <= 80 lines, and `.claude/rules/*.md` files <= 80 lines.
- Kept conflict backups for clobbered symlinks using `*.clobbered-<timestamp>` files.

### Removed

- Removed `scripts/docreview.sh`.

### Adoption Notes

- Replace old shell-script references with `python3 scripts/docreview.py`.
- If an installed repo has automation, hooks, README snippets, or skills that still call
  `scripts/docreview.sh`, update them to the Python command.
- Keep `AGENTS.md` as a symlink to `CLAUDE.md`, then run `python3 scripts/docreview.py` and confirm
  `docreview: PASS`.

## 2026-06-08

### Added

- Created the initial multi-agent starter kit (`9477f7d`):
  `CLAUDE.md` as the canonical rulebook, `AGENTS.md` as a symlink to it, README, MIT license,
  `.gitignore`, the `docreview` skill, doctrine references, and the original shell-based
  `docreview` script.
- Added the GitHub "Use this template" path and an agent paste prompt for adopting the kit into
  existing repos (`3ca72ac`).
- Added scoped `CLAUDE.md` doctrine: only create folder-level instruction files for real
  folder-specific foot-guns or when root instructions grow too large, and keep scoped files <= 80
  non-blank lines (`0adbf7d`, `1683657`).
- Added cross-agent skill sharing: `.claude/skills/` is canonical, and `.agents/skills` is a folder
  symlink to it for Codex and Antigravity (`28574ef`).

### Changed

- Retired the separate `GEMINI.md` topology and collapsed the repo to `CLAUDE.md` plus
  `AGENTS.md -> CLAUDE.md`, with Antigravity covered by `AGENTS.md` (`25e8ba6`).
- Reworked README into a fuller OSS-style guide with features, quick start, how it works, cloud
  sync notes, manual install, FAQ, and bootstrap prompt (`0adbf7d`).
- Made existing-repo adoption explicitly additive: agents should incorporate the wiring around a
  repo's own rules, not replace project conventions (`5ff397b`).
- Documented Claude Code support across CLI, desktop, web, and IDE surfaces (`bb7ad60`).
- Clarified scoped-rule precedence: the more deeply nested `CLAUDE.md` wins inside its subtree;
  root rules hold everywhere else (`1683657`).

### Fixed

- Fixed Codex naming consistency in docs and script output (`1d562a5`).
- Expanded clobber backup ignores from `AGENTS.md.clobbered-*` to `*.clobbered-*`, covering both
  rule-file and skill-mirror backups (`5794959`).
- Updated docs and `docreview` guidance so both symlinks are treated as first-class wiring:
  `AGENTS.md -> CLAUDE.md` and `.agents/skills -> .claude/skills` (`5794959`).
- Clarified that `.agents/skills` is a mirror symlink and should not be audited as a separate skill
  tree (`5794959`).

### Removed

- Removed `GEMINI.md` after the topology collapsed around `AGENTS.md` (`25e8ba6`).

### Adoption Notes

- Existing installs from the first commit should remove `GEMINI.md`, keep `CLAUDE.md` canonical, and
  use `AGENTS.md -> CLAUDE.md` for Codex and Antigravity.
- Ensure `.agents/skills` is a folder symlink to `.claude/skills`; do not copy skills into the mirror.
- Merge `.gitignore` changes so `*.clobbered-*` backups are ignored.
- Preserve existing project conventions when adopting the kit into an existing repo; consolidate
  them into `CLAUDE.md` before replacing old instruction files with symlinks.
