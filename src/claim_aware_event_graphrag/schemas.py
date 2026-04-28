from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class Chunk(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    chunk_id: str
    doc_id: str
    source: str | None = None
    date: str | None = None
    text: str

    @field_validator("chunk_id", "doc_id", "text")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value


class Event(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_id: str
    time: str | None = None
    type: Literal[
        "military",
        "diplomatic",
        "economic",
        "maritime",
        "nuclear",
        "humanitarian",
        "political",
        "other",
    ]
    summary: str
    actors: list[str]
    location: str | None = None

    @field_validator("event_id", "summary")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value

    @field_validator("actors")
    @classmethod
    def actors_cannot_contain_empty_strings(cls, value: list[str]) -> list[str]:
        for actor in value:
            if actor.strip() == "":
                raise ValueError("actors must not contain empty strings")
        return value


class Claim(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    claim_id: str
    event_id: str
    claimant: str
    text: str
    topic: Literal[
        "responsibility",
        "target",
        "casualty",
        "damage",
        "economic_impact",
        "policy",
        "verification",
        "cause",
        "response",
        "other",
    ]
    stance: Literal["assert", "deny", "uncertain", "report"]
    source_chunk_id: str

    @field_validator("claim_id", "event_id", "claimant", "text", "source_chunk_id")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value
