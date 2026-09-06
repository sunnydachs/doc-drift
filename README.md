# doc-drift

**Detect drift between Markdown code examples and the actual codebase. Read-only, deterministic, no LLM.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-21%20passing-brightgreen.svg)](tests/)

`doc-drift` scans the Markdown files in a repository, extracts fenced Python code blocks, and checks whether the functions and classes defined in them still match the actual codebase:

- ⚠️ **SIGNATURE DRIFT** — the documented function exists, but its parameters diverge from the codebase
- ❌ **MISSING** — the documented function/class no longer exists anywhere in the repository (renamed or deleted?)
- · **UNPARSEABLE** — the block isn't valid Python (pseudo-code, placeholders) — informational
- ✅ **ok** — everything matches

Everything is **deterministic**: plain `ast` parsing and name/signature comparison. No LLM, no guessing — the same input always produces the same report. The tool is **read-only**: it never modifies your files.

## Status: practice/portfolio project — competition unverified

This tool was inspired by a recurring pain observed across dependency-heavy projects: documentation code examples drift out of sync with the code they illustrate, and nothing in CI catches it.

**Honest positioning**: this is a practice/portfolio project. The competition landscape for this idea has **not** been verified (evaluation was inconclusive due to search infrastructure issues), so no claim is made that this solves a validated market demand. It exists because the pain is real in projects I work with, and because building it was a useful exercise.

## How it works

1. Find Markdown files (`README.md`, `docs/**/*.md`, ...) — generated dirs are skipped
2. Extract fenced code blocks (``` and ~~~), tracking file + line number of each block
3. For blocks tagged `python`: collect function/class definitions via `ast`
4. Build a symbol table of the whole repository (also via `ast`)
5. Compare and classify:

| Block defines | Repository has | Status |
|---|---|---|
| `fetch(url)` | `fetch(url, retries=3)` | ✅ ok — optional args may be omitted in docs |
| `fetch(url, retries)` | `fetch(url, timeout=30)` | ⚠️ signature drift — arg names diverge |
| `fetch_all(url)` | *(nothing named fetch_all)* | ❌ missing — renamed or deleted? |
| *(not parseable as Python)* | — | · unparseable — informational |
| *(calls only, no definitions)* | — | ⏭️ not a finding |

Class examples are checked as subsets: documented methods must all exist on the actual class (docs frequently omit methods, so a subset is fine — an extra documented method that doesn't exist is drift).

Multi-dependency and optional-argument cases follow one conservative rule: docs may *omit*, but never *invent*.

## Install

```bash
pip install git+https://github.com/sunnydachs/doc-drift.git
```

## Usage

```bash
# scan the current repository (read-only)
doc-drift

# another repository, machine-readable output
doc-drift /path/to/repo --json
```

Example output:

```
doc-drift — scanned /home/dev/myproject
  markdown files: 42 | python blocks checked: 87
  blocks total: 310 | by lang: {'python': 121, 'bash': 60, ...}
README.md:153  ⚠️ SIGNATURE DRIFT
    block defines (url, retries) but repository defines (url, timeout)
summary: {"signature_drift": 3, "missing": 1, "unparseable": 5} | clean blocks: 41
```

## Known limitations

- **Illustrative examples are indistinguishable from documentation-of-code.** A top-level README that shows a hypothetical example (code that was never in the repo) is reported as `missing`/`signature_drift`. The tool works best on `docs/` trees whose examples mirror the codebase. Interpret top-level README findings with that in mind.
- **Python only** for now (blocks tagged `python`/`py`). Other languages are counted but not checked.
- **Grouped/summary code blocks** ("the API in one snippet") with pseudo-code escalate to `unparseable` — informational only, never drift.
- **Signature comparison is name-based**: default values and type annotations are ignored, and a block may omit optional parameters. It detects renames, removals, and arity/name changes — not semantic drift.
- Diffs beyond 500 Python files are not scanned (safety cap).
- Repos where documented code lives outside `.py` files (e.g., generated docs) are out of scope.

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests/ -q   # 21 tests, fully offline
```

Validated against a real, large open-source repository (1,692 Markdown files / 4,451 code blocks scanned): the scan surfaced a genuine documentation drift — a documented 2-argument function whose tested implementation had moved to 1 argument — alongside confirmed false positives that led to removing an over-eager directory exclusion from the default configuration.

## Provenance

This tool was inspired by a recurring pain observed across projects: documentation examples drifting from the code they illustrate. This repository is an independent, general-purpose implementation.

## License

[MIT](LICENSE)
