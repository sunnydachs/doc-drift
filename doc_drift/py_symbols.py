"""py_symbols — Python ソースから関数/クラス定義を ast で収集する（純関数）。

正規表現ではなく ast を使う（docstring・文字列内の偽 match を避ける）。
比較対象は「引数名の並び」のみ。デフォルト値・型注釈・デコレータは
README 例では頻繁に省略されるため比較しない（ノイズ防止）。

SKIP_DIRS の注意（実データ e2e で判明）: docs_src/ や examples/ は
「ドキュメント化されたコードの本体」であることが多い（例: docs-first な
リポジトリ）ため、除外ディレクトリに入れないこと。除外すると
実際に存在するシンボルが missing と誤判定される。
"""
import ast
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__",
             "build", "dist", ".tox", ".mypy_cache", ".pytest_cache"}


def collect_symbols(py_source: str) -> dict:
    """1 ソースから定義シンボルを収集する（純関数）。

    返り値: {unparseable: bool,
             functions: {name: [arg_names]},
             classes: {name: [method_names]}}
    """
    try:
        tree = ast.parse(py_source)
    except SyntaxError:
        return {"unparseable": True, "functions": {}, "classes": {}}

    funcs, classes = {}, {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.posonlyargs + node.args.args]
            required = len(args) - len(node.args.defaults)
            funcs[node.name] = {"args": args, "required": max(0, required)}
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes[node.name] = methods
    return {"unparseable": False, "functions": funcs, "classes": classes}


def repo_symbol_table(root: Path) -> dict:
    """リポジトリ全体の Python シンボル表を作成する。

    同名の定義が複数ファイルに現れ得るため、値は定義リスト。
    返り値: {functions: {name: [[args], ...]}, classes: {name: [[methods], ...]},
             files_parsed: int, files_unparseable: int}
    """
    table = {"functions": {}, "classes": {}, "files_parsed": 0, "files_unparseable": 0}
    for p in sorted(Path(root).rglob("*.py")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            syms = collect_symbols(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if syms["unparseable"]:
            table["files_unparseable"] += 1
            continue
        table["files_parsed"] += 1
        for name, args in syms["functions"].items():
            table["functions"].setdefault(name, []).append(args)
        for name, methods in syms["classes"].items():
            table["classes"].setdefault(name, []).append(methods)
    return table
