import ast

from doc_drift.py_symbols import collect_symbols, repo_symbol_table


def test_collect_function_and_class():
    src = '''
def fetch(url, timeout=30):
    pass

class Client:
    def get(self, path):
        pass

    def post(self, path, data):
        pass
'''
    s = collect_symbols(src)
    assert s["unparseable"] is False
    assert s["functions"]["fetch"] == {"args": ["url", "timeout"], "required": 1}
    assert s["classes"]["Client"] == ["get", "post"]  # 変更なし


def test_collect_async_and_decorators():
    src = '''
@decorator
async def send(payload):
    pass
'''
    s = collect_symbols(src)
    assert s["functions"]["send"] == {"args": ["payload"], "required": 1}


def test_unparseable_source():
    s = collect_symbols("def broken(:\n")
    assert s["unparseable"] is True


def test_repo_symbol_table_multiple_definitions(tmp_path):
    (tmp_path / "a.py").write_text("def go(x):\n    pass\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.py").write_text("def go(y):\n    pass\nclass Widget:\n    def spin(self):\n        pass\n")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "junk.py").write_text("def should_be_skipped():\n    pass\n")
    table = repo_symbol_table(tmp_path)
    assert table["functions"]["go"] == [{"args": ["x"], "required": 1}, {"args": ["y"], "required": 1}]
    assert table["classes"]["Widget"] == [["spin"]]
    assert table["files_parsed"] == 2
    # SKIP_DIRS 除外で junk は含まれない
    assert "should_be_skipped" not in table["functions"]
