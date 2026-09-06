"""scanner — リポジトリを走査して doc drift レポートを作る（オーケストレータ）。

読み取り専用。ファイルへの書き込みは一切行わない。
"""
from pathlib import Path

from doc_drift.markdown_blocks import PYTHON_LANGS, extract_blocks, find_markdown_files
from doc_drift.py_symbols import repo_symbol_table
from doc_drift.compare import classify_block

# README 例としてよく出るが Python ではない言語（判定対象外として数えるのみ）
NON_PYTHON_NOTE = "not python"


def scan(root, langs=None) -> dict:
    """root を走査し、doc drift レポート dict を返す。

    返り値: {root, files_scanned, blocks_total, lang_counts, status_counts,
             ok_blocks, findings: [{file, line, lang, status, detail, findings}]}
    """
    root = Path(root)
    langs = langs or PYTHON_LANGS
    md_files = find_markdown_files(root)
    table = repo_symbol_table(root)

    findings, lang_counts, status_counts = [], {}, {}
    ok_blocks = 0
    blocks_total = 0
    files_scanned = 0
    # レポート対象のステータス（no_symbols は「判定対象外」なので findings に入れない）
    REPORTABLE = ("signature_drift", "missing", "unparseable")

    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files_scanned += 1
        rel = md.relative_to(root).as_posix()
        for block in extract_blocks(text, source_path=rel):
            blocks_total += 1
            lang_counts[block["lang"]] = lang_counts.get(block["lang"], 0) + 1
            if block["lang"] not in langs:
                continue
            res = classify_block(block, table)
            status_counts[res["status"]] = status_counts.get(res["status"], 0) + 1
            if res["status"] == "ok":
                ok_blocks += 1
                continue
            if res["status"] in REPORTABLE:
                findings.append({
                    "file": block["file"],
                    "line": block["line"],
                    "lang": block["lang"],
                    "status": res["status"],
                    "detail": res["detail"],
                    "findings": res["findings"],
                })

    findings.sort(key=lambda f: (f["file"], f["line"]))
    return {
        "root": str(root),
        "files_scanned": files_scanned,
        "blocks_total": blocks_total,
        "lang_counts": lang_counts,
        "status_counts": status_counts,
        "ok_blocks": ok_blocks,
        "findings": findings,
        "symbols": {
            "functions": len(table["functions"]),
            "classes": len(table["classes"]),
            "files_parsed": table["files_parsed"],
            "files_unparseable": table["files_unparseable"],
        },
    }
