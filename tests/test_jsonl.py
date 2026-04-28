from pathlib import Path

import pytest

from claim_aware_event_graphrag.jsonl import JsonlError, read_jsonl, write_jsonl


def test_write_and_read_jsonl_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "roundtrip.jsonl"
    rows = [{"a": 1}, {"b": "x"}]

    write_jsonl(path, rows)
    loaded = read_jsonl(path)

    assert loaded == rows


def test_read_jsonl_skips_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "blank_lines.jsonl"
    path.write_text('{"a": 1}\n\n  \n{"b": 2}\n', encoding="utf-8")

    loaded = read_jsonl(path)

    assert loaded == [{"a": 1}, {"b": 2}]


def test_read_jsonl_reports_line_number_for_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text('{"a": 1}\n{"b":\n', encoding="utf-8")

    with pytest.raises(JsonlError) as exc_info:
        read_jsonl(path)

    msg = str(exc_info.value)
    assert "line 2" in msg
    assert str(path) in msg
