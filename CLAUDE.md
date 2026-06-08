# <Project> — Agent Operating Rules

> Starter template. Replace the **Conventions** section with your project's real rules. Keep the
> **Canonical instructions file** section — it's the multi-agent wiring this kit provides.
> Claude Code is the primary agent; `CLAUDE.md` is the canonical rulebook every agent reads.

## Canonical instructions file
- **`CLAUDE.md` is canonical — edit shared rules HERE.** Claude Code is the primary agent.
- `AGENTS.md` is a **symlink → `CLAUDE.md`** (Codex and Antigravity read the rules through it).
- `GEMINI.md` is a real file that imports `@./CLAUDE.md`, plus Gemini-specific notes below it.
- Claude-only rules live in `.claude/rules/`.
- **Never write to `AGENTS.md`** — it is a symlink; an atomic-save there clobbers the link. Always edit `CLAUDE.md`.
- Run `/docreview` (or `bash scripts/docreview.sh`) to verify/repair this wiring and audit the docs.

## Conventions (example — replace with your own)
- Secrets via environment variables only — never commit keys.
- Branch per task; open a PR for review (cross-agent review encouraged).
- Keep `CLAUDE.md` under ~200 non-blank lines; push heavy content into `docs/` or a skill.
