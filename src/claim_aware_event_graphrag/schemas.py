from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


EventType = Literal[
    "military",
    "diplomatic",
    "economic",
    "maritime",
    "nuclear",
    "humanitarian",
    "political",
    "other",
]

ClaimTopic = Literal[
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

ClaimStance = Literal["assert", "deny", "uncertain", "report"]


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
    type: EventType
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
    topic: ClaimTopic
    stance: ClaimStance
    source_chunk_id: str

    @field_validator("claim_id", "event_id", "claimant", "text", "source_chunk_id")
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value


class TempEvent(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    temp_event_id: str
    chunk_id: str
    time: str | None = None
    type: EventType
    summary: str
    actors: list[str]
    location: str | None = None

    @field_validator("temp_event_id", "chunk_id", "summary")
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


class TempClaim(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    temp_claim_id: str
    temp_event_id: str
    chunk_id: str
    claimant: str
    text: str
    topic: ClaimTopic
    stance: ClaimStance
    source_chunk_id: str

    @field_validator(
        "temp_claim_id",
        "temp_event_id",
        "chunk_id",
        "claimant",
        "text",
        "source_chunk_id",
    )
    @classmethod
    def must_be_non_empty(cls, value: str) -> str:
        if value == "":
            raise ValueError("must not be empty")
        return value

    @model_validator(mode="after")
    def source_chunk_should_match_chunk(self) -> "TempClaim":
        if self.source_chunk_id != self.chunk_id:
            raise ValueError("source_chunk_id must equal chunk_id for TempClaim")
        return self


class ExtractionResult(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    temp_events: list[TempEvent]
    temp_claims: list[TempClaim]

    @model_validator(mode="after")
    def claims_must_reference_existing_temp_events(self) -> "ExtractionResult":
        event_ids = {event.temp_event_id for event in self.temp_events}
        for claim in self.temp_claims:
            if claim.temp_event_id not in event_ids:
                raise ValueError(
                    f"TempClaim {claim.temp_claim_id} references missing temp_event_id {claim.temp_event_id}"
                )
        return self
