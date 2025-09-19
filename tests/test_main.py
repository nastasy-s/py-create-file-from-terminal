# tests/test_main.py
import os
import re
import io
import builtins
import types

import pytest

from app.create_file import parse_args, ensure_dirs, append_block


def test_parse_args_dirs_only():
    dparts, fname = parse_args(["-d", "dir1", "dir2"])
    assert dparts == ["dir1", "dir2"]
    assert fname is None


def test_parse_args_file_only():
    dparts, fname = parse_args(["-f", "file.txt"])
    assert dparts == []
    assert fname == "file.txt"


def test_parse_args_dirs_and_file():
    dparts, fname = parse_args(["-d", "a", "b", "-f", "x.txt"])
    assert dparts == ["a", "b"]
    assert fname == "x.txt"


def test_parse_args_errors():
    with pytest.raises(SystemExit):
        parse_args([])  # no flags
    with pytest.raises(SystemExit):
        parse_args(["-d"])  # no dir after -d
    with pytest.raises(SystemExit):
        parse_args(["-f"])  # no file after -f
    with pytest.raises(SystemExit):
        parse_args(["-f", "a.txt", "-f", "b.txt"])  # duplicate -f
    with pytest.raises(SystemExit):
        parse_args(["--weird"])  # unknown flag


def test_ensure_dirs_creates_nested(tmp_path, monkeypatch):
    # work from tmp dir to avoid touching real CWD
    monkeypatch.chdir(tmp_path)
    base = ensure_dirs(["dir1", "dir2"])
    assert os.path.isdir(base)
    assert base.endswith(os.path.join("dir1", "dir2"))


def test_append_block_creates_and_appends(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    file_path = tmp_path / "file.txt"

    # 1st write
    append_block(str(file_path), ["Line1 content", "Line2 content", "Line3 content"])
    text1 = file_path.read_text(encoding="utf-8")
    # first line is timestamp
    first_line = text1.splitlines()[0]
    assert re.match(r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$", first_line)
    # numbered lines
    assert "1 Line1 content" in text1
    assert "2 Line2 content" in text1
    assert "3 Line3 content" in text1

    # 2nd write (append)
    append_block(str(file_path), ["Another line1", "Another line2"])
    text2 = file_path.read_text(encoding="utf-8")
    # There should be a blank line separating two blocks
    assert "\n\n" in text2
    blocks = text2.strip().split("\n\n")
    assert len(blocks) == 2

    # In the second block, numbering must restart from 1
    second_block = blocks[1].splitlines()
    assert re.match(r"\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$", second_block[0])
    assert second_block[1] == "1 Another line1"
    assert second_block[2] == "2 Another line2"


def test_append_block_empty_lines_creates_file_only(tmp_path, monkeypatch):
    """No lines => file should be created/touched but remain empty."""
    monkeypatch.chdir(tmp_path)
    p = tmp_path / "empty.txt"
    append_block(str(p), [])
    assert p.exists()
    assert p.read_text(encoding="utf-8") == ""
