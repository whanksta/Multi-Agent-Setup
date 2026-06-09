# <Project> — Agent Operating Rules

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
- Run `/docreview` (or `bash scripts/docreview.sh`) to verify/repair this wiring and audit the docs.

## Scoped CLAUDE.md files
- Start with just root `CLAUDE.md`. Add a scoped `CLAUDE.md` to a folder/subsystem **when it grows a
  convention or foot-gun not obvious from its code, or when root crosses ~200 lines** and a section
  is folder-specific. If you can't name the reason in one sentence, don't create the file.
- Scoped files **point to** root doctrine — never restate it. Keep each ≤ 80 non-blank lines.
- A must-hold-**everywhere** rule belongs in **root** `CLAUDE.md` — scoped files load only when that
  folder is touched and don't survive `/compact`.
- **On conflict, the more deeply-nested file wins for its subtree; root holds everywhere else.**
- Run `/docreview` after adding one.

## Conventions (example — replace with your own)
- Secrets via environment variables only — never commit keys.
- Branch per task; open a PR for review (cross-agent review encouraged).
- Keep `CLAUDE.md` under ~200 non-blank lines; push heavy content into `docs/` or a skill.
