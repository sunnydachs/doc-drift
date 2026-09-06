from doc_drift.compare import classify_block
from doc_drift.py_symbols import repo_symbol_table


def _table(tmp_path, files: dict):
    for name, src in files.items():
        (tmp_path / name).write_text(src)
    return repo_symbol_table(tmp_path)


def test_ok_when_signature_matches(tmp_path):
    table = _table(tmp_path, {"m.py": "def fetch(url, retries=3):\n    pass\n"})
    block = {"lang": "python", "code": "def fetch(url):\n    return url\n", "file": "r.md", "line": 1}
    r = classify_block(block, table)
    assert r["status"] == "ok"


def test_signature_drift_when_args_differ(tmp_path):
    table = _table(tmp_path, {"m.py": "def fetch(url, timeout=30):\n    pass\n"})
    block = {"lang": "python", "code": "def fetch(url, retries):\n    pass\n", "file": "r.md", "line": 1}
    r = classify_block(block, table)
    assert r["status"] == "signature_drift"
    assert "block defines (url, retries)" in r["detail"]


def test_missing_when_symbol_not_in_repo(tmp_path):
    table = _table(tmp_path, {"m.py": "def keep():\n    pass\n"})
    block = {"lang": "python", "code": "def fetch_all(url):\n    pass\n", "file": "r.md", "line": 1}
    r = classify_block(block, table)
    assert r["status"] == "missing"
    assert "renamed or deleted" in r["detail"]


def test_class_subset_is_ok_missing_method_is_drift(tmp_path):
    table = _table(tmp_path, {"m.py": "class Client:\n    def get(self):\n        pass\n\n    def post(self):\n        pass\n"})
    subset = {"lang": "python", "code": "class Client:\n    def get(self):\n        pass\n", "file": "r.md", "line": 1}
    assert classify_block(subset, table)["status"] == "ok"

    drifted = {"lang": "python",
               "code": "class Client:\n    def get(self):\n        pass\n\n    def put(self):\n        pass\n",
               "file": "r.md", "line": 1}
    r = classify_block(drifted, table)
    assert r["status"] == "signature_drift"
    assert "put" in r["detail"]


def test_unparseable_block():
    block = {"lang": "python", "code": "def broken(:\n", "file": "r.md", "line": 1}
    r = classify_block(block, {"functions": {}, "classes": {}})
    assert r["status"] == "unparseable"


def test_no_symbols_is_not_a_finding():
    block = {"lang": "python", "code": "import requests\nrequests.get('https://x')\n", "file": "r.md", "line": 1}
    r = classify_block(block, {"functions": {}, "classes": {}})
    assert r["status"] == "no_symbols"


def test_missing_wins_over_drift_in_priority(tmp_path):
    table = _table(tmp_path, {
        "m.py": "def keep(a):\n    pass\n",
    })
    block = {"lang": "python",
             "code": "def keep(b):\n    pass\n\ndef gone(a):\n    pass\n",
             "file": "r.md", "line": 1}
    r = classify_block(block, table)
    assert r["status"] == "missing"
