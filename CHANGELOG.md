# Changelog

This file is for agents as much as humans. When a user pastes the repo link into an agent later,
the agent should read this file to understand what changed and what the target repo should adopt.

This repo uses the GitHub repo link as the delivery channel, so dated sections represent update
batches available once committed. A batch that changes budget tiers, `CHARS_PER_TOKEN`, or the
umbrella/scoped classification rule must say so in its Adoption Notes — those changes silently
move adopters' files between budgets.

**Which batches apply to you:** exactly those dated after your marker — `.claude/.mas-version`,
or root `VERSION` on template-button adoptions. If the marker equals the newest batch above,
you are current: report "up to date" and apply nothing. Never re-apply batches at or before
your marker.

Historical entries were reconstructed from Git history through `7b20a84`.

## 2026-09-07

Stress-test feedback from updating an adopted repo ~2 months / 3 batches behind HEAD (~430
markdown docs, `.githooks` active, concurrent agent sessions in the tree). What held up:
`.mas-version` stamping, changelog-as-delivery-channel, the `tokens` subcommand, symlink
wiring checks. This batch closes the gaps that didn't.

### Added

- **`docreview.py debt` subcommand.** WITHIN-SLACK verdicts printed on every run with no memory
  between runs — "soft flag for next pass" produced nothing for the next pass to read. `debt`
  lists every WITHIN-SLACK and OVER file with its tokens/budget ratio, for CI or humans.
  Report-only, always exits 0 (the `check` command remains the gate). `check` and `debt` now
  share one budget-target discovery (`iter_budget_targets`), so they can never disagree about
  scope.
- **`.docreview-ignore` — local ignore customization.** Adopters needing extra ignored
  directories (generated-output folders, worktree checkouts) had to patch `docreview.py`
  itself; the next byte-exact copy silently destroyed the patch. All three walkers now merge
  directory names from a `.docreview-ignore` file at the scope root (one per line, `#`
  comments — full-line or trailing — and blanks skipped; gitignore-style trailing slashes and a
  leading BOM are normalized; path-shaped entries warn and are skipped; an unreadable file
  warns and keeps built-ins only; loaded once per run). Customization no longer forks kit
  bytes.
- **Doctrine: dated-truth carve-out (axis 5).** Dated records — changelog batches, append-only
  ledgers, completed plans — are correct as of their date, not stale. Staleness fires only when
  the framing claims currency (an undated "current"/"live" header) or a superseded record is
  still presented as current; supersession gets an explicit "Superseded YYYY-MM-DD" note.
- **Doctrine: Archive trees mode.** Large dated work-product trees (completed plans, task
  artifacts, generated reports) get a different audit: freshness is the wrong axis — for an
  archive, correctness means honest deadness. Procedure: read the tree's index/convention docs
  fully, spot-check bodies, sweep inbound links, verify generators still exist. Canonical fix
  is a one-line status banner ("Archived YYYY-MM" + "Superseded YYYY-MM-DD by X" when
  superseded); `[delete]` only when superseded AND unreferenced AND misleading.
  The skill's mode list gains a matching third mode (archive-tree review).
- **Doctrine: `[owner-call]` fix-class.** Real findings that must NOT be edited — deletions
  needing human judgment (tracked/regenerable data), evidence-grade do-not-rewrite files, files
  owned by a concurrent session. Reported with evidence, never applied.
- **Skill: coverage attestation.** The findings format gains a Coverage section — per file-set,
  state read-fully / sampled (+ strategy) / parity-checked / verified-by-grep-only. Sampling is
  fine; silent sampling reads as full coverage, and at fan-out scale the difference matters.
- **Skill: paste-ready auditor preamble + count-based fan-out.** Fresh-context audit subagents
  load no `CLAUDE.md`, so every dispatcher reinvented the restated-rules block — with real
  mistakes (auditing `AGENTS.md` mirrors, trusting stale worktree checkouts). The Scaling
  section now ships the preamble (canonical paths only, skip mirrors, fixed inventory,
  verify-don't-trust, findings format, anti-abort line) and sizes clusters by file count
  (~50–60 docs per auditor) instead of the fixed root/scoped/docs triple. Vendor guidance backs
  the fan-out pattern: "Separate, fresh-context verifier subagents tend to outperform
  self-critique" (Anthropic, verified 2026-09-07). It also adds concurrent-writer guidance:
  apply agents stage explicit pathspecs — foreign staged files are another session's
  work-in-progress, never `git add -A`.
- **Doctrine: C11 migration trigger + reasoning-extraction sweep.** When the consuming model
  generation changes, re-run the doctrine audit with a "too prescriptive?" lens — collapse
  enumerated-behavior rules into brief steering, delete rules restating the new model's
  defaults — and sweep for show-your-thinking / echo-your-reasoning directives, which current
  models can refuse outright. Evidence (verified against the live doc, 2026-09-07): Anthropic's
  Fable 5 prompting guide — "Skills developed for prior models are often too prescriptive for
  Claude Fable 5 and can degrade output quality"; instructions to "echo, transcribe, or explain
  its internal reasoning" can trigger the `reasoning_extraction` refusal category;
  and "avoid surfacing explicit context-budget counts where possible."

### Changed

- **Doctrine no longer inlines its own measurements.** The "~31 non-blank lines / ~2,200
  tokens" self-measurements rotted once already (refreshed 2026-08-19 after rotting inside
  2026-08-03). The Size budgets section now cites the `docreview.py tokens` commands instead
  of printing numbers that decay between releases, and notes the script's constants are the
  authoritative tier source.
- **"Versioned facts point, never restate" (OR5 extension).** OR5 caught verbatim prose
  restatement (≥3 consecutive sentences) but not paraphrased numbers. Adopting repos restating
  kit-owned budget figures/tiers/constants inside their own rulebooks see those paraphrases rot
  on the next kit update. Root `CLAUDE.md` self-applies the rule: the tier numbers became a
  pointer to the docreview gate plus the re-deriving command.
- **Budget arithmetic stays out of model-facing instruction files (doctrine, one line).**
  Runtime context-budget counts (tokens remaining, budget arithmetic) belong in human- and
  CI-facing reports, never pasted into instruction files the model itself reads. File-size
  ceilings are authoring rules, not runtime accounting, and stay.
- **Adoption flow hardened (README prompt).** The update path now covers the transition state
  where a budget-tightening release makes the newly copied script FAIL before any conformance
  edits exist (finish the conformance edits first; land kit update + conformance as adjacent
  commits, or one `--no-verify` commit for the regime change itself). It carries an anti-abort
  line — ample context remaining; do not stop, summarize, or suggest a new session mid-flow —
  since Fable-class agents can otherwise end a multi-hour adoption campaign silently. OpenAI's
  2026 Astra guidance warns of the sibling failure — agents stopping mid-work to ask
  clarifying questions; its counter is "complete the work that is already authorized from
  context." And it tells previously-patched adopters to diff kit-owned files against the clone
  before copying, re-apply patches, and record them.
- **Adoption prompt decides the situation mechanically (README step 2).** The agent no longer
  infers whether an update applies: it runs a four-line marker comparison (`.claude/.mas-version`,
  falling back to root `VERSION`, vs the newest CHANGELOG batch heading) and acts on exactly one
  of three outcomes — UP TO DATE reports "already on <version>, nothing to apply" and skips the
  install steps entirely; FRESH installs (an existing `docreview.py` with no marker is an
  unstamped old install, treated as fresh); UPDATE applies precisely the batches dated after the
  marker, oldest first. The CHANGELOG header now states the same applicability rule for agents
  that open this file first.
- **Changelog convention:** any batch that changes budget tiers, `CHARS_PER_TOKEN`, or the
  umbrella/scoped classification rule must say so in its Adoption Notes (stated in the header
  prose above).

### Fixed

- **`docreview.py` now enforces exact filename case (silent-pass fix).** Every `CLAUDE.md`/
  `AGENTS.md` membership test compares real directory entries instead of OS path lookups:
  on case-insensitive filesystems (macOS, Windows default) a lookup for `CLAUDE.md` folds case
  and finds `claude.md`, so the gate could print `docreview: PASS` on wiring that no
  case-sensitive agent ever reads — Claude Code and Codex match the literal names, and the
  AGENTS.md spec says outright: "The name is case-sensitive — agents look for exactly this
  filename" (verified 2026-09-07). `check` now FAILs wrong-case variants with a rename
  instruction before performing any repair, and `missing` reports them ("wrong case; no agent
  reads it"). The `missing` all-clear now reads "correctly-cased".

### Adoption Notes

- Replace `scripts/docreview.py` and `.claude/skills/docreview/` (SKILL.md +
  reference/doctrine.md); re-blend root `CLAUDE.md` — the budget tier numbers became a pointer
  to the docreview gate, so drop your copies of the figures too. `.githooks/pre-commit` is
  unchanged this batch.
- **No budget tier, `CHARS_PER_TOKEN`, or umbrella/scoped classification change in this
  batch** — your files' verdicts move only if their content did.
- If you patched `scripts/docreview.py` to ignore extra directories, revert to the kit copy
  and list those directory names in `.docreview-ignore` instead — that is what it is for.
- README changes are source-side guidance for future installs and updates; installed repos
  have no kit README and can skip them.

## 2026-08-21

### Fixed

- **`docreview.py` no longer passes silently on a nonexistent `--scope path` root.** It now exits 2
  with "scope path is not an existing directory", matching the other scope errors. Previously
  `missing --scope path --path <nonexistent>` walked nothing and printed "every directory in scope
  has CLAUDE.md and AGENTS.md" with exit 0 — a check that measured nothing while looking like a
  pass. A relative `--path` resolved from the wrong working directory hit the same hole, and a path
  pointing at a regular file did too. `check` on a bad scope path now also exits 2 with the scope
  error instead of exit 1's misleading "CLAUDE.md (canonical) is missing".
- **`docreview.py` fails loudly on unreadable docs and directories** (same failure class, found in
  a pre-public audit): an unreadable `CLAUDE.md`/rules file used to measure 0 tokens and PASS the
  budget check; an unreadable directory used to be skipped by `os.walk` while `missing` still
  claimed "every directory in scope". Now `check` exits 1 with "budget/wiring UNCHECKED" lines,
  `missing` prints "coverage there is UNKNOWN" instead of the all-clear, and `tokens` marks the
  gap and exits 1.
- **`docreview.py` budget math hardened:** an unclosed `<!--` comment no longer zeroes the rest of
  the file (malformed markdown is charged, not dropped); a fence line with trailing text no longer
  closes a code block (CommonMark closers are bare); the circular-import guard now catches
  `@AGENTS.md`, `@/AGENTS.md`, indented, and list-item forms, not just `@./AGENTS.md`;
  `--scope worktree` with no git binary on PATH exits 2 with a message instead of a traceback; a
  missing or symlinked `.claude/skills` prints a WARN instead of silently skipping the mirror
  check.
- **`audit.py` honesty fixes:** non-ASCII filenames are no longer silently dropped (git's default
  path quoting corrupted them; now `core.quotePath=off` for `ls-files` and both diff commands);
  unreadable files are counted and surfaced in the report's Skipped line and `--json` meta;
  `--path src` no longer also matches `srcx/` (prefix match now requires a boundary); `--changed`
  on an unborn HEAD (or when git fails) says "could not read the diff" instead of "0 source
  file(s) changed — all within normal ranges".
- **Windows pre-commit support:** added `.gitattributes` (the hook must check out with LF — Git
  for Windows defaults to CRLF, which kills the shebang), and the hook now resolves
  `python3`/`python`/`py` instead of hardcoding `python3` (python.org Windows installs expose
  `python`/`py` only).
- The adoption prompt's verification step (README step 6) now says to run the target repo's own
  `scripts/docreview.py` from the target root. Running the `/tmp/mas` clone's copy audits the kit
  itself and exits 0 regardless of the target's wiring — the first output line names the audited
  root, but the exit code alone certified nothing.

### Changed

- **Adoption flow gaps closed (README):** the update path now has a documented fallback when
  `.claude/.mas-version` is missing but root `VERSION` exists (template-button adoptions); the
  no-git zip fallback now warns that zip extraction stores symlinks as plain text files (never
  copy `AGENTS.md`/`.agents/skills` from a zip source) and that the wrapper folder name follows
  the ref; the PRE-CONSOLIDATE step now scopes "remove the redundant copies" to agent-instruction
  files only — never human-facing docs; step 3 no longer lists `VERSION` under "replicate exactly"
  (step 5's `.claude/.mas-version` stamp is its only action); the Adoption File Policy gains a
  `tests/` row (source-repo regression suite, not for adoption); the gitignore entry list in step 3
  is now explicit.
- **README corrections:** the CLAUDE.local.md FAQ no longer claims auto-discovery is deprecated
  (the live Claude Code docs present it as current; the `@` import is now the fallback, not the
  requirement); display name unified as "Multi-Agent-Setup"; a garbled sentence in Two Pillars
  fixed; `.githooks/pre-commit` added to the What You Get table; the template quick-start says
  what to do with inherited `tests/`/`README`/`CHANGELOG`/`LICENSE`.
- `CLAUDE.md` title now names the real repo instead of the `# <Project>` placeholder (the
  template guidance block is unchanged); `doctrine.md`'s self-measurements refreshed (31
  non-blank lines; widest row ~230 est. tokens); the `docreview` SKILL.md list/comment separation
  fixed; `.gitignore` now ignores `.claude/settings.local.json` (Claude Code local permissions).

### Adoption Notes

- Replace `scripts/docreview.py`, `.claude/skills/codebase-audit/scripts/audit.py`,
  `.githooks/pre-commit`, and `.claude/skills/docreview/` (SKILL.md + reference/doctrine.md), and
  add the new `.gitattributes`. Re-blend root `CLAUDE.md` (title change only). Append the
  `.claude/settings.local.json` line to your `.gitignore`.
- The README changes are source-side guidance for future installs and updates; installed repos
  have no kit README and can skip them.

## 2026-08-19

### Changed

- **A bare `/docreview` now means a full doc review.** The doctrine audit was opt-in-ish and
  every automatic path (script, pre-commit hook) runs only wiring + token budgets, so in practice
  docreview degraded to a context-limit check. Part 2 of the skill is now the default; it is
  skipped only when the user explicitly says "wiring only". The skill's `description` frontmatter
  states the default so it is visible at discovery time, when only the description loads.
- CLAUDE.md and README no longer present `python3 scripts/docreview.py` as equivalent to
  `/docreview`: the script is the mechanical half (wiring + budgets); the doctrine audit is the
  skill's judgment pass. README's `docreview` section and Daily Workflow say so explicitly.
- **Trimmed `doctrine.md` ~20% (6,342 → ~5,000 est. tokens)** against current published
  practice — Anthropic's July 2026 cut of >80% of Claude Code's system prompt ("smarter models
  need less direction"), an arXiv study of 100 real AGENTS.md/CLAUDE.md files, and HumanLayer's
  CLAUDE.md guide. No rule was dropped: all 11 C-axes, 10 audit axes, OR5/OR8, and all 10
  fix-classes remain. What changed:
  - Generalized volatile model references ("Opus 5") to "current frontier models" with one dated
    evidence cite — the principle is durable, the model name wasn't.
  - Sharpened three axes with research findings: C1 notes bloat degrades adherence *uniformly*;
    C3 names lint/formatter restatement as the most common real-world smell (62% of files in the
    arXiv sample); C10 requires pointers to say when/why, not just resolve (blind references get
    ignored).
  - Moved measurement provenance (tokenizer experiments, per-tier line estimates) out of the
    doctrine body — the operative rules stay, the history lives in this changelog.
  - Folded "Multi-agent specifics" into a closing line (it restated the skill's Gotchas — its
    own OR5 rule) and dropped redundant verify commands for axes that share one.

### Fixed

- Refreshed `doctrine.md`'s self-measurements, which had rotted inside the 2026-08-03 batch:
  `skill-axes.md` measures ~31 non-blank lines / ~2,200 est. tokens (was "30 / ~2,100"), and
  doctrine.md's widest table row costs ~270 tokens (was "~330").
- README's Python floor is now per-script: `docreview.py` requires 3.7+ (verified — it uses
  `from __future__ import annotations` and no 3.8+ syntax), while `codebase-audit` requires 3.8+
  (assignment expressions). The bare "Requires Python 3.7+" sat where readers could take it for
  the whole kit.
- README's local-instructions FAQ now notes Claude Code deprecated `CLAUDE.local.md`
  auto-discovery in favor of `@` imports — add `@./CLAUDE.local.md` to `CLAUDE.md`.
  (Superseded 2026-08-21: the live docs present auto-discovery as current; the FAQ now
  recommends the `@` import only as a fallback.)

### Adoption Notes

- Replace `scripts/docreview.py`, `.claude/skills/docreview/SKILL.md`, and
  `.claude/skills/docreview/reference/doctrine.md`; re-blend root `CLAUDE.md` — the
  "Generalized volatile model references" wording change applies to `CLAUDE.md` too, not only
  `doctrine.md`.
- The README bullets above are source-repo-only; installed repos have no kit README and can
  skip them.

## 2026-08-03

### Changed

- **Size budgets are now measured in estimated tokens, not non-blank lines.** Line counting was
  blind to line width: one long table row counted as 1, so a ~6,600-token file could report PASS.
  This kit's own `skill-axes.md` is 30 non-blank lines and ~2,100 tokens. Line counts are still
  printed, but only as an advisory readout.
- New budget tiers for always-loaded files: root `CLAUDE.md` <= 2,500 est. tokens, umbrella /
  subject `CLAUDE.md` <= 1,800, scoped `CLAUDE.md` and `.claude/rules/*.md` <= 1,000. These sit
  below the "under 200 lines" figure Anthropic publishes because 200 lines of dense markdown is
  ~6,400 tokens, Opus 5 needs less scaffolding, and this kit pays every root token three times
  (Claude, Codex, Antigravity).
- `docreview.py` now distinguishes an **umbrella** `CLAUDE.md` (one that tops a subtree containing
  further scoped files) from a leaf scoped file, and gives it the wider budget.
- Skill-authoring axis 3 (body size budget) switched from lines/words to estimated tokens: a domain
  skill <= ~5,000, an orchestrator <= ~10,000.
- Trimmed `doctrine.md` by 6.8% (6,803 -> 6,341 est. tokens) by applying its own OR5 rule to itself:
  "CLAUDE.md's budget matters 3x" was stated three times, "Multi-agent specifics" largely restated
  the skill's own Gotchas, and C3/C11 both owned "delete restated directory trees". No rule was
  dropped - all 11 C-axes, 10 audit axes, and 10 fix-classes remain.
- Added doctrine axis **C11 (obsolete safeguards)**: delete instructions written to defend against
  weaker models — "verify your work", "double-check before responding", review severity filters,
  and restated architecture / dependency lists / directory trees. Opus 5 self-verifies, and
  Anthropic cut >80% of Claude Code's own system prompt for these models with no eval loss.

### Added

- `python3 scripts/docreview.py tokens [paths...]` reports the estimated context cost of each doc.
  Replaces the `grep -cE` inventory one-liner in the `docreview` skill.
- Token estimation excludes content that never reaches the context window: block-level HTML comments
  everywhere, and YAML frontmatter everywhere except `SKILL.md` (a skill's `name`/`description` do
  load, via the always-present skill listing). Comments inside code fences are kept. Verified
  empirically — 7,200 chars inside `<!-- -->` cost 0 tokens vs 2,101 uncommented, and a 10,100-char
  frontmatter block cost nothing beyond run-to-run noise.
- `CHARS_PER_TOKEN = 2.5`, measured against this kit's own docs (range 2.42-2.58) via input-token
  deltas between otherwise-identical `claude -p` runs. The familiar "~3.5 chars per token" predates
  the Claude 4.7+ tokenizer and understates dense markdown by ~40%. Accuracy against measured truth:
  within ~1-5% on full-length docs, and ~10% high on short prose-heavy samples. It errs high, which
  is the safe direction for a gate.

### Fixed

- `.claude/rules/` files are now discovered recursively, matching Claude Code's documented
  behavior. Previously a rule in `.claude/rules/backend/testing.md` was never budget-checked.
- README no longer claims YAML frontmatter is excluded unconditionally; it states the `SKILL.md`
  exception, matching what the script reports (axis 8 drift).
- README's Gemini CLI note moved to past tense — the June 18, 2026 cutover date has passed.
- The manual-install `.gitignore` step is now idempotent. It appended the whole file, so re-running
  an install duplicated every entry; it now adds only missing lines, matching the Adoption File
  Policy's "preserve unrelated target entries". Verified: three consecutive runs, no duplicates.

## 2026-06-16

### Fixed

- Changed `scripts/docreview.py` default `--scope auto` to target the project that owns the script,
  independent of the caller's current working directory, so copied standalone installs repair their
  own `AGENTS.md` symlink.
- Kept `--scope worktree` as the explicit current-Git-worktree mode.
- Made `docreview.py` verify that `AGENTS.md` reads the same bytes as `CLAUDE.md` and that
  `.agents/skills` resolves to a real directory, so unusable links cannot report PASS.
- Updated README and `codebase-audit` docs to describe no-Git source zip installs and the audit
  script's filesystem fallback without Git history.
- Added regression coverage for invoking a copied `docreview.py` from another Git worktree and for
  unusable symlink targets.

## 2026-06-15

### Added

- Added `python3 scripts/docreview.py missing` to report folders missing `CLAUDE.md` and/or
  `AGENTS.md` without repairing or requiring scoped files.
- Added scope selection for the missing-file report: default current Git worktree, explicit source
  repo via `--scope repo`, or custom path via `--scope path --path ...`.
- Added `.claude/skills/codebase-audit/`, a repo-agnostic structural audit skill and stdlib Python
  script for size, churn, hotspot, and temporal-coupling signals. This explicitly expands the kit
  beyond instruction wiring with an advisory code-audit tool.
- Added stdlib `unittest` coverage for `codebase-audit` JSON output, generated-file skipping,
  staged advisory mode, and temporal coupling.
- Updated `.githooks/pre-commit` to run `codebase-audit --staged` as a non-blocking advisory after
  `docreview` passes.
- Updated the `docreview` skill and README with missing-file inventory guidance.
- Added a `VERSION` file and an adopted-version marker (`.claude/.mas-version`) so the update flow
  has a concrete baseline to diff the changelog against.

### Changed

- Rewrote the README adoption flow around an explicit **clone-first** step
  (`git clone --depth 1 … /tmp/mas`) so agents replicate exact bytes instead of retyping scripts
  from a web page, with a `raw.githubusercontent.com` fallback for agents that cannot run `git`.
- Collapsed the four overlapping paste-prompts (Start here / Existing Repo / Existing Install /
  Bootstrap) into a single decision-routed adoption prompt that detects fresh vs. has-other-files
  vs. update and adapts.
- Promoted the Adoption File Policy table directly under the prompt and reframed `codebase-audit` as
  a core pillar (with a "Two Pillars" section) rather than an advisory afterthought.

### Adoption Notes

- Replace `scripts/docreview.py`, `.claude/skills/docreview/`, `.claude/skills/codebase-audit/`,
  and `.githooks/pre-commit` from this source repo to adopt the new missing-file report and staged
  structural-audit advisory.
- Copy `VERSION` into the target as `.claude/.mas-version` so later updates know the baseline.

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
- Clarified that source `README.md` and `CHANGELOG.md` are guidance-only during adoption; agents
  should read them but not copy or overwrite target repo docs unless explicitly asked.
- Added an adoption file policy table that tells agents which files to read only, copy exactly,
  merge carefully, update additively, or create as symlinks.
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
