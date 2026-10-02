# Working agreement for this repository

Short rules for anyone — human or agent — changing `doc-drift`.

## What this tool is

`doc-drift` scans the Markdown in a repository, extracts fenced Python blocks, and
checks whether the functions and classes they document still match the codebase
(signature drift, missing, unparseable). It is **read-only** and **deterministic**.

## Ground rules

- **Read-only.** The tool reports; it never edits the files it scans.
- **No network, no LLM.** A drift report must be reproducible offline.
- **Tests come with the change.** `python -m pytest -q` must pass, and each
  reported category (drift / missing / unparseable / ok) needs a fixture that
  triggers it.
- **No secrets in Git**, and no absolute paths in code, tests or docs — a clone
  must run anywhere.
- **Do not bypass the secret scan.** `git commit --no-verify` is never a fix for a
  gitleaks hit; rotate the credential and rewrite the commit.
- **The README is a promise.** Every documented command must work on a fresh
  clone, and a badge must point at CI rather than hardcode a test count.

## Checks that must pass

```
pip install -e ".[dev]"
python -m pytest -q
```
