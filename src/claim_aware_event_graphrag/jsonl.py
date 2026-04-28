from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import ValidationError

from .schemas import Chunk, Claim, Conflict, Event, GraphEdge, GraphNode, TempClaim, TempEvent


class JsonlError(ValueError):
    """Raised when JSONL content is malformed."""


T = TypeVar("T")


def read_jsonl(path: str | Path) -> list[dict]:
    file_path = Path(path)
    rows: list[dict] = []

    with file_path.open("r", encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise JsonlError(f"Invalid JSON in {file_path} at line {lineno}: {exc.msg}") from exc
            if not isinstance(data, dict):
                raise JsonlError(f"Invalid JSON object in {file_path} at line {lineno}: expected object")
            rows.append(data)

    return rows


def write_jsonl(path: str | Path, rows: list[dict]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as f:
        for row in rows:
            if not isinstance(row, dict):
                raise TypeError("write_jsonl expects rows to be a list[dict]")
            json_line = json.dumps(row, ensure_ascii=False)
            f.write(json_line + "\n")


def _load_models(path: str | Path, model_cls: type[T]) -> list[T]:
    file_path = Path(path)
    models: list[T] = []

    with file_path.open("r", encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise JsonlError(f"Invalid JSON in {file_path} at line {lineno}: {exc.msg}") from exc
            if not isinstance(data, dict):
                raise JsonlError(f"Invalid JSON object in {file_path} at line {lineno}: expected object")

            try:
                models.append(model_cls.model_validate(data))
            except ValidationError as exc:
                raise JsonlError(f"Schema validation failed in {file_path} at line {lineno}: {exc}") from exc

    return models


def load_chunks(path: str | Path) -> list[Chunk]:
    return _load_models(path, Chunk)


def load_events(path: str | Path) -> list[Event]:
    return _load_models(path, Event)


def load_claims(path: str | Path) -> list[Claim]:
    return _load_models(path, Claim)


def load_temp_events(path: str | Path) -> list[TempEvent]:
    return _load_models(path, TempEvent)


def load_temp_claims(path: str | Path) -> list[TempClaim]:
    return _load_models(path, TempClaim)



def load_conflicts(path: str | Path) -> list[Conflict]:
    return _load_models(path, Conflict)



def load_graph_nodes(path: str | Path) -> list[GraphNode]:
    return _load_models(path, GraphNode)


def load_graph_edges(path: str | Path) -> list[GraphEdge]:
    return _load_models(path, GraphEdge)
