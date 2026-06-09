# Doc doctrine — how instruction files & docs should be built

The rubric `docreview` audits against. Distilled from doc-review skills across several repos and
generalized. Load this when running the **doctrine audit** (Part 2 of the skill).

Contents:
- [Loading model](#loading-model) — what's always loaded vs on-demand vs referenced
- [Size budgets](#size-budgets) — the non-blank-line ceilings + verdict scale
- [CLAUDE.md authoring rubric (C1–C10)](#claudemd-authoring-rubric-c1c10)
- [The 9 audit axes](#the-9-audit-axes) — catch + verify command for each
- [Scope-discipline principles](#scope-discipline-principles)
- [Fix-classes](#fix-classes) — how a finding routes to an edit
- [Multi-agent specifics](#multi-agent-specifics) — the wiring this kit uses

---

## Loading model

The whole doctrine rests on *when* a doc enters the context window:

- **Always-loaded.** The root instruction file loads in full at launch **and re-injects after
  `/compact`**. It's the only guaranteed-present layer. That file is `CLAUDE.md` — and via the
  `AGENTS.md` symlink it's *also* what Codex and Antigravity load. So every line in `CLAUDE.md`
  is paid per turn by **three** agents. Budget hard.
- **Scoped / on-demand.** A `*/CLAUDE.md` (or `.claude/rules/` file) loads only when an agent
  touches that folder, and **does NOT survive `/compact`**. A rule that must hold *everywhere*
  but lives only in a scoped file will be silently missed — that's a BLOCKER (axis 6 / C6).
- **Referenced-not-loaded.** `docs/*.md`, reference files like this one — cost nothing until
  something opens them. No hard size ceiling, but still flag genuine bloat.

Three consequences:
- **CLAUDE.md is a contract surface, not a content surface.** Contracts + pointers live there;
  heavy content lives in referenced docs or lazy-loaded skills.
- **Pointers beat restatement.** A child doc points to parent doctrine; it never restates it.
- **Guidance, not enforcement.** A must-always-hold guarantee needs a hook or CI, not a sentence.

---

## Size budgets

Count **non-blank lines only** — blank lines are one newline token each, aid readability, and
don't eat the budget:

```sh
grep -cE '[^[:space:]]' <file>     # canonical non-blank line count
```

**Anthropic-2026 budget tiers** (always-loaded files only):

| Tier | File | Budget (non-blank lines) |
|------|------|--------------------------|
| Root | `CLAUDE.md` | ≤ 200 |
| Umbrella / subject | a subtree's top `CLAUDE.md` | ≤ 150 |
| Module / scoped | a folder-level `CLAUDE.md`, a `.claude/rules/` file | ≤ 80 |

**Verdict scale** per always-loaded file:
- **PASS** — at or under budget.
- **WITHIN-SLACK** — over budget but < 1.5×. Soft flag; note for next pass.
- **OVER** — ≥ 1.5× budget. Hard flag; the finding must propose a concrete trim target (which
  sections move where, est. lines saved).

Referenced-not-loaded docs have **no ceiling** but are still subject to genuine-bloat flagging
(a 60-line table where 15 rows do; prose where structured rows belong).

---

## CLAUDE.md authoring rubric (C1–C10)

Classify each finding **BLOCKER** (breaks loading/correctness) / **SHOULD** (degrades adherence)
/ **NIT** (polish). Cite `file:line`, name the axis.

| Axis | Catch | Threshold / verify |
|------|-------|--------------------|
| **C1 Size** | Bloat dilutes adherence | < 200 non-blank lines (root). Cut anything learnable in one session (file locations, obvious commands); move occasional-reference material behind a pointer. |
| **C2 Specificity + imperative** | Vague / observational rules | Concrete + verifiable, not aspirational. Direct commands ("never X") not observations ("we generally don't"). **Prefer exact, copy-pasteable commands (`uv run pytest tests/unit/ -v`) over vague tool names ("run the tests").** Mark load-bearing rules `IMPORTANT`/`YOU MUST`. Include **negative** rules, not only positive. |
| **C3 Beyond-inference** | Restating what code already says | Keep only what's NOT derivable from reading code (conventions, "why we rejected X", domain decodes, non-obvious gotchas). Delete restated signatures / directory listings. |
| **C4 No contradiction** | Conflicting guidance across layers | Cross-check root ↔ scoped ↔ auto-memory. **Precedence: the more deeply-nested file wins within its subtree; root holds everywhere else** — a scoped rule *refining* root is a valid override, not a defect. Flag true conflicts: two layers disagreeing at the *same* scope, a scoped rule contradicting a meant-to-be-universal root rule, a rule contradicting verified code/behavior, or a stale survivor of a reversed instruction. |
| **C5 Structure** | Rules buried in prose | Headers + bullets, scannable. Split dense multi-claim paragraphs; one idea per bullet. |
| **C6 Scope placement** | Rule in the wrong layer | A hold-**everywhere** rule belongs in **root** (scoped files may not load / don't survive `/compact`) — an always-rule living only in a scoped file is a **BLOCKER**. A folder-only rule bloating root is a SHOULD-fix. |
| **C7 Freshness / no drift** | Stale counts, dates, paths | Verify every count/claim against reality (run the test, grep the source, `ls` the folder). Make relative dates absolute ("as of 2026-06-08", not "recently"). Flag paths/modules that no longer exist. |
| **C8 Right mechanism** | Rule parked in the wrong tool | Multi-step or subtree-only → a **skill** or path-scoped rule (`.claude/rules/` with `paths:`). "Run before every commit / after every edit" → a **hook**, not prose. |
| **C9 No secrets** | Leaked credentials | No passwords / tokens / connection strings / PII in any instruction file — a **BLOCKER**. The risk compounds if the repo syncs to cloud storage or is public. Secrets → env vars only. |
| **C10 Imports + pointers** | Broken / expensive references | `@path` imports must resolve, be needed, and not pull in huge files (imports load in full at launch). "See X.md" pointers must resolve. `<!-- comments -->` are stripped from context — never put a load-bearing rule in one. |

---

## The 9 audit axes

Run every axis against each in-scope doc. Each has a one-line catch and a verify recipe.

**1 — Trim.** Bloat; walls of text that should be tables; rationale dumps where a pointer would do.
Size-budget violations on always-loaded files.
```sh
for f in CLAUDE.md .claude/rules/*.md; do printf "%-32s %s\n" "$f" "$(grep -cE '[^[:space:]]' "$f" 2>/dev/null)"; done
```

**2 — Tighten.** Restatement of parent doctrine in a child doc; scope creep; imprecise wording;
forensic/transient detail (one-off command output, state snapshots) sitting in the doctrine body.
Judgment axis — open the linked doc and compare.

**3 — Conflict.** Cross-doc contradictions (same fact stated two ways) + internal contradictions.
```sh
grep -nE "<term-A>|<term-B>" CLAUDE.md docs/*.md
```
Resolve by authority: the doc that owns the topic wins; rewrite the loser.

**4 — Consistency.** Terminology / tag / naming / casing / date-format drift. One canonical form;
sweep for stragglers.
```sh
grep -rnE "(Variant1|Variant2)" .   # then pick canonical, re-sweep to confirm zero stragglers
```

**5 — Staleness + volatility.** *Stale* = facts that rotted (counts changed, items renamed/moved,
"as of <date>" aged, resolved items still listed open). *Volatile* = facts that WILL rot and
shouldn't be in always-loaded doctrine at all (dates, versions, owners, "currently using X").
```sh
grep -rnE "as of [0-9]{4}-[0-9]{2}-[0-9]{2}|currently|recently" CLAUDE.md docs/
```
Stale → update/remove. Volatile → move to git history / CHANGELOG / a live-state doc + leave a stable rule.

**6 — Placement.** Right info, wrong scope: module-only rule at root, project-wide rule restated in
a scoped file, pointer-only scoped file. Push doctrine to the narrowest scope it applies to; pull
genuinely-broad content up. Collapse pointer-only headings.

**7 — Reachability.** Broken file links, dead anchors, unexpanded acronyms.
```sh
grep -hoE "\]\([^)]+\.md[^)]*\)" CLAUDE.md docs/*.md \
  | sed -E 's/^\]\(//; s/\)$//' | sort -u \
  | while read l; do f="${l%%#*}"; [ -z "$f" ] || [ -e "$f" ] || echo "MISSING: $l"; done
```
Anchors: confirm a matching `## Heading` exists. Acronyms: expand once as `Full Name (TLA)`.

**8 — Doctrine-vs-reality.** A claim ("X is wired", "we use Y", "no Z", "module M exists") not
backed by the repo. **Verify, don't trust.** For each load-bearing claim, run the grep/ls that
proves or disproves it.
```sh
grep -rn "<forbidden-pattern>" .      # "Z is never used" → must return nothing
ls <dir>/ 2>/dev/null                  # "module M exists" / "no code yet" → check
```
Discipline: if doctrine is *descriptive* but reality disagrees, the **doc lied — fix the doc**.
If it's *aspirational*, tag `ASPIRATIONAL` and ask the user — the gap may be a real bug; never
silently rewrite the doc to match reality.

**9 — Lazy-load-eligibility.** ≥ 40 contiguous lines of heavy content (deep spec, long table,
worked example, code block ≥ 20 lines) in an always-loaded file → move to a skill reference or a
`docs/<topic>.md`, leaving a ≤ 5-line pointer that says *when* to load it.
```sh
awk '/^## /{if(last)print last_l,last; last=$0; last_l=0; next}{last_l++}END{if(last)print last_l,last}' CLAUDE.md | sort -rn | head
```
Do NOT apply to short gotchas, axiom one-liners, or anything needed every turn.

---

## Scope-discipline principles

- **OR5 — right-sized scope.** A child doc *points to* parent doctrine, never restates it.
  Operational test: restating ≥ 3 consecutive sentences from a linked doc is a violation —
  collapse to one sentence + a pointer. This is the single most common real defect.
- **OR8 — minimal-but-correct.** Every line in an always-loaded doc must justify its per-turn
  token cost. Prefer a pointer over a restatement, a table over prose, a row over narrative.
  Don't trim for its own sake and don't add speculatively — content earns its place when it
  states a rule future agents need at this scope.
- **Contract surface, not content surface.** Always-loaded files hold contracts + pointers; heavy
  content lives in lazy-loaded skills or referenced docs.
- **Stale vs volatile split.** Stale → fix against live source. Volatile → relocate out of doctrine.
- **Verify, don't trust the doc about itself.** Every count / path / test-result / claim is checked
  against reality before it's believed.
- **Scoped files earn their place.** A folder-scoped `CLAUDE.md` exists to capture a foot-gun
  invisible from filenames, or to hold a folder-specific section split out of an over-budget root.
  If you can't state its reason in one sentence, the file shouldn't exist.

---

## Fix-classes

Tag each finding so the apply step knows what edit it implies:

- `[delete]` — remove a section/entry, no replacement (resolved item whose stale entry lingers).
- `[trim]` — compress a block to fewer lines (the routine axis-1 fix).
- `[propagate-down]` — move content to a narrower scope (root → scoped). The canonical OR5 fix.
- `[propagate-up]` — move content to a broader scope because it applies wider than where it sits.
- `[propagate-to-skill]` — axis-9 heavy content → a lazy-loaded `.claude/skills/<t>/SKILL.md`; leave a pointer.
- `[propagate-to-docs]` — axis-9 heavy content → a referenced `docs/<t>.md`; leave a pointer.
- `[cross-doc-edit]` — fix touches 2+ files (reconciling a conflict / a cascading rename) — edit together.
- `[one-line-tweak]` — single-line precision fix (casing, date format, tag, acronym first-use).
- `[propose-hook]` — advisory prose describing must-happen behavior that should be a deterministic
  hook. **NOT applied as a doc edit.** Surface to the user with the proposed hook (which event,
  what guard) — never silently deferred.

---

## Multi-agent specifics

The wiring this kit uses changes how a few axes apply:

- **`AGENTS.md` is a symlink to `CLAUDE.md`** — never audit it as a separate file; auditing
  `CLAUDE.md` covers it. (The wiring check in Part 1 confirms the link itself.)
- **`.agents/skills/` is a symlink to `.claude/skills/`** — Codex/Antigravity read skills through it;
  audit each skill once under `.claude/skills/`, never via the mirror. Part 1 confirms the link.
- **CLAUDE.md's budget matters 3×.** It's the always-loaded file for Claude *and* (via the symlink)
  Codex and Antigravity. Trim wins here pay off three times.
- **Secrets compound on sync/public repos (C9).** A leaked credential in any instruction file is a
  BLOCKER — more so if the repo syncs to cloud storage or is published.
