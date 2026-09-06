"""compare — コードブロック内の定義とリポジトリ実装を比較し判定する（純関数）。

ステータス:
  ok              — ブロック内の全定義がリポジトリと一致
  signature_drift — シンボルは存在するが引数（またはメソッド構成）が一致しない
  missing         — シンボルがリポジトリに存在しない（リネーム・削除の疑い）
  unparseable     — ブロックが Python として構文解釈できない（疑似コード等）
  no_symbols      — 関数/クラス定義を含まないブロック（呼び出し例など）→ 判定対象外

引数比較の方針:
  README 例はデフォルト値付き引数を省略するのが普通なので、
  「全引数と完全一致」または「必須引数をすべて満たす先頭一致」を許す。
  （例: リポジトリが fetch(url, retries=3) ならドキュメントの fetch(url) は OK、
        fetch(url, retries) も OK、fetch(url, other) は drift）

見つからない場合のカテゴリ分け（元 issue の要件）:
  対応する関数/クラスがリポジトリから見つからない場合(リネーム・削除の可能性)
  は drift とは区別して missing として報告する。
"""


def _sig_match(block_args: list, repo_variants: list) -> bool:
    """ブロックの引数リストが、リポジトリ側のいずれかの定義と整合するか。"""
    for v in repo_variants:
        full, required = v["args"], v["required"]
        if block_args == full:
            return True
        if len(block_args) < len(full) and full[: len(block_args)] == block_args \
                and len(block_args) >= required:
            return True
    return False


def _format_sig(variant: dict) -> str:
    return "(" + ", ".join(variant["args"]) + ")"


def classify_block(block: dict, repo_table: dict) -> dict:
    """python コードブロック1個を判定する（純関数）。

    返り値: {status, findings: [{symbol, kind, status, detail}], ...}
    status は findings のうち最も重大なもの（missing > signature_drift > ok）。
    """
    from doc_drift.py_symbols import collect_symbols

    syms = collect_symbols(block["code"])
    if syms["unparseable"]:
        return {"status": "unparseable", "findings": [],
                "detail": "block is not valid Python (pseudo-code?)"}

    findings = []
    if not syms["functions"] and not syms["classes"]:
        return {"status": "no_symbols", "findings": [],
                "detail": "no function/class definitions in block"}

    # 関数: 存在確認 → 引数比較
    for name, entry in syms["functions"].items():
        block_args = entry["args"]
        if name not in repo_table["functions"]:
            findings.append({
                "symbol": name, "kind": "function", "status": "missing",
                "detail": f"function '{name}' not found in repository "
                          f"(renamed or deleted?) — block defines ({', '.join(block_args)})",
            })
            continue
        variants = repo_table["functions"][name]
        if _sig_match(block_args, variants):
            findings.append({"symbol": name, "kind": "function", "status": "ok",
                             "detail": f"matches {_format_sig(variants[0])}"})
        else:
            expected = " | ".join(_format_sig(v) for v in variants[:3])
            findings.append({
                "symbol": name, "kind": "function", "status": "signature_drift",
                "detail": f"block defines ({', '.join(block_args)}) but repository defines {expected}",
            })

    # クラス: 存在確認 → メソッド部分集合チェック
    for name, methods in syms["classes"].items():
        if name not in repo_table["classes"]:
            findings.append({
                "symbol": name, "kind": "class", "status": "missing",
                "detail": f"class '{name}' not found in repository (renamed or deleted?)",
            })
            continue
        variants = repo_table["classes"][name]
        # README 例は頻繁にメソッドを省略するため「部分集合なら OK」
        if any(set(methods) <= set(v) for v in variants):
            findings.append({"symbol": name, "kind": "class", "status": "ok",
                             "detail": "all documented methods exist"})
        else:
            missing = sorted(set(methods) - set(variants[0]))
            findings.append({
                "symbol": name, "kind": "class", "status": "signature_drift",
                "detail": f"documented methods not found on class '{name}': {', '.join(missing)}",
            })

    worst = "ok"
    for f in findings:
        if f["status"] == "missing":
            worst = "missing"
            break
        if f["status"] == "signature_drift":
            worst = "signature_drift"
    detail = "; ".join(f["detail"] for f in findings if f["status"] != "ok")
    return {"status": worst, "findings": findings, "detail": detail}
