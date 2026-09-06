"""markdown_blocks — Markdown から fenced code block を抽出する（純関数）。

- ``` と ~~~ の両方に対応（開閉は同じフェンス文字で揃える必要がある）
- インデントされたフェンス（リスト内のコード例）も扱う
- 返り値の line はブロック開始フェンスの行番号（1-based）
- 閉じられていないブロックは不正な Markdown として無視する
"""
import re
from pathlib import Path

_FENCE_RE = re.compile(r"^\s{0,3}(?P<fence>`{3,}|~{3,})\s*(?P<lang>[A-Za-z0-9_+\-]*)\s*$")

PYTHON_LANGS = {"python", "py", "python3"}


def extract_blocks(md_text: str, source_path: str = "<text>") -> list:
    """Markdown テキストから fenced code block のリストを返す（純関数）。

    返り値: [{lang, code, file, line}]（出現順）
    """
    blocks = []
    open_fence = None   # 開いているフェンスの文字列（```+ or ~~~+）
    lang = None
    start = None
    buf = []

    for lineno, line in enumerate(md_text.splitlines(), 1):
        m = _FENCE_RE.match(line)
        if open_fence is None:
            if m:
                open_fence = m.group("fence")
                lang = m.group("lang").lower()
                start = lineno
                buf = []
        else:
            if m and line.lstrip().startswith(open_fence[0] * 3):
                blocks.append({
                    "lang": lang,
                    "code": "\n".join(buf),
                    "file": source_path,
                    "line": start,
                })
                open_fence = None
                lang = None
                start = None
                buf = []
            else:
                buf.append(line)
    return blocks


def find_markdown_files(root: Path, max_files: int = 2000) -> list:
    """リポジトリ内の Markdown ファイルを列挙（生成物ディレクトリは除外）。"""
    skip = {".git", ".venv", "venv", "node_modules", "__pycache__",
            "build", "dist", ".tox", ".mypy_cache", ".pytest_cache"}
    out = []
    for p in sorted(Path(root).rglob("*.md")):
        if any(part in skip for part in p.parts):
            continue
        out.append(p)
        if len(out) >= max_files:
            break
    return out
