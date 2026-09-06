"""cli — doc-drift コマンドライン入口（読み取り専用・dry-run のみ）。

usage:
  doc-drift [ROOT]          # ROOT 内の Markdown を走査（既定: カレントディレクトリ）
  doc-drift . --json        # 機械可読出力
"""
import argparse
import json
import sys

from doc_drift import scanner

FINDING_MARK = {
    "missing": "❌ MISSING",
    "signature_drift": "⚠️ SIGNATURE DRIFT",
    "unparseable": "· UNPARSEABLE (informational)",
}


def render(report: dict, json_output: bool) -> str:
    if json_output:
        return json.dumps(report, ensure_ascii=False, indent=2)

    lines = [
        f"doc-drift — scanned {report['root']}",
        f"  markdown files: {report['files_scanned']} | python blocks checked: "
        f"{report['status_counts'].get('ok', 0) + sum(v for k, v in report['status_counts'].items() if k in ('missing', 'signature_drift', 'unparseable'))}",
        f"  blocks total: {report['blocks_total']} | by lang: {report['lang_counts']}",
        f"  repo symbols: {report['symbols']['functions']} functions, "
        f"{report['symbols']['classes']} classes "
        f"({report['symbols']['files_parsed']} files parsed, "
        f"{report['symbols']['files_unparseable']} unparseable)",
        "",
    ]
    if not report["findings"]:
        lines.append("no drift detected.")
    for f in report["findings"]:
        lines.append(f"{f['file']}:{f['line']}  {FINDING_MARK.get(f['status'], f['status'])}")
        lines.append(f"    {f['detail']}")
    lines.append("")
    lines.append(f"summary: {json.dumps(report['status_counts'], ensure_ascii=False)} "
                 f"| clean blocks: {report['ok_blocks']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="doc-drift",
        description="Detect drift between Markdown code examples and the actual codebase. Read-only.")
    ap.add_argument("root", nargs="?", default=".", help="repository root (default: .)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    report = scanner.scan(args.root)
    print(render(report, json_output=args.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
