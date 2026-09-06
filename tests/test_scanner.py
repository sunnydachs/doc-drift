"""scanner / CLI の結合テスト（tmp リポジトリで完結・オフライン）。"""
import json

from doc_drift import scanner
from doc_drift.cli import main, render


def _make_repo(tmp_path):
    (tmp_path / "pkg.py").write_text(
        "def fetch(url, timeout=30):\n    pass\n\n\nclass Client:\n    def get(self):\n        pass\n"
    )
    (tmp_path / "README.md").write_text(
        "# Demo\n\n"
        "```python\n"                       # OK: 署名一致（デフォルト値は無視）
        "def fetch(url):\n    return url\n"
        "```\n\n"
        "```python\n"                       # drift: 引数名が違う
        "def fetch(url, retries):\n    return url\n"
        "```\n\n"
        "```python\n"                       # missing: 関数が存在しない
        "def fetch_all_and_save(url):\n    pass\n"
        "```\n\n"
        "```shell\n"                        # 対象外: python ではない
        "pip install requests\n"
        "```\n\n"
        "```python\n"                       # unparseable: 疑似コード
        "def <something>(...):\n    ...\n"
        "```\n"
    )


def test_scan_reports_expected_categories(tmp_path):
    _make_repo(tmp_path)
    report = scanner.scan(tmp_path)
    by_file = {}
    for f in report["findings"]:
        by_file.setdefault(f["status"], []).append(f)

    assert report["files_scanned"] == 1
    assert report["blocks_total"] == 5
    # OK 1 + findings 4（drift / missing / unparseable）
    assert report["ok_blocks"] == 1
    assert len(report["findings"]) == 3
    statuses = {f["status"] for f in report["findings"]}
    assert statuses == {"signature_drift", "missing", "unparseable"}
    # 対象外言語がカウントされている
    assert report["lang_counts"].get("shell") == 1
    # 行番号が正しい（フェンス開始行）
    lines = {f["line"]: f["status"] for f in report["findings"]}
    assert lines[8] == "signature_drift"     # ブロック開始フェンスの行
    assert lines[13] == "missing"
    assert lines[22] == "unparseable"


def test_scan_clean_repo_reports_no_drift(tmp_path):
    (tmp_path / "lib.py").write_text("def alpha(x):\n    pass\n")
    (tmp_path / "README.md").write_text(
        "```python\ndef alpha(x):\n    return x\n```\n"
        "```python\nimport os\nos.getcwd()\n```\n"
    )
    report = scanner.scan(tmp_path)
    assert report["findings"] == []
    assert report["status_counts"].get("ok") == 1
    assert report["status_counts"].get("no_symbols") == 1


def test_cli_main_json(tmp_path, capsys):
    _make_repo(tmp_path)
    rc = main([str(tmp_path), "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["files_scanned"] == 1
    assert len(data["findings"]) == 3


def test_render_text_contains_summary(tmp_path, capsys):
    _make_repo(tmp_path)
    main([str(tmp_path)])
    out = capsys.readouterr().out
    assert "SIGNATURE DRIFT" in out
    assert "MISSING" in out
    assert "summary:" in out
