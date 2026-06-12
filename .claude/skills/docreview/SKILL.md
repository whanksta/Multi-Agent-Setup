---
name: docreview
description: Verifies and repairs the multi-agent instruction-file wiring (CLAUDE.md canonical, AGENTS.md symlink → CLAUDE.md) AND audits the documentation surface against doc doctrine — size budgets, scope placement, staleness/drift, broken links, doctrine-vs-reality, and CLAUDE.md / SKILL.md authoring quality. Use to check or fix AGENTS.md/CLAUDE.md consistency, after any agent may have edited an instruction file, when the AGENTS.md symlink may have been clobbered, when a CLAUDE.md is bloated/stale/duplicative, or before committing changes to instruction files or skills. Triggers - /docreview, "check doc wiring", "audit docs", "review CLAUDE.md", "doc drift", "is this skill well written".
---

# docreview

Two jobs, run in order. **Part 1 (wiring)** is mechanical and always runs first; after any doctrine
fixes, run it again as the final check. **Part 2 (doctrine)** is a judgment audit — run it on
request, before committing instruction-file changes, or whenever a doc looks bloated/stale.

Choose one doctrine mode after Part 1:

- **Full doc review** — use when the user asks for a full / repo-wide / all-docs audit, before a
  release, or before committing documentation-system changes. Audit every repo-owned Markdown doc
  exactly once: `CLAUDE.md`, `CLAUDE.local.md` if present, scoped `*/CLAUDE.md`,
  `.claude/rules/*.md`, `.claude/skills/**/*.md`, top-level docs such as `README.md` /
  `CHANGELOG.md`, and anything under `docs/`.
- **Scoped doc review** — use when the user names a path, glob, skill, subsystem, or asks to review
  recent/touched docs. Audit only that target set plus any docs it directly links to or depends on
  for doctrine. State the chosen scope before inventorying it.

Exclude generated/dependency dirs and symlink mirrors in both modes. **Never audit `AGENTS.md` as
its own file — it's a symlink to `CLAUDE.md`. Never audit `.agents/skills` separately — it's a
mirror of `.claude/skills`.** If the user only asks for "just the wiring," run Part 1 and stop.

---

## Part 1 — Wiring check (mechanical, always)

1. Run the repo-level script from the root:
   ```bash
   python3 scripts/docreview.py
   ```
   It verifies + auto-repairs: `CLAUDE.md` is the real canonical file; `AGENTS.md` is a symlink →
   `CLAUDE.md` (re-links if missing/wrong); the skills mirror `.agents/skills` (Codex + Antigravity)
   is a folder symlink → `.claude/skills`; no circular `@./AGENTS.md` in `CLAUDE.md`. It also
   audits size budgets — non-blank counts + PASS/WITHIN-SLACK/OVER verdicts for root and scoped
   `CLAUDE.md` and `.claude/rules/` files.
2. Report which files were `ok`, `FIX`ed, or `WARN`ed.
3. If it saved an `AGENTS.md.clobbered-*` backup (an agent wrote diverging rules into the symlink),
   open that backup, summarize what differs from `CLAUDE.md`, and **ask** before folding changes in.
   Do not discard the backup without confirmation.
4. After any repair, re-run the script and confirm `docreview: PASS`.

> The script lives at **`scripts/docreview.py`, not inside this skill, on purpose**: the wiring is a
> *cross-agent* concern — Codex, Antigravity, and any pre-commit hook / CI all run
> `python3 scripts/docreview.py`. Burying it under `.claude/` would make shared infrastructure
> Claude-private. The skill is just a convenience entry point to it for whichever agent you're in
> (Claude natively; Codex & Antigravity through the `.agents/skills` symlink).

If the user only asked to "check the wiring," stop here.

---

## Part 2 — Doctrine audit (judgment)

Before starting, **read [`reference/doctrine.md`](reference/doctrine.md)** — the size budgets,
the C1–C10 CLAUDE.md rubric, the 10 audit axes (each with a verify command), the scope-discipline
principles, and the fix-class tags. When the target is a *skill* (a `SKILL.md`), also read
[`reference/skill-axes.md`](reference/skill-axes.md).

Procedure:

1. **Pick and state the mode.** Say whether this is a full doc review or scoped doc review and list
   the target set. If the user asked only for wiring, skip Part 2.
2. **Inventory.** List in-scope files with non-blank line counts vs budget. Print it first — a
   silent scope expansion is the most common failure mode. For always-loaded files, reuse the
   counts + verdicts the Part 1 script just printed (budget tiers: `reference/doctrine.md` →
   Size budgets). For full doc review, count every other in-scope Markdown doc (no ceiling) with:
   ```bash
   find . \
     \( -path './.git' -o -path './.agents' -o -path './node_modules' -o -path './.venv' -o -path './venv' -o -path './build' -o -path './dist' \) -prune -o \
     -name '*.md' ! -name 'AGENTS.md' -print | sort \
     | while read -r f; do printf "%-70s %s\n" "$f" "$(grep -cE '[^[:space:]]' "$f")"; done
   ```
   For scoped doc review, run the same count shape against the selected files only, then add direct
   dependency docs that the target relies on.
3. **Run every axis** from `reference/doctrine.md` against each in-scope Markdown file, using its
   verify command — don't eyeball. For `CLAUDE.md` also walk the C1–C10 rubric; for each
   `.claude/skills/*/SKILL.md`, also walk axes 1–12 in `reference/skill-axes.md`. Skill reference
   files are regular docs: run the doctrine axes, then verify their links from the owning skill.
   **Verify every claim against reality** (run the grep, `ls` the folder) — drift is the most
   common real defect, so claims like "X is wired", "N/N tests passing", or "module M exists" must
   be checked, not trusted.
4. **Emit findings** in the format below. Tag each with a fix-class.
5. **Confirm before editing.** Summarize which files change, how many lines, which axes drove it.
   Wait for go-ahead. (Any plan-mode rules in `.claude/rules/` still apply.)
6. **Apply** approved fixes; re-run axes 1 (Trim), 7 (Reachability), 8 (Doctrine-vs-reality) on
   touched files; if any always-loaded file is still OVER, surface it. Then re-run Part 1
   (`python3 scripts/docreview.py`) as the final mechanical check and confirm `docreview: PASS`.
7. **Commit** — the user runs it. Offer a draft message; never auto-commit or auto-push.

### Findings format

```
## docreview — findings

### Inventory
Mode: full doc review

| File | Non-blank | Budget | Verdict |
|------|-----------|--------|---------|
| CLAUDE.md | 56 | ≤200 | PASS |

### Findings
| Sev | Axis | File:line | Catch | Fix (class) |
|-----|------|-----------|-------|-------------|
| BLOCKER | C9 | CLAUDE.md:21 | API token in plain text | move to env var [one-line-tweak] |
| SHOULD  | 2  | docs/api.md:8 | restates a root CLAUDE.md rule | collapse to a pointer [trim] |

Verdict: N blockers, M should-fix, K nits — + the single highest-leverage change.
```

Clean axes: write `clean` or omit the row. Don't inflate nits.

### Scaling

At a handful of docs, audit inline. If the doc tree grows past ~15 files, fan out: one sub-agent
per cluster (root / scoped / docs), each reading `reference/doctrine.md` first and returning
ranked findings; then dedupe and apply. Keep live-state verification (axis 8 against any MCP/API)
to a single agent so the audit stays reproducible.

---

## Gotchas

- **`AGENTS.md` is the symlink — audit `CLAUDE.md`, not it.** Part 1 checks the link; Part 2 reads
  through it.
- **`.agents/skills/` is a symlink to `.claude/skills/` — audit each skill once under
  `.claude/skills/`, never via the mirror,** or you double-count the same `SKILL.md`.
- **CLAUDE.md's size budget pays off 3×.** It's the always-loaded file for all three agents — Claude
  natively, Codex and Antigravity via the symlink — so a trim there is a trim for everyone.
- **Verify, don't trust the doc about itself.** "N/N passing", a path that "exists", "X is wired" —
  each is a claim to check, not a fact.
- **Descriptive vs aspirational (axis 8).** If the doc describes reality and reality disagrees, fix
  the doc. If it states an intent, tag `ASPIRATIONAL` and ask — the gap may be a real bug.
- **The skill is a wrapper, not the owner of the script.** Don't move `scripts/docreview.py` into
  this skill folder; it must stay runnable by every agent and any hook/CI.

## Self-check before reporting

- Ran Part 1 and confirmed `PASS` (or surfaced the clobbered backup)?
- Stated `full doc review` or `scoped doc review` and listed the target set?
- Printed the inventory + per-file verdict before auditing?
- Audited every in-scope Markdown doc exactly once, excluding `AGENTS.md` and `.agents/skills`?
- Ran every axis with its verify command — not from memory?
- Every finding cites `file:line`, names its axis, carries a fix-class, has a severity?
- Verified every count/path/claim I flagged (or relied on) against reality?
- Did NOT flag `AGENTS.md` as a separate file, and did NOT propose moving the script into the skill?
- Blockers separated from nits; nothing inflated?

## What this skill does NOT do

- **Edit code.** Doc/instruction files only. Code mismatches found via axis 8 are reported, not fixed.
- **Auto-commit or auto-push.** Produces a draft message; the user commits.
- **Author hooks or scripts.** Prose that should be a hook or bundled script is tagged
  `[propose-hook]` / `[propose-script]` and surfaced to the user.
- **Benchmark or A/B-test skills.** The skill audit is static review plus running the skill's own
  commands (axis 11); empirical eval loops are development workflow, not audit.
- **Re-architect docs.** Trim, tighten, fix conflicts/drift — not "rewrite the architecture doc."
