# Multi-Agent-Setup — Agent Operating Rules

> Starter template. Replace the **Conventions** section with your project's real rules. Keep the
> **Canonical instructions file** section — it's the multi-agent wiring this kit provides.
> Claude Code is the primary agent; `CLAUDE.md` is the canonical rulebook every agent reads.

## Canonical instructions file
- **`CLAUDE.md` is canonical — edit shared rules HERE.** Claude Code is the primary agent.
- `AGENTS.md` is a **symlink → `CLAUDE.md`** — Codex and Antigravity read the rules through it.
- **Skills are canonical in `.claude/skills/`** — Codex & Antigravity read them via `.agents/skills`
  (a folder symlink). Author/edit skills there, never through the mirror; `docreview` maintains it.
- Claude-only rules live in `.claude/rules/`.
- **Never write to `AGENTS.md`** — it is a symlink; an atomic-save there clobbers the link. Always edit `CLAUDE.md`.
- Run `/docreview` to verify/repair this wiring **and audit the docs against doctrine**. The bare
  script (`python3 scripts/docreview.py`) is only the mechanical half — wiring + token budgets;
  the doctrine audit is the skill's judgment pass, not the script's.
- A pre-commit hook runs the script automatically — enable once per clone: `git config core.hooksPath .githooks`.

## Scoped CLAUDE.md files
- Start with just root `CLAUDE.md`. Add a scoped `CLAUDE.md` to a folder/subsystem **when it grows a
  convention or foot-gun not obvious from its code, or when root crosses its token budget** and a
  section is folder-specific. If you can't name the reason in one sentence, don't create the file.
- Scoped files **point to** root doctrine — never restate it, numbers included: figures owned
  elsewhere (budgets, tiers, constants) get a pointer plus the command that re-derives them.
- Keep root and scoped files inside the docreview budget tiers — `python3 scripts/docreview.py`
  gates them (tiers explained in `.claude/skills/docreview/reference/doctrine.md`). Push heavy
  content into `docs/` or a skill. **Budget tokens, not lines** — a wide table row can cost 300+
  on its own. Check with `python3 scripts/docreview.py tokens`.
- Prefer deleting to adding. Current frontier models self-verify and read context — rules like
  "double-check your work", restated directory trees, and dependency lists cost adherence
  without buying anything.
- A must-hold-**everywhere** rule belongs in **root** `CLAUDE.md` — scoped files load only when that
  folder is touched and don't survive `/compact`.
- **On conflict, the more deeply-nested file wins for its subtree; root holds everywhere else.**
- Run `/docreview` after adding one.

## Conventions (example — replace with your own)
- Secrets via environment variables only — never commit keys.
- Branch per task; open a PR for review; have a different agent review than the one that authored.
