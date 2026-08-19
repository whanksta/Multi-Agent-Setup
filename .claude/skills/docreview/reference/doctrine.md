# Doc doctrine — how instruction files & docs should be built

The rubric `docreview` audits against. Load when running the **doctrine audit** (Part 2 of the
skill).

Contents:
- [Loading model](#loading-model) — what's always loaded vs on-demand vs referenced
- [Size budgets](#size-budgets) — token ceilings + verdict scale
- [CLAUDE.md authoring rubric (C1–C11)](#claudemd-authoring-rubric-c1c11)
- [The 10 audit axes](#the-10-audit-axes) — catch + verify recipe for each
- [Scope discipline](#scope-discipline) — OR5, OR8, subtraction-first
- [Fix-classes](#fix-classes) — how a finding routes to an edit

---

## Loading model

Everything rests on *when a doc enters the context window*:

- **Always-loaded.** The root instruction file loads at launch **and re-injects after
  `/compact`** — the only guaranteed-present layer. That file is `CLAUDE.md`; via the
  `AGENTS.md` symlink it's *also* what Codex and Antigravity load, so every token is paid per
  turn by **three** agents. Budget hard.
- **Scoped / on-demand.** A `*/CLAUDE.md` or `.claude/rules/` file loads only when an agent
  touches that folder and **does NOT survive `/compact`**. A must-hold-everywhere rule living
  only in a scoped file is silently missed — a BLOCKER (C6).
- **Referenced-not-loaded.** `README.md`, `CHANGELOG.md`, `docs/*.md`, and skill reference files
  cost nothing until opened. No ceiling, but still flag genuine bloat.

Consequences: **CLAUDE.md is a contract surface, not a content surface** — contracts + pointers
live there, heavy content in referenced docs or lazy-loaded skills. And **guidance is not
enforcement** — a must-always-hold guarantee needs a hook or CI, not a sentence.

## Size budgets

Budget **estimated tokens that load** — never lines. Lines are a broken proxy: one long table
row counts as 1, so a ~6,600-token file could report PASS. This kit's `skill-axes.md` is ~30
non-blank lines and ~2,200 tokens; a single wide row costs ~270.

```sh
python3 scripts/docreview.py tokens              # every doc in scope
python3 scripts/docreview.py tokens CLAUDE.md    # named files
```

Two rules keep the estimate honest: **measure only what loads** — block-level HTML comments are
excluded everywhere, YAML frontmatter everywhere except a `SKILL.md` (whose `name`/`description`
do load via the skill listing); comments inside code fences are kept — and
**`CHARS_PER_TOKEN = 2.5`**, measured across this kit's docs (range 2.42–2.58; the familiar
"~3.5" predates current tokenizers and understates dense markdown by ~40%).

Budget tiers (always-loaded files only):

| Tier | File | Budget (est. tokens) |
|------|------|----------------------|
| Root | `CLAUDE.md` | ≤ 2,500 |
| Umbrella / subject | a subtree's top `CLAUDE.md` | ≤ 1,800 |
| Module / scoped | a folder-level `CLAUDE.md`, a `.claude/rules/` file | ≤ 1,000 |

These sit **below** Anthropic's published "under 200 lines" deliberately: 200 lines at this
density is ~6,800 tokens, current frontier models need less scaffolding than that figure assumes
(C11), and every root token is paid **three times**. Line counts print advisory-only — never
gate on them.

Verdict scale per always-loaded file: **PASS** at/under budget · **WITHIN-SLACK** over but
< 1.5×, soft flag for next pass · **OVER** ≥ 1.5×, hard flag — the finding must propose which
sections move where and est. tokens saved.

## CLAUDE.md authoring rubric (C1–C11)

Classify each finding **BLOCKER** (breaks loading/correctness) / **SHOULD** (degrades adherence) /
**NIT** (polish). Cite `file:line`, name the axis.

| Axis | Catch | Threshold / verify |
|------|-------|--------------------|
| **C1 Size** | Bloat dilutes adherence — uniformly, across every rule | ≤ 2,500 est. tokens (root), checked with `docreview.py tokens`, never by eye. Cut anything learnable in one session (file locations, obvious commands); move occasional-reference material behind a pointer. |
| **C2 Specificity + imperative** | Vague / observational rules | Concrete + verifiable, not aspirational. Direct commands ("never X") not observations ("we generally don't"). Exact, copy-pasteable commands (`uv run pytest tests/unit/ -v`) over vague tool names ("run the tests"). Mark load-bearing rules `IMPORTANT`/`YOU MUST`. Include negative rules, not only positive. |
| **C3 Beyond-inference** | Restating what code or a linter already says | Keep only what's NOT derivable from reading the repo and NOT already known to the model. Delete restated signatures, directory trees, architecture overviews, dependency lists, and generic best practices ("write tests") — plus rules a linter/formatter/pre-commit hook already enforces, the most common real-world smell. |
| **C4 No contradiction** | Conflicting guidance across layers | Cross-check every loaded layer: root ↔ scoped ↔ `CLAUDE.local.md` ↔ `~/.claude/CLAUDE.md` (global; audit only for conflicts) ↔ auto-memory. Precedence: the more deeply-nested file wins within its subtree; root holds everywhere else — a scoped rule *refining* root is a valid override. Flag same-scope disagreements and rules contradicting verified behavior. |
| **C5 Structure** | Rules buried in prose | Headers + bullets, scannable. Split dense multi-claim paragraphs; one idea per bullet. |
| **C6 Scope placement** | Rule in the wrong layer | Hold-**everywhere** → root — an always-rule living only in a scoped file is a **BLOCKER**. Folder-only rule bloating root is a SHOULD-fix. |
| **C7 Freshness / no drift** | Stale counts, dates, paths | Verify every count/claim against reality (run the test, grep the source, `ls` the folder). Relative dates made absolute ("as of 2026-06-08", not "recently"). Flag paths/modules that no longer exist. |
| **C8 Right mechanism** | Rule parked in the wrong tool | Multi-step or subtree-only → a **skill** or path-scoped rule (`.claude/rules/` with `paths:`). "Run before every commit / after every edit" → a **hook**, not prose. |
| **C9 No secrets** | Leaked credentials | No passwords / tokens / connection strings / PII — **BLOCKER**. Secrets → env vars only. |
| **C10 Imports + pointers** | Broken, expensive, or blind references | `@path` imports must resolve, be needed, and not pull in huge files (imports load in full at launch). "See X.md" pointers must resolve **and** say when/why to read the file — a bare path gets ignored. `<!-- comments -->` are stripped from context: never load-bearing, never budgeted. |
| **C11 Obsolete safeguards** | Rules written to defend against weaker models | Frontier models self-verify; in 2026 Anthropic cut **>80% of Claude Code's own system prompt** for its newest models with no measured eval loss. **Delete:** "verify your work" / "double-check before responding" / "re-read the file after editing" (they cause *over*-verification), severity filters that muzzle a review, and any rule freezing one answer to a question the model now judges per-situation. **Keep:** repo-specific gotchas, rationale, conventions differing from tool defaults. |

## The 10 audit axes

Run every axis against each in-scope doc. Recipe paths are examples — substitute the audited
inventory for the current full or scoped run.

**1 — Trim.** Bloat; walls of text that should be tables; rationale dumps where a pointer would
do; budget violations on always-loaded files (`docreview.py tokens`). Judge by tokens, not
line count.
**2 — Tighten.** Restatement of parent doctrine in a child doc (OR5); scope creep; imprecise
wording; forensic/transient detail (one-off output, state snapshots) in the doctrine body.
Judgment axis — open the linked doc and compare.
**3 — Conflict.** Cross-doc contradictions (same fact stated two ways) + internal ones.
`grep -rnE --include='*.md' "<term-A>|<term-B>" CLAUDE.md docs/` — resolve by authority: the
topic-owning doc wins, rewrite the loser.
**4 — Consistency.** Terminology / tag / naming / casing / date-format drift. One canonical
form, then `grep -rnE "(Variant1|Variant2)" .` and re-sweep until zero stragglers.
**5 — Staleness + volatility.** *Stale* = facts that rotted (counts changed, items renamed,
"as of" dates aged, resolved items still open, scaffolding never customized).
*Volatile* = facts that WILL rot and don't belong in always-loaded doctrine (dates, versions,
owners, "currently X").
`grep -rnE "as of [0-9]{4}-[0-9]{2}-[0-9]{2}|currently|recently" CLAUDE.md docs/` — stale →
update/remove; volatile → move to git history / CHANGELOG, leave a stable rule.
**6 — Placement.** Right info, wrong scope: module-only rule at root, project-wide rule
restated in a scoped file, pointer-only heading. Push doctrine to the narrowest scope it
applies to; pull genuinely-broad content up.
**7 — Reachability.** Broken file links, dead anchors, unexpanded acronyms. Extract with
`grep -rhoE --include='*.md' "\]\([^)]+\.md[^)]*\)" CLAUDE.md docs/ | sort -u`, check each
resolves, confirm anchors have a matching `## Heading`, expand acronyms once as
`Full Name (TLA)`.
**8 — Doctrine-vs-reality.** A claim ("X is wired", "we use Y", "no Z", "N/N passing",
"module M exists") is a claim to test, not trust: run the grep/`ls`/test that proves or
disproves it. Documented commands are claims too — run each (its `--help`/dry-run form if
destructive). Descriptive-but-wrong → the doc lied, fix the doc. Aspirational → tag
`ASPIRATIONAL` and ask — never silently rewrite doctrine to match reality.
**9 — Lazy-load-eligibility.** A contiguous block of heavy content (deep spec, long table,
worked example, code block ≥ 20 lines) worth ≥ ~40 lines or ~1,200 tokens in an always-loaded
file → move to a skill reference or `docs/<topic>.md`, leaving a ≤ 5-line pointer that says
*when* to load it. Not for short gotchas, axiom one-liners, or every-turn content.
**10 — Completeness.** The inverse of Trim: the operational contract a fresh session needs —
install/build/test/lint commands (copy-paste ready), required env vars, non-obvious gotchas.
Probe only where the project warrants. Missing-but-needed = SHOULD; never licenses directory
listings or generic advice (C3 still deletes those).

## Scope discipline

- **OR5 — right-sized scope.** A child doc *points to* parent doctrine, never restates it.
  Operational test: restating ≥ 3 consecutive sentences from a linked doc is a violation —
  collapse to one sentence + a pointer. The single most common real defect.
- **OR8 — minimal-but-correct.** Every token in an always-loaded doc must justify its per-turn
  cost: pointer over restatement, table over prose, row over narrative. Don't trim for its own
  sake or add speculatively — content earns its place by stating a rule future agents need at
  this scope.
- **Subtraction is the default edit (C11).** The burden of proof sits on the line that stays,
  not the line that goes. A rule written to prevent a specific failure freezes one answer to a
  question the model now answers better by reading the situation.
- **Scoped files earn their place.** A folder-scoped `CLAUDE.md` must capture a foot-gun
  invisible from filenames or hold a folder-specific section split out of an over-budget root.
  No one-sentence reason → no file.

## Fix-classes

Tag each finding so the apply step knows the edit it implies:

- `[delete]` — remove, no replacement.
- `[trim]` — compress a block to fewer lines (the routine axis-1 fix).
- `[one-line-tweak]` — single-line precision fix (casing, date, tag, acronym first-use).
- `[propagate-down]` — move to a narrower scope; the canonical OR5 fix.
- `[propagate-up]` — move to a broader scope.
- `[propagate-to-skill]` / `[propagate-to-docs]` — axis-9 heavy content → its lazy-loaded home;
  leave a pointer.
- `[cross-doc-edit]` — the fix touches 2+ files; edit together.
- `[propose-hook]` — must-happen prose → surfaced hook proposal (which event, what guard);
  **not applied as a doc edit**.
- `[propose-script]` — deterministic repeated prose → surfaced `scripts/` helper proposal;
  **not applied**.

---

Audit each file once through its canonical path: `AGENTS.md` and `.agents/skills/` are symlinks,
so auditing `CLAUDE.md` and `.claude/skills/` already covers them. Part 1 of the skill confirms
both links; its Gotchas carry the operational detail.
