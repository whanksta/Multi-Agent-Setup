# Skill-authoring rubric — reviewing a SKILL.md

Load this only when `docreview` is asked to review a **skill** (a `.claude/skills/<name>/SKILL.md`
+ its bundled files), not when auditing CLAUDE.md/docs. Classify each finding **BLOCKER** /
**SHOULD** / **NIT**; cite `file:line`; name the axis.

| Axis | Catch | Threshold / rule |
|------|-------|------------------|
| **1 Frontmatter validity** | Malformed / illegal metadata | YAML parses; only `name` + `description` required (flag typo'd/unknown keys). `name`: ≤ 64 chars, `[a-z0-9-]` only, no XML tags, no reserved words (`anthropic`/`claude`), should match the dir name. `description`: non-empty, ≤ 1024 chars, no XML tags. **Name colliding with a built-in / sibling command = BLOCKER.** |
| **2 Trigger precision** | Skill won't fire (or over-fires) | The `description` is the ONLY thing loaded at startup for discovery. Third person; states BOTH *what it does* AND *when to use it*; names the literal words a user would type; front-loads triggers. Be slightly **pushy** (skills under-trigger) but never claim scope it lacks. The reverse too: a skill doing **more** than its description implies (file writes, network calls, side effects) = BLOCKER — no surprises. |
| **3 Body size budget** | Bloated SKILL.md | Body ≤ 500 lines (hard split signal). Domain skill ≤ ~2000 words; an orchestrator ≤ ~4000. **No single section > 25% of body.** Cut stock-phrase clusters + whitespace bloat. |
| **4 Progressive disclosure** | Poorly layered content | Extract a section once it passes ~40 lines or is scenario-specific; leave a one-line pointer. **One level deep only** — every reference links directly from SKILL.md (no forward-pointing chains). No orphan files. No extract-AND-inline (content lives in exactly one place). Reference files > 100 lines open with a contents list. |
| **5 Voice + person** | Wrong grammatical mode | `description` third person ("Reviews…", "Catches…"). Body **imperative** ("Run every axis", "Cite file:line"). Flag passive voice + pronoun ambiguity ("it"/"this" with no referent). Bare all-caps ALWAYS/NEVER with no stated *why* = SHOULD — a skill body is an instruction doc; explain the reason (terse `YOU MUST` belongs in contract files like CLAUDE.md, per C2). |
| **6 Resource references** | Dangling / dead links (bidirectional) | Forward: every link resolves — bundled file exists, code path exists (grep it), URL well-formed, sibling-skill name real. Backward: every bundled file is referenced by something (no dead weight). A pointer to a doctrine/file that doesn't exist = BLOCKER. |
| **7 Gotchas presence** | Missing trap-knowledge | A `Gotchas`/`Don't` section with ≥ 3 items, each a real anti-pattern — NOT the procedure restated as a warning. A `Self-check` exists; each item maps to a gotcha or axis. |
| **8 Beyond-defaults** | Re-documenting what the model already has | Delete: general knowledge (what JSON/SQL is); the harness/tool spec (how Read/Edit behave); **root CLAUDE.md doctrine** (already loaded — point to it); standard syntax. Keep only what's specific to THIS skill and not inferable. |
| **9 Cross-skill coherence** | Broken handoffs / trigger fights | Handoff targets resolve (named phase/skill exists). **No trigger overlap** — don't fight a sibling for the same request; define clear lanes. No name-drop without saying *when* to switch. |
| **10 Logical simplification** | Tangled / redundant structure — fixed catalog (a)–(l) | (a) duplicated rule; (b) inline + extracted; (c) dead section; (d) option soup (no default); (e) procedure-as-prose; (f) orphan/broken reference; (g) over-nesting (>1 level); (h) restated default; (i) buried trigger; (j) mixed concern; (k) conditional sprawl; (l) stale scaffold (boilerplate/TODO). Don't invent new letters mid-review. |
| **11 Commands run** | Broken verify/setup commands | Execute every inline + bundled command on the skill's home repo (or a safe dry-run) — don't just read it. A command that errors where the skill lives = BLOCKER. Watch shell portability: a failed zsh glob (`docs/*.md` with no `docs/`) aborts the whole command line. |
| **12 Script-worthy procedure** | Deterministic work left as prose | Multi-step deterministic/repeated work described in prose (every run would re-derive the same helper) → bundle as `scripts/<t>` + one calling line. Tag `[propose-script]` — surfaced, not silently authored. |

## Gotchas when reviewing skills

- **Root CLAUDE.md is always loaded — a skill *pointing* to it is correct, not a gap.** A skill
  that *duplicates* root doctrine fails axis 8; one that *points* passes.
- **Scoped CLAUDE.md does NOT survive `/compact`** — a must-always rule belongs in root, never
  only in a scoped file.
- **A real gotcha ≠ the procedure restated.** "Don't forget to run every axis" is just step 1.
- **`<!-- comments -->` are stripped from context** — fatal for a rule you expect acted on.
- **Verify, don't trust the doc about itself** — every count/path/claim checked against reality.
- **Trivial one-step asks don't consult skills at all** — judge axis 2 against substantive tasks;
  no description fixes that.
- **A mandated output format needs a copyable template** — prose descriptions of structure drift;
  an example block doesn't.
