# MultiAgentSetup

A drop-in starter kit for repos worked on by **multiple AI coding agents** — Claude Code, Codex
CLI, Gemini CLI, and Antigravity. It keeps **one source of truth** for shared rules, **survives
cloud sync** (OneDrive / Google Drive / Dropbox), and **self-heals** when an agent's atomic-save
breaks the wiring. It also ships a `docreview` skill that audits your docs against a doc-quality
rubric.

Everything here is the deliverable — copy these files into your repo and you're set.

## What's in here

```
CLAUDE.md                              canonical rules — every agent reads this (edit per project)
AGENTS.md → CLAUDE.md                  symlink: Codex + Antigravity read the rules through it
GEMINI.md                              imports @./CLAUDE.md + Gemini/Antigravity edges only
.gitignore                             ignores CLAUDE.local.md + clobbered-symlink backups
scripts/docreview.sh                   verify + auto-repair the wiring (every agent + hooks/CI run this)
.claude/skills/docreview/
  SKILL.md                             the /docreview skill (Claude-only): wiring check + doc audit
  reference/doctrine.md                CLAUDE.md rubric, 9 audit axes, size budgets, fix-classes
  reference/skill-axes.md              rubric for reviewing SKILL.md files
```

## Why it works this way

**Claude Code is the primary agent, so `CLAUDE.md` is canonical** — it holds all shared rules.
Every other agent's file points back to it; they collaborate, they don't own the rulebook.

| Agent | Reads | `@import`? |
|-------|-------|------------|
| Claude Code (primary) | `CLAUDE.md` | yes |
| Codex CLI | `AGENTS.md` | no |
| Gemini CLI | `GEMINI.md` | yes |
| Antigravity | `AGENTS.md` | no |

Codex and Antigravity can't auto-`@import`, so `AGENTS.md` is a **symlink** to `CLAUDE.md` — they
read the canonical bytes directly. Gemini *can* import, so `GEMINI.md` imports `@./CLAUDE.md` and
adds only Gemini/Antigravity edges. Claude owns `CLAUDE.md` natively, with Claude-only rules in
`.claude/rules/`.

### Cloud sync + symlinks (the part people get wrong)
- OneDrive / Google Drive on macOS **preserve and sync symlinks** (verified) — the "OneDrive
  mangles symlinks" claim is false.
- Git stores symlinks portably (mode `120000`), so clones reconstruct them.
- **Windows:** symlinks need Developer Mode + `git config core.symlinks true`, else `AGENTS.md`
  checks out as a text file containing "CLAUDE.md". `docreview` repairs it.

### The one fragility → `docreview`
An **atomic save** (write-temp-then-rename) replaces the `AGENTS.md` symlink with a regular file,
and edits to `CLAUDE.md` stop propagating. `scripts/docreview.sh` detects it and re-links —
backing up any diverging content to `AGENTS.md.clobbered-<ts>` first, so nothing is lost.

`docreview` does two jobs: **(1) wiring** (the script) and **(2) a doc-doctrine audit** — size
budgets, scope placement, drift, broken links, and CLAUDE.md/SKILL.md authoring quality (see
`.claude/skills/docreview/reference/`).

**Rule of the road:** never write to `AGENTS.md`; edit `CLAUDE.md`; run `/docreview` (or
`bash scripts/docreview.sh`) after touching any instruction file.

## Adopt it in your repo

**Option A — copy the files** (then edit `CLAUDE.md` for your project):

```bash
SRC=path/to/MultiAgentSetup; DST=.
mkdir -p "$DST"/{scripts,.claude/skills}
cp "$SRC"/CLAUDE.md "$SRC"/GEMINI.md "$DST"/        # then replace CLAUDE.md's rules with yours
cp "$SRC"/scripts/docreview.sh "$DST"/scripts/
cp -r "$SRC"/.claude/skills/docreview "$DST"/.claude/skills/
cat "$SRC"/.gitignore >> "$DST"/.gitignore          # or merge by hand
ln -snf CLAUDE.md "$DST"/AGENTS.md
bash "$DST"/scripts/docreview.sh                    # expect: docreview: PASS
```

**Option B — paste the Bootstrap Prompt** below into Claude Code from inside your repo and let it
build the wiring (useful when the agent can't see this repo's files).

## Survives wipes

Keep this bundle in a **git repo** (cloud + a public/private GitHub remote). User-profile config
(`~/.claude/`) is **not** backed up or migrated and is exactly what a machine wipe erases — so the
durable, migratable unit is always the repo, never user-scope. To carry the setup forward, copy
from this repo into the new one (Option A) or paste the Bootstrap Prompt (Option B).

## Bootstrap Prompt

> Paste into Claude Code **from inside the target repo**.

```
Set up this repo for multi-agent instruction files, with Claude Code as the primary agent and
CLAUDE.md as the single canonical rulebook the other agents point at. Do all of the following:

1. CLAUDE.md (REAL, canonical): keep it if present; else create it with a short project
   description + a "Canonical instructions file" section stating CLAUDE.md is canonical (edited
   here), AGENTS.md is a symlink to it, GEMINI.md imports it + holds Gemini edges, .claude/rules/
   is Claude-only, never write to AGENTS.md, run /docreview after edits. If shared rules currently
   live in AGENTS.md / .cursorrules / elsewhere, consolidate them into CLAUDE.md first.
2. AGENTS.md: delete any existing file, then  ln -snf CLAUDE.md AGENTS.md
3. GEMINI.md (REAL): first line "@./CLAUDE.md", then a short Gemini/Antigravity edges section. Do
   NOT duplicate shared rules — they're imported.
4. scripts/docreview.sh: create the verify/auto-repair script that enforces this topology
   (CLAUDE.md real canonical; AGENTS.md symlink→CLAUDE.md, re-linking and backing up a clobbered
   diverging AGENTS.md to AGENTS.md.clobbered-<ts>; GEMINI.md real file importing @./CLAUDE.md; no
   circular @./AGENTS.md). chmod +x it.
5. .claude/skills/docreview/SKILL.md: a "docreview" skill that runs bash scripts/docreview.sh,
   reports the result, handles AGENTS.md.clobbered-* backups (summarize the diff, ask before
   folding in), and re-runs to confirm PASS.
6. .gitignore: add CLAUDE.local.md and AGENTS.md.clobbered-*.
7. Run bash scripts/docreview.sh, confirm "docreview: PASS", then summarize and remind me to edit
   shared rules only in CLAUDE.md.

Context: Codex CLI + Antigravity read AGENTS.md but can't auto-@import, which is why AGENTS.md is a
symlink (they read CLAUDE.md's bytes directly). Gemini CLI + Claude Code DO support @import. The
only fragility is an atomic-save turning the symlink into a regular file — docreview repairs that.
OneDrive/Google Drive on macOS preserve symlinks; git stores them mode 120000; Windows needs
Developer Mode + core.symlinks=true.
```

## License

MIT — do whatever; no warranty.
