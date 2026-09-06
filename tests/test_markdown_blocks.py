from doc_drift.markdown_blocks import extract_blocks, find_markdown_files


def test_extract_simple_block():
    md = "# Title\n\n```python\ndef foo():\n    pass\n```\n"
    blocks = extract_blocks(md, "README.md")
    assert len(blocks) == 1
    assert blocks[0]["lang"] == "python"
    assert blocks[0]["code"] == "def foo():\n    pass"
    assert blocks[0]["file"] == "README.md"
    assert blocks[0]["line"] == 3  # フェンスの開始行


def test_extract_multiple_and_untagged():
    md = "```python\na = 1\n```\ntext\n\n```\nplain untagged\n```\n"
    blocks = extract_blocks(md)
    assert [b["lang"] for b in blocks] == ["python", ""]
    assert blocks[1]["code"] == "plain untagged"


def test_tilde_fences_and_indent():
    md = "text\n\n  ~~~python\n  def bar():\n      pass\n  ~~~\n"
    blocks = extract_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["lang"] == "python"
    assert "def bar():" in blocks[0]["code"]


def test_nested_backticks_do_not_break():
    """コードブロック内に ``` を含む行があっても（インデントされ閉じフェンスが
    異なる種類の場合など）、開いたブロックは正しく継続する。"""
    md = "```python\ns = '```'\n```\nafter\n"
    blocks = extract_blocks(md)
    assert len(blocks) == 1
    assert "s = '```'" in blocks[0]["code"]


def test_unterminated_block_ignored():
    md = "```python\ndef broken(:\n"  # 閉じフェンス無し
    assert extract_blocks(md) == []


def test_find_markdown_files_skips_junk(tmp_path):
    (tmp_path / "README.md").write_text("# t")
    junk = tmp_path / "node_modules" / "x"
    junk.mkdir(parents=True)
    (junk / "note.md").write_text("junk")
    files = find_markdown_files(tmp_path)
    assert [f.name for f in files] == ["README.md"]
