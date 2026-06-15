---
name: codebase-audit
description: Run the bundled deterministic audit script to get a ranked, evidence-rich health digest of any git repo (decomposed size, git churn/hotspot/temporal-coupling, density) for an agent to judge. Use this whenever the user asks "what should I refactor", "is this file getting too big", "find the hotspots / god classes / tangled code", "what's coupled to what", "where do bugs accrue", "audit the codebase", "check modularity / structure / technical debt", or before a large refactor when you need to know where the mass and the churn actually are — even if they don't say the word "audit". Repo-agnostic and zero-config. It is signal-gathering, NOT a gate or a linter.
---

# codebase-audit — wide signal for a modularity judgment

This skill exists because of a division of labor: **the script does the wide,
cheap, quantitative gathering an agent can't do without reading every file and
running `git log` (which would burn the whole context window); the agent reads the
compact digest and makes the narrow judgment.** It is not a gate and emits no
verdicts — it says "here is where the mass, the change, and the coupling are, with
evidence," and *you* decide what (if anything) to do.

Why this beats eyeballing file sizes: raw LOC is the least informative number. A
790-line file that is 22 small types (a registry) is healthy; one where a single
function is 400 lines is not — same LOC, opposite verdict. The script decomposes
size so you can tell those apart, and adds the git-temporal signals (the half a
static linter is blind to) that actually predict where defects accrue. This is the
established behavioral-code-analysis method (CodeScene / Tornhill's *Code as a
Crime Scene*), not an invention: hotspot = size × churn; temporal coupling reveals
module boundaries the directory tree doesn't show.

**Repo-agnostic, zero-config.** Discovery is `git ls-files` (the version-controlled
working tree), languages are auto-detected (Swift, TS/JS, Python, Go, Rust, Java,
Kotlin, C/C++, C#, Ruby), and machine-generated files (`@generated` / "Generated
by" / "DO NOT EDIT" headers) are skipped automatically. Drop it into any git repo
and run it.

## Run it

```sh
python3 .claude/skills/codebase-audit/scripts/audit.py            # default: whole working tree, 90-day window
python3 .claude/skills/codebase-audit/scripts/audit.py --path src/api   # scope to a subtree (repeatable)
python3 .claude/skills/codebase-audit/scripts/audit.py --lang swift     # one language
python3 .claude/skills/codebase-audit/scripts/audit.py --since-days 30  # tighter churn window
python3 .claude/skills/codebase-audit/scripts/audit.py --top 25         # longer leaderboards
python3 .claude/skills/codebase-audit/scripts/audit.py --module-depth 3 # path segments that define a "module" for coupling
python3 .claude/skills/codebase-audit/scripts/audit.py --changed        # only files in the last commit, flagged if structural outliers (non-blocking heads-up)
python3 .claude/skills/codebase-audit/scripts/audit.py --staged         # like --changed but scoped to the staged diff (the pre-commit hook uses this)
python3 .claude/skills/codebase-audit/scripts/audit.py --json           # machine-readable, full per-file record
python3 .claude/skills/codebase-audit/scripts/audit.py --repo /path/to/other/repo
```

Stdlib + `git` only — no install. Defaults to the whole working tree; **scope with
`--path` when you already know where to look** (full coverage is the default so
nothing is silently missed).

## How to read the digest

**Coverage header** — files, LOC, git window, languages, roots, and anything skipped
(generated / oversized). Coverage is always shown so a partial scan never reads as
"covered everything."

**Distributions** (per language) — the percentile context for everything below.
Percentiles in the leaderboard are computed *within a language*, so Swift outliers
rank against Swift, Python against Python.

**Attention leaderboard** — sorted by `hotspot = LOC × churn` (the "look here
first" composite). Each column is signal, not score, so you see *why* a file ranks:

| column | meaning | how to read it |
|---|---|---|
| `LOC` / `LOC°` | non-blank lines / its within-language percentile | size, self-calibrated |
| `maxSym` | largest single symbol (type or function) + its non-blank span | the file's biggest indivisible chunk |
| `god%` | that symbol as a share of the file | high = one symbol dominates; low = many parts |
| `maxFn` | the **single biggest function/method** (measured at every nesting depth) | **the key tell: a 400-line method here = tangled even if god% looks like a normal class** |
| `decls` | count of types + functions (incl. nested methods) | many small decls = a registry/flat file; 1–2 = a blob |
| `c/l` | avg chars per non-blank line (density) | dense logic / data-packing vs. airy |
| `nest°` | max nesting-depth percentile | structural complexity (Tornhill's whitespace complexity) |
| `churn°` | commits-touching-file percentile (git window) | **where change concentrates → where bugs accrue** |
| `last` | days since last commit | hot vs. dormant |

The reading heuristic (also printed at the bottom of the report):
- **High `LOC°` + low `god%`, or small `maxFn` + many `decls`** → big but *flat*: a
  registry of small parts, usually fine. Don't split for a line count — that's
  Goodhart, trading real cohesion for a green number.
- **High `god%` *with a large `maxFn`*, or high `nest°`** → one symbol/function is
  eating the file: a genuine refactor candidate. (`maxFn` is what separates a
  tangled 700-line class with a 443-line method from a healthy class of 30 small ones.)
- **High `churn°`** → defect-prone surface; worth the most review attention.

Note: `maxFn` needs a function *keyword* or a `name(args) {` / `const f = () => {`
shape; C/C++ (and out-of-line definitions) get type-level sizing only, so their
`maxFn` may be blank — read `god%` + `nest°` there instead.

**God-symbol files** — the subset where one symbol *is* most of the file, ranked by
absolute symbol size, with each file's biggest function shown. The clearest "split
me" candidates.

**Temporal coupling** — files that change together (co-change ≥ 50%, support ≥ 4).
A `★` marks pairs that cross a module boundary (default: first 2 path segments;
tune with `--module-depth`) — a hidden coupling the directory structure hides, and a
candidate for a shared abstraction or a module split.

## What this is and isn't

- **Is:** a thinking aid. Read the digest, form a hypothesis ("this file is a
  96%-god 700-line class with p97 churn — split it"), then verify in the actual file.
- **Isn't a gate** — never block a commit on it; sizes are proxies and brace/indent
  spans are approximate (it says so in the header).
- **Isn't a diff reviewer** — it audits *structure* across the whole tree, not the
  correctness of a specific change.

When the digest surfaces a candidate, confirm by reading the file before acting —
the script points the flashlight; it doesn't pull the trigger.
