@./CLAUDE.md

## Gemini & Antigravity — our setup (read once)
Shared rules import from **CLAUDE.md** (the canonical file). This section is only Gemini/Antigravity edges.

**Do**
- Treat `CLAUDE.md` as the single source of truth; open the **repo root** as your workspace so it loads.
- Make shared-rule changes in `CLAUDE.md`; keep Gemini/Antigravity-only notes here.
- After editing any instruction file, run `bash scripts/docreview.sh` to verify/repair the wiring.

**Don't**
- Don't write to `AGENTS.md` — it's a symlink to `CLAUDE.md`; writing there clobbers the link. Edit `CLAUDE.md`.
- Don't duplicate the shared rules here — they already load (import for Gemini CLI, `AGENTS.md` symlink for Antigravity).
