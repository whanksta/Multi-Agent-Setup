# Calibration fixture — do not edit

Frozen sample of the kind of markdown these budgets actually govern: prose, bullets, a wide table
row, inline code, and a fenced block. Its true token cost is recorded in `test_docreview.py`. Edit
this file and that test becomes a lie — add a new fixture instead.

## Conventions

- Secrets via environment variables only — never commit keys.
- Branch per task; open a PR for review; have a different agent review than the one that authored.
- Run `uv run pytest tests/unit/ -v` before every commit. **YOU MUST** fix a red test, never skip it.

| Axis | Catch | Threshold / verify |
|------|-------|--------------------|
| **C1 Size** | Bloat dilutes adherence | Cut anything learnable in one session (file locations, obvious commands); move occasional-reference material behind a pointer. Prefer exact, copy-pasteable commands over vague tool names. |

```sh
python3 scripts/docreview.py tokens
```

Scoped files point to root doctrine — they never restate it.
